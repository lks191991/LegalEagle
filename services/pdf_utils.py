import fitz  # PyMuPDF
import os

def extract_text_from_pdf(file_path):
    """Extract text from PDF file and split into chunks"""
    chunks = []
    
    try:
        doc = fitz.open(file_path)
        
        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)
            text = page.get_text()
            
            # Split text into paragraphs (chunks)
            paragraphs = text.split('\n\n')
            
            for para in paragraphs:
                para = para.strip()
                if para and len(para) > 50:  # Only keep substantial paragraphs
                    chunks.append({
                        "text": para,
                        "page": page_num + 1
                    })
        
        doc.close()
        return chunks
        
    except Exception as e:
        raise Exception(f"Error extracting text from PDF: {str(e)}")

def extract_text_from_txt(file_path):
    """Extract text from plain text file and split into chunks"""
    chunks = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
            
        # Split text into paragraphs (chunks)
        paragraphs = text.split('\n\n')
        
        for para in paragraphs:
            para = para.strip()
            if para and len(para) > 50:  # Only keep substantial paragraphs
                chunks.append({
                    "text": para,
                    "page": None  # No page numbers for text files
                })
        
        return chunks
        
    except Exception as e:
        raise Exception(f"Error extracting text from file: {str(e)}")

def process_uploaded_file(file_path, content_type):
    """Process uploaded file based on content type"""
    if content_type == "application/pdf":
        return extract_text_from_pdf(file_path)
    elif content_type == "text/plain":
        return extract_text_from_txt(file_path)
    else:
        raise Exception("Unsupported file type. Please upload PDF or text files only.")