from fastapi import APIRouter, HTTPException, Depends
from database import supabase
from .auth import get_current_user
from pydantic import BaseModel


router = APIRouter(
    tags=["chats"],
    prefix="/api/chats"
    )

class ChatCreate(BaseModel):
    title: str
    project_id: str
    

@router.post("/")
async def create_chats(
    chat: ChatCreate,
    clerk_id: str = Depends(get_current_user)
):
    try:
        result = supabase.table('chats').insert({
            "title": chat.title,
            "project_id": chat.project_id,
            "clerk_id": clerk_id
        }).execute()
        
        
        return{
            "message":"Chat created successfully",
            "data": result.data[0]
        }
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed create the chat: {str(e)}",
        )
    
@router.delete("/{chat_id}")
async def delete_chats(
    chat_id: str,
    clerk_id: str = Depends(get_current_user)
):
    try:
        result = supabase.table('chats').delete().eq("id",chat_id).eq("clerk_id",clerk_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404,detail="Chat not found or access denied")
        
        return{
            "message":"Chat deleted successfully",
            "data": result.data[0]
        }
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete the chat: {str(e)}",
        )