from fastapi import APIRouter, Request, UploadFile, File, Cookie
from fastapi.responses import HTMLResponse, JSONResponse
from template_config import templates
import os
import tempfile
from datetime import datetime
from typing import Optional
from services.pdf_utils import process_uploaded_file
from services.vector_store import VectorStore
from db_operations import DatabaseOperations

router = APIRouter()

def get_template_context(request: Request, current_page: str, **kwargs):
    """Helper function to get common template context including settings"""
    from db_operations import DatabaseOperations
    
    try:
        settings = DatabaseOperations.get_settings_dict()
    except Exception as e:
        print(f"Settings error: {e}")
        settings = {}
    
    context = {
        "request": request,
        "current_page": current_page,
        "settings": settings
    }
    context.update(kwargs)
    return context

@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    """Home page"""
    return templates.TemplateResponse("home.html", get_template_context(request, "home"))

@router.get("/upload", response_class=HTMLResponse)
def upload_page(request: Request):
    """Upload page"""
    from routes.auth import verify_user_session
    from db_operations import DatabaseOperations
    user_session = request.cookies.get("user_session")
    user_data = verify_user_session(user_session)
    if not user_data:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/login", status_code=302)
    user_plan = DatabaseOperations.get_user_plan(int(user_data['user_id']))
    if not user_plan:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/plan", status_code=302)
    return templates.TemplateResponse("upload.html", get_template_context(request, "upload", user=user_data, user_plan=user_plan))

