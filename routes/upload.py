from fastapi import APIRouter, Request, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import os
import tempfile
from services.pdf_utils import process_uploaded_file
from services.vector_store import VectorStore

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    """Home page"""
    return templates.TemplateResponse("home.html", {"request": request})

@router.get("/upload", response_class=HTMLResponse)
def upload_page(request: Request):
    """Upload page"""
    return templates.TemplateResponse("upload.html", {"request": request})

@router.post("/upload")
async def upload_file(request: Request, file: UploadFile = File(...)):
    """Handle file upload and processing"""
    try:
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
            
            # Store in document-specific vector database
            vector_store = VectorStore(document_name=file.filename)
            num_chunks = vector_store.add_documents(chunks, file.filename)
            
            # Prepare success message
            result_msg = f"Successfully processed {file.filename}\n"
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