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
        """Log an agent action."""
        if not self.task_log:
            return

        self.task_log[0]["agents"].append({
            "timestamp": datetime.now().isoformat(),
            "agent": agent_name,
            "action": action,
            "content": content[:500] if len(content) > 500 else content  # Truncate long content
        })

    def log_tool_call(self, agent_name: str, tool_name: str, arguments: Dict[str, Any], result: str):
        """Log a tool call."""
        if not self.task_log:
            return

        self.task_log[0]["tool_calls"].append({
            "timestamp": datetime.now().isoformat(),
            "agent": agent_name,
            "tool": tool_name,
            "arguments": arguments,
            "result_preview": result[:200] if len(result) > 200 else result,
            "result_length": len(result),
            "success": not result.startswith("Error:")
        })

    def log_message(self, source: str, message_type: str, content: str):
        """Log a message."""
        if not self.task_log:
            return

        self.task_log[0]["messages"].append({
            "timestamp": datetime.now().isoformat(),
            "source": source,
            "type": message_type,
            "content": content[:300] if len(content) > 300 else content
        })

    def end_session(self, summary: str = ""):
        """End the logging session and save to file."""
        if not self.task_log or not self.current_session:
            return

        self.task_log[0]["end_time"] = datetime.now().isoformat()
        self.task_log[0]["summary"] = summary

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

            f.write("AGENT WORKFLOW:\n")
            f.write("-" * 80 + "\n")
            for i, agent_action in enumerate(log.get('agents', []), 1):
                f.write(f"\n[{i}] {agent_action['timestamp']} - {agent_action['agent']}\n")
                f.write(f"    Action: {agent_action['action']}\n")
                f.write(f"    Content: {agent_action['content']}\n")

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

            f.write("\n\nMESSAGE TIMELINE:\n")
            f.write("-" * 80 + "\n")
            for i, msg in enumerate(log.get('messages', []), 1):
                f.write(f"\n[{i}] {msg['timestamp']} - {msg['source']} ({msg['type']})\n")
                f.write(f"    {msg['content']}\n")

            if log.get('summary'):
                f.write("\n\nSUMMARY:\n")
                f.write("-" * 80 + "\n")
                f.write(f"{log['summary']}\n")

            f.write("\n" + "=" * 80 + "\n")

        logger.info(f"Human-readable summary saved to: {path}")


