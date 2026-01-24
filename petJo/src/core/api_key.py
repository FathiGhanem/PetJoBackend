"""API Key authentication and request signing."""
import hashlib
import hmac
import secrets
from typing import Optional

from fastapi import Header, HTTPException, status

from core.config import settings


def generate_api_key() -> tuple[str, str]:
    """
    Generate a new API key and secret.
    
    Returns:
        Tuple of (api_key, api_secret)
    """
    api_key = f"pk_{secrets.token_urlsafe(32)}"
    api_secret = f"sk_{secrets.token_urlsafe(48)}"
    return api_key, api_secret


def compute_signature(method: str, path: str, timestamp: str, body: str, api_secret: str) -> str:
    """
    Compute HMAC signature for request.
    
    Args:
        method: HTTP method (GET, POST, etc.)
        path: Request path
        timestamp: Unix timestamp as string
        body: Request body (empty string for GET)
        api_secret: API secret key
        
    Returns:
        Hex signature string
    """
    # Create signature string
    message = f"{method}|{path}|{timestamp}|{body}"
    
    # Compute HMAC-SHA256
    signature = hmac.new(
        api_secret.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return signature


def verify_signature(
    method: str,
    path: str,
    timestamp: str,
    body: str,
    api_key: str,
    signature: str,
    max_age: int = 300  # 5 minutes
) -> bool:
    """
    Verify HMAC signature for request.
    
    Args:
        method: HTTP method
        path: Request path
        timestamp: Unix timestamp as string
        body: Request body
        api_key: API key
        signature: Signature to verify
        max_age: Maximum age of request in seconds
        
    Returns:
        True if signature is valid, False otherwise
    """
    import time
    
    # Check timestamp freshness (prevent replay attacks)
    try:
        request_time = int(timestamp)
        current_time = int(time.time())
        
        if abs(current_time - request_time) > max_age:
            return False
    except (ValueError, TypeError):
        return False
    
    # In production, look up api_secret from database using api_key
    # For now, this is a placeholder - you'd need to implement API key storage
    # api_secret = get_api_secret_from_db(api_key)
    
    # For demo purposes, return True if API key looks valid
    # In production, compute and compare signatures
    if not api_key.startswith("pk_"):
        return False
    
    # TODO: Implement actual signature verification when API key storage is ready
    # expected_signature = compute_signature(method, path, timestamp, body, api_secret)
    # return hmac.compare_digest(signature, expected_signature)
    
    return True


async def verify_api_key(
    x_api_key: Optional[str] = Header(None, description="API Key"),
    x_signature: Optional[str] = Header(None, description="Request signature"),
    x_timestamp: Optional[str] = Header(None, description="Unix timestamp"),
) -> Optional[str]:
    """
    Dependency to verify API key and optional signature.
    
    Returns:
        API key if valid, None otherwise
    """
    if not x_api_key:
        return None
    
    # Basic API key validation
    if not x_api_key.startswith("pk_"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key format"
        )
    
    # If signature and timestamp provided, verify them
    if x_signature and x_timestamp:
        # This would verify the full HMAC signature
        # For now, just validate the format
        if len(x_signature) != 64:  # SHA256 hex length
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid signature format"
            )
    
    # In production: verify API key exists in database and is active
    # For now, accept any properly formatted key
    return x_api_key


# Example usage in endpoints:
# @router.get("/protected")
# async def protected_endpoint(api_key: Optional[str] = Depends(verify_api_key)):
#     if not api_key:
#         raise HTTPException(status_code=401, detail="API key required")
#     # Process request...