@router.get("/check-document")
def check_document(document_name: str, user_session: Optional[str] = Cookie(None)):
    """Check if document already exists for the current user"""
    try:
        # Check user authentication
        from routes.auth import verify_user_session
        user_data = verify_user_session(user_session)
        if not user_data:
            return JSONResponse({"error": "Authentication required"}, status_code=401)
        
        vector_store = VectorStore(user_id=int(user_data['user_id']))
        documents, total = vector_store.get_available_documents(limit=50)
        
        existing_doc = None
        for doc in documents:
            if doc['document_name'].lower() == document_name.lower():
                existing_doc = doc
                break
        
        if existing_doc:
            return JSONResponse({
                "exists": True,
                "document": existing_doc
            })
        else:
            return JSONResponse({"exists": False})
            
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@router.post("/upload")
async def upload_file(request: Request, file: UploadFile = File(...), user_session: Optional[str] = Cookie(None)):
    """Handle file upload and processing"""
    try:
        # Check user authentication
        from routes.auth import verify_user_session
        user_data = verify_user_session(user_session)
        if not user_data:
            return JSONResponse({"error": True, "result": "Please login to upload documents"}, status_code=401)
        
        # Check document upload limit
        limit_check = DatabaseOperations.check_document_limit(int(user_data['user_id']))
        if not limit_check['can_upload']:
            if 'message' in limit_check and 'No active plan' in limit_check['message']:
                error_message = "Please purchase a plan to upload documents. You don't have any active subscription plan."
            else:
                error_message = f"Document limit exceeded! You have used {limit_check['used']}/{limit_check['max']} documents. Please upgrade your plan to upload more documents."
            
            return JSONResponse({
                "error": True, 
                "result": error_message,
                "limit_exceeded": True,
                "limit_info": limit_check
            }, status_code=403)
        # Validate file type
        if file.content_type not in ["application/pdf", "text/plain"]:
            error_msg = "Unsupported file type. Please upload PDF or text files only."
            if request.headers.get("x-requested-with", "").lower() == "xmlhttprequest":
                return JSONResponse({"error": True, "result": error_msg}, status_code=400)
            return templates.TemplateResponse("upload.html", {"request": request, "error": error_msg})
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file.filename}") as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name
        
        try:
            # Process file and extract chunks
            chunks = process_uploaded_file(temp_path, file.content_type)
            
            if not chunks:
                raise Exception("No text content found in the uploaded file.")
            
            # Get current upload date
            current_upload_date = datetime.now().strftime("%d-%m-%Y")
            
            # Get form data
            form_data = await request.form()
            document_name = form_data.get("document_name", file.filename)
            document_tags = form_data.get("document_tags", "")
            document_date = form_data.get("document_date", "")
            overwrite = form_data.get("overwrite", "false") == "true"
            
            # Handle 'None' string or empty values - use current date as default
            if document_date in ["None", "null", "undefined", "", None]:
                document_date = current_upload_date
                
            # Created date is always current date (auto-generated)
            created_date = current_upload_date
            
            print(f"DEBUG: Upload form data - document_date: '{document_date}', created_date: '{created_date}', upload_date: '{current_upload_date}'")
            
            # Check if document exists (unless overwrite is confirmed)
            if not overwrite:
                vector_store_check = VectorStore(user_id=int(user_data['user_id']))
                existing_docs, total = vector_store_check.get_available_documents(limit=50)
                
                for existing_doc in existing_docs:
                    if existing_doc['document_name'].lower() == document_name.lower():
                        # Document exists, return conflict response
                        if request.headers.get("x-requested-with", "").lower() == "xmlhttprequest":
                            return JSONResponse({
                                "conflict": True,
                                "existing_document": existing_doc,
                                "message": f"Document '{document_name}' already exists. Do you want to overwrite it?"
                            })
            
            # Store in user-specific document collection
            vector_store = VectorStore(document_name=document_name, user_id=int(user_data['user_id']))
            num_chunks = vector_store.add_documents(chunks, file.filename, document_tags, 
                                                  document_date=document_date, 
                                                  created_date=created_date,
                                                  upload_date=current_upload_date)
            
            # Save document metadata to database
            from services.vector_store import collection_name_from_document
            collection_name = f"user_{user_data['user_id']}_{collection_name_from_document(document_name)}"
            
            DatabaseOperations.save_user_document(
                user_id=int(user_data['user_id']),
                filename=file.filename,
                original_filename=file.filename,
                document_name=document_name,
                file_size=len(content),
                file_type=file.content_type,
                collection_name=collection_name,
                tags=document_tags,
                document_date=document_date,
                created_date=created_date,
                chunk_count=num_chunks
            )
            
            # Save collection mapping for user
            DatabaseOperations.save_user_collection(
                user_id=int(user_data['user_id']),
                collection_name=collection_name,
                document_name=document_name
            )
            
            # Increment user's document usage count
            DatabaseOperations.increment_document_usage(int(user_data['user_id']))
            
            #print(f"DEBUG: Stored {num_chunks} chunks with document_date: '{document_date}'")
            
            # Prepare success message
            result_msg = f"Successfully processed {file.filename}\n"
            result_msg += f"Document Date: {document_date}\n"
            result_msg += f"Created Date: {created_date}\n"
            result_msg += f"Upload Date: {current_upload_date}\n"
            result_msg += f"Extracted {len(chunks)} chunks\n"
            result_msg += f"Stored {num_chunks} vectors in database\n\n"
            result_msg += "Sample chunks:\n"
            
            # Show first 3 chunks as preview
            for i, chunk in enumerate(chunks[:3]):
                result_msg += f"\nChunk {i+1} (Page {chunk.get('page', 'N/A')}):\n"
                result_msg += chunk['text'][:200] + "..." if len(chunk['text']) > 200 else chunk['text']
                result_msg += "\n" + "-" * 50
            
            # Return JSON for AJAX requests
            if request.headers.get("x-requested-with", "").lower() == "xmlhttprequest":
                return JSONResponse({
                    "success": True,
                    "result": result_msg,
                    "filename": file.filename,
                    "num_chunks": num_chunks
                })
            
            return templates.TemplateResponse("upload.html", {
                "request": request,
                "result": result_msg,
                "success": True
            })
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)
                
    except Exception as e:
        error_msg = f"Error processing file: {str(e)}"
        
        # Return JSON for AJAX requests
        if request.headers.get("x-requested-with", "").lower() == "xmlhttprequest":
            return JSONResponse({"error": True, "result": error_msg}, status_code=500)
        
        return templates.TemplateResponse("upload.html", {
            "request": request,
            "error": error_msg
        })