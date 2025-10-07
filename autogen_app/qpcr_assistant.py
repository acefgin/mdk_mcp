"""
qPCR Assay Design Assistant

Multi-agent system for designing species-specific qPCR assays.
Built with AG2 (formerly AutoGen) multi-agent framework.
"""

import os
import sys
import asyncio
import logging
import json
import readline  # Import readline for proper line editing support
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
import autogen
from autogen import ConversableAgent, AssistantAgent, UserProxyAgent, GroupChat, GroupChatManager
from autogen.cache import Cache

from autogen_mcp_bridge import (
    MCPClientBridge,
    create_autogen_functions,
    AutoGenMCPFunctionExecutor,
    summarize_large_result
)
from text_resources import (
    COORDINATOR_SYSTEM_MESSAGE,
    DATABASE_AGENT_SYSTEM_MESSAGE,
    ANALYST_SYSTEM_MESSAGE,
    README_TEMPLATE,
    BANNER_LINES,
    COMMANDS_TEXT,
    AGENTS_INFO,
    GETTING_STARTED_TEXT,
    EXAMPLE_REQUEST,
    HELP_EXAMPLES,
    HELP_TIPS,
    CLARIFICATION_QUESTIONS,
    WORKFLOW_STEPS,
    WORKFLOW_STEPS_AUTO_OFFTARGETS,
    MODEL_DISPLAY_NAMES,
    STATUS_MESSAGES,
    ERROR_MESSAGES,
    SUCCESS_MESSAGES,
    COMPREHENSIVE_REQUEST_TEMPLATE
)

# Configure logging - only show WARNING and above to user
logging.basicConfig(
    level=logging.WARNING,  # Hide INFO logs from user interface
    format='%(levelname)s:%(name)s:%(message)s'
)
logger = logging.getLogger(__name__)

