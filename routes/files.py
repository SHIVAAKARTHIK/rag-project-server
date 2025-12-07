from fastapi import APIRouter, HTTPException, Depends
from database import supabase
from .auth import get_current_user
from pydantic import BaseModel,Field
from services.s3_service import S3Service


router = APIRouter(
    tags=["files"],
    prefix="/api/projects"
    )

class FileUploadRequest(BaseModel):
    filename: str
    file_size: int
    file_type: str

class UrlRequest(BaseModel):
    url: str = Field(..., description="The URL to process")

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
        
@router.post("/{project_id}/files/upload-url")
async def get_upload_url(
    project_id: str,
    file_request: FileUploadRequest,
    clerk_id: str = Depends(get_current_user)
):
    try:
        project_result = supabase.table("projects").select("id").eq("id",project_id).eq("clerk_id",clerk_id).execute()
        
        if not project_result.data:
            raise HTTPException(status_code=400,details="Project not found or access denied")
        
        s3_client = S3Service()
        presigned_url,s3_key = s3_client.generate_upload_url(
            file_name=file_request.filename,
            file_type=file_request.file_type,
            project_id=project_id
        )
        
        document_result = supabase.table("project_documents").insert({
            "project_id":project_id,
            "filename":file_request.filename,
            "s3_key":s3_key,
            "file_size":file_request.file_size,
            "file_type":file_request.file_type,
            "processing_status": 'uploading',
            "clerk_id":clerk_id
        }).execute()
        
        if not document_result.data:
            raise HTTPException(status_code=500,details="Failed to create document record")
        
        return {
            "message":"Upload URL generated successfully",
            "data":{
                "upload_url":presigned_url,
                "s3_key":s3_key,
                "document":document_result.data[0]
            }
        }
        
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate presigned url: {str(e)}",
        )

@router.post("/{project_id}/files/confirm")
async def confirm_file_upload(
    project_id: str,
    confirm_request: dict,
    clerk_id: str = Depends(get_current_user)
):
    try:
        s3_key = confirm_request.get("s3_key")
        
        if not s3_key:
            raise HTTPException(status_code=400,details="s3_key is required")
        
        result = supabase.table("project_documents").update({
            "processing_status": "queued"
        }).eq("s3_key",s3_key).eq("project_id",project_id).eq("clerk_id",clerk_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404,details="Document not found or access denied")
        
        # Start the background preprocessing of the current file
        
        # retrun json
        return{
            "message": "Upload confirmed, processing started with Celery",
            "data": result.data[0]
        }
        
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to confirm upload: {str(e)}",
        )
        
@router.post("/{project_id}/urls")
async def process_url(
    project_id: str,
    url: UrlRequest,
    current_user_clerk_id: str = Depends(get_current_user),
):
    """
    ! Logic Flow:
    * 1. Validate URL
    * 2. Add website URL to database
    * 3. Start background pre-processing of this URL
    * 4. Return successfully processed URL data
    """
    try:
        # Validate URL
        url = url.url
        if url.startswith("http://") or url.startswith("https://"):
            url = url
        else:
            url = f"https://{url}"

        # if not validate_url(url):
        #     raise HTTPException(
        #         status_code=400,
        #         detail="Invalid URL",
        #     )

        # Add website Url to database
        document_creation_result = (
            supabase.table("project_documents")
            .insert(
                {
                    "project_id": project_id,
                    "filename": url,
                    "s3_key": "",
                    "file_size": 0,
                    "file_type": "text/html",
                    "processing_status": "queued",
                    "clerk_id": current_user_clerk_id,
                    "source_type": "url",
                    "source_url": url,
                }
            )
            .execute()
        )

        if not document_creation_result.data:
            raise HTTPException(
                status_code=422,
                detail="Failed to create project document with URL Record - invalid data provided",
            )

        # ! Celery - Starts Background Processing - RAG Ingestion Task
        # document_id = document_creation_result.data[0]["id"]
        # task_result = perform_rag_ingestion_task.delay(document_id)
        # task_id = task_result.id

        # document_update_result = (
        #     supabase.table("project_documents")
        #     .update(
        #         {
        #             "task_id": task_id,
        #         }
        #     )
        #     .eq("id", document_id)
        #     .execute()
        # )

        # if not document_update_result.data:
        #     raise HTTPException(
        #         status_code=422,
        #         detail="Failed to update project document record with task_id",
        #     )

        return {
            "message": "Website URL added to database successfully And Started Background Pre-Processing of this URL",
            "data": document_creation_result.data[0],
        }

    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An internal server error occurred while processing urls for {project_id}: {str(e)}",
        )

@router.delete("/{project_id}/files/{file_id}")
async def delete_project_document(
    project_id: str,
    file_id: str,
    current_user_clerk_id: str = Depends(get_current_user),
):
    """
    ! Logic Flow:
    * 1. Verify document exists and belongs to the current user and take complete project document record
    * 2. Delete file from S3 (only for actual files, not for URLs)
    * 3. Delete document from database
    * 4. Return successfully deleted document data
    """
    try:
        # Verify document exists and belongs to the current user and Take complete project document record
        document_ownership_verification_result = (
            supabase.table("project_documents")
            .select("*")
            .eq("id", file_id)
            .eq("project_id", project_id)
            .eq("clerk_id", current_user_clerk_id)
            .execute()
        )

        if not document_ownership_verification_result.data:
            raise HTTPException(
                status_code=404,
                detail="Document not found or you don't have permission to delete this document",
            )

        # Delete file from S3 (only for actual files, not for URLs)
        s3_key = document_ownership_verification_result.data[0]["s3_key"]
        if s3_key:
            s3_client = S3Service()
            s3_client.delete_file(file_key=s3_key)

        # Delete document from database
        document_deletion_result = (
            supabase.table("project_documents")
            .delete()
            .eq("id", file_id)
            .eq("project_id", project_id)
            .eq("clerk_id", current_user_clerk_id)
            .execute()
        )

        if not document_deletion_result.data:
            raise HTTPException(
                status_code=404,
                detail="Failed to delete document",
            )

        return {
            "message": "Document deleted successfully",
            "data": document_deletion_result.data[0],
        }

    except HTTPException as e:
        raise e

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"An internal server error occurred while deleting project document {file_id} for {project_id}: {str(e)}",
        )

