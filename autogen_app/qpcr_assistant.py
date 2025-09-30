"""
qPCR Assay Design Assistant

AutoGen-powered multi-agent system for designing species-specific qPCR assays.
"""

import os
import asyncio
import logging
from typing import Dict, Any
import autogen
from autogen_mcp_bridge import (
    MCPClientBridge,
    create_autogen_functions,
    AutoGenMCPFunctionExecutor
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QPCRAssistant:
    """Multi-agent qPCR assay design assistant."""

    def __init__(self, openai_api_key: str):
        """
        Initialize qPCR assistant.

        Args:
            openai_api_key: OpenAI API key for LLM
        """
        self.api_key = openai_api_key
        self.mcp_bridge = None
        self.agents = {}
        self.group_chat = None
        self.manager = None

    async def initialize(self):
        """Initialize MCP bridge and AutoGen agents."""
        logger.info("Initializing qPCR Assistant...")

        # Initialize MCP bridge
        await self._setup_mcp_bridge()

        # Create AutoGen agents
        await self._create_agents()

        logger.info("✅ qPCR Assistant ready!")

    async def _setup_mcp_bridge(self):
        """Setup MCP server connections."""
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

        logger.info("MCP servers connected")

    async def _create_agents(self):
        """Create AutoGen agent team."""
        # LLM configuration
        config_list = [{
            "model": "gpt-4",
            "api_key": self.api_key,
        }]

        llm_config = {
            "config_list": config_list,
            "timeout": 120,
            "temperature": 0.7,
        }

        # Get available MCP functions
        mcp_functions = create_autogen_functions(["database"])

        # Create function executor
        executor = AutoGenMCPFunctionExecutor(self.mcp_bridge)

        # 1. User Proxy (human interface)
        self.agents["user"] = autogen.UserProxyAgent(
            name="User",
            system_message="You are the user requesting qPCR assay design.",
            human_input_mode="ALWAYS",
            max_consecutive_auto_reply=0,
            code_execution_config=False
        )

        # 2. Coordinator Agent
        self.agents["coordinator"] = autogen.AssistantAgent(
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

Think step-by-step and explain your reasoning.""",
            llm_config=llm_config
        )

        # 3. Database Agent (with MCP tools)
        self.agents["database"] = autogen.AssistantAgent(
            name="DatabaseAgent",
            system_message="""You are a biological database specialist with access to NCBI, BOLD, and other databases.

Your responsibilities:
1. Retrieve sequences for target species using get_sequences
2. Identify taxonomically similar species using get_neighbors (these are off-targets!)
3. Gather comprehensive sequence datasets for both targets and off-targets
4. Extract and organize metadata using extract_sequence_columns
5. Search for existing studies using search_sra_studies

Best practices:
- For COI barcoding, use source='bold' or 'ncbi'
- Always get sequences for potential off-targets to ensure specificity
- Retrieve enough sequences (50-100) for robust primer design
- Check taxonomy with get_taxonomy to verify scientific names

Always report:
- Number of sequences retrieved
- Species coverage
- Any issues or warnings""",
            llm_config={
                **llm_config,
                "functions": mcp_functions
            }
        )

        # Register MCP function implementations
        for func_def in mcp_functions:
            func_name = func_def["name"]

            # Create async wrapper
            async def mcp_func_wrapper(**kwargs):
                return await executor.execute_function(func_name, kwargs)

            # Register with agents
            self.agents["user"].register_function(
                function_map={func_name: mcp_func_wrapper}
            )

        # 4. Analysis Agent (will use MCP tools when Phase 4 complete)
        self.agents["analyst"] = autogen.AssistantAgent(
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

For now, provide analysis based on sequence data.""",
            llm_config=llm_config
        )

        logger.info(f"Created {len(self.agents)} agents")

    async def run_workflow(self, user_message: str):
        """
        Run a qPCR design workflow.

        Args:
            user_message: User's request for qPCR design
        """
        # Create group chat
        self.group_chat = autogen.GroupChat(
            agents=list(self.agents.values()),
            messages=[],
            max_round=20,
            speaker_selection_method="round_robin"
        )

        # Create manager
        manager_config = {
            "config_list": [{
                "model": "gpt-4",
                "api_key": self.api_key
            }],
            "timeout": 120,
        }

        self.manager = autogen.GroupChatManager(
            groupchat=self.group_chat,
            llm_config=manager_config
        )

        # Start conversation
        await self.agents["user"].a_initiate_chat(
            self.manager,
            message=user_message
        )

    async def shutdown(self):
        """Cleanup resources."""
        if self.mcp_bridge:
            await self.mcp_bridge.shutdown()
        logger.info("qPCR Assistant shutdown complete")


async def main():
    """Main entry point."""
    # Get API key
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        logger.error("OPENAI_API_KEY environment variable not set")
        return

    # Create assistant
    assistant = QPCRAssistant(openai_api_key)

    try:
        # Initialize
        await assistant.initialize()

        # Example workflow
        user_request = """
I need to design a qPCR assay to identify Atlantic salmon (Salmo salar)
and distinguish it from rainbow trout (Oncorhynchus mykiss) and other salmonids.

Requirements:
- Target: Salmo salar
- Off-targets: Oncorhynchus genus (especially mykiss)
- Genomic region: COI (cytochrome oxidase I)
- Application: Species verification in aquaculture

Please:
1. Retrieve COI sequences for target and off-targets
2. Identify other potential cross-reactive species
3. Analyze sequences to find signature regions
4. Recommend primer design strategy
"""

        # Run workflow
        await assistant.run_workflow(user_request)

    except Exception as e:
        logger.error(f"Error: {e}")
        raise

    finally:
        await assistant.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
