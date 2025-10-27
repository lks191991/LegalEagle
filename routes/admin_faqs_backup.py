from fastapi import APIRouter, Request, HTTPException, De    @staticmethod
    def get_faq_by_id(faq_id):
        """Get FAQ by ID"""
        try:
            connection = get_db_connection()
            if not connection:
                return NoneForm, Cookie
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
from pydantic import BaseModel
from db_operations import DatabaseOperations
from database import get_db_connection
from .admin_auth import verify_admin_session
import mysql.connector

router = APIRouter()
templates = Jinja2Templates(directory="templates")

class FAQCreate(BaseModel):
    question: str
    answer: str
    category: str = "General"
    is_active: bool = True
    sort_order: int = 0

class FAQUpdate(BaseModel):
    question: str
    answer: str
    category: str
    is_active: bool
    sort_order: int

class FAQOperations:
    @staticmethod
    def get_all_faqs():
        """Get all FAQs"""
        try:
            connection = get_db_connection()
            if not connection:
                return []
            
            cursor = connection.cursor(dictionary=True)
            
            query = """
            SELECT f.*, u.username as created_by_name
            FROM faqs f
            LEFT JOIN users u ON f.created_by = u.id
            ORDER BY f.sort_order ASC, f.created_at DESC
            """
            
            cursor.execute(query)
            faqs = cursor.fetchall()
            
            cursor.close()
            connection.close()
            
            return faqs
            
        except Exception as e:
            print(f"Error getting FAQs: {e}")
            return []
    
    @staticmethod
    def get_faq_by_id(faq_id):
        """Get single FAQ by ID"""
        try:
            connection = DatabaseOperations.get_db_connection()
            if not connection:
                return None
            
            cursor = connection.cursor(dictionary=True)
            
            query = "SELECT * FROM faqs WHERE id = %s"
            cursor.execute(query, (faq_id,))
            faq = cursor.fetchone()
            
            cursor.close()
            connection.close()
            
            return faq
            
        except Exception as e:
            print(f"Error getting FAQ: {e}")
            return None
    
    @staticmethod
    def create_faq(question, answer, category, is_active=True, sort_order=0):
        """Create new FAQ"""
        try:
            connection = DatabaseOperations.get_db_connection()
            if not connection:
                return None
            
            cursor = connection.cursor()
            
            query = """
            INSERT INTO faqs (question, answer, category, is_active, sort_order)
            VALUES (%s, %s, %s, %s, %s)
            """
            
            cursor.execute(query, (question, answer, category, is_active, sort_order))
            faq_id = cursor.lastrowid
            
            connection.commit()
            cursor.close()
            connection.close()
            
            return faq_id
            
        except Exception as e:
            print(f"Error creating FAQ: {e}")
            return None
    
    @staticmethod
    def update_faq(faq_id, question, answer, category, is_active, sort_order):
        """Update existing FAQ"""
        try:
            connection = DatabaseOperations.get_db_connection()
            if not connection:
                return False
            
            cursor = connection.cursor()
            
            query = """
            UPDATE faqs 
            SET question = %s, answer = %s, category = %s, is_active = %s, sort_order = %s
            WHERE id = %s
            """
            
            cursor.execute(query, (question, answer, category, is_active, sort_order, faq_id))
            
            connection.commit()
            cursor.close()
            connection.close()
            
            return True
            
        except Exception as e:
            print(f"Error updating FAQ: {e}")
            return False
    
    @staticmethod
    def delete_faq(faq_id):
        """Delete FAQ"""
        try:
            connection = DatabaseOperations.get_db_connection()
            if not connection:
                return False
            
            cursor = connection.cursor()
            
            query = "DELETE FROM faqs WHERE id = %s"
            cursor.execute(query, (faq_id,))
            
            connection.commit()
            cursor.close()
            connection.close()
            
            return True
            
        except Exception as e:
            print(f"Error deleting FAQ: {e}")
            return False
    
    @staticmethod
    def get_categories():
        """Get all unique categories"""
        connection = DatabaseOperations.get_db_connection()
        if not connection:
            return []
        
        cursor = connection.cursor()
        
        query = "SELECT DISTINCT category FROM faqs ORDER BY category"
        cursor.execute(query)
        categories = [row[0] for row in cursor.fetchall()]
        
        cursor.close()
        connection.close()
        
        return categories

