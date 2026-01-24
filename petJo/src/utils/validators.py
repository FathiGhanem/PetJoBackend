"""Validation utilities."""

import re
from typing import Optional


def validate_phone_number(phone: Optional[str]) -> bool:
    """Validate phone number format."""
    if not phone:
        return True
    
    # Remove common separators
    cleaned = re.sub(r'[\s\-\(\)\.]+', '', phone)
    
    # Accept multiple formats:
    # - International: +1234567890 (10-15 digits with optional +)
    # - Local: 07XXXXXXXX, 01XXXXXXXX (starts with 0, 10-11 digits)
    # - Simple: 1234567890 (10-15 digits)
    patterns = [
        r'^\+?[1-9]\d{9,14}$',  # International format
        r'^0[1-9]\d{8,10}$',     # Local format starting with 0
    ]
    
    return any(re.match(pattern, cleaned) for pattern in patterns)


def validate_url(url: Optional[str]) -> bool:
    """Validate URL format."""
    if not url:
        return True
    
    pattern = r'^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$'
    return bool(re.match(pattern, url))


def sanitize_string(text: str, max_length: int = 1000) -> str:
    """Sanitize string input."""
    if not text:
        return ""
    
    # Remove excessive whitespace
    text = " ".join(text.split())
    
    # Truncate if too long
    if len(text) > max_length:
        text = text[:max_length]
    
    return text.strip()


def validate_age(age: Optional[int]) -> bool:
    """Validate pet age."""
    if age is None:
        return True
    return 0 <= age <= 50  # Reasonable age range for pets


def validate_coordinates(lat: Optional[float], lng: Optional[float]) -> bool:
    """Validate geographic coordinates."""
    if lat is None or lng is None:
        return True
    
    return -90 <= lat <= 90 and -180 <= lng <= 180
