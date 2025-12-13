from fastapi import APIRouter, HTTPException, Depends
from database import supabase
from .auth import get_current_user
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv


load_dotenv()

llm = ChatOpenAI(
    model="gpt-4-turbo",
    temperature=0,
    openai_api_base="https://openrouter.ai/api/v1",
    openai_api_key=os.getenv("OPENROUTER_API_KEY")
)

router = APIRouter(
    tags=["chats"],
    prefix="/api"
    )

class ChatCreate(BaseModel):
    title: str
    project_id: str
    

@router.post("/chats")
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
    
@router.delete("/chats/{chat_id}")
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
@router.get("/chats/{chat_id}")
async def get_chat(
    chat_id: str,
    clerk_id: str = Depends(get_current_user)
):
    try:
        # Get the chat and verify it belongs to the user AND has a project_id
        result = supabase.table('chats').select('*').eq('id', chat_id).eq('clerk_id', clerk_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Chat not found or access denied")
        
        chat = result.data[0]
        
        # Get messages for this chat
        messages_result = supabase.table('messages').select('*').eq('chat_id', chat_id).order('created_at', desc=False).execute()
        
        # Add messages to chat object
        chat['messages'] = messages_result.data or []
        
        return {
            "message": "Chat retrieved successfully",
            "data": chat
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get chat: {str(e)}")

class SendMessageRequest(BaseModel):
    content: str

@router.post("/projects/{project_id}/chats/{chat_id}/messages")
async def send_message(
    chat_id: str,
    request: SendMessageRequest,
    clerk_id: str = Depends(get_current_user)
):
    """
        User message → LLM → AI response
    """
    try:
        message = request.content
        
        print(f"💬 New message: {message[:50]}...")
        
        # 1. Save user message
        print(f"💾 Saving user message...")
        user_message_result = supabase.table('messages').insert({
            "chat_id": chat_id,
            "content": message,
            "role": "user",
            "clerk_id": clerk_id
        }).execute()
        
        user_message = user_message_result.data[0]
        print(f"✅ User message saved: {user_message['id']}")
        
        # 2. Call LLM with system prompt + user message
        print(f"🤖 Calling LLM...")
        messages = [
            SystemMessage(content="You are a helpful AI assistant. Provide clear, concise, and accurate responses."),
            HumanMessage(content=message)
        ]
        
        response = llm.invoke(messages)
        ai_response = response.content
        
        print(f"✅ LLM response received: {len(ai_response)} chars")
        
        # 3. Save AI message
        print(f"💾 Saving AI message...")
        ai_message_result = supabase.table('messages').insert({
            "chat_id": chat_id,
            "content": ai_response,
            "role": "assistant",
            "clerk_id": clerk_id,
            "citations": []
        }).execute()
        
        ai_message = ai_message_result.data[0]
        print(f"✅ AI message saved: {ai_message['id']}")
        
        # 4. Return data
        return {
            "message": "Messages sent successfully",
            "data": {
                "userMessage": user_message,
                "aiMessage": ai_message
            }
        }
        
    except Exception as e:
        print(f"❌ Error in send_message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