@router.get("/faqs", response_class=HTMLResponse)
async def admin_faqs(request: Request, admin_data: dict = Depends(verify_admin_session)):
    """Admin FAQ management page"""
    if not admin_data:
        return RedirectResponse(url="/admin/login", status_code=302)
    
    faqs = FAQOperations.get_all_faqs()
    categories = FAQOperations.get_categories()
    
    return templates.TemplateResponse("admin_faqs.html", {
        "request": request,
        "faqs": faqs,
        "categories": categories,
        "admin": admin_data
    })

@router.post("/faqs/create")
async def create_faq(request: Request, faq_data: FAQCreate, admin_data: dict = Depends(verify_admin_session)):
    """Create new FAQ"""
    if not admin_data:
        return JSONResponse(content={"success": False, "message": "Unauthorized"}, status_code=401)
    
    if not faq_data.question.strip() or not faq_data.answer.strip():
        return JSONResponse(content={"success": False, "message": "Question and answer are required"})
    
    faq_id = FAQOperations.create_faq(
        faq_data.question.strip(),
        faq_data.answer.strip(),
        faq_data.category.strip(),
        faq_data.is_active,
        faq_data.sort_order
    )
    
    if faq_id:
        return JSONResponse(content={"success": True, "message": "FAQ created successfully", "id": faq_id})
    else:
        return JSONResponse(content={"success": False, "message": "Failed to create FAQ"})

@router.post("/faqs/{faq_id}/edit")
async def edit_faq(faq_id: int, faq_data: FAQUpdate, admin_data: dict = Depends(verify_admin_session)):
    """Edit existing FAQ"""
    if not admin_data:
        return JSONResponse(content={"success": False, "message": "Unauthorized"}, status_code=401)
    
    if not faq_data.question.strip() or not faq_data.answer.strip():
        return JSONResponse(content={"success": False, "message": "Question and answer are required"})
    
    success = FAQOperations.update_faq(
        faq_id,
        faq_data.question.strip(),
        faq_data.answer.strip(),
        faq_data.category.strip(),
        faq_data.is_active,
        faq_data.sort_order
    )
    
    if success:
        return JSONResponse(content={"success": True, "message": "FAQ updated successfully"})
    else:
        return JSONResponse(content={"success": False, "message": "Failed to update FAQ"})

@router.post("/faqs/{faq_id}/delete")
async def delete_faq(faq_id: int, admin_data: dict = Depends(verify_admin_session)):
    """Delete FAQ"""
    if not admin_data:
        return JSONResponse(content={"success": False, "message": "Unauthorized"}, status_code=401)
    
    success = FAQOperations.delete_faq(faq_id)
    
    return JSONResponse(content={
        "success": success,
        "message": "FAQ deleted successfully" if success else "Failed to delete FAQ"
    })

@router.post("/faqs/{faq_id}/toggle")
async def toggle_faq_status(faq_id: int, admin_data: dict = Depends(verify_admin_session)):
    """Toggle FAQ active status"""
    if not admin_data:
        return JSONResponse(content={"success": False, "message": "Unauthorized"}, status_code=401)
    
    faq = FAQOperations.get_faq_by_id(faq_id)
    if not faq:
        return JSONResponse(content={"success": False, "message": "FAQ not found"})
    
    new_status = not faq['is_active']
    success = FAQOperations.update_faq(
        faq_id, faq['question'], faq['answer'], 
        faq['category'], new_status, faq['sort_order']
    )
    
    return JSONResponse(content={
        "success": success,
        "message": f'FAQ {"activated" if new_status else "deactivated"} successfully' if success else 'Failed to update FAQ',
        "is_active": new_status
    })