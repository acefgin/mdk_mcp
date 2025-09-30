"""
AutoGen-MCP Bridge

Connects AutoGen agents to MCP servers for bioinformatics tool access.
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
import subprocess
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MCPClientBridge:
    """Bridge between AutoGen agents and MCP servers."""

    def __init__(self, server_configs: Dict[str, Dict[str, str]]):
        """
        Initialize MCP client bridge.

        Args:
            server_configs: Dict mapping server names to config
                {
                    "database": {
                        "container": "ndiag-database-server",
                        "command": ["python", "/app/database_mcp_server.py"]
                    }
                }
        """
        self.servers = server_configs
        self.processes = {}
        self.request_counter = 0
        self.initialized = False

    async def start_servers(self) -> None:
        """Start stdio connections to all MCP servers."""
        logger.info("Starting MCP server connections...")

        for server_name, config in self.servers.items():
            try:
                await self._start_server(server_name, config)
                logger.info(f"✅ Connected to {server_name} MCP server")
            except Exception as e:
                logger.error(f"❌ Failed to connect to {server_name}: {e}")
                raise

        self.initialized = True
        logger.info("All MCP servers connected successfully")

    async def _start_server(self, server_name: str, config: Dict[str, str]) -> None:
        """Start a single MCP server connection."""
        container = config["container"]
        command = config["command"]

        # Connect via docker exec for stdio communication
        full_command = ["docker", "exec", "-i", container] + command

        process = await asyncio.create_subprocess_exec(
            *full_command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        self.processes[server_name] = process

        # Initialize MCP protocol
        await self._initialize_mcp_connection(server_name)

    async def _initialize_mcp_connection(self, server_name: str) -> None:
        """Initialize MCP protocol with a server."""
        init_request = {
            "jsonrpc": "2.0",
            "id": self._gen_request_id(),
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "autogen-mcp-bridge",
                    "version": "1.0.0"
                }
            }
        }

        try:
            response = await self._send_request(server_name, init_request)
            if "error" in response:
                raise Exception(f"Initialization failed: {response['error']}")

            logger.debug(f"MCP server {server_name} initialized: {response.get('result', {})}")

        except Exception as e:
            logger.error(f"Failed to initialize {server_name}: {e}")
            raise

    async def call_tool(
        self,
        server: str,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Any:
        """
        Call an MCP tool.

        Args:
            server: Server name (e.g., "database")
            tool_name: Tool to call (e.g., "get_sequences")
            arguments: Tool arguments

        Returns:
            Tool result

        Raises:
            ValueError: If server not found or not initialized
            Exception: If MCP call fails
        """
        if not self.initialized:
            raise ValueError("MCP bridge not initialized. Call start_servers() first.")

        if server not in self.processes:
            raise ValueError(f"Unknown server: {server}")

        logger.info(f"Calling {server}.{tool_name} with args: {arguments}")

        request = {
            "jsonrpc": "2.0",
            "id": self._gen_request_id(),
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }

        try:
            response = await self._send_request(server, request)

            if "error" in response:
                error_msg = response["error"]
                logger.error(f"MCP error from {server}.{tool_name}: {error_msg}")
                raise Exception(f"MCP Error: {error_msg}")

            result = response.get("result", [])

            # Extract text content from MCP result
            if isinstance(result, list) and len(result) > 0:
                if isinstance(result[0], dict) and "text" in result[0]:
                    return result[0]["text"]

            return result

        except Exception as e:
            logger.error(f"Failed to call {server}.{tool_name}: {e}")
            raise

    async def list_tools(self, server: str) -> List[Dict[str, Any]]:
        """
        List available tools from a server.

        Args:
            server: Server name

        Returns:
            List of tool definitions
        """
        if not self.initialized:
            raise ValueError("MCP bridge not initialized")

        if server not in self.processes:
            raise ValueError(f"Unknown server: {server}")

        request = {
            "jsonrpc": "2.0",
            "id": self._gen_request_id(),
            "method": "tools/list",
            "params": {}
        }

        response = await self._send_request(server, request)

        if "error" in response:
            raise Exception(f"Failed to list tools: {response['error']}")

        return response.get("result", {}).get("tools", [])

    async def _send_request(self, server: str, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send a JSON-RPC request to a server and get response."""
        process = self.processes[server]

        # Send request
        request_json = json.dumps(request) + "\n"
        process.stdin.write(request_json.encode())
        await process.stdin.drain()

        # Read response
        response_line = await asyncio.wait_for(
            process.stdout.readline(),
            timeout=30.0  # 30 second timeout
        )

        if not response_line:
            raise Exception(f"No response from {server}")

        response = json.loads(response_line.decode())
        return response

    def _gen_request_id(self) -> int:
        """Generate unique request ID."""
        self.request_counter += 1
        return self.request_counter

    async def shutdown(self) -> None:
        """Shutdown all MCP server connections."""
        logger.info("Shutting down MCP connections...")

        for server_name, process in self.processes.items():
            try:
                process.stdin.close()
                await process.wait()
                logger.info(f"Closed connection to {server_name}")
            except Exception as e:
                logger.error(f"Error closing {server_name}: {e}")

        self.processes.clear()
        self.initialized = False


