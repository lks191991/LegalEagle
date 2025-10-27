from fastapi import APIRouter, Request, HTTPException, Depends, Form, Cookie, Query
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
            SELECT f.*, u.name as created_by_name
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
        """Get FAQ by ID"""
        try:
            connection = get_db_connection()
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
            print(f"Error getting FAQ by ID: {e}")
            return None
    
    @staticmethod
    def create_faq(faq_data, created_by):
        """Create new FAQ"""
        try:
            connection = get_db_connection()
            if not connection:
                return False
            
            cursor = connection.cursor()
            
            query = """
            INSERT INTO faqs (question, answer, category, is_active, sort_order, created_by)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            
            cursor.execute(query, (
                faq_data.question,
                faq_data.answer,
                faq_data.category,
                faq_data.is_active,
                faq_data.sort_order,
                created_by
            ))
            
            connection.commit()
            cursor.close()
            connection.close()
            
            return True
            
        except Exception as e:
            print(f"Error creating FAQ: {e}")
            return False
    
    @staticmethod
    def update_faq(faq_id, faq_data):
        """Update FAQ"""
        try:
            connection = get_db_connection()
            if not connection:
                return False
            
            cursor = connection.cursor()
            
            query = """
            UPDATE faqs 
            SET question = %s, answer = %s, category = %s, 
                is_active = %s, sort_order = %s, updated_at = NOW()
            WHERE id = %s
            """
            
            cursor.execute(query, (
                faq_data.question,
                faq_data.answer,
                faq_data.category,
                faq_data.is_active,
                faq_data.sort_order,
                faq_id
            ))
            
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
            connection = get_db_connection()
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
    def toggle_faq_status(faq_id):
        """Toggle FAQ active status"""
        try:
            connection = get_db_connection()
            if not connection:
                return False
            
            cursor = connection.cursor()
            
            # First get current status
            query = "SELECT is_active FROM faqs WHERE id = %s"
            cursor.execute(query, (faq_id,))
            result = cursor.fetchone()
            
            if not result:
                return False
            
            # Toggle status
            new_status = not result[0]
            update_query = "UPDATE faqs SET is_active = %s WHERE id = %s"
            cursor.execute(update_query, (new_status, faq_id))
            
            connection.commit()
            cursor.close()
            connection.close()
            
            return True
            
        except Exception as e:
            print(f"Error toggling FAQ status: {e}")
            return False

# Admin FAQ Management Routes
@router.get("/faqs", response_class=HTMLResponse)
async def admin_faqs(request: Request, 
                     category: Optional[str] = Query(None),
                     question: Optional[str] = Query(None), 
                     status: Optional[str] = Query(None),
                     admin_data: dict = Depends(verify_admin_session)):
    """Admin FAQ management page"""
    try:
        # Get all FAQs
        all_faqs = FAQOperations.get_all_faqs()
        
        # Apply filters
        filtered_faqs = all_faqs
        
        # Filter by category
        if category and category.strip():
            filtered_faqs = [faq for faq in filtered_faqs if faq['category'] == category]
        
        # Filter by question (search in question text)
        if question and question.strip():
            question_lower = question.lower()
            filtered_faqs = [faq for faq in filtered_faqs if question_lower in faq['question'].lower()]
        
        # Filter by status
        if status and status.strip():
            if status == 'active':
                filtered_faqs = [faq for faq in filtered_faqs if faq['is_active']]
            elif status == 'inactive':
                filtered_faqs = [faq for faq in filtered_faqs if not faq['is_active']]
        
        # Get unique categories for dropdown (excluding None and empty strings)
        categories = list(set(faq['category'] for faq in all_faqs if faq['category'] and faq['category'].strip()))
        categories.sort()
        
        return templates.TemplateResponse("admin_faqs.html", {
            "request": request,
            "faqs": filtered_faqs,
            "categories": categories,
            "admin_data": admin_data,
            "category_filter": category,
            "question_filter": question,
            "status_filter": status
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/faqs")
async def create_faq(request: Request, faq_data: FAQCreate, admin_data: dict = Depends(verify_admin_session)):
    """Create new FAQ"""
    try:
        success = FAQOperations.create_faq(faq_data, admin_data['id'])
        
        if success:
            return JSONResponse({
                "status": "success",
                "message": "FAQ created successfully"
            })
        else:
            return JSONResponse({
                "status": "error",
                "message": "Failed to create FAQ"
            }, status_code=500)
            
    except Exception as e:
        return JSONResponse({
            "status": "error",
            "message": str(e)
        }, status_code=500)

@router.put("/faqs/{faq_id}")
async def edit_faq(faq_id: int, faq_data: FAQUpdate, admin_data: dict = Depends(verify_admin_session)):
    """Update FAQ"""
    try:
        success = FAQOperations.update_faq(faq_id, faq_data)
        
        if success:
            return JSONResponse({
                "status": "success",
                "message": "FAQ updated successfully"
            })
        else:
            return JSONResponse({
                "status": "error", 
                "message": "Failed to update FAQ"
            }, status_code=500)
            
    except Exception as e:
        return JSONResponse({
            "status": "error",
            "message": str(e)
        }, status_code=500)

@router.delete("/faqs/{faq_id}")
async def delete_faq(faq_id: int, admin_data: dict = Depends(verify_admin_session)):
    """Delete FAQ"""
    try:
        success = FAQOperations.delete_faq(faq_id)
        
        if success:
            return JSONResponse({
                "status": "success",
                "message": "FAQ deleted successfully"
            })
        else:
            return JSONResponse({
                "status": "error",
                "message": "Failed to delete FAQ"
            }, status_code=500)
            
    except Exception as e:
        return JSONResponse({
            "status": "error",
            "message": str(e)
        }, status_code=500)

@router.patch("/faqs/{faq_id}/toggle")
async def toggle_faq_status(faq_id: int, admin_data: dict = Depends(verify_admin_session)):
    """Toggle FAQ status"""
    try:
        success = FAQOperations.toggle_faq_status(faq_id)
        
        if success:
            return JSONResponse({
                "status": "success",
                "message": "FAQ status updated successfully"
            })
        else:
            return JSONResponse({
                "status": "error",
                "message": "Failed to update FAQ status"
            }, status_code=500)
            
    except Exception as e:
        return JSONResponse({
            "status": "error",
            "message": str(e)
        }, status_code=500)