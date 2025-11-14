"""
Server Registry

Central registry for MCP servers and their tools
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import mcp.types as types
import traceback

from .tool_handler import ToolHandler, ToolError, ExecutionError


@dataclass
class ServerConfig:
    """Server configuration"""
    name: str
    version: str
    description: str
    capabilities: Dict[str, Any] = field(default_factory=dict)
    protocol_version: str = "2024-11-05"


class ServerRegistry:
    """
    Central registry for MCP servers
    
    This class manages all tools for a server and provides
    the interface between MCP protocol and tool handlers
    """
    
    def __init__(self, config: ServerConfig):
        """
        Initialize server registry
        
        Args:
            config: Server configuration
        """
        self.config = config
        self.tools: Dict[str, ToolHandler] = {}
    
    def register_tool(self, handler: ToolHandler) -> None:
        """
        Register a tool handler
        
        Args:
            handler: Tool handler instance
        
        Raises:
            ValueError: If tool with same name already registered
        """
        name = handler.get_name()
        
        if name in self.tools:
            raise ValueError(f"Tool '{name}' already registered")
        
        self.tools[name] = handler
    
    def register_tools(self, handlers: List[ToolHandler]) -> None:
        """
        Register multiple tool handlers
        
        Args:
            handlers: List of tool handler instances
        """
        for handler in handlers:
            self.register_tool(handler)
    
    def unregister_tool(self, name: str) -> None:
        """
        Unregister a tool
        
        Args:
            name: Tool name
        """
        if name in self.tools:
            del self.tools[name]
    
    def get_tool(self, name: str) -> Optional[ToolHandler]:
        """
        Get tool handler by name
        
        Args:
            name: Tool name
        
        Returns:
            ToolHandler or None if not found
        """
        return self.tools.get(name)
    
    def has_tool(self, name: str) -> bool:
        """
        Check if tool exists
        
        Args:
            name: Tool name
        
        Returns:
            bool: True if tool exists
        """
        return name in self.tools
    
    def list_tool_names(self) -> List[str]:
        """
        List all tool names
        
        Returns:
            List of tool names
        """
        return list(self.tools.keys())
    
    def list_tools(self) -> List[types.Tool]:
        """
        List all tools as MCP Tool objects
        
        Returns:
            List of MCP Tool objects
        """
        return [
            types.Tool(
                name=handler.get_name(),
                description=handler.get_description(),
                inputSchema=handler.input_schema
            )
            for handler in self.tools.values()
        ]
    
    async def call_tool(
        self,
        name: str,
        arguments: Dict[str, Any]
    ) -> types.CallToolResult:
        """
        Call a tool by name
        
        Args:
            name: Tool name
            arguments: Tool arguments
        
        Returns:
            MCP CallToolResult
        
        Raises:
            ToolError: If tool not found or execution fails
        """
        # Get tool handler
        handler = self.get_tool(name)
        if not handler:
            raise ToolError(
                f"Tool '{name}' not found",
                code=-32601  # Method not found
            )
        
        try:
            # Execute tool with full validation pipeline
            result = await handler.handle(arguments)
            
            # Convert result to string for MCP response
            # (tools should return JSON-serializable dicts)
            import json
            result_text = json.dumps(result, indent=2, ensure_ascii=False)
            
            return types.CallToolResult(
                content=[
                    types.TextContent(
                        type="text",
                        text=result_text
                    )
                ]
            )
        
        except ToolError as e:
            # Return tool errors in the response
            # (MCP protocol allows tools to return errors in content)
            import json
            error_text = json.dumps({
                "error": {
                    "code": e.code,
                    "message": e.message,
                    "data": e.data
                }
            }, indent=2)
            
            return types.CallToolResult(
                content=[
                    types.TextContent(
                        type="text",
                        text=error_text
                    )
                ],
                isError=True
            )
        
        except Exception as e:
            # Wrap unexpected errors
            import json
            error_text = json.dumps({
                "error": {
                    "code": -32603,  # Internal error
                    "message": f"Internal error: {str(e)}",
                    "data": {
                        "traceback": traceback.format_exc()
                    }
                }
            }, indent=2)
            
            return types.CallToolResult(
                content=[
                    types.TextContent(
                        type="text",
                        text=error_text
                    )
                ],
                isError=True
            )
    
    def get_server_info(self) -> Dict[str, Any]:
        """
        Get server information
        
        Returns:
            dict: Server information
        """
        return {
            "name": self.config.name,
            "version": self.config.version,
            "description": self.config.description,
            "protocol_version": self.config.protocol_version,
            "tool_count": len(self.tools)
        }
    
    def get_capabilities(self) -> Dict[str, Any]:
        """
        Get server capabilities
        
        Returns:
            dict: Server capabilities
        """
        return {
            "tools": self.config.capabilities.get("tools", {}),
            "prompts": self.config.capabilities.get("prompts", {}),
            "resources": self.config.capabilities.get("resources", {})
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get server statistics
        
        Returns:
            dict: Server statistics
        """
        deprecated_count = sum(
            1 for handler in self.tools.values()
            if handler.is_deprecated()
        )
        
        categories = {}
        for handler in self.tools.values():
            category = handler.metadata.category
            categories[category] = categories.get(category, 0) + 1
        
        return {
            "total_tools": len(self.tools),
            "deprecated_tools": deprecated_count,
            "categories": categories
        }

