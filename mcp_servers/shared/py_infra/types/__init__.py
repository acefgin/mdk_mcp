"""
Shared type definitions for MCP servers
"""

from .tool_handler import (
    ToolInput,
    ToolOutput,
    ToolMetadata,
    ToolHandler,
    ToolError,
    ValidationError,
    ExecutionError,
    TimeoutError
)

from .server_registry import (
    ServerConfig,
    ServerRegistry
)

__all__ = [
    'ToolInput',
    'ToolOutput',
    'ToolMetadata',
    'ToolHandler',
    'ToolError',
    'ValidationError',
    'ExecutionError',
    'TimeoutError',
    'ServerConfig',
    'ServerRegistry',
]

