"""
Validation utilities for MCP servers
"""

from typing import Any, Dict


def validate_schema(data: Any, schema: Dict[str, Any]) -> bool:
    """
    Validate data against JSON schema
    
    This is a placeholder - in production, use a library like jsonschema
    
    Args:
        data: Data to validate
        schema: JSON schema
    
    Returns:
        True if valid, False otherwise
    """
    # TODO: Implement proper JSON schema validation
    # For now, just return True
    return True


def sanitize_input(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize input data
    
    Args:
        data: Input data dictionary
    
    Returns:
        Sanitized data dictionary
    """
    sanitized = {}
    
    for key, value in data.items():
        if isinstance(value, str):
            # Strip whitespace
            sanitized[key] = value.strip()
        elif isinstance(value, dict):
            # Recursively sanitize nested dicts
            sanitized[key] = sanitize_input(value)
        else:
            sanitized[key] = value
    
    return sanitized

