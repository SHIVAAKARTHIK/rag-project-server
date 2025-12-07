from dotenv import load_dotenv
import os
from supabase import create_client, Client

load_dotenv()

supabase_url = os.getenv("SUPABASE_API_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_KEY")


if not supabase_url or not supabase_key:
    raise ValueError("SUPABASE_URL or SUPABASE_SERVICE_KEY is not set")

supabase: Client = create_client(supabase_url, supabase_key)
