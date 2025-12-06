from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from routes import users



# Create a FastAPI app
app = FastAPI(
    title="RAG PROJECT",
    description="A simple example of how to use Supabase with FastAPI",
    version="0.1.0",
    contact={
        "name": "Karthik",
        "email": "karthik@example.com",
    }
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)

@app.get("/")
def read_root():
    return {"message": "Hello World"}

@app.get("/health")
def health_check():
    return {"message": "OK"}

# @app.post("/posts")
# async def get_posts():
#     try:
#         response = supabase.table("posts").select("*").order("created_at",desc=True).execute()
#         return response.data
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))



            
        
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
