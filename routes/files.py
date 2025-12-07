from fastapi import APIRouter, HTTPException, Depends
from database import supabase
from .auth import get_current_user
from pydantic import BaseModel


router = APIRouter(
    tags=["files"],
    prefix="/api/projects"
    )


@router.get("/{project_id}/files")
async def get_projects_files(
    project_id: str,
    clerk_id: str = Depends(get_current_user)
):
    try:
        result = supabase.table('project_documents').select("*").eq("project_id",project_id).eq("clerk_id",clerk_id).order("created_at",desc=True).execute()
        
        
        return{
            "message":"Project files retrieved successfully",
            "data": result.data or []
        }
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get the project files: {str(e)}",
        )