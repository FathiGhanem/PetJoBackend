"""Rate limiting configuration and utilities."""
from slowapi import Limiter
from slowapi.util import get_remote_address

# Create limiter instance
limiter = Limiter(key_func=get_remote_address)

# Rate limit configurations
RATE_LIMITS = {
    "default": "100/minute",
    "auth": "5/minute",  # Login/register endpoints
    "upload": "10/minute",  # File upload endpoints
    "search": "30/minute",  # Search endpoints
    "public": "200/minute",  # Public endpoints (higher limit)
}
