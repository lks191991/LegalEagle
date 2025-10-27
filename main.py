from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(title="LegalEagle", description="AI-powered Legal Q&A Chatbot")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
from routes.upload_simple import router as upload_router
from routes.chat_simple import router as chat_router
from routes.pages import router as pages_router
from routes.admin_main import router as admin_router
from routes.auth import router as auth_router
from routes.user_pages import router as user_pages_router
from routes.payments import router as payments_router

app.include_router(upload_router)
app.include_router(chat_router)
app.include_router(pages_router)
app.include_router(admin_router)
app.include_router(auth_router)
app.include_router(user_pages_router)
app.include_router(payments_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8004)