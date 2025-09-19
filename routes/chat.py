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

@router.post("/chat")
async def chat_api(message: str = Form(...)):
    """Chat API endpoint with RAG functionality"""
    try:
        if not message.strip():
            return JSONResponse({
                "role": "assistant",
                "success": False,
                "answer": "Please provide a question.",
                "sources": [],
                "error": True
            }, status_code=400)

        # Use RAG pipeline to get answer
        result = query_rag(message)

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