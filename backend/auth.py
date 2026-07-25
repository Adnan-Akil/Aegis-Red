"""
backend/auth.py

Supabase JWT verification dependency for FastAPI backend routes.
Validates the 'Authorization: Bearer <token>' header against Supabase Auth.
"""
import os
import logging
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client

logger = logging.getLogger(__name__)

# HTTP Bearer scheme for token extraction
security = HTTPBearer(auto_error=False)

# Cached Supabase auth client
_supabase_client: Optional[Client] = None

def get_supabase_client() -> Client:
    global _supabase_client
    if _supabase_client is None:
        supabase_url = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
        supabase_key = (
            os.getenv("SUPABASE_SERVICE_KEY") or 
            os.getenv("SUPABASE_SERVICE_ROLE_KEY") or 
            os.getenv("SUPABASE_ANON_KEY") or 
            os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
        )
        if not supabase_url or not supabase_key:
            raise RuntimeError("Supabase URL and Key must be set in environment for JWT verification.")
        _supabase_client = create_client(supabase_url, supabase_key)
    return _supabase_client

async def verify_supabase_jwt(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Dict[str, Any]:
    """
    Verifies Supabase JWT token passed via Bearer authorization header.
    Returns user dictionary containing authenticated 'id' (UUID) and email.
    Raises HTTP 401 if missing, invalid, or expired.
    """
    # Allow bypassing authentication in explicit local dev testing if AUTH_DISABLED=true
    if os.getenv("AUTH_DISABLED", "false").lower() == "true":
        return {
            "id": "00000000-0000-0000-0000-000000000000",
            "email": "dev-local@aegis.red",
            "role": "authenticated"
        }

    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization Bearer header.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    try:
        supabase = get_supabase_client()
        # Verify token with Supabase Auth service
        user_response = supabase.auth.get_user(token)
        if not user_response or not user_response.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired authentication token.",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user = user_response.user
        return {
            "id": str(user.id),
            "email": user.email,
            "role": getattr(user, "role", "authenticated")
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"JWT Verification failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
