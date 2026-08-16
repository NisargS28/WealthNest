from fastapi import Header, HTTPException
from typing import Optional

def get_auth_token(authorization: Optional[str] = Header(None)) -> Optional[str]:
    if not authorization:
        return None
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header format. Must be Bearer <token>")
        
    return authorization.split(" ")[1]
