from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from services.rag import query_rag

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/chat", response_class=HTMLResponse)
def chat_page(request: Request):
    """Chat interface page"""
    return templates.TemplateResponse("chat.html", {"request": request})

@router.get("/get-documents")
def get_documents():
    """Get available document collections"""
    try:
        from services.vector_store import VectorStore
        vector_store = VectorStore()
        documents = vector_store.get_available_documents()
        print(f"DEBUG: Found {len(documents)} documents: {documents}")
        return JSONResponse({"documents": documents})
    except Exception as e:
        print(f"DEBUG: Error getting documents: {str(e)}")
        return JSONResponse({"error": str(e), "documents": []})

@router.post("/chat")
async def chat_api(request: Request):
    """Chat API endpoint with RAG functionality"""
    try:
        form_data = await request.form()
        message = form_data.get("message", "")
        selected_document = form_data.get("selected_document", "")
        
        if not message.strip():
            return JSONResponse({
                "role": "assistant",
                "success": False,
                "answer": "Please provide a question.",
                "sources": [],
                "error": True
            }, status_code=400)

        # Use RAG pipeline to get answer with document filter
        doc_filter = selected_document if selected_document else None
        print(f"DEBUG: Chat request - message: {message}, selected_document: {selected_document}")
        result = query_rag(message, doc_filter)

        return JSONResponse({
            "role": "assistant",
            "success": True,
            "answer": result["answer"],
            "sources": result["sources"] if result["sources"] else [],
            "error": False
        })

    except Exception as e:
        return JSONResponse({
            "role": "assistant",
            "success": False,
            "answer": f"Error processing your question: {str(e)}",
            "sources": [],
            "error": True
        }, status_code=500)