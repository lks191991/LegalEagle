from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(title="LegalEagle", description="AI-powered Legal Q&A Chatbot")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
from routes.upload import router as upload_router
from routes.chat import router as chat_router

app.include_router(upload_router)
app.include_router(chat_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8002)