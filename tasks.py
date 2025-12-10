from celery import Celery
import os
from database import supabase
from services.s3_service import S3Service
from unstructured.partition.pdf import partition_pdf
from unstructured.partition.docx import partition_docx
from unstructured.partition.html import partition_html


celery_app = Celery(
    "document_processos",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
)

@celery_app.task
def processing_document(document_id):
    """
        Document processing
    """
    try:
        
        doc_result = supabase.table("project_documents").select("*").eq("id",document_id).execute()
        document = doc_result.data[0]
        
        # 1. Download and partition
        elemetns = download_and_partotion(
            document_id=document_id,
            document=document
        )
        
        tables = sum(1 for e in elemetns if e.category=='Table')
        images = sum(1 for e in elemetns if e.category=='Image')
        text_elements = sum(1 for e in elemetns if e.category in ['NarrativeText','Title','Text'])
        print(f'Extracted: {tables} talbes, {images} images, {text_elements} text elements')

        
        # 2. Chunk the element
        # 3. summarize the chunks
        # 4. Vectorization and storing
    except Exception as e:
        print(str(e))
    
def download_and_partotion(document_id: str,document: dict):
    """
        Download document from S3 / Crwal the URL and partition the elements
    """
    try:
        source_type = document.get("source_type","file")
        
        if source_type == "url":
            pass
        else:
            s3_key = document.get("s3_key")
            file_name = document.get('filename')
            file_type = file_name.split('.')[-1].lower()
            
            s3_client = S3Service()
            temp_file = s3_client.download_file_to_temp(
                document_id=document_id,
                file_key=s3_key,
                file_type=file_type
            )
            
            elements = partition_document(temp_file,file_type,source_type='file')
            return elements
        os.remove(temp_file)
    except Exception as e:
        print(str(e))

def partition_document(temp_file: str,file_type: str,source_type: str ='file'):
    '''partistioning the documents'''
    
    try:
        
        if source_type == "url":
            pass
        if file_type=='pdf':
           return partition_pdf(
                    filename=temp_file,  # Path to your PDF file
                    strategy="hi_res", # Use the most accurate (but slower) processing method of extraction
                    infer_table_structure=True, # Keep tables as structured HTML, not jumbled text
                    extract_image_block_types=["Image"], # Grab images found in the PDF
                    extract_image_block_to_payload=True # Store images as base64 data you can actually use
                )
    except Exception as e:
        print(str(e))   
    
    