# ANSI Color Codes
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'

    # Foreground colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'

    # Bright foreground colors
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'

    # Background colors
    BG_BLACK = '\033[40m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    BG_WHITE = '\033[47m'

def colored(text: str, color: str, bold: bool = False) -> str:
    """Apply color to text."""
    prefix = Colors.BOLD if bold else ''
    return f"{prefix}{color}{text}{Colors.RESET}"

def print_colored(text: str, color: str, bold: bool = False):
    """Print colored text."""
    print(colored(text, color, bold))


class TaskLogger:
    """Logger for multi-agent task execution."""

    def __init__(self, log_dir: str = "/results"):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        self.current_session = None
        self.task_log = []

    def start_session(self, user_request: str):
        """Start a new logging session."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_session = f"task_{timestamp}.json"
        self.task_log = [{
            "session_id": timestamp,
            "start_time": datetime.now().isoformat(),
            "user_request": user_request,
            "agents": [],
            "tool_calls": [],
            "messages": []
        }]

    def log_agent_action(self, agent_name: str, action: str, content: str):
        """Log an agent action with smart truncation."""
        if not self.task_log:
            return

        # Smart truncation with sentence boundary preservation
        processed_content = self._smart_truncate(content, 2000)
        
        self.task_log[0]["agents"].append({
            "timestamp": datetime.now().isoformat(),
            "agent": agent_name,
            "action": action,
            "content": processed_content,
            "original_length": len(content),
            "truncated": len(content) > 2000
        })

    def log_tool_call(self, agent_name: str, tool_name: str, arguments: Dict[str, Any], result: str):
        """Log a tool call with smart truncation."""
        if not self.task_log:
            return

        # Smart truncation for tool results
        processed_result = self._smart_truncate(result, 1000)

        self.task_log[0]["tool_calls"].append({
            "timestamp": datetime.now().isoformat(),
            "agent": agent_name,
            "tool": tool_name,
            "arguments": arguments,
            "result_preview": processed_result,
            "result_length": len(result),
            "success": not result.startswith("Error:"),
            "truncated": len(result) > 1000
        })

    def log_message(self, source: str, message_type: str, content: str):
        """Log a message with smart truncation."""
        if not self.task_log:
            return

        # Smart truncation for messages
        processed_content = self._smart_truncate(content, 2000)

        self.task_log[0]["messages"].append({
            "timestamp": datetime.now().isoformat(),
            "source": source,
            "type": message_type,
            "content": processed_content,
            "original_length": len(content),
            "truncated": len(content) > 2000
        })

    def end_session(self, summary: str = "", termination_info: Dict[str, Any] = None):
        """End the logging session and save to file."""
        if not self.task_log or not self.current_session:
            return

        self.task_log[0]["end_time"] = datetime.now().isoformat()
        self.task_log[0]["summary"] = summary
        
        # Add termination information if provided
        if termination_info:
            self.task_log[0]["termination_info"] = termination_info

        # Calculate statistics
        tool_calls = self.task_log[0]["tool_calls"]
        self.task_log[0]["statistics"] = {
            "total_agents": len(set(a["agent"] for a in self.task_log[0]["agents"])),
            "total_actions": len(self.task_log[0]["agents"]),
            "total_tool_calls": len(tool_calls),
            "successful_tool_calls": sum(1 for tc in tool_calls if tc["success"]),
            "failed_tool_calls": sum(1 for tc in tool_calls if not tc["success"]),
            "total_messages": len(self.task_log[0]["messages"])
        }

        # Save to file
        log_path = os.path.join(self.log_dir, self.current_session)
        with open(log_path, 'w') as f:
            json.dump(self.task_log[0], f, indent=2)

        logger.info(f"Task log saved to: {log_path}")

        # Also create a human-readable summary
        summary_path = log_path.replace('.json', '_summary.txt')
        self._write_summary(summary_path)

        return log_path

    def _write_summary(self, path: str):
        """Write a human-readable summary."""
        if not self.task_log:
            return

        log = self.task_log[0]

        with open(path, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("qPCR ASSISTANT - TASK EXECUTION LOG\n")
            f.write("=" * 80 + "\n\n")

            f.write(f"Session ID: {log['session_id']}\n")
            f.write(f"Start Time: {log['start_time']}\n")
            f.write(f"End Time: {log.get('end_time', 'In Progress')}\n\n")

            f.write("USER REQUEST:\n")
            f.write("-" * 80 + "\n")
            f.write(f"{log['user_request']}\n\n")

            f.write("STATISTICS:\n")
            f.write("-" * 80 + "\n")
            stats = log.get('statistics', {})
            f.write(f"  Total Agents Involved: {stats.get('total_agents', 0)}\n")
            f.write(f"  Total Agent Actions: {stats.get('total_actions', 0)}\n")
            f.write(f"  Total Tool Calls: {stats.get('total_tool_calls', 0)}\n")
            f.write(f"    - Successful: {stats.get('successful_tool_calls', 0)}\n")
            f.write(f"    - Failed: {stats.get('failed_tool_calls', 0)}\n")
            f.write(f"  Total Messages: {stats.get('total_messages', 0)}\n\n")

            # Add termination information if available
            termination_info = log.get('termination_info')
            if termination_info:
                f.write("TERMINATION INFORMATION:\n")
                f.write("-" * 80 + "\n")
                f.write(f"  Termination Reason: {termination_info.get('termination_reason', 'UNKNOWN')}\n")
                f.write(f"  Terminated By: {termination_info.get('sender', 'UNKNOWN')}\n")
                f.write(f"  Termination Time: {termination_info.get('timestamp', 'UNKNOWN')}\n")
                
                # Key accomplishments
                accomplishments = termination_info.get('key_accomplishments', [])
                if accomplishments:
                    f.write(f"  Key Accomplishments:\n")
                    for acc in accomplishments:
                        f.write(f"    - {acc}\n")
                
                # Next steps
                next_steps = termination_info.get('next_steps', [])
                if next_steps:
                    f.write(f"  Next Steps:\n")
                    for step in next_steps:
                        f.write(f"    - {step}\n")
                
                f.write("\n")

            f.write("AGENT WORKFLOW:\n")
            f.write("-" * 80 + "\n")
            for i, agent_action in enumerate(log.get('agents', []), 1):
                f.write(f"\n[{i}] {agent_action['timestamp']} - {agent_action['agent']}\n")
                f.write(f"    Action: {agent_action['action']}\n")
                f.write(f"    Content: {agent_action['content']}\n")
                if agent_action.get('truncated', False):
                    f.write(f"    [TRUNCATED - Original length: {agent_action.get('original_length', 'unknown')} characters]\n")

            f.write("\n\nTOOL CALLS:\n")
            f.write("-" * 80 + "\n")
            for i, tc in enumerate(log.get('tool_calls', []), 1):
                status = "✓ SUCCESS" if tc['success'] else "✗ FAILED"
                f.write(f"\n[{i}] {tc['timestamp']} - {tc['agent']}\n")
                f.write(f"    Tool: {tc['tool']}\n")
                f.write(f"    Arguments: {json.dumps(tc['arguments'], indent=6)}\n")
                f.write(f"    Status: {status}\n")
                f.write(f"    Result Preview: {tc['result_preview']}\n")
                f.write(f"    Result Length: {tc['result_length']} characters\n")
                if tc.get('truncated', False):
                    f.write(f"    [RESULT TRUNCATED - Full result available in detailed logs]\n")

            f.write("\n\nMESSAGE TIMELINE:\n")
            f.write("-" * 80 + "\n")
            for i, msg in enumerate(log.get('messages', []), 1):
                f.write(f"\n[{i}] {msg['timestamp']} - {msg['source']} ({msg['type']})\n")
                f.write(f"    {msg['content']}\n")
                if msg.get('truncated', False):
                    f.write(f"    [TRUNCATED - Original length: {msg.get('original_length', 'unknown')} characters]\n")

            if log.get('summary'):
                f.write("\n\nSUMMARY:\n")
                f.write("-" * 80 + "\n")
                f.write(f"{log['summary']}\n")

            f.write("\n" + "=" * 80 + "\n")

        logger.info(f"Human-readable summary saved to: {path}")

    def _smart_truncate(self, content: str, max_length: int) -> str:
        """Smart truncation that preserves sentence boundaries."""
        if len(content) <= max_length:
            return content
        
        # Try to find a good truncation point
        truncated = content[:max_length]
        
        # Look for sentence endings within the last 20% of the limit
        search_start = int(max_length * 0.8)
        last_period = truncated.rfind('.', search_start)
        last_exclamation = truncated.rfind('!', search_start)
        last_question = truncated.rfind('?', search_start)
        
        # Find the best sentence boundary
        best_boundary = max(last_period, last_exclamation, last_question)
        
        if best_boundary > search_start:
            truncated = truncated[:best_boundary + 1]
        
        # Add truncation indicator
        truncated += f"\n\n[Content truncated - Full length: {len(content)} characters]"
        
        return truncated


class QPCRAssistant:
    """Multi-agent qPCR assay design assistant using AG2 (AutoGen 0.2.x)."""

    def __init__(self, config_list: List[Dict[str, Any]], log_dir: str = "/results",
                 model_name: Optional[str] = None):
        """
        Initialize qPCR assistant.

        Args:
            config_list: AG2 config list (from OAI_CONFIG_LIST.json)
            log_dir: Directory to save task logs
            model_name: Specific model to use (e.g., "gpt-4o", "gpt-4o-mini").
                       Defaults to "gpt-4o" if not specified (required for function calling).
        """
        self.config_list = config_list
        # Default to gpt-4o if no model specified (needed for function calling)
        self.model_name = model_name or "gpt-4o"
        self.log_dir = log_dir
        self.mcp_bridge = None
        self.mcp_executor = None
        self.agents = {}
        self.groupchat = None
        self.manager = None
        self.task_logger = TaskLogger(log_dir)
        self.event_loop = None  # For running async MCP calls

        # Create llm_config for agents
        self.llm_config = self._build_llm_config()

    def _build_llm_config(self) -> Dict[str, Any]:
        """Build LLM configuration for AG2 agents."""
        # Filter by model name
        filtered_config_list = [
            c for c in self.config_list
            if c.get("model") == self.model_name
        ]
        
        if not filtered_config_list:
            available_models = [c.get("model") for c in self.config_list]
            raise ValueError(
                f"Model '{self.model_name}' not found in config_list. "
                f"Available models: {available_models}"
            )
        
        config = {
            "config_list": filtered_config_list,
            "timeout": 120,
            "temperature": 0.7,
        }
        
        logger.info(f"Using model: {self.model_name} for LLM config")
        return config

    def _build_database_agent_llm_config(self) -> Dict[str, Any]:
        """
        Build LLM configuration specifically for DatabaseAgent with function schemas.
        
        CRITICAL: Function calling in AutoGen requires TWO components:
        1. Function SCHEMAS in llm_config (tells LLM which functions exist)
           - This method adds those schemas
        2. Function HANDLERS in function_map (tells AutoGen how to execute)
           - These are registered separately via agent.register_function()
        
        Both are required for successful function calling.
        """
        # Start with base config
        config = self._build_llm_config().copy()
        
        # Add function schemas for MCP tools
        # This tells the LLM which functions are available and how to call them
        function_schemas = create_autogen_functions(["database"])
        config["functions"] = function_schemas
        
        logger.info(f"DatabaseAgent llm_config includes {len(function_schemas)} function schemas")
        logger.debug(f"Function schemas: {[f['name'] for f in function_schemas]}")
        
        return config

    def initialize(self):
        """Initialize MCP bridge and AutoGen agents (synchronous wrapper)."""
        logger.info("Initializing qPCR Assistant...")

        # Create event loop for async operations
        try:
            self.event_loop = asyncio.get_event_loop()
        except RuntimeError:
            self.event_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.event_loop)

        # Initialize MCP bridge (async)
        self.event_loop.run_until_complete(self._setup_mcp_bridge())

        # Create AutoGen agents (sync)
        self._create_agents()

        logger.info("✅ qPCR Assistant ready!")

    async def _setup_mcp_bridge(self):
        """Setup MCP server connections (async)."""
        server_configs = {
            "database": {
                "container": os.getenv("MCP_DATABASE_SERVER", "ndiag-database-server"),
                "command": ["python", "/app/database_mcp_server.py"]
            }
            # Add more servers as phases complete:
            # "processing": {...},
            # "alignment": {...},
            # "design": {...},
        }

        self.mcp_bridge = MCPClientBridge(server_configs)
        await self.mcp_bridge.start_servers()

        # Create MCP executor
        self.mcp_executor = AutoGenMCPFunctionExecutor(self.mcp_bridge, self.log_dir)

        logger.info("MCP servers connected")

    def _save_sequences_to_file(self, sequences: str, taxon: str, region: str, category: str) -> str:
        """Save sequences to organized folder structure."""
        import os
        import re
        from datetime import datetime

        # Create folder structure
        category_folder = os.path.join(self.log_dir, category)
        os.makedirs(category_folder, exist_ok=True)

        # Sanitize taxon name for filename
        safe_taxon = re.sub(r'[^\w\s-]', '', taxon).replace(' ', '_')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{safe_taxon}_{region}_{timestamp}.fasta"
        filepath = os.path.join(category_folder, filename)

        # Save sequences
        with open(filepath, 'w') as f:
            f.write(sequences)

        # Count sequences
        seq_count = sequences.count(">")

        # Update or create README
        self._update_readme(category_folder, safe_taxon, region, filename, seq_count)

        return filepath

    def _update_readme(self, folder: str, taxon: str, region: str, filename: str, seq_count: int):
        """Create or update README.md in the sequences folder."""
        import os
        from datetime import datetime

        readme_path = os.path.join(folder, "README.md")
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Read existing content if file exists
        existing_entries = ""
        if os.path.exists(readme_path):
            with open(readme_path, 'r') as f:
                content = f.read()
                # Extract existing entries (between table header and downstream section)
                if "## Downloaded Sequences" in content:
                    parts = content.split("## Downstream Workflow")[0]
                    if "| Taxon" in parts:
                        table_lines = [line for line in parts.split('\n') if line.strip().startswith('|') and 'Taxon' not in line and '---' not in line]
                        existing_entries = '\n'.join(table_lines) + '\n' if table_lines else ""

        readme_content = README_TEMPLATE.format(
            timestamp=timestamp,
            existing_entries=existing_entries,
            taxon=taxon,
            region=region,
            filename=filename,
            seq_count=seq_count,
            folder=folder
        )

        with open(readme_path, 'w') as f:
            f.write(readme_content)

    def _create_mcp_function_wrappers(self) -> Dict[str, Callable]:
        """
        Create synchronous wrapper functions for MCP tools.
        AG2 expects synchronous functions, but MCP bridge is async.
        """
        def make_sync_wrapper(func_name: str) -> Callable:
            """Create a sync wrapper for an async MCP function."""
            def wrapper(**kwargs) -> str:
                """Synchronous wrapper that runs async MCP call."""
                try:
                    # CRITICAL: For get_sequences, we need the FULL result before summarization
                    # So we call the MCP bridge directly and handle summarization ourselves
                    if func_name == "get_sequences":
                        # Get full result directly from MCP bridge (no summarization)
                        full_result = self.event_loop.run_until_complete(
                            self.mcp_executor._call_mcp_tool_raw(func_name, kwargs)
                        )
                        
                        # Log the tool call (with full result)
                        self.task_logger.log_tool_call(
                            "DatabaseAgent",
                            func_name,
                            kwargs,
                            full_result
                        )
                        
                        # Save to file and return metadata only
                        result = self._handle_sequence_result(full_result, kwargs)
                        return result
                    
                    # For other functions, use normal flow with summarization
                    result = self.event_loop.run_until_complete(
                        self.mcp_executor.execute_function(func_name, kwargs)
                    )

                    # Log the tool call
                    self.task_logger.log_tool_call(
                        "DatabaseAgent",
                        func_name,
                        kwargs,
                        result
                    )

                    # For extract_sequence_columns, limit output
                    if func_name == "extract_sequence_columns":
                        result = self._handle_metadata_result(result, kwargs)

                    return result
                except Exception as e:
                    error_msg = f"Error calling {func_name}: {str(e)}"
                    logger.error(error_msg)
                    return error_msg

            return wrapper

        # Create wrappers for all MCP tools
        return {
            "get_sequences": make_sync_wrapper("get_sequences"),
            "get_taxonomy": make_sync_wrapper("get_taxonomy"),
            "get_neighbors": make_sync_wrapper("get_neighbors"),
            "extract_sequence_columns": make_sync_wrapper("extract_sequence_columns"),
            "search_sra_studies": make_sync_wrapper("search_sra_studies"),
        }
    
    def _handle_sequence_result(self, result: str, kwargs: dict) -> str:
        """
        Handle get_sequences result: Save to file, return only metadata.
        NEVER send full sequences to LLM (token budget issue).
        
        Args:
            result: FULL sequence data from MCP server (FASTA format)
            kwargs: Original function arguments
        
        Returns:
            Metadata summary (no sequences)
        """
        if not result or result.startswith("Error"):
            return result
        
        # Extract actual FASTA content from MCP response if it's wrapped
        # MCP returns: {'content': [{'type': 'text', 'text': 'FASTA DATA'}], 'isError': False}
        actual_fasta = result
        try:
            import json
            parsed = json.loads(result) if isinstance(result, str) and result.startswith('{') else None
            if parsed and isinstance(parsed, dict):
                if 'content' in parsed:
                    content_list = parsed['content']
                    if isinstance(content_list, list) and len(content_list) > 0:
                        first_content = content_list[0]
                        if isinstance(first_content, dict) and 'text' in first_content:
                            actual_fasta = first_content['text']
        except:
            pass  # Use result as-is if not JSON
        
        # Extract info from kwargs
        taxon = kwargs.get("taxon", "unknown").replace(" ", "_")
        region = kwargs.get("region", "unknown")
        source = kwargs.get("source", "unknown")
        
        # Save PURE FASTA sequences to file (no metadata, no wrapping)
        category = "sequences"
        filepath = self._save_sequences_to_file(actual_fasta, taxon, region, category)
        
        # Count sequences
        seq_count = actual_fasta.count(">")
        
        # Extract first 3 sequence headers (not full sequences!)
        lines = actual_fasta.split('\n')
        headers = []
        for line in lines[:50]:  # Only look at first 50 lines
            if line.startswith('>'):
                headers.append(line[:100])  # Truncate long headers
                if len(headers) >= 3:
                    break
        
        # Calculate average sequence length
        sequences_only = actual_fasta.split('>')[1:]  # Split by header
        if sequences_only:
            total_length = 0
            count = 0
            for seq in sequences_only[:10]:  # Sample first 10
                seq_lines = seq.split('\n')[1:]  # Skip header
                seq_data = ''.join(seq_lines)
                total_length += len(seq_data)
                count += 1
            avg_length = total_length // count if count > 0 else 0
        else:
            avg_length = 0
        
        # Return ONLY metadata - no actual sequence data
        summary = f"""✓ Retrieved {seq_count} sequences for {taxon} ({region} from {source})

**File saved:** {filepath}

**Sample headers (first 3):**
{chr(10).join(headers) if headers else "No headers found"}

**Statistics:**
- Total sequences: {seq_count}
- Average length: ~{avg_length}bp
- Source: {source}
- Region: {region}

The sequences have been saved to the file above. Use extract_sequence_columns if you need to parse metadata.
Do NOT request the full sequence content - it's already saved."""
        
        return summary
    
    def _handle_metadata_result(self, result: str, kwargs: dict) -> str:
        """
        Handle extract_sequence_columns result: Limit to first 10 records.
        """
        if not result or result.startswith("Error"):
            return result
        
        # If result is very long, truncate to first 10 records
        try:
            import json
            data = json.loads(result) if isinstance(result, str) else result
            
            if isinstance(data, list) and len(data) > 10:
                truncated_data = data[:10]
                summary = json.dumps(truncated_data, indent=2)
                summary += f"\n\n... and {len(data) - 10} more records (total: {len(data)} records)"
                return summary
            elif isinstance(data, dict) and "records" in data:
                records = data["records"]
                if len(records) > 10:
                    data["records"] = records[:10]
                    summary = json.dumps(data, indent=2)
                    summary += f"\n\n... and {len(records) - 10} more records (total: {len(records)} records)"
                    return summary
        except:
            pass
        
        # If not too long or can't parse, return as-is (but limit to 3000 chars)
        if len(result) > 3000:
            return result[:3000] + f"\n\n... [Truncated: {len(result) - 3000} more characters]"
        
        return result

    def _create_agents(self):
        """Create AutoGen agent team (AG2 0.2.x style)."""

        # Verify MCP bridge is initialized
        if not self.mcp_executor:
            raise RuntimeError("MCP executor not initialized. Call _initialize_mcp_bridge() first.")
        
        logger.info("MCP executor verified - creating agents with tool access")

        # Display model information
        model_info = self.config_list[0] if self.config_list else {}
        model_name = self.model_name or model_info.get("model", "unknown")
        api_type = model_info.get("api_type", "unknown")

        model_display = MODEL_DISPLAY_NAMES.get(model_name, f"{api_type.upper()} - {model_name}")

        print_colored(f"🤖 Using {model_display}", Colors.BRIGHT_GREEN)

        # Create MCP function wrappers
        mcp_functions = self._create_mcp_function_wrappers()

        # Create function map for registration
        function_map = {
            "get_sequences": mcp_functions["get_sequences"],
            "get_taxonomy": mcp_functions["get_taxonomy"],
            "get_neighbors": mcp_functions["get_neighbors"],
            "extract_sequence_columns": mcp_functions["extract_sequence_columns"],
            "search_sra_studies": mcp_functions["search_sra_studies"],
        }

        # 1. Coordinator Agent
        self.agents["coordinator"] = AssistantAgent(
            name="Coordinator",
            system_message=COORDINATOR_SYSTEM_MESSAGE,
            llm_config=self.llm_config
        )

        # 2. Database Agent (with MCP tools)
        # CRITICAL FIX: Create specialized llm_config with function schemas
        # This tells the LLM which functions are available so it can generate proper function calls
        database_llm_config = self._build_database_agent_llm_config()
        
        self.agents["database"] = AssistantAgent(
            name="DatabaseAgent",
            system_message=DATABASE_AGENT_SYSTEM_MESSAGE,
            llm_config=database_llm_config  # ← Now includes function schemas
        )

        # Register functions with DatabaseAgent for execution
        # This provides the actual execution handlers when LLM generates function calls
        self.agents["database"].register_function(
            function_map=function_map
        )
        
        # Verify function registration
        logger.info(f"DatabaseAgent registered functions: {list(function_map.keys())}")
        logger.debug(f"DatabaseAgent function_map keys: {list(self.agents['database']._function_map.keys()) if hasattr(self.agents['database'], '_function_map') else 'N/A'}")
        
        # Validate that function schemas match execution handlers
        schema_names = {f["name"] for f in database_llm_config["functions"]}
        handler_names = set(function_map.keys())
        if schema_names == handler_names:
            logger.info(f"✓ Function schemas and handlers match: {sorted(schema_names)}")
        else:
            missing_handlers = schema_names - handler_names
            extra_handlers = handler_names - schema_names
            if missing_handlers:
                logger.warning(f"⚠️  Function schemas without handlers: {missing_handlers}")
            if extra_handlers:
                logger.warning(f"⚠️  Function handlers without schemas: {extra_handlers}")

        # 3. Analysis Agent
        self.agents["analyst"] = AssistantAgent(
            name="AnalystAgent",
            system_message=ANALYST_SYSTEM_MESSAGE,
            llm_config=self.llm_config
        )

        # 4. User Proxy (for termination and user interaction)
        self.agents["user_proxy"] = UserProxyAgent(
            name="User",
            human_input_mode="NEVER",  # Don't ask for user input during workflow
            max_consecutive_auto_reply=50,  # Allow more interactions
            is_termination_msg=self._is_termination_message,
            code_execution_config=False,
            function_map=function_map,  # Register functions with user proxy for execution
        )

        # Create group chat
        max_rounds = int(os.getenv("AUTOGEN_MAX_ROUNDS", "20"))  # Use environment variable or default to 20
        logger.info(f"Setting max_rounds to {max_rounds} (from AUTOGEN_MAX_ROUNDS env var)")
        self.groupchat = GroupChat(
            agents=[
                self.agents["coordinator"],
                self.agents["database"],
                self.agents["analyst"],
                self.agents["user_proxy"]
            ],
            messages=[],
            max_round=max_rounds,  # Use environment variable for max rounds
            speaker_selection_method="auto",  # Let LLM decide next speaker
            allow_repeat_speaker=False,  # Prevent infinite loops
        )

        # Create group chat manager
        self.manager = GroupChatManager(
            groupchat=self.groupchat,
            llm_config=self.llm_config
        )

        logger.info(f"Created {len(self.agents)} agents")
        
        # Test function availability (optional - only log, don't fail)
        try:
            test_func = function_map.get("get_taxonomy")
            if test_func and callable(test_func):
                logger.info("✓ Function registration test: get_taxonomy is callable")
            else:
                logger.warning("⚠ Function registration test: get_taxonomy is NOT callable")
        except Exception as e:
            logger.warning(f"Function registration test failed (non-critical): {e}")

    def health_check(self) -> Dict[str, Any]:
        """
        Check if agent system is properly configured for function calling.
        
        Returns:
            Dictionary with health status and configuration details.
        """
        checks = {
            "mcp_bridge_initialized": self.mcp_bridge is not None,
            "mcp_executor_initialized": self.mcp_executor is not None,
            "agents_created": len(self.agents) > 0,
            "database_agent_exists": "database" in self.agents,
        }
        
        # Check if DatabaseAgent has functions in llm_config
        if checks["database_agent_exists"]:
            db_agent = self.agents["database"]
            checks["database_agent_has_function_schemas"] = (
                hasattr(db_agent, "llm_config") and
                isinstance(db_agent.llm_config, dict) and
                "functions" in db_agent.llm_config
            )
            
            if checks["database_agent_has_function_schemas"]:
                checks["function_count"] = len(db_agent.llm_config["functions"])
                checks["function_names"] = [
                    f["name"] for f in db_agent.llm_config["functions"]
                ]
            
            # Check if functions are registered for execution
            checks["database_agent_has_function_map"] = (
                hasattr(db_agent, "_function_map") and
                len(db_agent._function_map) > 0
            )
            
            if checks["database_agent_has_function_map"]:
                checks["registered_handlers"] = list(db_agent._function_map.keys())
                
                # Check for schema-handler consistency
                if checks["database_agent_has_function_schemas"]:
                    schema_names = set(checks["function_names"])
                    handler_names = set(checks["registered_handlers"])
                    checks["schemas_and_handlers_match"] = schema_names == handler_names
        
        # Overall health status
        critical_checks = [
            checks["mcp_bridge_initialized"],
            checks["database_agent_exists"],
            checks.get("database_agent_has_function_schemas", False),
            checks.get("database_agent_has_function_map", False),
            checks.get("schemas_and_handlers_match", False)
        ]
        
        checks["status"] = "healthy" if all(critical_checks) else "unhealthy"
        checks["ready_for_function_calling"] = all(critical_checks)
        
        return checks

    def _is_termination_message(self, message: Dict[str, Any]) -> bool:
        """
        Enhanced termination condition to prevent infinite loops and handle task completion.
        
        Args:
            message: The message to check for termination
            
        Returns:
            True if the conversation should terminate
        """
        content = message.get("content", "").rstrip()
        sender = message.get("name", "unknown")
        
        # 1. Explicit termination condition (highest priority)
        if content.endswith("TERMINATE"):
            logger.info(f"Explicit termination message detected from {sender}: 'TERMINATE'")
            self._log_termination_reason("EXPLICIT_TERMINATE", content, sender)
            return True
            
        # 2. Check for repetitive messages (loop detection)
        if hasattr(self, 'groupchat') and self.groupchat and len(self.groupchat.messages) > 5:
            recent_messages = self.groupchat.messages[-8:]  # Last 8 messages
            if len(recent_messages) >= 6:
                # Check if the last 6 messages are very similar
                contents = [msg.get("content", "") for msg in recent_messages[-6:] if isinstance(msg, dict)]
                unique_contents = len(set(contents))
                if unique_contents <= 2:  # Only 1-2 unique messages in last 6
                    logger.warning(f"Detected potential infinite loop - only {unique_contents} unique messages in last 6")
                    self._log_termination_reason("INFINITE_LOOP", content, sender)
                    return True
                    
        # 3. Check for task completion indicators
        completion_phrases = [
            "workflow completed",
            "task completed", 
            "design completed",
            "analysis completed",
            "project completed",
            "experimental validation phase",
            "ready to advance",
            "data collection complete",
            "sequences retrieved",
            "primer design complete",
            "assay design complete"
        ]
        
        content_lower = content.lower()
        for phrase in completion_phrases:
            if phrase in content_lower:
                logger.info(f"Task completion phrase detected from {sender}: '{phrase}'")
                self._log_termination_reason("TASK_COMPLETION", content, sender)
                return True
                
        # 4. Check for error conditions that prevent progress
        error_phrases = [
            "cannot proceed",
            "unable to continue",
            "critical error",
            "tool failure",
            "insufficient data",
            "no sequences found",
            "database error"
        ]
        
        for phrase in error_phrases:
            if phrase in content_lower:
                logger.warning(f"Error condition detected from {sender}: '{phrase}'")
                self._log_termination_reason("ERROR_CONDITION", content, sender)
                return True
                
        # 5. Check conversation length (safety net)
        if hasattr(self, 'groupchat') and self.groupchat:
            current_rounds = len(self.groupchat.messages)
            max_rounds = int(os.getenv("AUTOGEN_MAX_ROUNDS", "20"))
            if current_rounds >= max_rounds - 2:  # Stop 2 rounds before max
                logger.warning(f"Approaching maximum rounds ({current_rounds}/{max_rounds}) - terminating conversation")
                self._log_termination_reason("MAX_ROUNDS_APPROACHING", content, sender)
                return True
                
        return False
    
    def _log_termination_reason(self, reason: str, content: str, sender: str):
        """Log the reason for termination with context."""
        termination_info = {
            "reason": reason,
            "sender": sender,
            "message_preview": content[:200] + "..." if len(content) > 200 else content,
            "timestamp": datetime.now().isoformat(),
            "termination_reason": reason  # For consistency with summary structure
        }
        
        # Store termination info for summary generation
        if not hasattr(self, '_termination_info'):
            self._termination_info = termination_info
        else:
            self._termination_info.update(termination_info)
            
        # Log the termination reason to the task logger
        self.task_logger.log_agent_action(
            "SYSTEM", 
            "termination_detected", 
            f"Conversation terminated by {sender}. Reason: {reason}. Message: {content[:100]}..."
        )
            
        logger.info(f"Termination reason logged: {reason} from {sender}")

    def _detect_termination_from_messages(self, messages: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        Detect termination reason by analyzing messages.
        Fallback method when is_termination_msg was not called by AutoGen GroupChat.
        
        Args:
            messages: List of conversation messages
            
        Returns:
            Dictionary with termination info (reason, sender, timestamp)
        """
        # First check if _termination_info was already set
        if hasattr(self, '_termination_info') and self._termination_info:
            return self._termination_info
        
        # Fallback: Analyze messages to detect termination
        if not messages:
            return {'reason': 'NO_MESSAGES', 'sender': 'SYSTEM', 'timestamp': datetime.now().isoformat()}
        
        # Check last few messages for termination indicators
        for msg in reversed(messages[-10:]):  # Check last 10 messages
            if not isinstance(msg, dict):
                continue
                
            content = msg.get("content", "").rstrip()
            sender = msg.get("name", "unknown")
            
            # 1. Explicit TERMINATE keyword
            if content.endswith("TERMINATE"):
                return {
                    'reason': 'EXPLICIT_TERMINATE',
                    'sender': sender,
                    'timestamp': datetime.now().isoformat()
                }
            
            # 2. Task completion phrases
            content_lower = content.lower()
            completion_phrases = [
                "workflow completed",
                "task completed",
                "design completed",
                "analysis completed",
                "project completed",
                "experimental validation phase",
                "ready to advance",
                "data collection complete",
                "sequences retrieved",
                "primer design complete",
                "assay design complete"
            ]
            
            for phrase in completion_phrases:
                if phrase in content_lower:
                    return {
                        'reason': 'TASK_COMPLETION',
                        'sender': sender,
                        'timestamp': datetime.now().isoformat()
                    }
        
        # 3. Check if max rounds was reached
        max_rounds = int(os.getenv("AUTOGEN_MAX_ROUNDS", "20"))
        if len(messages) >= max_rounds:
            return {
                'reason': 'MAX_ROUNDS_REACHED',
                'sender': 'SYSTEM',
                'timestamp': datetime.now().isoformat()
            }
        
        # 4. Default: Unknown termination
        return {
            'reason': 'CONVERSATION_ENDED',
            'sender': messages[-1].get("name", "unknown") if messages else 'UNKNOWN',
            'timestamp': datetime.now().isoformat()
        }
    
    def _log_termination_summary(self, termination_summary: Dict[str, Any]):
        """Log the comprehensive termination summary to the task logger."""
        # Log key accomplishments
        accomplishments = termination_summary.get('key_accomplishments', [])
        if accomplishments:
            self.task_logger.log_agent_action(
                "SYSTEM",
                "termination_summary",
                f"Key accomplishments: {'; '.join(accomplishments)}"
            )
        
        # Log recommendations
        recommendations = termination_summary.get('recommendations', [])
        if recommendations:
            self.task_logger.log_agent_action(
                "SYSTEM",
                "termination_recommendations",
                f"Recommendations: {'; '.join(recommendations[:3])}"  # Limit to top 3
            )
        
        # Log next steps
        next_steps = termination_summary.get('next_steps', [])
        if next_steps:
            self.task_logger.log_agent_action(
                "SYSTEM",
                "termination_next_steps",
                f"Next steps: {'; '.join(next_steps)}"
            )
        
        # Log overall summary
        summary_text = f"Workflow terminated with reason: {termination_summary.get('termination_reason', 'UNKNOWN')}. "
        summary_text += f"Total messages: {termination_summary.get('total_messages', 0)}. "
        summary_text += f"Agents involved: {', '.join(termination_summary.get('agents_involved', []))}"
        
        self.task_logger.log_agent_action(
            "SYSTEM",
            "termination_final_summary",
            summary_text
        )

    def _generate_termination_summary(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a comprehensive summary of what was accomplished and next steps.
        
        Args:
            messages: List of conversation messages
            
        Returns:
            Dictionary containing summary information
        """
        # FALLBACK: If _termination_info was not set (GroupChat bypassed UserProxy's termination check),
        # analyze the messages to determine termination reason
        termination_info = self._detect_termination_from_messages(messages)
        
        summary = {
            "termination_reason": termination_info.get('reason', 'UNKNOWN'),
            "sender": termination_info.get('sender', 'UNKNOWN'),
            "timestamp": termination_info.get('timestamp', 'UNKNOWN'),
            "total_messages": len(messages),
            "agents_involved": [],
            "key_accomplishments": [],
            "data_retrieved": {},
            "recommendations": [],
            "next_steps": [],
            "files_generated": []
        }
        
        # Analyze messages to extract key information
        for msg in messages:
            if not isinstance(msg, dict):
                continue
                
            sender = msg.get("name", "unknown")
            content = msg.get("content", "")
            
            # Track agents involved
            if sender not in summary["agents_involved"]:
                summary["agents_involved"].append(sender)
            
            # Extract key accomplishments based on content
            content_lower = content.lower()
            
            # Data retrieval accomplishments
            if "sequences" in content_lower and "retrieved" in content_lower:
                summary["key_accomplishments"].append("Sequences retrieved from databases")
            if "taxonomy" in content_lower and "verified" in content_lower:
                summary["key_accomplishments"].append("Species taxonomy verified")
            if "off-target" in content_lower and "identified" in content_lower:
                summary["key_accomplishments"].append("Off-target species identified")
            
            # Analysis accomplishments
            if "analysis" in content_lower and "complete" in content_lower:
                summary["key_accomplishments"].append("Sequence analysis completed")
            if "primer" in content_lower and ("recommended" in content_lower or "designed" in content_lower):
                summary["key_accomplishments"].append("Primer design recommendations provided")
            
            # Extract recommendations
            if "recommend" in content_lower or "suggest" in content_lower:
                # Extract recommendation sentences
                sentences = content.split('.')
                for sentence in sentences:
                    if "recommend" in sentence.lower() or "suggest" in sentence.lower():
                        summary["recommendations"].append(sentence.strip())
            
            # Extract next steps
            if "next step" in content_lower or "validation" in content_lower or "experiment" in content_lower:
                sentences = content.split('.')
                for sentence in sentences:
                    if any(phrase in sentence.lower() for phrase in ["next step", "validation", "experiment", "should", "need to"]):
                        summary["next_steps"].append(sentence.strip())
        
        # Generate appropriate next steps based on termination reason
        termination_reason = summary["termination_reason"]
        if termination_reason == "EXPLICIT_TERMINATE":
            summary["next_steps"].append("Review the generated data files in /results/ directory")
            summary["next_steps"].append("Proceed with experimental validation of recommended primers")
        elif termination_reason == "TASK_COMPLETION":
            summary["next_steps"].append("Data collection phase completed successfully")
            summary["next_steps"].append("Ready to advance to primer design and validation phase")
        elif termination_reason == "ERROR_CONDITION":
            summary["next_steps"].append("Review error logs and consider alternative approaches")
            summary["next_steps"].append("Verify species names and database connectivity")
        elif termination_reason in ["MAX_ROUNDS_APPROACHING", "MAX_ROUNDS_REACHED"]:
            summary["next_steps"].append("Conversation reached maximum rounds limit")
            summary["next_steps"].append("Review partial results and consider continuing with new session")
        elif termination_reason == "INFINITE_LOOP":
            summary["next_steps"].append("Conversation terminated due to detected loop")
            summary["next_steps"].append("Review conversation logs and restart with clearer objectives")
        elif termination_reason == "CONVERSATION_ENDED":
            summary["next_steps"].append("Workflow completed - review results in /results/ directory")
            summary["next_steps"].append("Continue with next phase of qPCR assay design")
        
        return summary

    def _print_termination_summary(self, summary: Dict[str, Any]):
        """Print a formatted termination summary to the user."""
        print()
        print_colored("═══════════════════════════════════════════════════════════════════════════", Colors.CYAN)
        print_colored("📋 TASK TERMINATION SUMMARY", Colors.BRIGHT_YELLOW, bold=True)
        print_colored("═══════════════════════════════════════════════════════════════════════════", Colors.CYAN)
        print()
        
        # Termination reason
        reason_colors = {
            "EXPLICIT_TERMINATE": Colors.GREEN,
            "TASK_COMPLETION": Colors.GREEN,
            "ERROR_CONDITION": Colors.RED,
            "MAX_ROUNDS_APPROACHING": Colors.YELLOW,
            "MAX_ROUNDS_REACHED": Colors.YELLOW,
            "INFINITE_LOOP": Colors.YELLOW,
            "CONVERSATION_ENDED": Colors.CYAN,
            "NO_MESSAGES": Colors.RED
        }
        reason_color = reason_colors.get(summary["termination_reason"], Colors.WHITE)
        print_colored(f"Termination Reason: {summary['termination_reason']}", reason_color, bold=True)
        print()
        
        # Statistics
        print_colored("📊 Statistics:", Colors.BRIGHT_CYAN, bold=True)
        print(f"  • Total Messages: {summary['total_messages']}")
        print(f"  • Agents Involved: {', '.join(summary['agents_involved'])}")
        print()
        
        # Key accomplishments
        if summary["key_accomplishments"]:
            print_colored("✅ Key Accomplishments:", Colors.BRIGHT_GREEN, bold=True)
            for accomplishment in summary["key_accomplishments"]:
                print(f"  • {accomplishment}")
            print()
        
        # Recommendations
        if summary["recommendations"]:
            print_colored("💡 Recommendations:", Colors.BRIGHT_YELLOW, bold=True)
            for rec in summary["recommendations"][:3]:  # Limit to top 3
                print(f"  • {rec}")
            print()
        
        # Next steps
        if summary["next_steps"]:
            print_colored("🚀 Next Steps:", Colors.BRIGHT_BLUE, bold=True)
            for step in summary["next_steps"]:
                print(f"  • {step}")
            print()
        
        print_colored("═══════════════════════════════════════════════════════════════════════════", Colors.CYAN)
        print()

    def run_workflow(self, user_message: str) -> List[Dict[str, Any]]:
        """
        Run a qPCR design workflow (synchronous).

        Args:
            user_message: User's request for qPCR design

        Returns:
            List of messages from the conversation
        """
        logger.info("Starting qPCR design workflow...")

        # Start logging session
        self.task_logger.start_session(user_message)
        self.task_logger.log_message("user", "request", user_message)

        try:
            # Initiate the chat
            self.agents["user_proxy"].initiate_chat(
                self.manager,
                message=user_message
            )

            # Get all messages
            messages = self.groupchat.messages

            # Log messages (avoid duplicate logging)
            for msg in messages:
                if isinstance(msg, dict):
                    sender = msg.get("name", "unknown")
                    content = msg.get("content", "")
                    # Only log as message to avoid duplication
                    self.task_logger.log_message(sender, "message", content)

            # Generate and display termination summary
            termination_summary = self._generate_termination_summary(messages)
            self._print_termination_summary(termination_summary)

            # Log the termination summary to task logger
            self._log_termination_summary(termination_summary)

            # End logging session with detailed summary and termination info
            detailed_summary = f"Completed qPCR design workflow with {len(messages)} messages exchanged. Termination reason: {termination_summary['termination_reason']}. Key accomplishments: {', '.join(termination_summary['key_accomplishments'])}"
            log_path = self.task_logger.end_session(detailed_summary, termination_info=termination_summary)

            logger.info(f"Workflow completed with {len(messages)} messages. Termination reason: {termination_summary['termination_reason']}")

            return messages

        except Exception as e:
            logger.error(f"Error in workflow: {e}", exc_info=True)
            self.task_logger.end_session(f"Workflow failed with error: {str(e)}")
            raise

    def shutdown(self):
        """Cleanup resources (synchronous wrapper)."""
        try:
            if self.mcp_bridge:
                self.event_loop.run_until_complete(self.mcp_bridge.shutdown())
        except Exception as e:
            logger.warning(f"Error during shutdown: {e}")
        finally:
            if self.event_loop and self.event_loop.is_running():
                self.event_loop.close()


def print_banner():
    """Print welcome banner with colors."""
    print()
    
    # Print banner lines
    for i, line in enumerate(BANNER_LINES):
        if i in [0, 7]:  # Top and bottom borders
            print_colored(line, Colors.CYAN, bold=True)
        elif i in [1, 3, 6]:  # Empty lines
            print_colored(line, Colors.CYAN, bold=True)
        elif i == 2:  # Title line
            print_colored(line, Colors.CYAN, bold=True)
        else:  # Content lines
            print_colored(line, Colors.BRIGHT_WHITE)
    print()

    # Print commands
    print_colored("📋 Available Commands:", Colors.BRIGHT_YELLOW, bold=True)
    for cmd, desc in COMMANDS_TEXT.items():
        print(f"  {colored(cmd, Colors.GREEN)}    - {desc}")
    print()

    # Print agents
    print_colored("🤖 Active Agents:", Colors.BRIGHT_YELLOW, bold=True)
    for agent_name, agent_desc in AGENTS_INFO:
        print(f"  {colored('•', Colors.BLUE)} {colored(agent_name, Colors.BRIGHT_CYAN)}  - {agent_desc}")
    print()

    # Print getting started
    print_colored("💡 Getting Started:", Colors.BRIGHT_YELLOW, bold=True)
    for text in GETTING_STARTED_TEXT:
        color = Colors.WHITE if "naturally" in text else Colors.BRIGHT_BLACK
        print_colored(f"  {text}", color)
    print()

    # Print example
    print_colored("📝 Example:", Colors.BRIGHT_GREEN, bold=True)
    print_colored(f'  {EXAMPLE_REQUEST}', Colors.WHITE)
    print()
    print_colored("═══════════════════════════════════════════════════════════════════════════", Colors.CYAN)


def print_help():
    """Print help information with colors."""
    print()
    print_colored("═══════════════════════════════════════════════════════════════════════════", Colors.CYAN)
    print_colored("📚 USAGE EXAMPLES", Colors.BRIGHT_YELLOW, bold=True)
    print_colored("═══════════════════════════════════════════════════════════════════════════", Colors.CYAN)
    print()

    # Print examples
    for i, example in enumerate(HELP_EXAMPLES, 1):
        print_colored(f"{i}. {example['title']}", Colors.BRIGHT_GREEN, bold=True)
        for line in example['description']:
            print_colored(f'   {line}', Colors.WHITE)
        print()

    # Print tips
    print_colored("💡 TIPS:", Colors.BRIGHT_YELLOW, bold=True)
    for tip in HELP_TIPS:
        print(f"  {colored('•', Colors.BLUE)} {tip}")
    print()

    print_colored("📁 All workflows are logged to /results/task_TIMESTAMP.json", Colors.BRIGHT_BLACK)
    print_colored("═══════════════════════════════════════════════════════════════════════════", Colors.CYAN)
    print()


def show_recent_logs():
    """Show recent task logs (synchronous)."""
    try:
        log_dir = "/results"
        if not os.path.exists(log_dir):
            print("\nNo task logs found yet.\n")
            return

        log_files = sorted(
            [f for f in os.listdir(log_dir) if f.endswith("_summary.txt")],
            reverse=True
        )

        if not log_files:
            print("\nNo task logs found yet.\n")
            return

        print(f"\n{'='*75}")
        print("RECENT TASK LOGS:")
        print(f"{'='*75}\n")

        for i, log_file in enumerate(log_files[:5], 1):
            log_path = os.path.join(log_dir, log_file)
            print(f"{i}. {log_file}")

            # Show first few lines of summary
            with open(log_path, 'r') as f:
                lines = f.readlines()
                if len(lines) > 30:
                    print("".join(lines[:30]))
                    print(f"   ... (truncated, {len(lines)} total lines)")
                else:
                    print("".join(lines))
            print(f"\n{'-'*75}\n")

    except Exception as e:
        print(f"\nError reading logs: {e}\n")


def clarify_and_confirm_request(initial_request: str) -> tuple:
    """
    Clarify the user's request through interactive Q&A and build a comprehensive plan.
    Returns (proceed, plan_dict) where proceed indicates if user confirmed.
    """
    print()
    print_colored("═══════════════════════════════════════════════════════════════════════════", Colors.CYAN)
    print_colored("🔍 REQUEST CLARIFICATION", Colors.BRIGHT_YELLOW, bold=True)
    print_colored("═══════════════════════════════════════════════════════════════════════════", Colors.CYAN)
    print()

    print_colored("I'll help you design a qPCR assay. Let me ask a few questions to ensure", Colors.WHITE)
    print_colored("we create the best possible design for your needs.", Colors.WHITE)
    print()

    plan = {
        "initial_request": initial_request,
        "target_species": None,
        "off_target_species": [],
        "genomic_region": None,
        "application": None,
        "additional_requirements": []
    }

    # Ask questions using the resource data
    for i, question in enumerate(CLARIFICATION_QUESTIONS, 1):
        print_colored(f"Question {i}/5: {question['title']}", Colors.BRIGHT_GREEN, bold=True)
        print_colored(question['prompt'], Colors.WHITE)
        print(f"{colored('Example:', Colors.BRIGHT_BLACK)} {question['example']}")
        
        if 'tip' in question:
            print(f"{colored('Tip:', Colors.BRIGHT_YELLOW)} {question['tip']}")
        
        user_input = colored_input("└─> ").strip()
        
        # Store the response based on question type
        if question['title'] == "Target Species":
            plan["target_species"] = user_input
        elif question['title'] == "Off-Target Species":
            if user_input:
                plan["off_target_species"] = [s.strip() for s in user_input.split(',')]
        elif question['title'] == "Genomic Region":
            plan["genomic_region"] = user_input if user_input else "auto-select"
        elif question['title'] == "Application Context":
            plan["application"] = user_input
        elif question['title'] == "Additional Requirements":
            if user_input:
                plan["additional_requirements"] = [r.strip() for r in user_input.split(',')]
        
        print()

    # Display comprehensive plan
    print_colored("═══════════════════════════════════════════════════════════════════════════", Colors.CYAN)
    print_colored("📋 COMPREHENSIVE ASSAY DESIGN PLAN", Colors.BRIGHT_YELLOW, bold=True)
    print_colored("═══════════════════════════════════════════════════════════════════════════", Colors.CYAN)
    print()

    print_colored("Target Species:", Colors.BRIGHT_CYAN, bold=True)
    print(f"  {colored('→', Colors.BLUE)} {plan['target_species']}")
    print()

    if plan["off_target_species"]:
        print_colored("Off-Target Species:", Colors.BRIGHT_CYAN, bold=True)
        for off_target in plan["off_target_species"]:
            print(f"  {colored('→', Colors.BLUE)} {off_target}")
    else:
        print_colored("Off-Target Species:", Colors.BRIGHT_CYAN, bold=True)
        print(f"  {colored('→', Colors.YELLOW)} Will identify taxonomically related species automatically")
    print()

    print_colored("Genomic Region:", Colors.BRIGHT_CYAN, bold=True)
    print(f"  {colored('→', Colors.BLUE)} {plan['genomic_region']}")
    print()

    print_colored("Application:", Colors.BRIGHT_CYAN, bold=True)
    print(f"  {colored('→', Colors.BLUE)} {plan['application']}")
    print()

    if plan["additional_requirements"]:
        print_colored("Additional Requirements:", Colors.BRIGHT_CYAN, bold=True)
        for req in plan["additional_requirements"]:
            print(f"  {colored('→', Colors.BLUE)} {req}")
        print()

    print_colored("Planned Workflow Steps:", Colors.BRIGHT_CYAN, bold=True)
    workflow_steps = WORKFLOW_STEPS if plan["off_target_species"] else WORKFLOW_STEPS_AUTO_OFFTARGETS
    for i, step in enumerate(workflow_steps, 1):
        print(f"  {colored(f'{i}.', Colors.GREEN)} {step}")
    print()

    print_colored("═══════════════════════════════════════════════════════════════════════════", Colors.CYAN)
    print()

    # Confirmation
    print_colored("⚠️  Please review the plan above carefully.", Colors.BRIGHT_YELLOW, bold=True)
    print()
    print_colored("Do you want to proceed with this workflow?", Colors.WHITE, bold=True)
    print(f"  {colored('yes', Colors.GREEN)} / {colored('y', Colors.GREEN)}  - Start the workflow")
    print(f"  {colored('no', Colors.RED)}  / {colored('n', Colors.RED)}  - Cancel and start over")
    print(f"  {colored('edit', Colors.YELLOW)} / {colored('e', Colors.YELLOW)} - Modify the plan")
    print()

    confirmation = colored_input("└─> ").strip().lower()
    print()

    if confirmation in ['yes', 'y']:
        print_colored(SUCCESS_MESSAGES["confirmed"], Colors.BRIGHT_GREEN, bold=True)
        print()
        return True, plan
    elif confirmation in ['edit', 'e']:
        print_colored(SUCCESS_MESSAGES["modify_plan"], Colors.YELLOW)
        print()
        return False, None
    else:
        print_colored(SUCCESS_MESSAGES["cancelled"], Colors.RED)
        print()
        return False, None


def setup_readline():
    """Configure readline for proper line editing (backspace, arrow keys, etc.)"""
    try:
        # Enable readline features
        readline.parse_and_bind('tab: complete')  # Tab completion
        readline.parse_and_bind('set editing-mode emacs')  # Emacs-style editing

        # Set up history
        histfile = os.path.join(os.path.expanduser("~"), ".qpcr_assistant_history")
        try:
            readline.read_history_file(histfile)
            readline.set_history_length(1000)
        except FileNotFoundError:
            pass

        # Save history on exit
        import atexit
        atexit.register(readline.write_history_file, histfile)

    except Exception as e:
        # Readline might not be available on all systems
        pass


def colored_input(prompt_text: str, prompt_color: str = Colors.BRIGHT_CYAN) -> str:
    """
    Get input with a colored prompt that readline understands.
    Uses readline-compatible escape sequences to prevent prompt deletion.
    """
    # Readline escape sequences to mark non-printing characters
    # \001 = RL_PROMPT_START_IGNORE
    # \002 = RL_PROMPT_END_IGNORE
    rl_start = '\001'
    rl_end = '\002'

    # Wrap color codes in readline ignore markers
    colored_prompt = f"{rl_start}{prompt_color}{rl_end}{prompt_text}{rl_start}{Colors.RESET}{rl_end}"

    return input(colored_prompt)


def interactive_mode():
    """Run interactive chat interface (synchronous)."""
    # Setup readline for proper terminal input handling
    setup_readline()

    # Ensure terminal is in proper state
    try:
        os.system('stty sane 2>/dev/null')  # Fix terminal settings (Unix/Linux/Mac)
    except:
        pass

    # Load environment variables from .env file (CRITICAL for API keys)
    try:
        from dotenv import load_dotenv
        env_file = os.path.join(os.path.dirname(__file__), ".env")
        if os.path.exists(env_file):
            load_dotenv(env_file)
            logger.info(f"Loaded environment from {env_file}")
    except ImportError:
        logger.warning("python-dotenv not installed, using existing environment variables")

    # Load config from OAI_CONFIG_LIST.json
    config_file = os.path.join(os.path.dirname(__file__), "OAI_CONFIG_LIST.json")
    if not os.path.exists(config_file):
        print_colored(f"\n{ERROR_MESSAGES['config_not_found']}", Colors.BRIGHT_RED, bold=True)
        print_colored(f"Expected at: {config_file}\n", Colors.WHITE)
        return

    with open(config_file, 'r') as f:
        config_list = json.load(f)

    # Determine which model to use
    # CRITICAL: Default to gpt-4o for function calling support
    # Gemini client doesn't support function calling yet
    model_name = os.getenv("MODEL_NAME", "gpt-4o")

    # Check if API keys are available
    gemini_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    # Validate that at least one API key is set
    if not gemini_key and not openai_key:
        print_colored(f"\n{ERROR_MESSAGES['no_api_keys']}", Colors.BRIGHT_RED, bold=True)
        print_colored("Please set GOOGLE_API_KEY or OPENAI_API_KEY in autogen_app/.env\n", Colors.WHITE)
        return

    # Resolve environment variables in config_list
    # AG2 doesn't automatically resolve "env:VAR_NAME" syntax
    for config in config_list:
        api_key = config.get("api_key", "")
        if isinstance(api_key, str) and api_key.startswith("env:"):
            env_var = api_key[4:]  # Remove "env:" prefix
            actual_key = os.getenv(env_var)
            if actual_key:
                config["api_key"] = actual_key
            else:
                # Remove config if key not available
                config["api_key"] = None

    # Filter out configs with missing API keys
    config_list = [cfg for cfg in config_list if cfg.get("api_key")]

    if not config_list:
        print_colored(f"\n{ERROR_MESSAGES['no_valid_configs']}", Colors.BRIGHT_RED, bold=True)
        print_colored("Please check that API keys are set in autogen_app/.env\n", Colors.WHITE)
        return

    # Create assistant
    assistant = QPCRAssistant(config_list, model_name=model_name)

    try:
        # Initialize
        print()
        print_colored(STATUS_MESSAGES["initializing"], Colors.BRIGHT_YELLOW, bold=True)
        print_colored(STATUS_MESSAGES["connecting_mcp"], Colors.WHITE)
        assistant.initialize()
        print_colored(STATUS_MESSAGES["mcp_connected"], Colors.GREEN)
        print_colored(STATUS_MESSAGES["agents_initialized"], Colors.GREEN)
        print_colored(STATUS_MESSAGES["ready"], Colors.BRIGHT_GREEN, bold=True)
        print()

        # Print welcome banner
        print_banner()

        # Interactive loop
        while True:
            try:
                # Prompt for input
                print()
                print_colored("┌─[qPCR Assistant]", Colors.BRIGHT_CYAN)
                print_colored("│", Colors.BRIGHT_CYAN)

                # Read user input with colored prompt
                user_input = colored_input("└─> ").strip()

                # Handle empty input
                if not user_input:
                    print_colored(ERROR_MESSAGES["empty_input"], Colors.YELLOW)
                    continue

                # Handle commands
                if user_input.lower() in ['exit', 'quit']:
                    print()
                    print_colored(SUCCESS_MESSAGES["goodbye"], Colors.BRIGHT_GREEN, bold=True)
                    print()
                    break

                elif user_input.lower() == 'help':
                    print_help()
                    continue

                elif user_input.lower() == 'logs':
                    show_recent_logs()
                    continue

                elif user_input.lower() == 'clear':
                    os.system('clear' if os.name == 'posix' else 'cls')
                    print_banner()
                    continue

                # Clarify and confirm request before starting workflow
                proceed, plan = clarify_and_confirm_request(user_input)

                if not proceed:
                    continue

                # Build comprehensive request from plan
                off_target_species = ', '.join(plan['off_target_species']) if plan['off_target_species'] else 'Identify taxonomically related species'
                additional_requirements = ', '.join(plan['additional_requirements']) if plan['additional_requirements'] else 'None'
                off_target_step = 'Retrieve sequences for off-target species' if plan['off_target_species'] else 'Identify and retrieve sequences for taxonomically related species'
                
                comprehensive_request = COMPREHENSIVE_REQUEST_TEMPLATE.format(
                    target_species=plan['target_species'],
                    off_target_species=off_target_species,
                    genomic_region=plan['genomic_region'],
                    application=plan['application'],
                    additional_requirements=additional_requirements,
                    off_target_step=off_target_step
                )

                # Process qPCR design request
                print()
                print_colored("═══════════════════════════════════════════════════════════════════════════", Colors.CYAN)
                print_colored(STATUS_MESSAGES["starting_workflow"], Colors.BRIGHT_GREEN, bold=True)
                print_colored("═══════════════════════════════════════════════════════════════════════════", Colors.CYAN)
                print()

                # Run workflow (synchronous)
                messages = assistant.run_workflow(comprehensive_request)

                # The termination summary is already printed by run_workflow()
                print_colored(SUCCESS_MESSAGES["task_log_saved"], Colors.GREEN)
                print_colored(SUCCESS_MESSAGES["view_logs_tip"], Colors.BRIGHT_BLACK)
                print()

            except KeyboardInterrupt:
                print()
                print_colored(ERROR_MESSAGES["workflow_interrupted"], Colors.YELLOW, bold=True)
                print_colored("Type 'exit' to quit or continue with a new request", Colors.WHITE)
                print()
                continue

            except EOFError:
                print()
                print_colored(ERROR_MESSAGES["eof_detected"], Colors.BRIGHT_GREEN)
                print()
                break

            except Exception as e:
                print()
                print_colored(f"❌ ERROR: {e}", Colors.BRIGHT_RED, bold=True)
                logger.error(f"Error in interactive loop: {e}", exc_info=True)
                print_colored("You can continue with a new request or type 'exit' to quit", Colors.WHITE)
                print()
                continue

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print()
        print_colored(ERROR_MESSAGES["fatal_error"].format(error=e), Colors.BRIGHT_RED, bold=True)
        print()

    finally:
        print()
        print_colored(STATUS_MESSAGES["shutting_down"], Colors.BRIGHT_YELLOW)
        try:
            assistant.shutdown()
            print_colored(STATUS_MESSAGES["shutdown_complete"], Colors.GREEN)
        except Exception as e:
            print_colored(STATUS_MESSAGES["shutdown_warnings"], Colors.YELLOW)
        print()


def main():
    """Main entry point."""
    interactive_mode()


if __name__ == "__main__":
    main()