def create_autogen_functions(available_servers: List[str]) -> List[Dict[str, Any]]:
    """
    Create AutoGen-compatible function definitions.

    Args:
        available_servers: List of available server names

    Returns:
        List of function definitions for AutoGen
    """
    functions = []

    # Database Server Functions (Phase 1)
    if "database" in available_servers:
        functions.extend([
            {
                "name": "get_sequences",
                "description": "Retrieve biological sequences from multiple databases (NCBI, BOLD, gget). "
                              "Use this to get target species sequences and off-target sequences for primer design.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "taxon": {
                            "type": "string",
                            "description": "Scientific name or taxon ID (e.g., 'Salmo salar', 'Oncorhynchus mykiss')"
                        },
                        "region": {
                            "type": "string",
                            "enum": ["COI", "16S", "ITS", "mitogenome", "whole"],
                            "description": "Target genomic region for primers. COI is common for species ID.",
                            "default": "COI"
                        },
                        "source": {
                            "type": "string",
                            "enum": ["gget", "ncbi", "bold", "silva", "unite"],
                            "default": "ncbi",
                            "description": "Database source. NCBI for general, BOLD for COI barcodes."
                        },
                        "max_results": {
                            "type": "integer",
                            "default": 100,
                            "description": "Maximum sequences to retrieve (1-10000)"
                        }
                    },
                    "required": ["taxon"]
                }
            },
            {
                "name": "get_taxonomy",
                "description": "Get detailed taxonomic information including lineage and rank. "
                              "Use this to understand species relationships and validate scientific names.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Species name, common name, or accession number"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "get_neighbors",
                "description": "Find taxonomically similar species (potential qPCR off-targets). "
                              "Critical for designing specific primers that won't cross-react.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "taxon": {
                            "type": "string",
                            "description": "Target taxon name (e.g., 'Salmo salar')"
                        },
                        "rank": {
                            "type": "string",
                            "enum": ["species", "genus", "family"],
                            "description": "Taxonomic rank for neighbor search. 'genus' finds related species, 'family' finds related genera."
                        },
                        "distance": {
                            "type": "integer",
                            "default": 1,
                            "description": "Taxonomic distance (1=close relatives, 2=more distant)"
                        }
                    },
                    "required": ["taxon", "rank"]
                }
            },
            {
                "name": "extract_sequence_columns",
                "description": "Extract and organize metadata from sequence data. "
                              "Use this to parse sequence information after retrieval.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "sequence_data": {
                            "type": "string",
                            "description": "FASTA, GenBank, or JSON sequence data from get_sequences"
                        },
                        "columns": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Metadata fields to extract: Id, Accession, Organism, Length, Marker, Country, etc.",
                            "default": ["Id", "Accession", "Organism", "Length", "Marker"]
                        },
                        "output_format": {
                            "type": "string",
                            "enum": ["json", "csv", "tsv", "table"],
                            "default": "json",
                            "description": "Output format"
                        }
                    },
                    "required": ["sequence_data"]
                }
            },
            {
                "name": "search_sra_studies",
                "description": "Search NCBI SRA/BioProject for sequencing studies. "
                              "Use this to find existing qPCR or sequencing studies for reference.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Search query (e.g., 'Salmo salar qPCR', 'salmon COI amplicon')"
                        },
                        "filters": {
                            "type": "object",
                            "properties": {
                                "organism": {"type": "string"},
                                "library_strategy": {
                                    "type": "string",
                                    "enum": ["AMPLICON", "RNA-Seq", "WGS", "METAGENOMIC"]
                                },
                                "max_results": {"type": "integer", "default": 50}
                            }
                        }
                    },
                    "required": ["query"]
                }
            }
        ])

    # Future servers (when Phase 2+ implemented)
    # Processing server functions would go here
    # Alignment server functions would go here
    # Design server functions would go here

    return functions


class AutoGenMCPFunctionExecutor:
    """Execute MCP functions for AutoGen agents."""

    def __init__(self, bridge: MCPClientBridge):
        """
        Initialize function executor.

        Args:
            bridge: Initialized MCPClientBridge instance
        """
        self.bridge = bridge

    async def execute_function(
        self,
        function_name: str,
        arguments: Dict[str, Any]
    ) -> str:
        """
        Execute a function by name.

        Args:
            function_name: Name of function to execute
            arguments: Function arguments

        Returns:
            Function result as string
        """
        # Map function names to server.tool
        function_map = {
            "get_sequences": ("database", "get_sequences"),
            "get_taxonomy": ("database", "get_taxonomy"),
            "get_neighbors": ("database", "get_neighbors"),
            "extract_sequence_columns": ("database", "extract_sequence_columns"),
            "search_sra_studies": ("database", "search_sra_studies"),
        }

        if function_name not in function_map:
            raise ValueError(f"Unknown function: {function_name}")

        server, tool = function_map[function_name]

        try:
            result = await self.bridge.call_tool(server, tool, arguments)
            return str(result)
        except Exception as e:
            logger.error(f"Function execution failed: {e}")
            return f"Error: {str(e)}"