class QPCRAssistant:
    """Multi-agent qPCR assay design assistant using AG2 (AutoGen 0.2.x)."""

    def __init__(self, config_list: List[Dict[str, Any]], log_dir: str = "/results",
                 model_name: Optional[str] = None):
        """
        Initialize qPCR assistant.

        Args:
            config_list: AG2 config list (from OAI_CONFIG_LIST.json)
            log_dir: Directory to save task logs
            model_name: Specific model to use (e.g., "gemini-2.5-flash-lite", "gpt-4")
        """
        self.config_list = config_list
        self.model_name = model_name
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
        config = {
            "config_list": self.config_list,
            "timeout": 120,
            "temperature": 0.7,
        }

        # Filter by model if specified
        if self.model_name:
            config["config_list"] = [
                c for c in self.config_list
                if c.get("model") == self.model_name
            ]
            if not config["config_list"]:
                raise ValueError(f"Model {self.model_name} not found in config_list")

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

        readme_content = f"""# Sequence Data Repository

This folder contains FASTA sequences retrieved from public databases (NCBI, BOLD) for qPCR assay design.

**Last Updated:** {timestamp}

## Downloaded Sequences

| Taxon | Region | Filename | Sequences | Downloaded |
|-------|--------|----------|-----------|------------|
{existing_entries}| {taxon} | {region} | `{filename}` | {seq_count} | {timestamp} |

## Downstream Workflow

### 1. Quality Control & Deduplication
```bash
# Remove duplicate sequences
cd {folder}
seqkit rmdup -s *.fasta > deduplicated.fasta

# Check sequence statistics
seqkit stats *.fasta
```

### 2. Multiple Sequence Alignment
```bash
# Align sequences with MAFFT
mafft --auto deduplicated.fasta > aligned.fasta

# Or use MUSCLE
muscle -in deduplicated.fasta -out aligned.fasta
```

### 3. Signature Region Discovery
```bash
# Identify conserved and variable regions
# Use alignment visualization tools or custom scripts
# Look for regions with:
#   - High conservation within target species
#   - High variation between target and off-targets
```

### 4. Primer Design
```bash
# Option 1: Use Primer3
primer3_core < primer3_input.txt

# Option 2: Use PrimerBLAST (NCBI)
# Upload aligned.fasta to https://www.ncbi.nlm.nih.gov/tools/primer-blast/

# Option 3: Use the Design MCP Server (Phase 4)
# Coming soon in Phase 4 implementation
```

### 5. In Silico Validation
```bash
# BLAST primers against all sequences
blastn -query primers.fasta -subject *.fasta -task blastn-short

# Check for off-target amplification
# Primers should NOT amplify off-target species
```

## File Organization

- **Target species**: Sequences from the species you want to detect
- **Off-target species**: Sequences from closely-related species that should NOT be detected
- Each file is named: `Taxon_Region_Timestamp.fasta`

## Data Provenance

All sequences were retrieved using the MCP Database Server, which queries:
- **BOLD Systems** (Barcode of Life Data System)
- **NCBI GenBank** (National Center for Biotechnology Information)
- **NCBI SRA** (Sequence Read Archive - for raw data)

## Citation

If you use these sequences in a publication, please cite:
- BOLD Systems: Ratnasingham S, Hebert PDN (2007) BOLD: The Barcode of Life Data System. Mol Ecol Notes 7:355-364
- NCBI GenBank: Benson DA et al. (2013) GenBank. Nucleic Acids Res 41:D36-42

---

*Generated by qPCR Assistant (mdk_mcp) - https://github.com/your-org/mdk_mcp*
"""

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
                    # Run async function in event loop
                    result = self.event_loop.run_until_complete(
                        self.mcp_executor.execute_function(func_name, kwargs)
                    )

                    # Log the tool call
                    self.task_logger.log_tool_call(
                        "DatabaseAgent",  # Agent name
                        func_name,
                        kwargs,
                        result
                    )

                    # For get_sequences, save to file
                    if func_name == "get_sequences" and result and not result.startswith("Error"):
                        taxon = kwargs.get("taxon", "unknown")
                        region = kwargs.get("region", "unknown")
                        # Determine if target or off-target (simple heuristic)
                        category = "sequences"  # Default folder
                        filepath = self._save_sequences_to_file(result, taxon, region, category)

                        # Count sequences
                        seq_count = result.count(">")
                        result += f"\n\n✓ Saved {seq_count} sequences to: {filepath}"

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

    def _create_agents(self):
        """Create AutoGen agent team (AG2 0.2.x style)."""

        # Display model information
        model_info = self.config_list[0] if self.config_list else {}
        model_name = self.model_name or model_info.get("model", "unknown")
        api_type = model_info.get("api_type", "unknown")

        model_display = {
            "gemini-2.5-flash-lite": "Google Gemini 2.5 Flash Lite (1M token context, fastest)",
            "gemini-2.0-flash-lite": "Google Gemini 2.0 Flash Lite (1M token context)",
            "gemini-1.5-flash": "Google Gemini 1.5 Flash (1M token context)",
            "gemini-1.5-pro": "Google Gemini 1.5 Pro (2M token context)",
            "gemini-pro": "Google Gemini Pro (1M token context)",
            "gpt-4": "OpenAI GPT-4 (128K token context)",
            "gpt-4-turbo": "OpenAI GPT-4 Turbo (128K token context)",
        }.get(model_name, f"{api_type.upper()} - {model_name}")

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
            system_message="""You are a qPCR assay design coordinator specializing in species identification.

Your responsibilities:
1. Understand user requirements (target species, off-targets, genomic region)
2. Create a step-by-step workflow plan
3. Coordinate with DatabaseAgent to gather sequence data
4. Summarize findings and recommend next steps
5. Ensure specificity and sensitivity requirements are met

When designing for species identification:
- Always identify potential off-target species (closely related)
- Consider the target genomic region (COI is common for species ID)
- Aim for 100-300bp amplicons for qPCR
- Ensure primers are specific to avoid false positives

Think step-by-step and explain your reasoning.

When you have a complete workflow plan, delegate to DatabaseAgent to retrieve sequences.""",
            llm_config=self.llm_config
        )

        # 2. Database Agent (with MCP tools)
        self.agents["database"] = AssistantAgent(
            name="DatabaseAgent",
            system_message="""You are a biological database specialist with access to NCBI, BOLD, and other databases via MCP tools.

CRITICAL: You MUST actually call the tools using function calls. DO NOT hallucinate or pretend to call tools.

Your workflow:
1. CALL get_taxonomy() to verify species names
2. CALL get_neighbors() to identify off-target species
3. CALL get_sequences() for each target and off-target species
4. CALL extract_sequence_columns() to get metadata (accession, organism, length, location)
5. Report actual results from tool calls

Tool parameters:
- get_sequences(taxon="Species name", region="COI", source="bold", max_results=100)
- get_taxonomy(query="Species name")
- get_neighbors(taxon="Species name", rank="species", distance=1)
- extract_sequence_columns(sequence_data="<sequences>", columns=["Accession", "Organism", "Sequence_Length"], output_format="tsv")

IMPORTANT:
- Always use source='bold' for COI sequences
- Retrieve 50-100 sequences per species
- Save sequences to /results/target/ and /results/off-target/ folders
- Create a detailed log file explaining the data structure

After ACTUAL tool execution, report the real numbers and results.""",
            llm_config=self.llm_config
        )

        # Register functions with DatabaseAgent
        for func_name, func in function_map.items():
            self.agents["database"].register_function(
                function_map={func_name: func}
            )

        # 3. Analysis Agent
        self.agents["analyst"] = AssistantAgent(
            name="AnalystAgent",
            system_message="""You are a molecular biology analyst specializing in qPCR primer design.

Your responsibilities:
1. Analyze sequences from DatabaseAgent
2. Identify conserved regions in target species
3. Identify variable regions between target and off-targets
4. Recommend candidate regions for primer design
5. Assess potential primer specificity

When Phase 4 MCP tools are available, you will use:
- find_signature_regions: Find target-specific regions
- primer3_design: Design primers
- oligo_qc: Validate primer quality

For now, provide analysis based on sequence data.

When you have analyzed the data and made recommendations, summarize your findings for the Coordinator.""",
            llm_config=self.llm_config
        )

        # 4. User Proxy (for termination and user interaction)
        self.agents["user_proxy"] = UserProxyAgent(
            name="User",
            human_input_mode="NEVER",  # Don't ask for user input during workflow
            max_consecutive_auto_reply=50,  # Allow more interactions
            is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
            code_execution_config=False,
            function_map=function_map,  # Register functions with user proxy for execution
        )

        # Create group chat
        self.groupchat = GroupChat(
            agents=[
                self.agents["coordinator"],
                self.agents["database"],
                self.agents["analyst"],
                self.agents["user_proxy"]
            ],
            messages=[],
            max_round=100,  # Allow more rounds for complex workflows
            speaker_selection_method="auto",  # Let LLM decide next speaker
            allow_repeat_speaker=False,  # Prevent infinite loops
        )

        # Create group chat manager
        self.manager = GroupChatManager(
            groupchat=self.groupchat,
            llm_config=self.llm_config
        )

        logger.info(f"Created {len(self.agents)} agents")

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

            # Log messages
            for msg in messages:
                if isinstance(msg, dict):
                    sender = msg.get("name", "unknown")
                    content = msg.get("content", "")
                    self.task_logger.log_message(sender, "message", content)
                    self.task_logger.log_agent_action(sender, "message", content)

            # End logging session
            summary = f"Completed qPCR design workflow with {len(messages)} messages exchanged."
            log_path = self.task_logger.end_session(summary)

            logger.info(f"Workflow completed with {len(messages)} messages")

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
    print_colored("╔══════════════════════════════════════════════════════════════════════════╗", Colors.CYAN, bold=True)
    print_colored("║                                                                          ║", Colors.CYAN, bold=True)
    print_colored("║                     qPCR ASSISTANT - Interactive Mode                   ║", Colors.CYAN, bold=True)
    print_colored("║                                                                          ║", Colors.CYAN, bold=True)
    print_colored("║  Multi-Agent AI System for qPCR Assay Design                           ║", Colors.BRIGHT_WHITE)
    print_colored("║  Powered by AG2 (AutoGen 0.2.x) + MCP Tools                            ║", Colors.BRIGHT_WHITE)
    print_colored("║                                                                          ║", Colors.CYAN, bold=True)
    print_colored("╚══════════════════════════════════════════════════════════════════════════╝", Colors.CYAN, bold=True)
    print()

    print_colored("📋 Available Commands:", Colors.BRIGHT_YELLOW, bold=True)
    print(f"  {colored('help', Colors.GREEN)}    - Show usage examples")
    print(f"  {colored('logs', Colors.GREEN)}    - View recent task logs")
    print(f"  {colored('clear', Colors.GREEN)}   - Clear screen")
    print(f"  {colored('exit', Colors.GREEN)}    - Exit the assistant")
    print()

    print_colored("🤖 Active Agents:", Colors.BRIGHT_YELLOW, bold=True)
    print(f"  {colored('•', Colors.BLUE)} {colored('Coordinator', Colors.BRIGHT_CYAN)}  - Plans workflow and coordinates tasks")
    print(f"  {colored('•', Colors.BLUE)} {colored('DatabaseAgent', Colors.BRIGHT_CYAN)} - Retrieves sequences from NCBI/BOLD (5 MCP tools)")
    print(f"  {colored('•', Colors.BLUE)} {colored('AnalystAgent', Colors.BRIGHT_CYAN)}  - Analyzes sequences and recommends primers")
    print()

    print_colored("💡 Getting Started:", Colors.BRIGHT_YELLOW, bold=True)
    print_colored("  Just describe your qPCR assay design request naturally!", Colors.WHITE)
    print_colored("  The assistant will ask clarifying questions before starting.", Colors.BRIGHT_BLACK)
    print()

    print_colored("📝 Example:", Colors.BRIGHT_GREEN, bold=True)
    print_colored('  "I need to design a qPCR assay for Atlantic salmon"', Colors.WHITE)
    print()
    print_colored("═══════════════════════════════════════════════════════════════════════════", Colors.CYAN)


