"""Helper utilities."""

from typing import Optional
from datetime import datetime, timedelta
import hashlib
import secrets


def generate_token(length: int = 32) -> str:
    """Generate a random token."""
    return secrets.token_urlsafe(length)


def generate_file_hash(content: bytes) -> str:
    """Generate hash for file content."""
    return hashlib.sha256(content).hexdigest()


def format_datetime(dt: Optional[datetime], format: str = "%Y-%m-%d %H:%M:%S") -> Optional[str]:
    """Format datetime to string."""
    if not dt:
        return None
    return dt.strftime(format)


def calculate_age_from_years(years: int) -> datetime:
    """Calculate birth date from age in years."""
    return datetime.now() - timedelta(days=years * 365)


def is_recent(dt: datetime, days: int = 7) -> bool:
    """Check if datetime is within recent days."""
    if not dt:
        return False
    return datetime.now() - dt <= timedelta(days=days)


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to max length with suffix."""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def build_file_url(base_url: str, file_path: str) -> str:
    """Build complete file URL."""
    return f"{base_url.rstrip('/')}/{file_path.lstrip('/')}"
