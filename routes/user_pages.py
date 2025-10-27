from fastapi import APIRouter, Request, Cookie, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from template_config import templates
from typing import Optional
from routes.auth import verify_user_session
from db_operations import DatabaseOperations

router = APIRouter()
@router.get("/get-documents")
def get_documents(request: Request, user_session: Optional[str] = Cookie(None)):
    """Return user's documents in JSON format (for AJAX)"""
    user_data = verify_user_session(user_session)
    if not user_data:
        return JSONResponse({"error": "Authentication required"}, status_code=401)
    try:
        documents = DatabaseOperations.get_user_documents(int(user_data['user_id']))
        # Convert datetime fields to string for JSON serialization
        for doc in documents:
            for key, value in doc.items():
                if hasattr(value, 'isoformat'):
                    doc[key] = value.isoformat()
        return JSONResponse({"documents": documents})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@router.get("/profile", response_class=HTMLResponse)
def user_profile(request: Request, user_session: Optional[str] = Cookie(None)):
    """User profile page"""
    user_data = verify_user_session(user_session)
    if not user_data:
        return RedirectResponse(url="/login", status_code=302)
    
    # Get user plan but don't redirect if none exists - allow profile access
    user_plan = DatabaseOperations.get_user_plan(int(user_data['user_id']))
    
    # Get full user data with address fields
    full_user_data = DatabaseOperations.get_user_by_id(user_data['user_id'])
    if not full_user_data:
        return RedirectResponse(url="/login", status_code=302)
    
    # Get available plans for upgrade/purchase options
    available_plans = DatabaseOperations.get_all_plans()
    
    return templates.TemplateResponse("profile.html", {
        "request": request, 
        "user": full_user_data,
        "current_page": "profile",
        "user_plan": user_plan,
        "available_plans": available_plans
    })

@router.post("/update-profile", response_class=HTMLResponse)
def update_user_profile(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    mobile_number: str = Form(""),
    address_line1: str = Form(None),
    address_line2: str = Form(None),
    city: str = Form(None),
    state: str = Form(None),
    postal_code: str = Form(None),
    country: str = Form("India"),
    user_session: Optional[str] = Cookie(None)
):
    """Update user profile"""
    user_data = verify_user_session(user_session)
    if not user_data:
        return RedirectResponse(url="/login", status_code=302)
    
    # Clean mobile number (None if empty)
    mobile_number = mobile_number.strip() if mobile_number else None
    
    # Update basic profile information
    success1 = DatabaseOperations.update_user_profile(
        user_id=user_data['user_id'],
        name=name,
        email=email,
        mobile_number=mobile_number
    )
    
    # Update address information
    success2 = DatabaseOperations.update_user_address(
        user_id=user_data['user_id'],
        address_line1=address_line1,
        address_line2=address_line2,
        city=city,
        state=state,
        postal_code=postal_code,
        country=country
    )
    
    if success1 and success2:
        return RedirectResponse(url="/profile?updated=1", status_code=302)
    else:
        return RedirectResponse(url="/profile?error=1", status_code=302)

@router.get("/documents", response_class=HTMLResponse)
def user_documents(request: Request, user_session: Optional[str] = Cookie(None)):
    """User documents page"""
    user_data = verify_user_session(user_session)
    if not user_data:
        return RedirectResponse(url="/login", status_code=302)
    user_plan = DatabaseOperations.get_user_plan(int(user_data['user_id']))
    if not user_plan:
        return RedirectResponse(url="/plan?message=documents_access&feature=View Documents", status_code=302)
    # Get user's documents from database
    documents = DatabaseOperations.get_user_documents(int(user_data['user_id']))
    return templates.TemplateResponse("documents.html", {
        "request": request, 
        "user": user_data,
        "documents": documents,
        "user_plan": user_plan
    })

@router.get("/activity", response_class=HTMLResponse)
def user_activity(request: Request, user_session: Optional[str] = Cookie(None)):
    """User activity page"""
    user_data = verify_user_session(user_session)
    if not user_data:
        return RedirectResponse(url="/login", status_code=302)
    
    # TODO: Get user's activity from database
    activities = []  # Placeholder
    
    return templates.TemplateResponse("activity.html", {
        "request": request, 
        "user": user_data,
        "activities": activities
    })

