"""CSRF protection middleware."""
import secrets
from typing import Optional

from fastapi import HTTPException, Request, status
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from starlette.middleware.base import BaseHTTPMiddleware

from core.config import settings

# CSRF token serializer
csrf_serializer = URLSafeTimedSerializer(settings.SECRET_KEY, salt="csrf-token")

# Methods that require CSRF protection
CSRF_PROTECTED_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

# Paths that don't require CSRF (public endpoints, auth endpoints)
CSRF_EXEMPT_PATHS = {
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/api/v1/auth/refresh",
    "/api/v1/auth/reset-password",
    "/api/v1/public",
    "/health",
    "/",
    "/api/v1/docs",
    "/api/v1/openapi.json",
}


def generate_csrf_token() -> str:
    """Generate a new CSRF token."""
    token = secrets.token_urlsafe(32)
    # Sign the token with timestamp (expires in 1 hour)
    signed_token = csrf_serializer.dumps(token)
    return signed_token


def validate_csrf_token(token: str, max_age: int = 3600) -> bool:
    """
    Validate a CSRF token.
    
    Args:
        token: The signed CSRF token
        max_age: Maximum age of token in seconds (default: 1 hour)
        
    Returns:
        True if valid, False otherwise
    """
    try:
        csrf_serializer.loads(token, max_age=max_age)
        return True
    except (BadSignature, SignatureExpired):
        return False


class CSRFMiddleware(BaseHTTPMiddleware):
    """Middleware to handle CSRF protection for state-changing requests."""
    
    async def dispatch(self, request: Request, call_next):
        """Process the request and validate CSRF token if needed."""
        
        # Skip CSRF check for safe methods
        if request.method not in CSRF_PROTECTED_METHODS:
            response = await call_next(request)
            # Add CSRF token to response headers for GET requests
            if request.method == "GET":
                csrf_token = generate_csrf_token()
                response.headers["X-CSRF-Token"] = csrf_token
            return response
        
        # Skip CSRF check for exempt paths
        path = request.url.path
        if any(path.startswith(exempt_path) for exempt_path in CSRF_EXEMPT_PATHS):
            return await call_next(request)
        
        # For API endpoints with Bearer tokens, CSRF is less critical
        # But we still check if CSRF token is provided
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            # API with JWT - CSRF is optional but recommended
            csrf_token = request.headers.get("X-CSRF-Token")
            
            if csrf_token and not validate_csrf_token(csrf_token):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid or expired CSRF token"
                )
            
            # Continue even if no CSRF token (JWT provides protection)
            return await call_next(request)
        
        # For cookie-based auth or no auth, CSRF is mandatory
        csrf_token = request.headers.get("X-CSRF-Token")
        
        if not csrf_token:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF token missing. Include X-CSRF-Token header."
            )
        
        if not validate_csrf_token(csrf_token):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid or expired CSRF token"
            )
        
        return await call_next(request)