def print_help():
    """Print help information with colors."""
    print()
    print_colored("═══════════════════════════════════════════════════════════════════════════", Colors.CYAN)
    print_colored("📚 USAGE EXAMPLES", Colors.BRIGHT_YELLOW, bold=True)
    print_colored("═══════════════════════════════════════════════════════════════════════════", Colors.CYAN)
    print()

    print_colored("1. Species Identification:", Colors.BRIGHT_GREEN, bold=True)
    print_colored('   "Design a qPCR assay to identify Atlantic salmon (Salmo salar)', Colors.WHITE)
    print_colored('    and distinguish it from rainbow trout (Oncorhynchus mykiss).', Colors.WHITE)
    print_colored('    Target: COI region for aquaculture verification."', Colors.WHITE)
    print()

    print_colored("2. Pathogen Detection:", Colors.BRIGHT_GREEN, bold=True)
    print_colored('   "Design a qPCR assay to detect Mycobacterium tuberculosis', Colors.WHITE)
    print_colored('    in clinical samples, with specificity against other Mycobacterium species."', Colors.WHITE)
    print()

    print_colored("3. Environmental Monitoring:", Colors.BRIGHT_GREEN, bold=True)
    print_colored('   "Design a qPCR assay for detecting invasive zebra mussels', Colors.WHITE)
    print_colored('    (Dreissena polymorpha) in eDNA samples."', Colors.WHITE)
    print()

    print_colored("💡 TIPS:", Colors.BRIGHT_YELLOW, bold=True)
    print(f"  {colored('•', Colors.BLUE)} Be specific about target and off-target species")
    print(f"  {colored('•', Colors.BLUE)} Mention preferred genomic region (COI, 16S, ITS, etc.)")
    print(f"  {colored('•', Colors.BLUE)} Describe the application context")
    print(f"  {colored('•', Colors.BLUE)} The assistant will ask clarifying questions")
    print(f"  {colored('•', Colors.BLUE)} Confirm the plan before workflow starts")
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

    # Question 1: Target species
    print_colored("Question 1/5: Target Species", Colors.BRIGHT_GREEN, bold=True)
    print_colored("What is the target species (scientific name preferred)?", Colors.WHITE)
    print(f"{colored('Example:', Colors.BRIGHT_BLACK)} Salmo salar, Mycobacterium tuberculosis, Escherichia coli")
    plan["target_species"] = colored_input("└─> ").strip()
    print()

    # Question 2: Off-target species
    print_colored("Question 2/5: Off-Target Species", Colors.BRIGHT_GREEN, bold=True)
    print_colored("Which species should the assay distinguish from (comma-separated)?", Colors.WHITE)
    print(f"{colored('Example:', Colors.BRIGHT_BLACK)} Oncorhynchus mykiss, Salmo trutta")
    print(f"{colored('Tip:', Colors.BRIGHT_YELLOW)} Leave blank if unsure - I'll identify related species")
    off_targets = colored_input("└─> ").strip()
    if off_targets:
        plan["off_target_species"] = [s.strip() for s in off_targets.split(',')]
    print()

    # Question 3: Genomic region
    print_colored("Question 3/5: Genomic Region", Colors.BRIGHT_GREEN, bold=True)
    print_colored("Which genomic region should we target?", Colors.WHITE)
    print(f"{colored('Common regions:', Colors.BRIGHT_BLACK)} COI, 16S, 18S, ITS, 23S, specific genes")
    print(f"{colored('Tip:', Colors.BRIGHT_YELLOW)} Leave blank for automatic selection based on target")
    region = colored_input("└─> ").strip()
    plan["genomic_region"] = region if region else "auto-select"
    print()

    # Question 4: Application context
    print_colored("Question 4/5: Application Context", Colors.BRIGHT_GREEN, bold=True)
    print_colored("What is the intended application for this assay?", Colors.WHITE)
    print(f"{colored('Examples:', Colors.BRIGHT_BLACK)} clinical diagnostics, food safety, environmental monitoring")
    plan["application"] = colored_input("└─> ").strip()
    print()

    # Question 5: Additional requirements
    print_colored("Question 5/5: Additional Requirements", Colors.BRIGHT_GREEN, bold=True)
    print_colored("Any special requirements or constraints?", Colors.WHITE)
    print(f"{colored('Examples:', Colors.BRIGHT_BLACK)} high sensitivity, rapid detection, multiplexing capability")
    print(f"{colored('Tip:', Colors.BRIGHT_YELLOW)} Leave blank if none")
    requirements = colored_input("└─> ").strip()
    if requirements:
        plan["additional_requirements"] = [r.strip() for r in requirements.split(',')]
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
    print(f"  {colored('1.', Colors.GREEN)} Retrieve sequences for target species")
    if plan["off_target_species"]:
        print(f"  {colored('2.', Colors.GREEN)} Retrieve sequences for off-target species")
        print(f"  {colored('3.', Colors.GREEN)} Identify additional related species")
    else:
        print(f"  {colored('2.', Colors.GREEN)} Identify taxonomically related species")
        print(f"  {colored('3.', Colors.GREEN)} Retrieve sequences for related species")
    print(f"  {colored('4.', Colors.GREEN)} Analyze sequences to find signature regions")
    print(f"  {colored('5.', Colors.GREEN)} Recommend primer design strategy")
    print(f"  {colored('6.', Colors.GREEN)} Generate comprehensive report")
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
        print_colored("✓ Confirmed! Starting workflow...", Colors.BRIGHT_GREEN, bold=True)
        print()
        return True, plan
    elif confirmation in ['edit', 'e']:
        print_colored("↻ Let's modify the plan. Please make your request again.", Colors.YELLOW)
        print()
        return False, None
    else:
        print_colored("✗ Workflow cancelled.", Colors.RED)
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

    # Load config from OAI_CONFIG_LIST.json
    config_file = os.path.join(os.path.dirname(__file__), "OAI_CONFIG_LIST.json")
    if not os.path.exists(config_file):
        print_colored("\n❌ ERROR: OAI_CONFIG_LIST.json not found.", Colors.BRIGHT_RED, bold=True)
        print_colored(f"Expected at: {config_file}\n", Colors.WHITE)
        return

    with open(config_file, 'r') as f:
        config_list = json.load(f)

    # Determine which model to use
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")

    # Check if API keys are available
    gemini_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    # Validate that at least one API key is set
    if not gemini_key and not openai_key:
        print_colored("\n❌ ERROR: No API keys found.", Colors.BRIGHT_RED, bold=True)
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
        print_colored("\n❌ ERROR: No valid API configurations found.", Colors.BRIGHT_RED, bold=True)
        print_colored("Please check that API keys are set in autogen_app/.env\n", Colors.WHITE)
        return

    # Create assistant
    assistant = QPCRAssistant(config_list, model_name=model_name)

    try:
        # Initialize
        print()
        print_colored("🔧 Initializing qPCR Assistant...", Colors.BRIGHT_YELLOW, bold=True)
        print_colored("   • Connecting to MCP servers...", Colors.WHITE)
        assistant.initialize()
        print_colored("   ✓ MCP servers connected", Colors.GREEN)
        print_colored("   ✓ Agents initialized", Colors.GREEN)
        print_colored("   ✓ Ready!", Colors.BRIGHT_GREEN, bold=True)
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
                    print_colored("⚠️  Please enter a command or request", Colors.YELLOW)
                    continue

                # Handle commands
                if user_input.lower() in ['exit', 'quit']:
                    print()
                    print_colored("👋 Goodbye! All task logs saved to /results/", Colors.BRIGHT_GREEN, bold=True)
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
                comprehensive_request = f"""
I need to design a qPCR assay with the following specifications:

Target Species: {plan['target_species']}
Off-Target Species: {', '.join(plan['off_target_species']) if plan['off_target_species'] else 'Identify taxonomically related species'}
Genomic Region: {plan['genomic_region']}
Application: {plan['application']}
Additional Requirements: {', '.join(plan['additional_requirements']) if plan['additional_requirements'] else 'None'}

Please:
1. Retrieve sequences for the target species
2. {'Retrieve sequences for off-target species' if plan['off_target_species'] else 'Identify and retrieve sequences for taxonomically related species'}
3. Analyze sequences to identify signature regions unique to the target
4. Recommend primer design strategy considering the application context
5. Provide a comprehensive report with all findings
"""

                # Process qPCR design request
                print()
                print_colored("═══════════════════════════════════════════════════════════════════════════", Colors.CYAN)
                print_colored("🚀 STARTING WORKFLOW", Colors.BRIGHT_GREEN, bold=True)
                print_colored("═══════════════════════════════════════════════════════════════════════════", Colors.CYAN)
                print()

                # Run workflow (synchronous)
                messages = assistant.run_workflow(comprehensive_request)

                print()
                print_colored("═══════════════════════════════════════════════════════════════════════════", Colors.CYAN)
                print_colored("✓ WORKFLOW COMPLETED", Colors.BRIGHT_GREEN, bold=True)
                print_colored("═══════════════════════════════════════════════════════════════════════════", Colors.CYAN)
                print()
                print_colored("📁 Task log saved to /results/", Colors.GREEN)
                print_colored("💡 Type 'logs' to view recent task logs", Colors.BRIGHT_BLACK)
                print()

            except KeyboardInterrupt:
                print()
                print_colored("⚠️  Workflow interrupted by user (Ctrl+C)", Colors.YELLOW, bold=True)
                print_colored("Type 'exit' to quit or continue with a new request", Colors.WHITE)
                print()
                continue

            except EOFError:
                print()
                print_colored("👋 EOF detected. Exiting...", Colors.BRIGHT_GREEN)
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
        print_colored(f"❌ FATAL ERROR: {e}", Colors.BRIGHT_RED, bold=True)
        print()

    finally:
        print()
        print_colored("🔧 Shutting down assistant...", Colors.BRIGHT_YELLOW)
        try:
            assistant.shutdown()
            print_colored("✓ Shutdown complete", Colors.GREEN)
        except Exception as e:
            print_colored("⚠️  Shutdown completed with warnings", Colors.YELLOW)
        print()


def main():
    """Main entry point."""
    interactive_mode()


if __name__ == "__main__":
    main()
