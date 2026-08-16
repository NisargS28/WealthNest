import os
import httpx
from supabase import create_client, Client, ClientOptions

def get_supabase_client(token: str = None) -> Client:
    url: str = os.environ.get("NEXT_PUBLIC_SUPABASE_URL", "")
    key: str = os.environ.get("NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY", "")
    
    if not url or not key:
        raise ValueError("Missing Supabase credentials in environment. Ensure NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY are set.")
    
    # Configure custom httpx client with larger timeout to avoid auth request timeouts (default is 5s)
    httpx_client = httpx.Client(timeout=30.0)
    opts = ClientOptions(httpx_client=httpx_client)
    
    client: Client = create_client(url, key, options=opts)
    if token:
        # Set the JWT to act on behalf of the user, obeying RLS
        client.postgrest.auth(token)
    return client
