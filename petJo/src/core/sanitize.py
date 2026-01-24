"""Input sanitization utilities to prevent XSS attacks."""
import bleach
from typing import Optional

# Allowed HTML tags and attributes (very restrictive for security)
ALLOWED_TAGS = []  # No HTML tags allowed by default
ALLOWED_ATTRIBUTES = {}

# For rich text fields (if needed in future)
RICH_TEXT_TAGS = ['p', 'br', 'strong', 'em', 'u', 'a']
RICH_TEXT_ATTRIBUTES = {'a': ['href', 'title']}


def sanitize_text(text: Optional[str], allow_rich_text: bool = False) -> Optional[str]:
    """
    Sanitize text input to prevent XSS attacks.
    
    Args:
        text: The text to sanitize
        allow_rich_text: If True, allows basic HTML tags (p, br, strong, em, u, a)
        
    Returns:
        Sanitized text with HTML stripped or escaped
    """
    if text is None:
        return None
    
    if not isinstance(text, str):
        return str(text)
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    if not text:
        return text
    
    # Choose allowed tags based on rich text flag
    tags = RICH_TEXT_TAGS if allow_rich_text else ALLOWED_TAGS
    attributes = RICH_TEXT_ATTRIBUTES if allow_rich_text else ALLOWED_ATTRIBUTES
    
    # Clean the text
    cleaned = bleach.clean(
        text,
        tags=tags,
        attributes=attributes,
        strip=True  # Strip disallowed tags instead of escaping
    )
    
    return cleaned


def sanitize_dict(data: dict, fields: list[str], allow_rich_text: bool = False) -> dict:
    """
    Sanitize specific fields in a dictionary.
    
    Args:
        data: Dictionary containing data to sanitize
        fields: List of field names to sanitize
        allow_rich_text: If True, allows basic HTML tags
        
    Returns:
        Dictionary with sanitized fields
    """
    for field in fields:
        if field in data and isinstance(data[field], str):
            data[field] = sanitize_text(data[field], allow_rich_text)
    return data