@router.get("/plan", response_class=HTMLResponse)
def user_plan_dashboard(request: Request, user_session: Optional[str] = Cookie(None)):
    """User plan dashboard showing usage and limits"""
    user_data = verify_user_session(user_session)
    if not user_data:
        return RedirectResponse(url="/login", status_code=302)
    
    # Get user's current plan
    user_plan = DatabaseOperations.get_user_plan(int(user_data['user_id']))
    
    # Get available plans for upgrade
    available_plans = DatabaseOperations.get_all_plans()
    
    # Calculate usage percentages only if user has a plan
    doc_percentage = 0
    prompt_percentage = 0
    
    if user_plan:
        doc_percentage = (user_plan['used_documents'] / user_plan['max_documents'] * 100) if user_plan['max_documents'] > 0 else 0
        prompt_percentage = (user_plan['used_prompts'] / user_plan['max_prompts'] * 100) if user_plan['max_prompts'] > 0 else 0
    
    return templates.TemplateResponse("user_plan.html", {
        "request": request,
        "user": user_data,
        "user_plan": user_plan,  # This will be None if no plan purchased
        "available_plans": available_plans,
        "doc_percentage": doc_percentage,
        "prompt_percentage": prompt_percentage
    })

@router.get("/get-documents")
def get_user_documents_api(request: Request, user_session: Optional[str] = Cookie(None)):
    """Get user's documents as JSON for AJAX calls"""
    user_data = verify_user_session(user_session)
    if not user_data:
        return JSONResponse({"error": "Authentication required"}, status_code=401)
    
    try:
        # Get user documents from database
        documents = DatabaseOperations.get_user_documents(int(user_data['user_id']))
        
        # Format documents for frontend
        formatted_docs = []
        for doc in documents:
            # Handle datetime serialization
            upload_date = doc.get('upload_date', '')
            if hasattr(upload_date, 'strftime'):
                upload_date = upload_date.strftime('%d %b %Y')
            elif upload_date and isinstance(upload_date, str):
                upload_date = upload_date
            else:
                upload_date = 'Unknown'
                
            formatted_docs.append({
                "id": doc.get('id'),
                "document_name": doc.get('document_name', ''),
                "filename": doc.get('filename', ''),
                "upload_date": upload_date,
                "file_size": doc.get('file_size', 0),
                "file_type": doc.get('file_type', ''),
                "tags": doc.get('tags', ''),
                "chunk_count": doc.get('chunk_count', 0),
                "status": doc.get('status', 'processed')
            })
        
        return JSONResponse({"documents": formatted_docs})
        
    except Exception as e:
        print(f"Error getting documents: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)

@router.delete("/documents/{doc_id}")
def delete_user_document(request: Request, doc_id: int, user_session: Optional[str] = Cookie(None)):
    """Delete a user's document from both local DB and vector DB"""
    user_data = verify_user_session(user_session)
    if not user_data:
        return JSONResponse({"success": False, "error": "Authentication required"}, status_code=401)
    
    # Validate doc_id
    if doc_id <= 0:
        return JSONResponse({"success": False, "error": "Invalid document ID"}, status_code=400)
    
    user_id = int(user_data['user_id'])
    
    try:
        print(f"DEBUG: Attempting to delete document {doc_id} for user {user_id}")
        
        # Get document info first to ensure it exists and belongs to the user
        document = DatabaseOperations.get_user_document_by_id(user_id, doc_id)
        if not document:
            print(f"DEBUG: Document {doc_id} not found for user {user_id}")
            return JSONResponse({"success": False, "error": "Document not found or access denied"}, status_code=404)
        
        document_name = document.get('document_name', '')
        collection_name = document.get('collection_name', '')
        filename = document.get('filename', '')
        
        print(f"DEBUG: Found document: '{document_name}' (ID: {doc_id}, Collection: {collection_name}, File: {filename})")
        
        # Initialize tracking variables
        vector_deleted = False
        collection_deleted = False
        usage_decremented = False
        
        # Step 1: Delete from vector database first (safer to fail early)
        if document_name:
            try:
                from services.vector_store import VectorStore
                vector_store = VectorStore(user_id=user_id)
                vector_deleted = vector_store.delete_user_documents(document_name)
                print(f"DEBUG: Vector DB deletion for '{document_name}': {vector_deleted}")
            except Exception as ve:
                print(f"WARNING: Vector DB deletion failed for '{document_name}': {ve}")
                # Continue with local deletion even if vector deletion fails
        
        # Step 2: Delete collection mapping (if exists)
        if collection_name:
            try:
                collection_deleted = DatabaseOperations.delete_user_collection(user_id, collection_name)
                print(f"DEBUG: Collection mapping deletion for '{collection_name}': {collection_deleted}")
            except Exception as ce:
                print(f"WARNING: Collection mapping deletion failed for '{collection_name}': {ce}")
        
        # Step 3: Decrement document usage count
        try:
            usage_decremented = DatabaseOperations.decrement_document_usage(user_id)
            print(f"DEBUG: Document usage count decremented: {usage_decremented}")
        except Exception as de:
            print(f"WARNING: Usage count decrement failed: {de}")
        
        # Step 4: Delete from local database (do this last to maintain data integrity)
        db_success = DatabaseOperations.delete_user_document(user_id, doc_id)
        print(f"DEBUG: Local DB deletion result: {db_success}")
        
        if db_success:
            # Build success message with details
            message_parts = [f"Document '{document_name}' deleted successfully"]
            
            if vector_deleted:
                message_parts.append("vector data removed")
            else:
                message_parts.append("vector data removal may have failed")
                
            if collection_name and collection_deleted:
                message_parts.append("collection mapping removed")
                
            if usage_decremented:
                message_parts.append("usage count updated")
            
            success_message = message_parts[0] + " (" + ", ".join(message_parts[1:]) + ")"
            
            return JSONResponse({
                "success": True, 
                "message": success_message,
                "deleted_document": {
                    "id": doc_id,
                    "name": document_name,
                    "filename": filename
                }
            }, status_code=200)
        else:
            return JSONResponse(
                {
                    "success": False,
                    "error": f"Failed to delete document '{document_name}' from database"
                }, 
                status_code=500
            )
            
    except Exception as e:
        print(f"ERROR: Delete operation failed for document {doc_id}, user {user_id}: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            {"success": False, "error": f"Delete operation failed: {str(e)}"}, 
            status_code=500
        )

@router.get("/chat-history")
def get_chat_history(request: Request, session_id: str = None, user_session: Optional[str] = Cookie(None)):
    """Get user's chat history"""
    user_data = verify_user_session(user_session)
    if not user_data:
        return JSONResponse({"error": "Authentication required"}, status_code=401)
    
    try:
        history = DatabaseOperations.get_user_chat_history(int(user_data['user_id']), session_id)
        return JSONResponse({"history": history})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@router.get("/chat-sessions")
def get_chat_sessions(request: Request, user_session: Optional[str] = Cookie(None)):
    """Get user's chat sessions"""
    user_data = verify_user_session(user_session)
    if not user_data:
        return JSONResponse({"error": "Authentication required"}, status_code=401)
    
    try:
        sessions = DatabaseOperations.get_user_chat_sessions(int(user_data['user_id']))
        return JSONResponse({"sessions": sessions})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@router.post("/submit-contact", response_class=JSONResponse)
def submit_contact_form(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    message: str = Form(...)
):
    """Handle contact form submission"""
    try:
        # Save contact form data to database
        success = DatabaseOperations.save_contact_submission(
            name=name,
            email=email,
            phone=phone,
            message=message
        )
        
        if success:
            # Send email to admin
            try:
                send_contact_email_to_admin(name, email, phone, message)
                email_sent = True
            except Exception as email_error:
                print(f"Warning: Email notification failed: {email_error}")
                email_sent = False
            
            return JSONResponse({
                "success": True,
                "message": f"Thank you {name.split()[0]}! Your message has been received and saved.",
                "email_sent": email_sent
            }, status_code=200)
        else:
            return JSONResponse({
                "success": False,
                "error": "Failed to save your message. Please try again."
            }, status_code=500)
            
    except Exception as e:
        print(f"Error submitting contact form: {e}")
        return JSONResponse({
            "success": False,
            "error": "An error occurred while processing your request."
        }, status_code=500)

def send_contact_email_to_admin(name: str, email: str, phone: str, message: str):
    """Send email notification to admin about new contact submission"""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    import os
    
    # Email configuration (you can add these to your .env file)
    smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    admin_email = os.getenv('ADMIN_EMAIL', 'admin@legaleagle.com')
    smtp_username = os.getenv('SMTP_USERNAME', '')
    smtp_password = os.getenv('SMTP_PASSWORD', '')
    
    if not smtp_username or not smtp_password:
        print("Email credentials not configured. Skipping email notification.")
        return False
    
    # Create email content
    subject = f"New Contact Form Submission from {name}"
    
    body = f"""
    New contact form submission received:
    
    Name: {name}
    Email: {email}
    Phone: {phone}
    
    Message:
    {message}
    
    ---
    Submitted via LegalEagle Contact Form
    """
    
    # Create email
    msg = MIMEMultipart()
    msg['From'] = smtp_username
    msg['To'] = admin_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    
    # Send email
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_username, smtp_password)
        server.send_message(msg)
        server.quit()
        print(f"Email notification sent to admin: {admin_email}")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False