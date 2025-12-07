from fastapi import APIRouter, HTTPException, Depends
from database import supabase
from .auth import get_current_user
from pydantic import BaseModel


router = APIRouter(
    tags=["projects"],
    prefix="/api/projects"
    )

class ProjectCreate(BaseModel):
    name: str
    description: str = ""
    

@router.get("/")
async def get_projects(current_user_clerk_id: str = Depends(get_current_user)): 

    """
    ! Logic Flow
    * 1. Get current user clerk_id
    * 2. Query projects table for projects related to the current user
    * 3. Return projects data
    """
    try:
        projects_query_result = (
            supabase.table("projects")
            .select("*")
            .eq("clerk_id", current_user_clerk_id)
            .execute()
        )

        return {
            "message": "Projects retrieved successfully",
            "data": projects_query_result.data or [],
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while fetching projects: {str(e)}",
        )
        
@router.post("/")
def create_project(project_data: ProjectCreate,clerk_id=Depends(get_current_user)):
    try:
        project_insert_data = {
            "name": project_data.name,
            "description": project_data.description,
            "clerk_id": clerk_id,
        }

        project_creation_result = (
            supabase.table("projects").insert(project_insert_data).execute()
        )

        if not project_creation_result.data:
            raise HTTPException(
                status_code=422,
                detail="Failed to create project - invalid data provided",
            )
            
        newly_created_project = project_creation_result.data[0]

        # Create default project settings for the new project
        project_settings_data = {
            "project_id": newly_created_project["id"],
            "embedding_model": "text-embedding-3-large",
            "rag_strategy": "basic",
            "agent_type": "agentic",
            "chunks_per_search": 10,
            "final_context_size": 5,
            "similarity_threshold": 0.3,
            "number_of_queries": 5,
            "reranking_enabled": True,
            "reranking_model": "reranker-english-v3.0",
            "vector_weight": 0.7,
            "keyword_weight": 0.3,
        }  
        
        project_settings_creation_result = (
            supabase.table("project_settings").insert(project_settings_data).execute()
        )
  
        if not project_settings_creation_result.data:
            # Rollback: Delete the project if settings creation fails
            supabase.table("projects").delete().eq(
                "id", newly_created_project["id"]
            ).execute()
            raise HTTPException(
                status_code=422,
                detail="Failed to create project settings - project creation rolled back",
            )

        return {
            "message": "Project created successfully",
            "data": newly_created_project,
        }
    except Exception as ex:
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while createin project: {str(ex)}",
        )
        
@router.delete("/{project_id}")
async def delete_project(
    project_id: str, current_user_clerk_id: str = Depends(get_current_user)
):
    """
    ! Logic Flow
    * 1. Get current user clerk_id
    * 2. Verify if the project exists and belongs to the current user
    * 3. Delete project - CASCADE will automatically delete all related data:
    * 4. Check if project deletion failed, then return error
    * 5. Return successfully deleted project data
    """
    try:
        # Verify if the project exists and belongs to the current user
        project_ownership_verification_result = (
            supabase.table("projects")
            .select("id")
            .eq("id", project_id)
            .eq("clerk_id", current_user_clerk_id)
            .execute()
        )

        if not project_ownership_verification_result.data:
            raise HTTPException(
                status_code=404,  # Not Found - project doesn't exist or doesn't belong to user
                detail="Project not found or you don't have permission to delete it",
            )

        # Delete project ~ "CASCADE" will automatically delete all related data: project_settings, project_documents, document_chunks, chats, messages, etc.
        project_deletion_result = (
            supabase.table("projects")
            .delete()
            .eq("id", project_id)
            .eq("clerk_id", current_user_clerk_id)
            .execute()
        )

        if not project_deletion_result.data:
            raise HTTPException(
                status_code=500,  # Internal Server Error - deletion failed unexpectedly
                detail="Failed to delete project - please try again",
            )

        successfully_deleted_project = project_deletion_result.data[0]

        return {
            "message": "Project deleted successfully",
            "data": successfully_deleted_project,
        }

    

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An internal server error occurred while deleting project: {str(e)}",
        )
        
@router.get("/{project_id}")
async def get_projects(
    project_id: str,
    clerk_id: str = Depends(get_current_user)
):
    try:
        result = supabase.table('projects').select("*").eq("id",project_id).eq("clerk_id",clerk_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404,detail="Project not found")
        
        return{
            "message":"Project retrieved successfully",
            "data": result.data[0]
        }
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get the project: {str(e)}",
        )

@router.get("/{project_id}/chats")
async def get_projects_chats(
    project_id: str,
    clerk_id: str = Depends(get_current_user)
):
    try:
        result = supabase.table('chats').select("*").eq("project_id",project_id).eq("clerk_id",clerk_id).order("created_at",desc=True).execute()
        
        return{
            "message":"Project retrieved successfully",
            "data": result.data or []
        }
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get the project : {str(e)}",
        )

@router.get("/{project_id}/settings")
async def get_projects_settings(
    project_id: str,
    clerk_id: str = Depends(get_current_user)
):
    try:
        result = supabase.table('project_settings').select("*").eq("project_id",project_id).execute()
        if not result.data:
            raise HTTPException(status_code=404,detail="Project settings not found")
        
        return{
            "message":"Project settings retrieved successfully",
            "data": result.data[0]
        }
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get the project settings : {str(e)}",
        )
        
