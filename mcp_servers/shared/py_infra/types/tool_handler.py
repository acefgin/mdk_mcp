"""
Tool Handler Base Classes

Abstract base classes and utilities for implementing MCP tools in Python
"""

from typing import Any, Dict, Optional, List, TypeVar
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field
import traceback

# Type variables
TInput = TypeVar('TInput', bound='ToolInput')
TOutput = TypeVar('TOutput', bound='ToolOutput')


class ToolInput(BaseModel):
    """
    Base class for tool input validation
    
    All tool inputs should extend this class and define their schema using Pydantic
    """
    
    class Config:
        extra = "forbid"  # Forbid extra fields by default
        validate_assignment = True


class ToolOutput(BaseModel):
    """
    Base class for tool output validation
    
    All tool outputs should extend this class and define their schema using Pydantic
    """
    
    class Config:
        validate_assignment = True


class ToolMetadata(BaseModel):
    """Tool metadata"""
    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    version: str = Field(..., description="Tool version (semver)")
    category: str = Field(..., description="Tool category")
    tags: List[str] = Field(default_factory=list, description="Tool tags")
    examples: List[Dict[str, Any]] = Field(default_factory=list, description="Usage examples")
    deprecated: bool = Field(default=False, description="Whether tool is deprecated")
    deprecation_message: Optional[str] = Field(None, description="Deprecation message")
    replaced_by: Optional[str] = Field(None, description="Replacement tool name")


class ToolError(Exception):
    """
    Base exception for tool errors
    
    All tool-specific errors should extend this class
    """
    
    def __init__(
        self,
        message: str,
        code: int = -32000,
        data: Optional[Any] = None
    ):
        self.message = message
        self.code = code
        self.data = data
        super().__init__(message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON-RPC error response"""
        return {
            "code": self.code,
            "message": self.message,
            "data": self.data
        }


class ValidationError(ToolError):
    """
    Input/output validation error
    """
    
    def __init__(self, message: str, errors: List[Dict[str, Any]]):
        super().__init__(
            message,
            code=-32602,  # Invalid params
            data={"errors": errors}
        )
        self.errors = errors


class ExecutionError(ToolError):
    """
    Tool execution error
    """
    
    def __init__(self, message: str, details: Optional[str] = None):
        super().__init__(
            message,
            code=-32000,
            data={"details": details}
        )


class TimeoutError(ToolError):
    """
    Tool execution timeout
    """
    
    def __init__(self, timeout: int, operation: Optional[str] = None):
        message = f"Operation exceeded timeout of {timeout}s"
        if operation:
            message = f"{operation} {message}"
        
        super().__init__(
            message,
            code=-32001,
            data={"timeout": timeout, "operation": operation}
        )


class ToolHandler(ABC):
    """
    Abstract base class for tool handlers
    
    All tools should extend this class and implement the required methods
    """
    
    @property
    @abstractmethod
    def metadata(self) -> ToolMetadata:
        """
        Get tool metadata
        
        Returns:
            ToolMetadata: Tool metadata including name, description, version, etc.
        """
        pass
    
    @property
    @abstractmethod
    def input_schema(self) -> Dict[str, Any]:
        """
        Get JSON schema for input validation
        
        Returns:
            dict: JSON schema object
        """
        pass
    
    @property
    @abstractmethod
    def output_schema(self) -> Dict[str, Any]:
        """
        Get JSON schema for output validation
        
        Returns:
            dict: JSON schema object
        """
        pass
    
    @abstractmethod
    async def validate_input(self, input_data: Dict[str, Any]) -> ToolInput:
        """
        Validate and parse input
        
        Args:
            input_data: Raw input dictionary
        
        Returns:
            ToolInput: Validated input object
        
        Raises:
            ValidationError: If validation fails
        """
        pass
    
    @abstractmethod
    async def execute(self, input_data: ToolInput) -> ToolOutput:
        """
        Execute the tool logic
        
        Args:
            input_data: Validated input object
        
        Returns:
            ToolOutput: Tool execution result
        
        Raises:
            ExecutionError: If execution fails
            TimeoutError: If execution times out
        """
        pass
    
    @abstractmethod
    async def validate_output(self, output_data: Any) -> ToolOutput:
        """
        Validate and parse output
        
        Args:
            output_data: Raw output data
        
        Returns:
            ToolOutput: Validated output object
        
        Raises:
            ValidationError: If validation fails
        """
        pass
    
    async def handle(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Full execution pipeline with validation
        
        This is the main entry point for tool execution. It handles:
        1. Input validation
        2. Tool execution
        3. Output validation
        4. Error handling
        
        Args:
            input_data: Raw input dictionary
        
        Returns:
            dict: Validated output as dictionary
        
        Raises:
            ToolError: If any step fails
        """
        try:
            # 1. Validate input
            validated_input = await self.validate_input(input_data)
            
            # 2. Execute
            result = await self.execute(validated_input)
            
            # 3. Validate output
            validated_output = await self.validate_output(result)
            
            # 4. Return as dict
            return validated_output.model_dump()
        
        except ToolError:
            # Re-raise tool errors as-is
            raise
        
        except Exception as e:
            # Wrap unexpected errors
            raise ExecutionError(
                message=f"Unexpected error: {str(e)}",
                details=traceback.format_exc()
            )
    
    def get_name(self) -> str:
        """Get tool name"""
        return self.metadata.name
    
    def get_description(self) -> str:
        """Get tool description"""
        return self.metadata.description
    
    def is_deprecated(self) -> bool:
        """Check if tool is deprecated"""
        return self.metadata.deprecated


def create_tool_handler(
    name: str,
    description: str,
    version: str,
    category: str,
    input_model: type[TInput],
    output_model: type[TOutput],
    execute_fn: callable,
    **kwargs
) -> ToolHandler:
    """
    Factory function to create a tool handler from components
    
    Args:
        name: Tool name
        description: Tool description
        version: Tool version
        category: Tool category
        input_model: Pydantic model for input
        output_model: Pydantic model for output
        execute_fn: Async function to execute tool
        **kwargs: Additional metadata fields
    
    Returns:
        ToolHandler: Tool handler instance
    """
    
    class DynamicToolHandler(ToolHandler):
        @property
        def metadata(self) -> ToolMetadata:
            return ToolMetadata(
                name=name,
                description=description,
                version=version,
                category=category,
                **kwargs
            )
        
        @property
        def input_schema(self) -> Dict[str, Any]:
            return input_model.model_json_schema()
        
        @property
        def output_schema(self) -> Dict[str, Any]:
            return output_model.model_json_schema()
        
        async def validate_input(self, input_data: Dict[str, Any]) -> ToolInput:
            try:
                return input_model(**input_data)
            except Exception as e:
                errors = []
                if hasattr(e, 'errors'):
                    errors = e.errors()
                raise ValidationError(f"Input validation failed: {str(e)}", errors)
        
        async def execute(self, input_data: ToolInput) -> ToolOutput:
            return await execute_fn(input_data)
        
        async def validate_output(self, output_data: Any) -> ToolOutput:
            if isinstance(output_data, output_model):
                return output_data
            try:
                return output_model(**output_data)
            except Exception as e:
                errors = []
                if hasattr(e, 'errors'):
                    errors = e.errors()
                raise ValidationError(f"Output validation failed: {str(e)}", errors)
    
    return DynamicToolHandler()

