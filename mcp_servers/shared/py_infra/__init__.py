"""
Python Infrastructure for MCP Servers

This package contains reusable base classes and utilities for implementing
MCP servers in Python.
"""

from .types import (
    ToolHandler,
    ToolInput,
    ToolOutput,
    ToolMetadata,
    ToolError,
    ValidationError,
    ExecutionError,
    TimeoutError,
    ServerRegistry,
    ServerConfig,
)

from .utils import (
    setup_logging,
    validate_schema,
)

__version__ = "1.0.0"

__all__ = [
    # Base classes
    "ToolHandler",
    "ToolInput",
    "ToolOutput",
    "ToolMetadata",
    
    # Errors
    "ToolError",
    "ValidationError",
    "ExecutionError",
    "TimeoutError",
    
    # Registry
    "ServerRegistry",
    "ServerConfig",
    
    # Utilities
    "setup_logging",
    "validate_schema",
]

