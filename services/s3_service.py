import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from botocore.config import Config
import os
import uuid

load_dotenv()

class S3Service:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION'),
            config=Config(
                s3={'addressing_style': 'virtual'},
                signature_version='s3v4'
            )
        )
        self.bucket_name = os.getenv('S3_BUCKET_NAME')
       

    def generate_upload_url(self, file_name: str, file_type: str, project_id: str, expires_in: int = 3600) -> dict:
        """
        Generate a presigned URL for uploading a file.
        
        Args:
            file_name: Original file name
            file_type: MIME type (e.g., 'application/pdf', 'image/png')
            expires_in: URL expiration time in seconds (default: 1 hour)
        
        Returns:
            dict with upload_url and file_key
        """
        try:
            # Generate unique file key
            file_extension = file_name.split('.')[-1]
            file_key = f"projects/{project_id}/documents/{uuid.uuid4()}.{file_extension}"
            
            presigned_url = self.s3_client.generate_presigned_url(
                'put_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': file_key,
                    'ContentType': file_type
                },
                ExpiresIn=expires_in
            )
            return presigned_url,file_key
           
        except ClientError as e:
            raise Exception(f"Failed to generate upload URL: {str(e)}")

    def generate_download_url(self, file_key: str, expires_in: int = 3600) -> str:
        """
        Generate a presigned URL for downloading a file.
        
        Args:
            file_key: S3 object key
            expires_in: URL expiration time in seconds
        
        Returns:
            Presigned download URL
        """
        try:
            presigned_url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': file_key
                },
                ExpiresIn=expires_in
            )
            return presigned_url
        except ClientError as e:
            raise Exception(f"Failed to generate download URL: {str(e)}")

    def delete_file(self, file_key: str) -> bool:
        """Delete a file from S3."""
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=file_key
            )
            return True
        except ClientError as e:
            raise Exception(f"Failed to delete file: {str(e)}")

# Initialize service
s3_service = S3Service()