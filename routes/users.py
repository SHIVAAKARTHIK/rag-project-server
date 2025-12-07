from fastapi import APIRouter,HTTPException,Request
from pydantic import BaseModel
from database import supabase
from svix.webhooks import Webhook, WebhookVerificationError
import os 

router = APIRouter(
    tags=["user"],
)

# @router.post("/creat-user")
# async def clerk_user_creation(webhook_data: dict):
#     try:
#         event_type = webhook_data.get("type")
#         if event_type == "user.created":
#             user_data = webhook_data.get("data",{})
#             clerk_id = user_data.get("id")
#         if not clerk_id:
#             raise HTTPException(status_code=400,detail="No User ID in webhook")
            
        
#         response = supabase.table("users").insert({
#             "clerk_id": clerk_id
#         }).execute()
        
#         return {
#             "message": "User creted successfully",
#             "data": response.data[0]
#         }
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Webhook processing failed: {str(e)}")
    
@router.post("/api/webhook/clerk")
async def clerk_webhook(request: Request):
    try:
        # Get raw body and headers
        payload = await request.body()
        headers = {
            "svix-id": request.headers.get("svix-id"),
            "svix-timestamp": request.headers.get("svix-timestamp"),
            "svix-signature": request.headers.get("svix-signature"),
        }
        
        # Verify the webhook signature
        wh = Webhook(os.getenv("CLERK_WEBHOOK_SECRET"))
        try:
            event = wh.verify(payload, headers)
        except WebhookVerificationError:
            raise HTTPException(status_code=400, detail="Invalid webhook signature")
        
        event_type = event.get("type")
        data = event.get("data")
        
        print(f"Received event: {event_type}")
        
        if event_type == "user.created":
            response = supabase.table("users").insert({
                "clerk_id": data["id"],
            }).execute()
            print(f"User created: {data['id']}")
            
            return {
                "message": "User creted successfully",
                "data": response.data[0]
            }
            
        
        return {"message": f"Event {event_type} received but not processed"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Webhook processing failed: {str(e)}")