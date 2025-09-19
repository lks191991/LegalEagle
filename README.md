# LegalEagle 🦅

AI-powered legal document assistant using FastAPI, Qdrant, and RAG (Retrieval-Augmented Generation).

## Features

- **Document Upload**: Upload PDF or text files containing legal documents
- **Text Extraction**: Automatic text extraction and chunking using PyMuPDF
- **Vector Storage**: Store document embeddings in Qdrant vector database
- **Semantic Search**: Find relevant document sections using vector similarity
- **AI Chat**: Get intelligent answers powered by OpenAI GPT with source citations
- **Web Interface**: Clean, responsive web UI built with Bootstrap

## Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Environment Setup**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Configure Services**
   - Get Qdrant Cloud account at https://cloud.qdrant.io
   - Get OpenAI API key at https://platform.openai.com
   - Update `.env` with your credentials

4. **Run Application**
   ```bash
   python main.py
   ```
   
   Visit http://localhost:8000

## Project Structure

```
LegalEagle/
├── main.py                 # FastAPI application entry point
├── routes/
│   ├── upload.py          # File upload and processing
│   └── chat.py            # Chat API endpoints
├── services/
│   ├── pdf_utils.py       # PDF/text processing utilities
│   ├── vector_store.py    # Qdrant vector database operations
│   └── rag.py             # RAG pipeline implementation
├── templates/
│   ├── base.html          # Base template
│   ├── home.html          # Landing page
│   ├── upload.html        # File upload interface
│   ├── chat.html          # Chat interface
│   ├── header.html        # Navigation header
│   └── footer.html        # Footer
├── static/                # Static assets (CSS, JS, images)
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
└── README.md             # This file
```

## API Endpoints

### Upload
- `GET /upload` - Upload page
- `POST /upload` - Process uploaded files

### Chat
- `GET /chat` - Chat interface
- `POST /chat` - Submit questions and get AI responses

## Environment Variables

```env
# Qdrant Configuration
QDRANT_URL=https://your-cluster.cloud.qdrant.io:6333
QDRANT_API_KEY=your_qdrant_api_key
QDRANT_COLLECTION=legaleagle_docs

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key
LLM_MODEL=gpt-3.5-turbo
```

## How It Works

1. **Document Processing**: Upload PDF/text files → Extract text → Split into chunks
2. **Embedding Generation**: Convert text chunks to vectors using SentenceTransformer
3. **Vector Storage**: Store embeddings in Qdrant with metadata (page, filename)
4. **Query Processing**: Convert user questions to embeddings
5. **Retrieval**: Find most similar document chunks using vector search
6. **Generation**: Send context + question to OpenAI GPT for intelligent answers

## Technologies Used

- **FastAPI**: Modern Python web framework
- **Qdrant**: Vector database for semantic search
- **SentenceTransformers**: Text embedding generation
- **OpenAI GPT**: Large language model for answer generation
- **PyMuPDF**: PDF text extraction
- **Bootstrap**: Responsive web UI
- **Jinja2**: Template engine

## License

MIT License