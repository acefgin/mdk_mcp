"""
AG2-MCP Bridge

Connects AG2 agents to MCP servers for bioinformatics tool access.
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
import subprocess
import uuid

# Configure logging - only show WARNING and above to user
logging.basicConfig(
    level=logging.WARNING,
    format='%(levelname)s:%(name)s:%(message)s'
)
logger = logging.getLogger(__name__)


def summarize_large_result(result: Any, max_chars: int = 1000) -> str:
    """
    Summarize large tool results to avoid token limit issues.
    
    CRITICAL: For sequence data, return ONLY metadata (count, headers, OUTPUT FILE PATH).
    NEVER return actual sequence content - it will break token budgets.
    ALWAYS include output_file path if present - agents need this to continue workflow!

    Args:
        result: Tool result (could be string, dict, list, etc.)
        max_chars: Maximum characters to include in summary (default 1000, down from 5000)

    Returns:
        Summarized string representation
    """
    result_str = str(result)

    # If result is small enough, return as-is
    if len(result_str) <= max_chars:
        return result_str

    # Try to parse as JSON for structured summarization
    try:
        if isinstance(result, str):
            data = json.loads(result)
        else:
            data = result

        # Handle sequence data (most common large result)
        if isinstance(data, dict):
            summary_parts = []
            
            # CRITICAL: Always extract and display output_file if present
            output_file = data.get("output_file")
            stats = data.get("stats", {})

            # Count sequences if FASTA format - ONLY return metadata
            if "sequences" in data or any(key.startswith('>') for key in str(data)[:1000]):
                # Count sequences in FASTA
                fasta_count = str(data).count('>')
                if fasta_count > 0:
                    summary_parts.append(f"✓ Processed {fasta_count} sequences successfully")
                    
                    # CRITICAL: Show output file path prominently
                    if output_file:
                        summary_parts.append(f"\n📁 OUTPUT FILE: {output_file}")
                        summary_parts.append("   ⚠️  USE THIS PATH for next steps (alignment, phylogeny, etc.)")
                    
                    # Show statistics if available
                    if stats:
                        if "input_sequences" in stats and "output_sequences" in stats:
                            summary_parts.append(f"\n📊 QC Statistics:")
                            summary_parts.append(f"   • Input: {stats['input_sequences']} sequences")
                            summary_parts.append(f"   • Output: {stats['output_sequences']} sequences")
                            summary_parts.append(f"   • Removed: {stats['input_sequences'] - stats['output_sequences']} sequences")
                    
                    # Show ONLY first 2 headers, NO sequence content
                    lines = str(data).split('\n')
                    headers = []
                    for line in lines[:30]:  # Only scan first 30 lines
                        if line.startswith('>'):
                            headers.append(line[:80])  # Truncate long headers
                            if len(headers) >= 2:
                                break
                    if headers:
                        summary_parts.append("\nSample headers:")
                        summary_parts.append('\n'.join(headers))
                    
                    summary_parts.append(f"\n... and {fasta_count - 2} more sequences")
                    summary_parts.append("\n[Full sequence data available in output file]")
                    
                    if output_file:
                        summary_parts.append(f"\n🔧 NEXT STEP: Use fasta_file=\"{output_file}\" for alignment")
                    
                    return '\n'.join(summary_parts)

            # Handle metadata extractions
            if "records" in data or "results" in data:
                records = data.get("records", data.get("results", []))
                if isinstance(records, list) and len(records) > 0:
                    summary_parts.append(f"Retrieved {len(records)} records")
                    # Show first 3 records
                    summary_parts.append("\nFirst 3 records (preview):")
                    for i, record in enumerate(records[:3]):
                        summary_parts.append(f"\nRecord {i+1}:")
                        if isinstance(record, dict):
                            for key, value in list(record.items())[:5]:  # First 5 fields
                                summary_parts.append(f"  {key}: {str(value)[:100]}")
                        else:
                            summary_parts.append(f"  {str(record)[:200]}")
                    if len(records) > 3:
                        summary_parts.append(f"\n... and {len(records) - 3} more records")
                    return '\n'.join(summary_parts)

            # Generic dict summarization
            summary_parts.append(f"Result contains {len(data)} top-level keys")
            summary_parts.append(f"Keys: {', '.join(list(data.keys())[:10])}")
            if len(data) > 10:
                summary_parts.append(f"... and {len(data) - 10} more keys")
            return '\n'.join(summary_parts)

        # Handle lists
        elif isinstance(data, list):
            summary_parts = [f"Retrieved {len(data)} items"]
            if len(data) > 0:
                summary_parts.append("\nFirst 3 items (preview):")
                for i, item in enumerate(data[:3]):
                    summary_parts.append(f"\n{i+1}. {str(item)[:200]}")
                if len(data) > 3:
                    summary_parts.append(f"\n... and {len(data) - 3} more items")
            return '\n'.join(summary_parts)

    except (json.JSONDecodeError, Exception) as e:
        logger.debug(f"Could not parse result as JSON: {e}")

    # Fallback: truncate with indication
    truncated = result_str[:max_chars]
    remaining_chars = len(result_str) - max_chars
    return f"{truncated}\n\n... [Output truncated: {remaining_chars:,} more characters. Full result saved to task log file.]"


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
        """
        Connect to a running MCP server.
        
        The MCP servers are already running in their containers (started by CMD in Dockerfile).
        We connect to them by running a new instance via docker exec with interactive stdin.
        """
        container = config["container"]
        command = config["command"]
        
        # Start a new instance of the MCP server to communicate with
        # This is necessary because docker attach doesn't work well with asyncio pipes
        full_command = ["docker", "exec", "-i", container] + command
        
        logger.debug(f"Connecting to {server_name} via: {' '.join(full_command)}")

        process = await asyncio.create_subprocess_exec(
            *full_command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        self.processes[server_name] = process
        
        logger.debug(f"Process created for {server_name}, initializing MCP protocol...")

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

            # Send initialized notification (required by MCP protocol)
            initialized_notification = {
                "jsonrpc": "2.0",
                "method": "notifications/initialized"
            }
            process = self.processes[server_name]
            notification_json = json.dumps(initialized_notification) + "\n"
            process.stdin.write(notification_json.encode())
            await process.stdin.drain()

            logger.debug(f"Sent initialized notification to {server_name}")

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
        
        # Check if process is still alive
        if process.returncode is not None:
            logger.error(f"Process for {server} has exited with code {process.returncode}")
            raise Exception(f"Connection lost - {server} process exited")

        # Send request
        request_json = json.dumps(request) + "\n"
        logger.debug(f"Sending request to {server}: {request_json[:200]}")
        
        try:
            process.stdin.write(request_json.encode())
            await process.stdin.drain()
        except Exception as e:
            logger.error(f"Failed to write to {server} stdin: {e}")
            raise Exception(f"Connection lost - failed to write to {server}")

        # Read response (handle large responses by reading until newline)
        response_data = b""
        response_line = None  # Initialize to prevent UnboundLocalError
        timeout_seconds = 60.0  # 60 second timeout for large responses

        # Start task to read stderr in parallel
        async def read_stderr():
            try:
                stderr_data = await asyncio.wait_for(process.stderr.read(4096), timeout=1.0)
                if stderr_data:
                    stderr_text = stderr_data.decode('utf-8', errors='ignore')
                    # Only log as warning if it contains actual errors
                    # MCP servers log INFO messages to stderr by default
                    if any(level in stderr_text for level in ['ERROR', 'CRITICAL', 'WARNING', 'Exception', 'Traceback']):
                        logger.warning(f"stderr from {server}: {stderr_text}")
                    else:
                        logger.debug(f"stderr from {server}: {stderr_text}")
            except asyncio.TimeoutError:
                pass  # No stderr data, that's fine
            except Exception as e:
                logger.debug(f"Error reading stderr from {server}: {e}")

        stderr_task = asyncio.create_task(read_stderr())

        try:
            while True:
                chunk = await asyncio.wait_for(
                    process.stdout.read(8192),  # Read in 8KB chunks
                    timeout=timeout_seconds
                )

                if not chunk:
                    # No more data available - check if we got any response
                    if response_data:
                        # Use whatever we have (might not end with newline)
                        response_line = response_data.rstrip(b'\n')
                    else:
                        # Check if process exited
                        if process.returncode is not None:
                            logger.error(f"Process {server} exited during read with code {process.returncode}")
                            await stderr_task  # Wait for stderr
                            raise Exception(f"Connection lost - {server} process exited unexpectedly")
                    break

                response_data += chunk

                # Check if we have a complete line (JSON-RPC responses end with \n)
                if b'\n' in response_data:
                    # Extract the first complete line
                    line_end = response_data.index(b'\n')
                    response_line = response_data[:line_end]
                    break

        except asyncio.TimeoutError:
            # If we got partial data before timeout, try to use it
            if response_data:
                logger.warning(f"Timeout reading from {server}, attempting to parse partial response")
                response_line = response_data.rstrip(b'\n')
            else:
                await stderr_task  # Check for errors in stderr
                raise Exception(f"Timeout reading response from {server}")
        finally:
            # Clean up stderr task
            if not stderr_task.done():
                stderr_task.cancel()

        if not response_line:
            logger.error(f"No response from {server}. Process alive: {process.returncode is None}")
            raise Exception(f"No response received from {server}")

        logger.debug(f"Received response from {server}: {response_line[:200]}")

        try:
            response = json.loads(response_line.decode())
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON response from {server}: {response_line[:200]}")
            raise Exception(f"Invalid JSON response from {server}: {e}")

        return response

    def _gen_request_id(self) -> int:
        """Generate unique request ID."""
        self.request_counter += 1
        return self.request_counter

    async def shutdown(self) -> None:
        """Shutdown all MCP server connections."""
        logger.warning("Shutting down MCP connections...")

        for server_name, process in self.processes.items():
            try:
                # Close stdin to signal shutdown
                if process.stdin and not process.stdin.is_closing():
                    process.stdin.close()

                # Terminate process gracefully
                try:
                    process.terminate()
                    # Wait with timeout
                    await asyncio.wait_for(process.wait(), timeout=2.0)
                except asyncio.TimeoutError:
                    # Force kill if not responding
                    process.kill()
                    await process.wait()

                logger.warning(f"Closed connection to {server_name}")
            except asyncio.CancelledError:
                # Handle cancellation gracefully
                process.kill()
                logger.warning(f"Forcefully terminated {server_name}")
            except Exception as e:
                logger.warning(f"Error closing {server_name}: {e}")

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

    # Processing Server Functions (Phase 2)
    if "processing" in available_servers:
        functions.extend([
            {
                "name": "fasta_qc",
                "description": "Perform quality control on FASTA sequences: filter by length, N-content, and remove duplicates. "
                              "Use this as the first step after retrieving sequences to ensure clean data. "
                              "Provide either fasta_content (string) OR fasta_file (file path from /results/sequences/).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "fasta_content": {
                            "type": "string",
                            "description": "Input FASTA sequences as plain text (use this OR fasta_file, not both)"
                        },
                        "fasta_file": {
                            "type": "string",
                            "description": "Path to FASTA file (e.g., /results/sequences/Salmo_salar_COI_20251023_180611.fasta). Use this when sequences are already saved to a file."
                        },
                        "min_length": {
                            "type": "integer",
                            "default": 100,
                            "description": "Minimum sequence length in bp"
                        },
                        "max_n_percent": {
                            "type": "number",
                            "default": 5.0,
                            "description": "Maximum percentage of N bases allowed (0-100)"
                        },
                        "remove_duplicates": {
                            "type": "boolean",
                            "default": True,
                            "description": "Remove duplicate sequences"
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "dereplicate_sequences",
                "description": "Remove duplicate or near-duplicate sequences using clustering at specified identity threshold. "
                              "Use this to reduce redundancy in sequence sets. "
                              "Provide either fasta_content (string) OR fasta_file (file path from /results/sequences/).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "fasta_content": {
                            "type": "string",
                            "description": "Input FASTA sequences as plain text (use this OR fasta_file, not both)"
                        },
                        "fasta_file": {
                            "type": "string",
                            "description": "Path to FASTA file (e.g., /results/sequences/Salmo_salar_COI_20251023_180611.fasta)"
                        },
                        "identity_threshold": {
                            "type": "number",
                            "default": 1.0,
                            "description": "Identity threshold for clustering (0.0-1.0). 1.0=exact duplicates, 0.97=97% similar"
                        },
                        "per_species": {
                            "type": "boolean",
                            "default": False,
                            "description": "Dereplicate within each species separately (requires organism info in headers)"
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "mask_low_complexity",
                "description": "Mask low-complexity regions (repeats, homopolymers) using DUST algorithm. "
                              "Use this before alignment to avoid spurious matches. "
                              "Provide either fasta_content (string) OR fasta_file (file path from /results/sequences/).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "fasta_content": {
                            "type": "string",
                            "description": "Input FASTA sequences as plain text (use this OR fasta_file, not both)"
                        },
                        "fasta_file": {
                            "type": "string",
                            "description": "Path to FASTA file (e.g., /results/sequences/Salmo_salar_COI_20251023_180611.fasta)"
                        },
                        "dust_threshold": {
                            "type": "number",
                            "default": 2.0,
                            "description": "DUST threshold (lower=more masking). Range: 0.0-100.0"
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "detect_chimeras",
                "description": "Detect and optionally remove chimeric sequences using UCHIME algorithm. "
                              "Important for PCR-amplified sequences to ensure authentic sequences. "
                              "Provide either fasta_content (string) OR fasta_file (file path from /results/sequences/).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "fasta_content": {
                            "type": "string",
                            "description": "Input FASTA sequences as plain text (use this OR fasta_file, not both)"
                        },
                        "fasta_file": {
                            "type": "string",
                            "description": "Path to FASTA file (e.g., /results/sequences/Salmo_salar_COI_20251023_180611.fasta)"
                        },
                        "remove_chimeras": {
                            "type": "boolean",
                            "default": True,
                            "description": "Remove chimeras (true) or just report them (false)"
                        },
                        "abskew": {
                            "type": "number",
                            "default": 2.0,
                            "description": "Abundance skew threshold (higher=more stringent)"
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "process_sequences",
                "description": "Run sequences through a customizable quality control pipeline. "
                              "WHEN TO USE: Prefer this for batch processing multiple steps in one call. "
                              "PIPELINE GUIDE: "
                              "• Basic QC only: ['qc'] - Fast, for trusted data sources "
                              "• Standard workflow: ['qc', 'dereplicate'] - Recommended for most cases (default) "
                              "• Comprehensive QC: ['qc', 'dereplicate', 'mask', 'chimera'] - For publication-quality data "
                              "• Alignment prep: ['qc', 'dereplicate', 'mask'] - Sequences for multiple alignment "
                              "INDIVIDUAL TOOLS: Use fasta_qc, dereplicate_sequences, mask_low_complexity, detect_chimeras "
                              "when you need fine-grained control over each step or want to inspect intermediate results. "
                              "Provide either fasta_content (string) OR fasta_file (file path from /results/sequences/).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "fasta_content": {
                            "type": "string",
                            "description": "Input FASTA sequences as plain text (use this OR fasta_file, not both)"
                        },
                        "fasta_file": {
                            "type": "string",
                            "description": "Path to FASTA file (e.g., /results/sequences/Salmo_salar_COI_20251023_180611.fasta)"
                        },
                        "pipeline": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": ["qc", "dereplicate", "mask", "chimera"]
                            },
                            "default": ["qc", "dereplicate", "mask", "chimera"],
                            "description": "Processing steps to execute in order. Available steps: "
                                          "'qc' (filter by length/quality), "
                                          "'dereplicate' (remove duplicates/near-duplicates), "
                                          "'mask' (mask low-complexity regions), "
                                          "'chimera' (detect and remove chimeric sequences). "
                                          "Default is full pipeline for comprehensive quality control."
                        },
                        "min_length": {
                            "type": "integer",
                            "default": 100,
                            "description": "Minimum sequence length for QC step"
                        },
                        "max_n_percent": {
                            "type": "number",
                            "default": 5.0,
                            "description": "Maximum N percentage for QC step"
                        },
                        "identity_threshold": {
                            "type": "number",
                            "default": 0.97,
                            "description": "Clustering identity threshold for dereplication (0.0-1.0, default 0.97 = 97% identity)"
                        },
                        "dust_threshold": {
                            "type": "number",
                            "default": 2.0,
                            "description": "Low-complexity masking threshold for mask step (lower = more aggressive masking)"
                        }
                    },
                    "required": []
                }
            }
        ])

    # Future servers (when Phase 3+ implemented)
    # Alignment server functions would go here
    # Design server functions would go here

    return functions


class AutoGenMCPFunctionExecutor:
    """Execute MCP functions for AutoGen agents."""

    def __init__(self, bridge: MCPClientBridge, full_result_dir: str = "/results"):
        """
        Initialize function executor.

        Args:
            bridge: Initialized MCPClientBridge instance
            full_result_dir: Directory to save full tool results
        """
        self.bridge = bridge
        self.full_result_dir = full_result_dir
        import os
        os.makedirs(full_result_dir, exist_ok=True)

    async def _call_mcp_tool_raw(
        self,
        function_name: str,
        arguments: Dict[str, Any]
    ) -> str:
        """
        Call MCP tool and return RAW result without summarization.
        Used when we need the full data (e.g., for saving sequences to file).

        Args:
            function_name: Name of the function
            arguments: Function arguments

        Returns:
            Full, unsummarized result from MCP server (extracted from JSON wrapper)
        """
        function_map = {
            # Database tools
            "get_sequences": ("database", "get_sequences"),
            "get_taxonomy": ("database", "get_taxonomy"),
            "get_neighbors": ("database", "get_neighbors"),
            "extract_sequence_columns": ("database", "extract_sequence_columns"),
            "search_sra_studies": ("database", "search_sra_studies"),
            # Processing tools
            "fasta_qc": ("processing", "fasta_qc"),
            "dereplicate_sequences": ("processing", "dereplicate_sequences"),
            "mask_low_complexity": ("processing", "mask_low_complexity"),
            "detect_chimeras": ("processing", "detect_chimeras"),
            "process_sequences": ("processing", "process_sequences"),
        }

        if function_name not in function_map:
            return f"Error: Unknown function '{function_name}'"

        server, tool = function_map[function_name]

        # PREPROCESSING: Handle fasta_file parameter for processing tools
        # If fasta_file is provided, read the file and populate fasta_content
        if "fasta_file" in arguments and arguments["fasta_file"]:
            fasta_file_path = arguments["fasta_file"]
            try:
                logger.info(f"Reading FASTA file for raw call: {fasta_file_path}")
                with open(fasta_file_path, 'r') as f:
                    arguments["fasta_content"] = f.read()
                # Remove fasta_file from arguments since MCP server expects fasta_content
                del arguments["fasta_file"]
                logger.info(f"Loaded {len(arguments['fasta_content'])} characters from {fasta_file_path}")
            except FileNotFoundError:
                return f"Error: File not found: {fasta_file_path}"
            except Exception as e:
                return f"Error reading file {fasta_file_path}: {str(e)}"

        try:
            result = await self.bridge.call_tool(server, tool, arguments)
            
            # Extract actual content from MCP response
            # MCP returns: {'content': [{'type': 'text', 'text': 'ACTUAL DATA'}], 'isError': False}
            if isinstance(result, dict):
                if 'content' in result:
                    content_list = result['content']
                    if isinstance(content_list, list) and len(content_list) > 0:
                        first_content = content_list[0]
                        if isinstance(first_content, dict) and 'text' in first_content:
                            # Return the pure text content
                            return first_content['text']
                # Fallback if structure is different
                return str(result)
            return str(result)
        except Exception as e:
            logger.error(f"Raw MCP call failed: {e}")
            return f"Error: {str(e)}"

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
            # Database tools
            "get_sequences": ("database", "get_sequences"),
            "get_taxonomy": ("database", "get_taxonomy"),
            "get_neighbors": ("database", "get_neighbors"),
            "extract_sequence_columns": ("database", "extract_sequence_columns"),
            "search_sra_studies": ("database", "search_sra_studies"),
            # Processing tools
            "fasta_qc": ("processing", "fasta_qc"),
            "dereplicate_sequences": ("processing", "dereplicate_sequences"),
            "mask_low_complexity": ("processing", "mask_low_complexity"),
            "detect_chimeras": ("processing", "detect_chimeras"),
            "process_sequences": ("processing", "process_sequences"),
        }

        if function_name not in function_map:
            raise ValueError(f"Unknown function: {function_name}")

        server, tool = function_map[function_name]

        # PREPROCESSING: Handle fasta_file parameter for processing tools
        # If fasta_file is provided, read the file and populate fasta_content
        if "fasta_file" in arguments and arguments["fasta_file"]:
            fasta_file_path = arguments["fasta_file"]
            try:
                logger.info(f"Reading FASTA file: {fasta_file_path}")
                with open(fasta_file_path, 'r') as f:
                    arguments["fasta_content"] = f.read()
                # Remove fasta_file from arguments since MCP server expects fasta_content
                del arguments["fasta_file"]
                logger.info(f"Loaded {len(arguments['fasta_content'])} characters from {fasta_file_path}")
            except FileNotFoundError:
                return f"Error: File not found: {fasta_file_path}"
            except Exception as e:
                return f"Error reading file {fasta_file_path}: {str(e)}"

        try:
            result = await self.bridge.call_tool(server, tool, arguments)

            # Save full result to file for later reference
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            result_filename = f"tool_result_{function_name}_{timestamp}.txt"
            result_path = f"{self.full_result_dir}/{result_filename}"

            # Save both raw MCP response and extracted content
            with open(result_path, 'w') as f:
                f.write(f"Tool: {function_name}\n")
                f.write(f"Arguments: {json.dumps(arguments, indent=2)}\n")
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                f.write("=" * 80 + "\n\n")
                
                # Save raw MCP response
                f.write("RAW MCP RESPONSE:\n")
                f.write("-" * 80 + "\n")
                f.write(str(result))
                f.write("\n\n")
                
                # Extract and save clean content
                f.write("EXTRACTED CONTENT:\n")
                f.write("-" * 80 + "\n")
                
                # Try to extract the 'text' field from MCP wrapper
                extracted_content = None
                if isinstance(result, dict):
                    if 'content' in result:
                        content_list = result['content']
                        if isinstance(content_list, list) and len(content_list) > 0:
                            first_content = content_list[0]
                            if isinstance(first_content, dict) and 'text' in first_content:
                                extracted_content = first_content['text']
                
                if extracted_content:
                    f.write(extracted_content)
                else:
                    f.write("(Could not extract - using raw result)")
                    f.write("\n")
                    f.write(str(result))

            # Summarize large results to avoid token limits
            # Full results are saved in the file above
            # Use 1000 chars max (reduced from 5000) to prevent token budget issues
            summarized = summarize_large_result(result, max_chars=1000)

            # Add reference to full result file in summary
            if len(str(result)) > 1000:
                summarized += f"\n\n[Full result saved to: {result_filename}]"

            result_size = len(str(result))
            summary_size = len(summarized)
            compression_ratio = (1 - summary_size / result_size) * 100 if result_size > 0 else 0
            
            logger.info(f"Function {function_name} result: {result_size:,} chars -> {summary_size:,} chars ({compression_ratio:.1f}% reduction)")
            logger.info(f"Full result saved to: {result_path}")

            return summarized
        except Exception as e:
            logger.error(f"Function execution failed: {e}")
            return f"Error: {str(e)}"
