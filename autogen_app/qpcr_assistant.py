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
import uuid
import hashlib
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
    PRIMER_DESIGN_AGENT_SYSTEM_MESSAGE,
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
        
        # NEW: Mask large fasta_content in arguments to avoid bloating logs
        cleaned_arguments = self._mask_fasta_content(arguments)

        self.task_log[0]["tool_calls"].append({
            "timestamp": datetime.now().isoformat(),
            "agent": agent_name,
            "tool": tool_name,
            "arguments": cleaned_arguments,
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
    
    def _mask_fasta_content(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Mask large fasta_content in arguments to avoid bloating logs."""
        if not arguments or "fasta_content" not in arguments:
            return arguments
        
        fasta_content = arguments.get("fasta_content", "")
        
        # If fasta_content is large (>500 chars), replace with summary
        if isinstance(fasta_content, str) and len(fasta_content) > 500:
            # Count sequences
            seq_count = fasta_content.count('>')
            
            # Extract first header only
            first_header = ""
            if '>' in fasta_content:
                first_newline = fasta_content.find('\n')
                if first_newline > 0:
                    first_header = fasta_content[:first_newline]
            
            # Create masked copy
            masked_args = arguments.copy()
            masked_args["fasta_content"] = (
                f"[MASKED: {seq_count} sequences, {len(fasta_content):,} characters]\n"
                f"First header: {first_header}\n"
                f"[Full content available in tool_result file]"
            )
            return masked_args
        
        return arguments


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
        self.run_id = None  # Will be generated when workflow starts
        self.run_dir = None  # Directory for current run: /results/{run_id}/
        self.mcp_bridge = None
        self.mcp_executor = None
        self.agents = {}
        self.groupchat = None
        self.manager = None
        self.task_logger = TaskLogger(log_dir)
        self.event_loop = None  # For running async MCP calls
        self.manifest = {}  # Manifest tracking for current run

        # Create llm_config for agents
        self.llm_config = self._build_llm_config()

    def _generate_run_id(self) -> str:
        """
        Generate unique run ID for this workflow.

        Returns:
            UUID string for this run
        """
        run_id = str(uuid.uuid4())
        logger.info(f"Generated run_id: {run_id}")
        return run_id

    def _create_run_directory(self):
        """
        Create directory structure for this run:
        /results/{run_id}/
        /results/{run_id}/phase1/  (Database retrieval)
        /results/{run_id}/phase2/  (Processing & QC)
        /results/{run_id}/phase3/  (Alignment & Phylogeny)
        /results/{run_id}/phase4/  (Primer Design)
        """
        self.run_dir = os.path.join(self.log_dir, self.run_id)

        # Create phase directories
        phase_dirs = [
            os.path.join(self.run_dir, "phase1"),  # Database retrieval
            os.path.join(self.run_dir, "phase2"),  # Processing & QC
            os.path.join(self.run_dir, "phase3"),  # Alignment & Phylogeny
            os.path.join(self.run_dir, "phase4"),  # Primer Design (future)
        ]

        for phase_dir in phase_dirs:
            os.makedirs(phase_dir, exist_ok=True)

        logger.info(f"Created run directory structure at {self.run_dir}")

        # Initialize manifest
        self.manifest = {
            "run_id": self.run_id,
            "created_at": datetime.now().isoformat(),
            "status": "in_progress",
            "phases": {
                "phase1": {"status": "pending", "artifacts": []},
                "phase2": {"status": "pending", "artifacts": []},
                "phase3": {"status": "pending", "artifacts": []},
                "phase4": {"status": "pending", "artifacts": []},
            },
            "tool_versions": {
                "gget": "unknown",
                "seqkit": "unknown",
                "vsearch": "unknown",
                "mafft": "unknown",
                "muscle": "unknown",
                "clustalo": "unknown",
            }
        }

        # Save initial manifest
        self._save_manifest()

    def _save_manifest(self):
        """Save manifest.json to run directory."""
        if not self.run_dir:
            return

        manifest_path = os.path.join(self.run_dir, "manifest.json")
        with open(manifest_path, 'w') as f:
            json.dump(self.manifest, f, indent=2)

        logger.debug(f"Saved manifest to {manifest_path}")

    def _check_cached_artifact(self, phase: str, artifact_type: str, metadata_match: Dict[str, Any] = None) -> Optional[str]:
        """
        Check if a cached artifact exists in the manifest.

        Args:
            phase: Phase name (e.g., "phase1", "phase2")
            artifact_type: Type of artifact to look for
            metadata_match: Optional metadata to match against (e.g., taxon, region)

        Returns:
            Path to cached artifact if found and valid, None otherwise
        """
        if not self.manifest or phase not in self.manifest.get("phases", {}):
            return None

        phase_artifacts = self.manifest["phases"][phase].get("artifacts", [])

        for artifact in phase_artifacts:
            # Check if type matches
            if artifact.get("type") != artifact_type:
                continue

            # Check if file still exists
            artifact_path = artifact.get("path")
            if not artifact_path or not os.path.exists(artifact_path):
                continue

            # If metadata matching requested, check if metadata matches
            if metadata_match:
                artifact_metadata = artifact.get("metadata", {})
                match = all(
                    artifact_metadata.get(key) == value
                    for key, value in metadata_match.items()
                )
                if not match:
                    continue

            # Verify file integrity if hash exists
            stored_hash = artifact.get("sha256")
            if stored_hash:
                with open(artifact_path, 'rb') as f:
                    current_hash = hashlib.sha256(f.read()).hexdigest()
                if current_hash != stored_hash:
                    logger.warning(f"Cached artifact at {artifact_path} has mismatched hash - ignoring")
                    continue

            logger.info(f"[IDEMPOTENCY] Found valid cached artifact: {artifact_path}")
            return artifact_path

        return None

    def _update_manifest_artifact(self, phase: str, artifact_path: str, artifact_type: str, metadata: Dict[str, Any] = None):
        """
        Add artifact to manifest.

        Args:
            phase: Phase name (e.g., "phase1", "phase2")
            artifact_path: Full path to artifact file
            artifact_type: Type of artifact (e.g., "sequences", "alignment", "tree")
            metadata: Additional metadata for the artifact
        """
        # Skip if manifest not initialized yet (before run_workflow starts)
        if not self.manifest or "phases" not in self.manifest:
            logger.debug(f"Manifest not initialized yet - skipping artifact tracking for {phase}/{artifact_type}")
            return
            
        if phase not in self.manifest["phases"]:
            logger.warning(f"Unknown phase '{phase}' - cannot update manifest")
            return

        # Calculate file hash for integrity checking
        file_hash = None
        if os.path.exists(artifact_path):
            with open(artifact_path, 'rb') as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()

        artifact = {
            "path": artifact_path,
            "type": artifact_type,
            "created_at": datetime.now().isoformat(),
            "size_bytes": os.path.getsize(artifact_path) if os.path.exists(artifact_path) else 0,
            "sha256": file_hash,
            "metadata": metadata or {}
        }

        self.manifest["phases"][phase]["artifacts"].append(artifact)
        self.manifest["phases"][phase]["status"] = "completed"

        # Save updated manifest
        self._save_manifest()

        logger.info(f"Added artifact to manifest: {phase}/{artifact_type}")

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
        
        DatabaseAgent has ONLY database tools (pure data retrieval) per 4-agent architecture.
        Processing tools belong to AnalystAgent.
        """
        # Start with base config
        config = self._build_llm_config().copy()

        # Add function schemas for MCP tools (DATABASE ONLY - pure data retrieval)
        # Processing and alignment tools belong to AnalystAgent
        function_schemas = create_autogen_functions(["database"])
        config["functions"] = function_schemas

        logger.info(f"DatabaseAgent llm_config includes {len(function_schemas)} function schemas (database only)")
        logger.debug(f"Function schemas: {[f['name'] for f in function_schemas]}")

        return config

    def _build_analyst_agent_llm_config(self) -> Dict[str, Any]:
        """
        Build LLM configuration specifically for AnalystAgent with processing + alignment function schemas.

        AnalystAgent handles ALL sequence curation and analysis tasks:
        - Quality control and processing (from processing server)
        - Alignment and phylogenetic analysis (from alignment server)
        This makes AnalystAgent responsible for preparing curated, analysis-ready data for primer design.
        """
        # Start with base config
        config = self._build_llm_config().copy()

        # Add function schemas for processing AND alignment MCP tools
        # AnalystAgent is responsible for the entire data curation pipeline
        function_schemas = create_autogen_functions(["processing", "alignment"])
        config["functions"] = function_schemas

        logger.info(f"AnalystAgent llm_config includes {len(function_schemas)} function schemas")
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
                "command": ["python3", "/app/database_mcp_server.py"]
            },
            "processing": {
                "container": os.getenv("MCP_PROCESSING_SERVER", "ndiag-processing-server"),
                "command": ["python3", "/app/processing_mcp_server.py"]
            },
            "alignment": {
                "container": os.getenv("MCP_ALIGNMENT_SERVER", "ndiag-alignment-server"),
                "command": ["python3", "/app/alignment_mcp_server.py"]
            },
            "design": {
                "container": os.getenv("MCP_DESIGN_SERVER", "ndiag-design-server"),
                "command": ["python3", "/app/design_mcp_server.py"]
            }
            # Add more servers as phases complete:
            # "validation": {...},
            # "export": {...}
        }

        self.mcp_bridge = MCPClientBridge(server_configs)
        await self.mcp_bridge.start_servers()

        # Create MCP executor
        self.mcp_executor = AutoGenMCPFunctionExecutor(self.mcp_bridge, self.log_dir)

        logger.info("MCP servers connected")

    def _save_sequences_to_file(self, sequences: str, taxon: str, region: str, category: str) -> str:
        """
        Save sequences to organized folder structure using run_id.

        Args:
            sequences: FASTA sequences to save
            taxon: Taxonomic name
            region: Gene region (e.g., "COI", "16S")
            category: Category for organizing (e.g., "sequences", "targets", "off_targets")

        Returns:
            Full path to saved file
        """
        import os
        import re
        from datetime import datetime

        # Map category to phase
        phase_mapping = {
            "sequences": "phase1",
            "targets": "phase1",
            "off_targets": "phase1",
            "processed": "phase2",
            "aligned": "phase3",
            "tree": "phase3",
        }
        phase = phase_mapping.get(category, "phase1")

        # Use run_id directory if available, otherwise fall back to legacy structure
        if self.run_dir and os.path.isdir(self.run_dir):
            category_folder = os.path.join(self.run_dir, phase)
        else:
            # Legacy path for backward compatibility (when run_workflow hasn't been called yet)
            logger.debug(f"Using legacy path for {category}, run_dir not available")
            category_folder = os.path.join(self.log_dir, category)

        try:
            os.makedirs(category_folder, exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to create directory {category_folder}: {e}")
            raise

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

        # Update manifest if run_id is active and manifest is initialized
        if self.run_dir and self.manifest and "phases" in self.manifest:
            try:
                self._update_manifest_artifact(
                    phase=phase,
                    artifact_path=filepath,
                    artifact_type="sequences",
                    metadata={
                        "taxon": taxon,
                        "region": region,
                        "category": category,
                        "sequence_count": seq_count
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to update manifest for {filepath}: {e}")

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
            folder=folder,
            run_id=self.run_id or "unknown"  # Use "unknown" if run_id not yet generated
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
                        logger.debug(f"[WRAPPER] Starting get_sequences, run_id={self.run_id}, run_dir={self.run_dir}")
                        
                        # Get full result directly from MCP bridge (no summarization)
                        full_result = self.event_loop.run_until_complete(
                            self.mcp_executor._call_mcp_tool_raw(func_name, kwargs)
                        )
                        logger.debug(f"[WRAPPER] Got MCP result, length={len(str(full_result))}")
                        
                        # Log the tool call (with full result)
                        logger.debug("[WRAPPER] About to log tool call")
                        self.task_logger.log_tool_call(
                            "DatabaseAgent",
                            func_name,
                            kwargs,
                            full_result
                        )
                        logger.debug("[WRAPPER] Logged tool call")
                        
                        # Save to file and return metadata only
                        logger.debug("[WRAPPER] About to handle sequence result")
                        result = self._handle_sequence_result(full_result, kwargs)
                        logger.debug(f"[WRAPPER] Handled sequence result, returning summary")
                        return result
                    
                    # For processing and alignment tools, get RAW result before summarization
                    # so we can extract file paths from JSON
                    if func_name in ["process_sequences", "fasta_qc", "dereplicate_sequences", 
                                     "mask_low_complexity", "detect_chimeras",
                                     "align_sequences", "align_and_analyze", "build_phylogeny", 
                                     "process_alignment", "calculate_distances"]:
                        # Inject run_id into processing tool calls for proper file organization
                        if func_name in ["process_sequences", "fasta_qc", "dereplicate_sequences", 
                                        "mask_low_complexity", "detect_chimeras"] and self.run_id:
                            kwargs_with_run_id = {**kwargs, "run_id": self.run_id}
                            logger.debug(f"[WRAPPER] Injecting run_id={self.run_id} into {func_name}")
                        else:
                            kwargs_with_run_id = kwargs
                        
                        # Get full RAW result (no summarization)
                        raw_result = self.event_loop.run_until_complete(
                            self.mcp_executor._call_mcp_tool_raw(func_name, kwargs_with_run_id)
                        )
                        
                        # Log the tool call with full result
                        self.task_logger.log_tool_call(
                            "AnalystAgent",  # These are AnalystAgent tools
                            func_name,
                            kwargs,
                            raw_result
                        )
                        
                        # Handle the result to extract file paths and update manifest
                        if func_name in ["process_sequences", "fasta_qc", "dereplicate_sequences", 
                                        "mask_low_complexity", "detect_chimeras"]:
                            result = self._handle_processing_tool_result(raw_result, kwargs, func_name)
                        else:
                            result = self._handle_alignment_tool_result(raw_result, kwargs, func_name)
                    
                    # For other functions, use normal flow with summarization
                    else:
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
                    import traceback
                    error_msg = f"Error calling {func_name}: {str(e)}"
                    logger.error(error_msg)
                    logger.error(f"Full traceback:\n{traceback.format_exc()}")
                    return error_msg

            return wrapper

        # Create wrappers for all MCP tools
        return {
            # Database tools
            "get_sequences": make_sync_wrapper("get_sequences"),
            "get_taxonomy": make_sync_wrapper("get_taxonomy"),
            "get_neighbors": make_sync_wrapper("get_neighbors"),
            "extract_sequence_columns": make_sync_wrapper("extract_sequence_columns"),
            "search_sra_studies": make_sync_wrapper("search_sra_studies"),
            # Processing tools
            "fasta_qc": make_sync_wrapper("fasta_qc"),
            "dereplicate_sequences": make_sync_wrapper("dereplicate_sequences"),
            "mask_low_complexity": make_sync_wrapper("mask_low_complexity"),
            "detect_chimeras": make_sync_wrapper("detect_chimeras"),
            "process_sequences": make_sync_wrapper("process_sequences"),
            # Alignment tools (Phase 3)
            "align_sequences": make_sync_wrapper("align_sequences"),
            "process_alignment": make_sync_wrapper("process_alignment"),
            "build_phylogeny": make_sync_wrapper("build_phylogeny"),
            "calculate_distances": make_sync_wrapper("calculate_distances"),
            "align_and_analyze": make_sync_wrapper("align_and_analyze"),
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
        Handle extract_sequence_columns result: Filter PII and limit to first 10 records.
        """
        if not result or result.startswith("Error"):
            return result

        # If result is very long, truncate to first 10 records and filter PII
        try:
            import json
            data = json.loads(result) if isinstance(result, str) else result

            # Filter PII from metadata records
            if isinstance(data, list):
                # Filter each record
                filtered_data = [self._filter_pii_from_metadata(record) if isinstance(record, dict) else record
                                 for record in data]

                if len(filtered_data) > 10:
                    truncated_data = filtered_data[:10]
                    summary = json.dumps(truncated_data, indent=2)
                    summary += f"\n\n... and {len(data) - 10} more records (total: {len(data)} records)"
                    return summary
                else:
                    return json.dumps(filtered_data, indent=2)

            elif isinstance(data, dict) and "records" in data:
                records = data["records"]
                # Filter each record
                filtered_records = [self._filter_pii_from_metadata(record) if isinstance(record, dict) else record
                                    for record in records]

                if len(filtered_records) > 10:
                    data["records"] = filtered_records[:10]
                    summary = json.dumps(data, indent=2)
                    summary += f"\n\n... and {len(records) - 10} more records (total: {len(records)} records)"
                    return summary
                else:
                    data["records"] = filtered_records
                    return json.dumps(data, indent=2)

            elif isinstance(data, dict):
                # Single record - filter it
                filtered_data = self._filter_pii_from_metadata(data)
                return json.dumps(filtered_data, indent=2)

        except:
            pass

        # If not too long or can't parse, return as-is (but limit to 3000 chars)
        if len(result) > 3000:
            return result[:3000] + f"\n\n... [Truncated: {len(result) - 3000} more characters]"

        return result

    def _handle_mcp_file_result(self, result: str, kwargs: dict, tool_config: Dict[str, Any]) -> str:
        """
        Generic handler for MCP tool results that export files.
        Parses JSON output, extracts file paths, updates manifest, and returns formatted summary.
        
        Args:
            result: JSON result from MCP tool (may be wrapped in MCP response format)
            kwargs: Original function arguments
            tool_config: Configuration dictionary with:
                - phase: Workflow phase (e.g., "phase1", "phase2", "phase3")
                - output_fields: List of field names to extract from JSON (e.g., ["output_file"])
                  or dict mapping field names to artifact types (e.g., {"alignment_file": "alignment"})
                - log_prefix: Prefix for log messages (e.g., "PROCESSING", "ALIGNMENT")
                - summary_template: Function that generates summary message from extracted data
        
        Returns:
            Summary message with actual output file paths for agents to use
        """
        if not result or (isinstance(result, str) and result.startswith("Error")):
            return result
        
        try:
            import json
            import os
            
            # Extract actual JSON from MCP response wrapper if needed
            # MCP returns: {'content': [{'type': 'text', 'text': 'JSON DATA'}], 'isError': False}
            actual_json = result
            if isinstance(result, dict):
                # Already a dict - check if it's MCP-wrapped
                if 'content' in result and isinstance(result['content'], list):
                    if len(result['content']) > 0 and 'text' in result['content'][0]:
                        actual_json = result['content'][0]['text']
            elif isinstance(result, str) and result.startswith('{'):
                # Try to parse as JSON
                try:
                    temp_parsed = json.loads(result)
                    if isinstance(temp_parsed, dict) and 'content' in temp_parsed:
                        # MCP-wrapped
                        if isinstance(temp_parsed['content'], list) and len(temp_parsed['content']) > 0:
                            if 'text' in temp_parsed['content'][0]:
                                actual_json = temp_parsed['content'][0]['text']
                    else:
                        actual_json = result
                except:
                    pass
            
            # Parse the actual JSON content
            if isinstance(actual_json, str):
                parsed = json.loads(actual_json) if actual_json.startswith('{') else None
            elif isinstance(actual_json, dict):
                parsed = actual_json
            else:
                return result
                
            if not parsed or not isinstance(parsed, dict):
                return result
            
            phase = tool_config.get("phase", "phase1")
            log_prefix = tool_config.get("log_prefix", "MCP")
            output_fields = tool_config.get("output_fields", {})
            
            # Extract output files
            # Support both list format ["output_file"] and dict format {"alignment_file": "alignment"}
            if isinstance(output_fields, list):
                # Convert list to dict with generic artifact type
                output_fields = {field: "output" for field in output_fields}
            
            extracted_files = []
            for field_name, artifact_type in output_fields.items():
                file_path = parsed.get(field_name)
                if file_path and os.path.exists(file_path):
                    extracted_files.append({
                        "field": field_name,
                        "path": file_path,
                        "type": artifact_type
                    })
                elif file_path:
                    logger.warning(f"[{log_prefix}] Output file doesn't exist: {file_path}")
            
            if not extracted_files:
                logger.warning(f"[{log_prefix}] No valid output files found in result")
                return result
            
            # Extract taxon from input filename if available
            input_file = kwargs.get("fasta_file", "unknown")
            taxon = self._extract_taxon_from_filename(input_file)
            
            # Filter out large FASTA/alignment content to prevent log and manifest bloat
            # These fields contain full sequence data and can be massive (>100KB)
            large_content_fields = ["alignment", "processed_fasta", "fasta_content", "sequences", "content", "text"]
            
            # Update manifest for each output file
            if self.run_dir and self.manifest and "phases" in self.manifest:
                for file_info in extracted_files:
                    try:
                        # Build metadata from kwargs and parsed result
                        # Exclude large content fields and file path fields from metadata
                        excluded_fields = set(output_fields.keys()) | set(large_content_fields)
                        metadata = {
                            "input_file": input_file,
                            "taxon": taxon,
                            **{k: v for k, v in kwargs.items() if k not in ["fasta_file"]},
                            **{k: v for k, v in parsed.items() if k not in excluded_fields and not k.endswith("_file")}
                        }
                        
                        self._update_manifest_artifact(
                            phase=phase,
                            artifact_path=file_info["path"],
                            artifact_type=file_info["type"],
                            metadata=metadata
                        )
                        logger.info(f"[{log_prefix}] Updated manifest with {file_info['type']} artifact: {file_info['path']}")
                    except Exception as e:
                        logger.warning(f"[{log_prefix}] Failed to update manifest for {file_info['type']}: {e}")
            
            # Generate summary using template function
            summary_template = tool_config.get("summary_template")
            if summary_template and callable(summary_template):
                return summary_template(parsed, kwargs, extracted_files)
            
            # Default summary if no template provided
            return self._format_default_summary(parsed, kwargs, extracted_files, log_prefix)
            
        except Exception as e:
            logger.error(f"[{tool_config.get('log_prefix', 'MCP')}] Error handling MCP result: {e}")
            return result
    
    def _parse_mcp_json(self, result: str) -> Optional[Dict]:
        """
        Lightweight JSON parser for MCP responses.
        Handles both raw JSON and MCP-wrapped responses.
        
        Args:
            result: JSON string or MCP-wrapped response
        
        Returns:
            Parsed dictionary or None if parsing fails
        """
        import json
        
        try:
            # If already a dict, check if MCP-wrapped
            if isinstance(result, dict):
                if 'content' in result and isinstance(result['content'], list):
                    if len(result['content']) > 0 and 'text' in result['content'][0]:
                        result = result['content'][0]['text']
                    else:
                        return result
                else:
                    return result
            
            # Parse string as JSON
            if isinstance(result, str) and result.startswith('{'):
                parsed = json.loads(result)
                
                # Check if MCP-wrapped
                if isinstance(parsed, dict) and 'content' in parsed:
                    if isinstance(parsed['content'], list) and len(parsed['content']) > 0:
                        if 'text' in parsed['content'][0]:
                            # Re-parse the inner text
                            inner_text = parsed['content'][0]['text']
                            if isinstance(inner_text, str) and inner_text.startswith('{'):
                                return json.loads(inner_text)
                            return {"text": inner_text}
                
                return parsed
            
        except json.JSONDecodeError as e:
            logger.debug(f"JSON parse failed: {e}")
        except Exception as e:
            logger.debug(f"Unexpected error parsing JSON: {e}")
        
        return None
    
    def _extract_taxon_from_filename(self, filename: str) -> str:
        """
        Extract taxon name from filename.
        Assumes format like "Salmo_salar_COI_20251031.fasta".
        
        Args:
            filename: Input file path or name
        
        Returns:
            Taxon name (e.g., "Salmo_salar") or "unknown"
        """
        import os
        basename = os.path.basename(filename)
        if "_" in basename:
            parts = basename.split("_")
            if len(parts) >= 2:
                return f"{parts[0]}_{parts[1]}"
        return "unknown"
    
    def _format_default_summary(self, parsed: Dict, kwargs: Dict, files: List[Dict], prefix: str) -> str:
        """
        Format a default summary message when no custom template is provided.
        
        Args:
            parsed: Parsed JSON result
            kwargs: Original function arguments
            files: List of extracted file info dicts
            prefix: Log prefix for context
        
        Returns:
            Formatted summary message
        """
        summary_parts = [f"✓ {prefix} complete!"]
        summary_parts.append(f"\n**Input:** {kwargs.get('fasta_file', 'unknown')}")
        
        for file_info in files:
            summary_parts.append(f"\n**{file_info['type'].replace('_', ' ').title()}:** {file_info['path']}")
        
        summary_parts.append("\n\n**IMPORTANT:** Use these exact paths for next steps.")
        
        return ''.join(summary_parts)
    
    def _get_tool_config(self, tool_name: str) -> Dict[str, Any]:
        """
        Get configuration for a specific MCP tool.
        Returns config dict with phase, output_fields, log_prefix, and optional summary_template.
        
        Args:
            tool_name: Name of the MCP tool (e.g., "process_sequences", "align_and_analyze")
        
        Returns:
            Configuration dictionary for the tool
        """
        # Processing tools configuration
        if tool_name == "process_sequences":
            def processing_summary(parsed: Dict, kwargs: Dict, files: List[Dict]) -> str:
                sequences_in = parsed.get("sequences_in", "unknown")
                sequences_out = parsed.get("sequences_out", "unknown")
                pipeline = kwargs.get("pipeline", [])
                output_file = files[0]["path"] if files else "unknown"
                
                return f"""✓ Processing complete!

**Input:** {kwargs.get('fasta_file', 'unknown')}
**Output:** {output_file}

**Pipeline:** {' → '.join(pipeline)}
**Sequences:** {sequences_in} → {sequences_out}

**IMPORTANT:** Use this exact path for next steps:
{output_file}

The processed sequences are ready for alignment and phylogenetic analysis."""
            
            return {
                "phase": "phase2",
                "output_fields": {"output_file": "processed_sequences"},
                "log_prefix": "PROCESSING",
                "summary_template": processing_summary
            }
        
        elif tool_name in ["fasta_qc", "dereplicate_sequences", "mask_low_complexity", "detect_chimeras"]:
            # Individual processing tools - use simple config
            tool_labels = {
                "fasta_qc": "QC",
                "dereplicate_sequences": "DEREPLICATION",
                "mask_low_complexity": "MASKING",
                "detect_chimeras": "CHIMERA_DETECTION"
            }
            return {
                "phase": "phase2",
                "output_fields": {"output_file": tool_name.replace("_", "-")},
                "log_prefix": tool_labels.get(tool_name, tool_name.upper())
            }
        
        # Alignment tools configuration
        elif tool_name in ["align_sequences", "align_and_analyze"]:
            def alignment_summary(parsed: Dict, kwargs: Dict, files: List[Dict]) -> str:
                algorithm = kwargs.get("algorithm", "unknown")
                summary_parts = [f"✓ Alignment and analysis complete using {algorithm}!"]
                summary_parts.append(f"\n**Input:** {kwargs.get('fasta_file', 'unknown')}")
                
                file_labels = {
                    "alignment": "Alignment file",
                    "phylogeny": "Phylogenetic tree",
                    "distances": "Distance matrix"
                }
                
                for file_info in files:
                    label = file_labels.get(file_info["type"], file_info["type"])
                    summary_parts.append(f"\n**{label}:** {file_info['path']}")
                
                summary_parts.append("\n\n**IMPORTANT:** Use these exact paths for primer design steps.")
                summary_parts.append("\nThe aligned sequences and phylogenetic analysis are ready for identifying signature regions.")
                
                return ''.join(summary_parts)
            
            return {
                "phase": "phase3",
                "output_fields": {
                    "alignment_file": "alignment",
                    "tree_file": "phylogeny",
                    "distance_file": "distances"
                },
                "log_prefix": "ALIGNMENT",
                "summary_template": alignment_summary
            }
        
        elif tool_name == "build_phylogeny":
            return {
                "phase": "phase3",
                "output_fields": {"tree_file": "phylogeny"},
                "log_prefix": "PHYLOGENY"
            }
        
        elif tool_name == "calculate_distances":
            return {
                "phase": "phase3",
                "output_fields": {"distance_file": "distances"},
                "log_prefix": "DISTANCES"
            }
        
        elif tool_name == "process_alignment":
            return {
                "phase": "phase3",
                "output_fields": {"output_file": "processed_alignment"},
                "log_prefix": "ALIGNMENT_PROCESSING"
            }
        
        # Default config for unknown tools
        else:
            return {
                "phase": "phase1",
                "output_fields": {"output_file": "output"},
                "log_prefix": tool_name.upper()
            }
    
    def _handle_processing_tool_result(self, result: str, kwargs: dict, tool_name: str) -> str:
        """
        Lightweight handler for processing tool results.
        
        Processing server saves files natively and returns paths in JSON.
        This handler just extracts paths, updates manifest, and returns summary.
        
        Args:
            result: JSON result from processing tool with output_file path
            kwargs: Original function arguments
            tool_name: Name of the tool being handled
        
        Returns:
            Formatted summary message
        """
        if not result or (isinstance(result, str) and result.startswith("Error")):
            return result
        
        try:
            import json
            import os
            
            # Quick JSON parse - processing server returns simple structure
            parsed = self._parse_mcp_json(result)
            if not parsed or not isinstance(parsed, dict):
                return result
            
            # Extract output file path
            output_file = parsed.get("output_file")
            if not output_file:
                logger.warning(f"[PROCESSING] No output_file in {tool_name} result")
                return result
            
            # Verify file exists
            if not os.path.exists(output_file):
                logger.error(f"[PROCESSING] Output file doesn't exist: {output_file}")
                return f"Error: Processing completed but output file not found: {output_file}"
            
            # Update manifest (lightweight - just track the file)
            if self.run_dir and self.manifest and "phases" in self.manifest:
                input_file = kwargs.get("fasta_file", "unknown")
                taxon = self._extract_taxon_from_filename(input_file)
                
                # Minimal metadata - no large content fields
                # Extract sequence counts from stats (MCP server returns stats.input_sequences/output_sequences)
                stats = parsed.get("stats", {})
                metadata = {
                    "input_file": input_file,
                    "taxon": taxon,
                    "sequences_in": stats.get("input_sequences", parsed.get("sequences_in")),
                    "sequences_out": stats.get("output_sequences", parsed.get("sequences_out")),
                    "pipeline": kwargs.get("pipeline", [])
                }
                
                self._update_manifest_artifact(
                    phase="phase2",
                    artifact_path=output_file,
                    artifact_type="processed_sequences",
                    metadata=metadata
                )
                logger.info(f"[PROCESSING] Tracked {output_file} in manifest")
            
            # Generate lightweight summary
            # Extract sequence counts from stats object (MCP server returns stats.input_sequences/output_sequences)
            stats = parsed.get("stats", {})
            sequences_in = stats.get("input_sequences", parsed.get("sequences_in", "unknown"))
            sequences_out = stats.get("output_sequences", parsed.get("sequences_out", "unknown"))
            pipeline = kwargs.get("pipeline", [])
            
            summary = f"""✓ Processing complete!

**Input:** {kwargs.get('fasta_file', 'unknown')}
**Output:** {output_file}

**Pipeline:** {' → '.join(pipeline) if pipeline else 'default'}
**Sequences:** {sequences_in} → {sequences_out}

**IMPORTANT:** Use this exact path for next steps:
{output_file}

The processed sequences are ready for alignment and phylogenetic analysis."""
            
            return summary
            
        except Exception as e:
            logger.error(f"[PROCESSING] Error handling {tool_name} result: {e}")
            return result
    
    def _handle_alignment_tool_result(self, result: str, kwargs: dict, tool_name: str) -> str:
        """
        Handle alignment tool results by saving data to files and returning summary.
        
        Unlike processing tools that return file paths, alignment tools return data
        (alignment content, distance matrices, phylogenetic trees) that we need to save.
        
        Args:
            result: JSON result from alignment tool with data fields
            kwargs: Original function arguments
            tool_name: Tool name (e.g., "align_and_analyze")
        
        Returns:
            Summary message with file paths for agents to use
        """
        import json
        import os
        from datetime import datetime
        
        if not result or (isinstance(result, str) and result.startswith("Error")):
            return result
        
        try:
            # Parse MCP-wrapped JSON
            actual_json = result
            if isinstance(result, dict) and 'content' in result:
                if len(result['content']) > 0 and 'text' in result['content'][0]:
                    actual_json = result['content'][0]['text']
            elif isinstance(result, str) and result.startswith('{'):
                temp_parsed = json.loads(result)
                if isinstance(temp_parsed, dict) and 'content' in temp_parsed:
                    if len(temp_parsed['content']) > 0 and 'text' in temp_parsed['content'][0]:
                        actual_json = temp_parsed['content'][0]['text']
            
            if isinstance(actual_json, str):
                parsed = json.loads(actual_json)
            else:
                parsed = actual_json
            
            if not isinstance(parsed, dict) or not parsed.get("success"):
                return result
            
            # Determine save location based on run_dir
            if self.run_dir:
                phase_dir = os.path.join(self.run_dir, "phase3")
                os.makedirs(phase_dir, exist_ok=True)
            else:
                phase_dir = "/results/alignments"
                os.makedirs(phase_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            input_file = kwargs.get("fasta_file", "unknown")
            taxon = self._extract_taxon_from_filename(input_file)
            
            saved_files = []
            
            # Save alignment if present
            if "alignment" in parsed and isinstance(parsed["alignment"], str):
                alignment_file = os.path.join(phase_dir, f"{taxon}_alignment_{timestamp}.fasta")
                with open(alignment_file, 'w') as f:
                    f.write(parsed["alignment"])
                saved_files.append({"path": alignment_file, "type": "alignment", "field": "alignment"})
                logger.info(f"[ALIGNMENT] Saved alignment to: {alignment_file}")
            
            # Save phylogeny if present  
            if "phylogeny" in parsed and isinstance(parsed["phylogeny"], dict):
                tree_file = os.path.join(phase_dir, f"{taxon}_tree_{timestamp}.nwk")
                tree_content = parsed["phylogeny"].get("tree", parsed["phylogeny"].get("newick", ""))
                if tree_content:
                    with open(tree_file, 'w') as f:
                        f.write(tree_content)
                    saved_files.append({"path": tree_file, "type": "phylogeny", "field": "phylogeny"})
                    logger.info(f"[ALIGNMENT] Saved phylogeny to: {tree_file}")
            
            # Save distance matrix if present
            if "distances" in parsed and isinstance(parsed["distances"], dict):
                distance_file = os.path.join(phase_dir, f"{taxon}_distances_{timestamp}.json")
                with open(distance_file, 'w') as f:
                    json.dump(parsed["distances"], f, indent=2)
                saved_files.append({"path": distance_file, "type": "distances", "field": "distances"})
                logger.info(f"[ALIGNMENT] Saved distances to: {distance_file}")
            
            if not saved_files:
                logger.warning("[ALIGNMENT] No alignment data found in result")
                return result
            
            # Update manifest
            if self.run_dir and self.manifest and "phases" in self.manifest:
                for file_info in saved_files:
                    try:
                        # Build metadata (exclude large content fields)
                        large_fields = ["alignment", "phylogeny", "distances", "processed_fasta", "fasta_content"]
                        metadata = {
                            "input_file": input_file,
                            "taxon": taxon,
                            **{k: v for k, v in kwargs.items() if k not in ["fasta_file", "fasta_content"]},
                            **{k: v for k, v in parsed.items() if k not in large_fields and not k.endswith("_content")}
                        }
                        
                        self._update_manifest_artifact(
                            phase="phase3",
                            artifact_path=file_info["path"],
                            artifact_type=file_info["type"],
                            metadata=metadata
                        )
                    except Exception as e:
                        logger.warning(f"[ALIGNMENT] Failed to update manifest: {e}")
            
            # Generate summary
            algorithm = kwargs.get("algorithm", "unknown")
            summary_parts = [f"✓ Alignment and analysis complete using {algorithm}!"]
            summary_parts.append(f"\n**Input:** {input_file}")
            
            file_labels = {
                "alignment": "Alignment file",
                "phylogeny": "Phylogenetic tree",
                "distances": "Distance matrix"
            }
            
            for file_info in saved_files:
                label = file_labels.get(file_info["type"], file_info["type"])
                summary_parts.append(f"\n**{label}:** {file_info['path']}")
            
            # Add statistics summary
            if "alignment_statistics" in parsed:
                stats = parsed["alignment_statistics"]
                summary_parts.append(f"\n\n**Alignment Statistics:**")
                summary_parts.append(f"- Sequences: {stats.get('num_sequences', 'unknown')}")
                summary_parts.append(f"- Length: {stats.get('alignment_length', 'unknown')}bp")
                summary_parts.append(f"- Average conservation: {stats.get('average_conservation', 0):.1%}")
            
            summary_parts.append("\n\n**IMPORTANT:** Use these exact paths for primer design steps.")
            summary_parts.append("\nThe aligned sequences and phylogenetic analysis are ready for identifying signature regions.")
            
            return ''.join(summary_parts)
            
        except Exception as e:
            logger.error(f"[ALIGNMENT] Error handling alignment result: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return result

    def _create_function_maps(self, mcp_functions: Dict[str, Callable]) -> Dict[str, Dict[str, Callable]]:
        """
        Create function maps for each agent based on 4-agent architecture.
        
        Args:
            mcp_functions: Dictionary of MCP function wrappers
            
        Returns:
            Dictionary containing function maps for each agent:
            - database_function_map: 5 database tools
            - analyst_function_map: 10 tools (5 processing + 5 alignment)
            - primer_design_function_map: 0 tools (Phase 4 pending)
        """
        database_function_map = {
            # Database tools - pure data retrieval (5 tools)
            "get_sequences": mcp_functions["get_sequences"],
            "get_taxonomy": mcp_functions["get_taxonomy"],
            "get_neighbors": mcp_functions["get_neighbors"],
            "extract_sequence_columns": mcp_functions["extract_sequence_columns"],
            "search_sra_studies": mcp_functions["search_sra_studies"],
        }

        analyst_function_map = {
            # Processing tools - sequence curation and QC (5 tools)
            "fasta_qc": mcp_functions["fasta_qc"],
            "dereplicate_sequences": mcp_functions["dereplicate_sequences"],
            "mask_low_complexity": mcp_functions["mask_low_complexity"],
            "detect_chimeras": mcp_functions["detect_chimeras"],
            "process_sequences": mcp_functions["process_sequences"],
            # Alignment tools - sequence analysis (5 tools)
            "align_sequences": mcp_functions["align_sequences"],
            "process_alignment": mcp_functions["process_alignment"],
            "build_phylogeny": mcp_functions["build_phylogeny"],
            "calculate_distances": mcp_functions["calculate_distances"],
            "align_and_analyze": mcp_functions["align_and_analyze"],
        }
        
        primer_design_function_map = {
            # Phase 4 tools will be added here (5 tools planned):
            # "find_signature_regions": mcp_functions["find_signature_regions"],
            # "design_primers": mcp_functions["design_primers"],
            # "validate_primers": mcp_functions["validate_primers"],
            # "insilico_pcr": mcp_functions["insilico_pcr"],
            # "blast_primers": mcp_functions["blast_primers"],
        }

        return {
            "database": database_function_map,
            "analyst": analyst_function_map,
            "primer_design": primer_design_function_map,
        }

    def _validate_agent_function_registration(
        self, 
        agent_name: str, 
        llm_config: Dict[str, Any], 
        function_map: Dict[str, Callable]
    ) -> None:
        """
        Validate that function schemas in llm_config match registered handlers in function_map.
        
        Args:
            agent_name: Name of the agent being validated
            llm_config: LLM configuration containing function schemas
            function_map: Dictionary of registered function handlers
        """
        if "functions" not in llm_config:
            logger.debug(f"{agent_name}: No function schemas in llm_config (expected for agents without tools)")
            return

        schema_names = {f["name"] for f in llm_config["functions"]}
        handler_names = set(function_map.keys())
        
        if schema_names == handler_names:
            logger.info(f"✓ {agent_name}: Function schemas and handlers match ({len(schema_names)} tools)")
            logger.debug(f"  Tools: {sorted(schema_names)}")
        else:
            missing_handlers = schema_names - handler_names
            extra_handlers = handler_names - schema_names
            if missing_handlers:
                logger.warning(f"⚠️  {agent_name}: Function schemas without handlers: {missing_handlers}")
            if extra_handlers:
                logger.warning(f"⚠️  {agent_name}: Function handlers without schemas: {extra_handlers}")

    def _create_coordinator_agent(self) -> AssistantAgent:
        """
        Create Coordinator agent (no tools - orchestration only).
        
        Returns:
            Configured CoordinatorAgent
        """
        coordinator = AssistantAgent(
            name="Coordinator",
            system_message=COORDINATOR_SYSTEM_MESSAGE,
            llm_config=self.llm_config
        )
        logger.info("Created Coordinator agent (orchestration, no tools)")
        return coordinator

    def _create_database_agent(self, function_map: Dict[str, Callable]) -> AssistantAgent:
        """
        Create DatabaseAgent with database retrieval tools.
        
        Args:
            function_map: Dictionary of database tool handlers (5 tools)
            
        Returns:
            Configured DatabaseAgent with registered functions
        """
        # Build specialized llm_config with function schemas
        llm_config = self._build_database_agent_llm_config()
        
        # Create agent
        database_agent = AssistantAgent(
            name="DatabaseAgent",
            system_message=DATABASE_AGENT_SYSTEM_MESSAGE,
            llm_config=llm_config
        )

        # Register function handlers
        database_agent.register_function(function_map=function_map)
        
        # Validate registration
        self._validate_agent_function_registration("DatabaseAgent", llm_config, function_map)
        
        return database_agent

    def _create_analyst_agent(self, function_map: Dict[str, Callable]) -> AssistantAgent:
        """
        Create AnalystAgent with processing and alignment tools.
        
        Args:
            function_map: Dictionary of processing + alignment tool handlers (10 tools)
            
        Returns:
            Configured AnalystAgent with registered functions
        """
        # Build specialized llm_config with function schemas
        llm_config = self._build_analyst_agent_llm_config()
        
        # Create agent
        analyst_agent = AssistantAgent(
            name="AnalystAgent",
            system_message=ANALYST_SYSTEM_MESSAGE,
            llm_config=llm_config
        )

        # Register function handlers
        analyst_agent.register_function(function_map=function_map)
        
        # Validate registration
        self._validate_agent_function_registration("AnalystAgent", llm_config, function_map)
        
        return analyst_agent

    def _create_primer_design_agent(self, function_map: Dict[str, Callable]) -> AssistantAgent:
        """
        Create PrimerDesignAgent (advisory mode - Phase 4 tools pending).
        
        Args:
            function_map: Dictionary of primer design tool handlers (0 tools currently)
            
        Returns:
            Configured PrimerDesignAgent
        """
        # No specialized llm_config yet - Phase 4 will add function schemas
        primer_agent = AssistantAgent(
            name="PrimerDesignAgent",
            system_message=PRIMER_DESIGN_AGENT_SYSTEM_MESSAGE,
            llm_config=self.llm_config
        )
        
        # Register functions if available (empty dict for now)
        if function_map:
            primer_agent.register_function(function_map=function_map)
            logger.info(f"PrimerDesignAgent created with {len(function_map)} tools")
        else:
            logger.info("PrimerDesignAgent created in advisory mode (Phase 4 tools pending)")
        
        return primer_agent

    def _create_user_proxy_agent(self, all_functions: Dict[str, Callable]) -> UserProxyAgent:
        """
        Create UserProxyAgent for termination and tool execution.
        
        Args:
            all_functions: Combined function map from all agents
            
        Returns:
            Configured UserProxyAgent
        """
        user_proxy = UserProxyAgent(
            name="User",
            human_input_mode="NEVER",
            max_consecutive_auto_reply=50,
            is_termination_msg=self._is_termination_message,
            code_execution_config=False,
            function_map=all_functions,
        )
        logger.info(f"Created UserProxyAgent with access to {len(all_functions)} tools")
        return user_proxy

    def _create_group_chat_and_manager(self) -> tuple:
        """
        Create GroupChat and GroupChatManager for multi-agent coordination.
        
        Returns:
            Tuple of (GroupChat, GroupChatManager)
        """
        max_rounds = int(os.getenv("AUTOGEN_MAX_ROUNDS", "50"))
        
        groupchat = GroupChat(
            agents=[
                self.agents["coordinator"],
                self.agents["database"],
                self.agents["analyst"],
                self.agents["primer_design"],
                self.agents["user_proxy"]
            ],
            messages=[],
            max_round=max_rounds,
            speaker_selection_method="auto",
            allow_repeat_speaker=False,
        )

        manager = GroupChatManager(
            groupchat=groupchat,
            llm_config=self.llm_config
        )
        
        logger.info(f"Created GroupChat with {len(groupchat.agents)} agents (max {max_rounds} rounds)")
        
        return groupchat, manager

    def _display_agent_summary(self, function_maps: Dict[str, Dict[str, Callable]]) -> None:
        """
        Display summary of created agents and their tool allocations.
        
        Args:
            function_maps: Dictionary of function maps for each agent
        """
        total_tools = sum(len(fm) for fm in function_maps.values())
        
        logger.info(f"✓ Created 4 specialized agents with {total_tools} total MCP tools:")
        logger.info(f"  • Coordinator: 0 tools (orchestration)")
        logger.info(f"  • DatabaseAgent: {len(function_maps['database'])} tools (data retrieval)")
        logger.info(f"  • AnalystAgent: {len(function_maps['analyst'])} tools (processing + alignment)")
        logger.info(f"  • PrimerDesignAgent: {len(function_maps['primer_design'])} tools (Phase 4 pending)")

    def _create_agents(self):
        """
        Create AutoGen agent team following 4-agent architecture.
        
        Architecture:
        - Coordinator: Workflow planning and orchestration (0 tools)
        - DatabaseAgent: Data retrieval from public databases (5 tools)
        - AnalystAgent: Data curation and analysis (10 tools: 5 processing + 5 alignment)
        - PrimerDesignAgent: Primer design and validation (0 tools - Phase 4 pending)
        - UserProxyAgent: Termination and tool execution coordination
        
        Raises:
            RuntimeError: If MCP executor not initialized
        """
        # Verify MCP bridge is initialized
        if not self.mcp_executor:
            raise RuntimeError("MCP executor not initialized. Call _setup_mcp_bridge() first.")
        
        logger.info("Initializing 4-agent qPCR design system...")

        # Display model information
        model_info = self.config_list[0] if self.config_list else {}
        model_name = self.model_name or model_info.get("model", "unknown")
        api_type = model_info.get("api_type", "unknown")
        model_display = MODEL_DISPLAY_NAMES.get(model_name, f"{api_type.upper()} - {model_name}")
        print_colored(f"🤖 Using {model_display}", Colors.BRIGHT_GREEN)

        # Step 1: Create MCP function wrappers
        mcp_functions = self._create_mcp_function_wrappers()
        logger.debug(f"Created {len(mcp_functions)} MCP function wrappers")

        # Step 2: Create function maps for each agent
        function_maps = self._create_function_maps(mcp_functions)

        # Step 3: Create specialized agents
        self.agents["coordinator"] = self._create_coordinator_agent()
        self.agents["database"] = self._create_database_agent(function_maps["database"])
        self.agents["analyst"] = self._create_analyst_agent(function_maps["analyst"])
        self.agents["primer_design"] = self._create_primer_design_agent(function_maps["primer_design"])
        
        # Step 4: Create user proxy with all functions
        all_functions = {
            **function_maps["database"],
            **function_maps["analyst"],
            **function_maps["primer_design"]
        }
        self.agents["user_proxy"] = self._create_user_proxy_agent(all_functions)

        # Step 5: Create group chat and manager
        self.groupchat, self.manager = self._create_group_chat_and_manager()

        # Step 6: Display summary
        self._display_agent_summary(function_maps)

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

        # Parse intent footer from message
        intent_info = self._parse_intent_footer(content, sender)

        # CRITICAL: Detect empty messages from User (AutoGen loop bug)
        # When Coordinator sends TERMINATE, AutoGen may select User with empty message
        # This causes an infinite loop - terminate immediately when User has no content
        if sender == "User" and not content:
            logger.warning("[TERMINATION] Detected empty User message - forcing termination to prevent loop")
            self._log_termination_reason("EMPTY_USER_MESSAGE", "Empty message from User after TERMINATE", sender)
            return True

        # CRITICAL: Check if TERMINATE was sent in recent messages (AutoGen loop bug)
        # If Coordinator sent TERMINATE recently and another agent is now speaking, terminate immediately
        # This catches the race condition where speaker selection happens before termination check
        if sender != "Coordinator" and hasattr(self, 'groupchat') and self.groupchat and len(self.groupchat.messages) > 1:
            # Check last 3 messages for TERMINATE from Coordinator
            recent_messages = self.groupchat.messages[-3:]
            for msg in recent_messages:
                if (isinstance(msg, dict) and 
                    msg.get("name") == "Coordinator" and 
                    msg.get("content", "").rstrip().endswith("TERMINATE")):
                    logger.warning(f"[TERMINATION] Coordinator sent TERMINATE recently, but {sender} is trying to respond")
                    logger.warning(f"  This is the AutoGen GroupChat bug - speaker selected after TERMINATE")
                    logger.warning(f"  FORCING TERMINATION to prevent loop")
                    self._log_termination_reason("TERMINATE_AFTER_COORDINATOR", f"Agent {sender} selected after Coordinator TERMINATE", sender)
                    return True

        # CRITICAL: Check if message contains a function call (work is continuing)
        # AutoGen/AG2 stores function calls in 'function_call' or 'tool_calls' field
        if message.get("function_call") or message.get("tool_calls"):
            logger.info(f"Message from {sender} contains function call - allowing execution")
            return False
        
        # 0. WORKFLOW ENFORCEMENT: Ensure complete 4-phase workflow before termination
        # Prevents premature termination at any phase
        if hasattr(self, 'task_logger') and self.task_logger and self.task_logger.task_log:
            tool_calls = self.task_logger.task_log[0].get("tool_calls", [])
            
            # Check for SUCCESSFUL completion of each phase
            has_successful_retrieval = any(
                "get_sequences" == tc.get("tool") and tc.get("success", False) 
                for tc in tool_calls
            )
            has_processing = any(
                tc.get("tool") in ["fasta_qc", "process_sequences", "dereplicate_sequences", 
                                   "mask_low_complexity", "detect_chimeras"] and tc.get("success", False)
                for tc in tool_calls
            )
            has_alignment = any(
                tc.get("tool") in ["align_sequences", "align_and_analyze"] and tc.get("success", False)
                for tc in tool_calls
            )
            has_phylogeny = any(
                tc.get("tool") in ["build_phylogeny", "calculate_distances", "align_and_analyze"] and tc.get("success", False)
                for tc in tool_calls
            )
            
            # PHASE 1: If sequences retrieved but not processed, don't terminate
            if has_successful_retrieval and not has_processing and content.endswith("TERMINATE"):
                logger.warning(f"[WORKFLOW] Preventing termination - Phase 1 complete but Phase 2 (processing) not started")
                logger.warning(f"  retrieval={has_successful_retrieval}, processing={has_processing}")
                return False
            
            # PHASE 2: If processing done but no alignment, don't terminate
            if has_processing and not has_alignment and content.endswith("TERMINATE"):
                logger.warning(f"[WORKFLOW] Preventing termination - Phase 2 (processing) complete but Phase 2b (alignment) not started")
                logger.warning(f"  processing={has_processing}, alignment={has_alignment}")
                return False
            
            # PHASE 3: If alignment done but no phylogeny, don't terminate  
            if has_alignment and not has_phylogeny and content.endswith("TERMINATE"):
                logger.warning(f"[WORKFLOW] Preventing termination - Alignment complete but phylogenetic analysis not done")
                logger.warning(f"  alignment={has_alignment}, phylogeny={has_phylogeny}")
                return False
            
            # Log workflow progress
            if has_successful_retrieval or has_processing or has_alignment or has_phylogeny:
                logger.info(f"[WORKFLOW] Phase completion: Retrieval={has_successful_retrieval}, Processing={has_processing}, Alignment={has_alignment}, Phylogeny={has_phylogeny}")
        
        # 1. Explicit termination condition (highest priority)
        # CRITICAL: Only Coordinator can issue TERMINATE command
        if content.endswith("TERMINATE"):
            if sender != "Coordinator":
                logger.warning(f"[SECURITY] Non-Coordinator agent '{sender}' attempted to TERMINATE - REJECTING")
                logger.warning(f"  Only Coordinator can issue TERMINATE to prevent premature workflow termination")
                return False
            
            # Check if this is a repeated TERMINATE (AutoGen loop bug)
            if hasattr(self, 'groupchat') and self.groupchat and len(self.groupchat.messages) > 2:
                recent_messages = self.groupchat.messages[-5:]  # Check last 5 messages
                terminate_count = sum(1 for msg in recent_messages 
                                     if isinstance(msg, dict) 
                                     and msg.get("content", "").rstrip().endswith("TERMINATE")
                                     and msg.get("name") == "Coordinator")
                
                if terminate_count > 1:
                    logger.error(f"[TERMINATION] Coordinator sent TERMINATE {terminate_count} times in last 5 messages!")
                    logger.error(f"  This indicates AutoGen GroupChat is not respecting termination signal")
                    logger.error(f"  FORCING TERMINATION to break infinite loop")
                    self._log_termination_reason("REPEATED_TERMINATE", f"TERMINATE sent {terminate_count} times", sender)
                    return True
            
            logger.info(f"Explicit termination message detected from Coordinator: 'TERMINATE'")
            self._log_termination_reason("EXPLICIT_TERMINATE", content, sender)
            return True
            
        # 2. LOOP DETECTION: Check if same tool called too many times
        if hasattr(self, 'task_logger') and self.task_logger and self.task_logger.task_log:
            tool_calls = self.task_logger.task_log[0].get("tool_calls", [])
            # Count occurrences of each tool
            tool_counts = {}
            for tc in tool_calls:
                tool_name = tc.get("tool", "")
                tool_counts[tool_name] = tool_counts.get(tool_name, 0) + 1
            
            # If any tool was called >10 times, it's a loop - force termination
            for tool_name, count in tool_counts.items():
                if count > 10:
                    logger.error(f"[LOOP DETECTED] Tool '{tool_name}' called {count} times - likely infinite loop!")
                    logger.error(f"  This usually means the agent is stuck and not progressing to the next phase")
                    logger.error(f"  Forcing termination to prevent further waste")
                    self._log_termination_reason("INFINITE_LOOP_DETECTED", f"Tool {tool_name} called {count} times", sender)
                    return True
        
        # 3. Check for repetitive messages (content-based loop detection)
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
        # CRITICAL: Only terminate on EXPLICIT completion indicators
        # DO NOT terminate on phase completions (e.g., "sequences retrieved", "data collection complete")
        # DO NOT terminate if agent is announcing next actions or suggesting function calls
        completion_phrases = [
            "all phases complete",
            "all 4 phases complete", 
            "complete 4-phase workflow finished",
            "workflow completed",
            "primer design complete and validated",
            "assay design complete and validated",
            "ready for wet lab implementation"
        ]
        
        content_lower = content.lower()
        
        # Check if agent is suggesting a function call (work is continuing)
        if "suggested function call" in content_lower or "function call:" in content_lower:
            logger.info(f"Agent {sender} suggesting function call - workflow continuing")
            return False
        
        # Check if agent is announcing next steps (work is continuing)
        continuation_indicators = [
            "i will initiate",
            "i will proceed",
            "let's start",
            "let's initiate",
            "next steps:",
            "proceeding to",
            "will now perform"
        ]
        for indicator in continuation_indicators:
            if indicator in content_lower:
                logger.info(f"Agent {sender} announcing continuation: '{indicator}' - allowing workflow to proceed")
                return False
        
        # Only check completion phrases if no continuation indicators found
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
            max_rounds = int(os.getenv("AUTOGEN_MAX_ROUNDS", "50"))
            if current_rounds >= max_rounds - 2:  # Stop 2 rounds before max
                logger.warning(f"Approaching maximum rounds ({current_rounds}/{max_rounds}) - terminating conversation")
                self._log_termination_reason("MAX_ROUNDS_APPROACHING", content, sender)
                return True
                
        return False
    
    def _filter_pii_from_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Filter PII (Personally Identifiable Information) from metadata.

        Removes fields that may contain:
        - Submitter names
        - Email addresses
        - Institution names
        - Contact information

        Args:
            metadata: Raw metadata dictionary

        Returns:
            Filtered metadata with PII removed
        """
        # PII fields to remove (case-insensitive)
        pii_fields = {
            "submitter", "submitted_by", "author", "authors",
            "email", "contact", "contact_email", "contact_person",
            "institution", "organization", "lab", "laboratory",
            "address", "phone", "fax",
            "principal_investigator", "pi", "researcher"
        }

        # Create filtered copy
        filtered = {}
        for key, value in metadata.items():
            key_lower = key.lower()

            # Skip if key matches PII field
            if key_lower in pii_fields:
                logger.debug(f"[PII] Filtered field: {key}")
                continue

            # Skip if key contains PII-related words
            if any(pii_word in key_lower for pii_word in ["submitter", "author", "email", "contact", "institution"]):
                logger.debug(f"[PII] Filtered field: {key}")
                continue

            filtered[key] = value

        if len(filtered) < len(metadata):
            logger.info(f"[PII] Filtered {len(metadata) - len(filtered)} PII fields from metadata")

        return filtered

    def _parse_intent_footer(self, content: str, sender: str) -> Dict[str, Optional[str]]:
        """
        Parse intent footer from agent message.

        Expected format:
        # intent: <handoff|continue|terminate|error>
        # next_agent: <Coordinator|DatabaseAgent|AnalystAgent|PrimerDesignAgent|none>

        Args:
            content: Message content
            sender: Agent name sending the message

        Returns:
            Dict with 'intent' and 'next_agent' keys (None if not found)
        """
        import re

        intent = None
        next_agent = None

        # Extract intent
        intent_match = re.search(r'#\s*intent:\s*(\w+)', content, re.IGNORECASE)
        if intent_match:
            intent = intent_match.group(1).lower()

        # Extract next_agent
        next_agent_match = re.search(r'#\s*next_agent:\s*(\w+)', content, re.IGNORECASE)
        if next_agent_match:
            next_agent = next_agent_match.group(1)

        # Validate intent
        valid_intents = ["handoff", "continue", "terminate", "error"]
        if intent and intent not in valid_intents:
            logger.warning(f"[INTENT] Invalid intent '{intent}' from {sender} - expected one of {valid_intents}")
            intent = None

        # Validate next_agent
        valid_agents = ["Coordinator", "DatabaseAgent", "AnalystAgent", "PrimerDesignAgent", "none"]
        if next_agent and next_agent not in valid_agents:
            logger.warning(f"[INTENT] Invalid next_agent '{next_agent}' from {sender} - expected one of {valid_agents}")
            next_agent = None

        # Log intent if found
        if intent or next_agent:
            logger.info(f"[INTENT] {sender} → intent={intent}, next_agent={next_agent}")

        # Validate intent-sender combination
        if intent == "terminate" and sender != "Coordinator":
            logger.warning(f"[INTENT] Non-Coordinator {sender} declared intent:terminate - this is invalid")
            logger.warning(f"  Only Coordinator can declare terminate intent")

        return {
            "intent": intent,
            "next_agent": next_agent
        }

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
            
            # 2. Task completion phrases (strict - avoid false positives)
            content_lower = content.lower()
            completion_phrases = [
                "all phases complete",
                "all 4 phases complete",
                "complete 4-phase workflow finished",
                "workflow completed",
                "primer design complete and validated",
                "assay design complete and validated",
                "ready for wet lab implementation"
            ]
            
            for phrase in completion_phrases:
                if phrase in content_lower:
                    return {
                        'reason': 'TASK_COMPLETION',
                        'sender': sender,
                        'timestamp': datetime.now().isoformat()
                    }
        
        # 3. Check if max rounds was reached
        max_rounds = int(os.getenv("AUTOGEN_MAX_ROUNDS", "50"))
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
        
        # Use a set to track unique accomplishment categories (prevent duplicates)
        accomplishment_categories = set()
        
        # First, check tool calls from the task logger for direct evidence (MOST RELIABLE)
        # NOTE: We only count actual TOP-LEVEL tool calls, not internal pipeline steps
        # to avoid hallucinating accomplishments that didn't actually happen
        if hasattr(self, 'task_logger') and self.task_logger and self.task_logger.task_log:
            tool_calls = self.task_logger.task_log[0].get("tool_calls", [])
            
            # Track tool-based accomplishments - ONLY count actual tool calls
            retrieval_count = sum(1 for tc in tool_calls if tc.get("tool") == "get_sequences" and tc.get("success", False))
            processing_count = sum(1 for tc in tool_calls if tc.get("tool") in ["process_sequences", "fasta_qc"] and tc.get("success", False))
            
            # NOTE: We do NOT check for dereplicate_sequences, detect_chimeras, mask_low_complexity
            # as separate tools because they may be internal steps within process_sequences.
            # We don't want to hallucinate accomplishments for steps that weren't actually run.
            
            # Add accomplishments based on actual tool calls ONLY
            if retrieval_count > 0:
                summary["key_accomplishments"].append(f"Retrieved sequences from {retrieval_count} species/datasets")
                accomplishment_categories.add("retrieval")
            if processing_count > 0:
                summary["key_accomplishments"].append(f"Processed {processing_count} sequence sets through quality pipeline")
                accomplishment_categories.add("processing")
        
        # Analyze messages to extract key information
        for msg in messages:
            if not isinstance(msg, dict):
                continue
                
            sender = msg.get("name", "unknown")
            content = msg.get("content", "")
            
            # Track agents involved
            if sender not in summary["agents_involved"]:
                summary["agents_involved"].append(sender)
            
            # Extract key accomplishments based on content (only if not already covered by tool calls)
            content_lower = content.lower()
            
            # Data retrieval accomplishments (only add if not already tracked via tool calls)
            if "taxonomy" in content_lower and "verified" in content_lower and "taxonomy" not in accomplishment_categories:
                summary["key_accomplishments"].append("Species taxonomy verified")
                accomplishment_categories.add("taxonomy")
            if "off-target" in content_lower and "identified" in content_lower and "off-targets" not in accomplishment_categories:
                summary["key_accomplishments"].append("Off-target species identified")
                accomplishment_categories.add("off-targets")
            
            # Analysis accomplishments
            if "analysis" in content_lower and "complete" in content_lower and "analysis" not in accomplishment_categories:
                summary["key_accomplishments"].append("Sequence analysis completed")
                accomplishment_categories.add("analysis")
            if "primer" in content_lower and ("recommended" in content_lower or "designed" in content_lower) and "primer_design" not in accomplishment_categories:
                summary["key_accomplishments"].append("Primer design recommendations provided")
                accomplishment_categories.add("primer_design")
            
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
        elif termination_reason == "REPEATED_TERMINATE":
            summary["next_steps"].append("⚠️  Conversation terminated due to repeated TERMINATE messages (AutoGen loop bug)")
            summary["next_steps"].append("Review results in /results/ directory - workflow likely completed successfully")
            summary["next_steps"].append("If workflow incomplete, restart with clearer objectives")
        elif termination_reason == "TERMINATE_AFTER_COORDINATOR":
            summary["next_steps"].append("⚠️  Agent attempted to respond after Coordinator TERMINATE (AutoGen loop bug)")
            summary["next_steps"].append("Review results in /results/ directory - workflow likely completed successfully")
            summary["next_steps"].append("This is expected behavior when AutoGen selects speakers before checking termination")
        elif termination_reason == "EMPTY_USER_MESSAGE":
            summary["next_steps"].append("⚠️  Conversation terminated due to empty User message after TERMINATE")
            summary["next_steps"].append("Review results in /results/ directory - workflow likely completed")
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
            "REPEATED_TERMINATE": Colors.YELLOW,  # Warning but likely successful
            "TERMINATE_AFTER_COORDINATOR": Colors.YELLOW,  # Warning but likely successful
            "EMPTY_USER_MESSAGE": Colors.YELLOW,  # Warning but likely successful
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

        # Compliance disclaimer (automatically injected)
        print_colored("⚠️  COMPLIANCE NOTICE", Colors.BRIGHT_YELLOW, bold=True)
        print_colored("Research Use Only - Not for Clinical Diagnostics", Colors.YELLOW)
        print()
        print("This tool is designed for research and educational purposes.")
        print("Results are NOT validated for clinical diagnostic use.")
        print("For clinical applications, consult regulatory guidelines and")
        print("conduct proper validation studies before implementation.")
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

        # Generate run_id and create directory structure
        self.run_id = self._generate_run_id()
        self._create_run_directory()

        print_colored(f"🆔 Run ID: {self.run_id}", Colors.CYAN)
        print_colored(f"📁 Results directory: {self.run_dir}", Colors.CYAN)
        print()

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
