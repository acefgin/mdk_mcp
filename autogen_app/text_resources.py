"""
Text Resources for qPCR Assistant

This module contains all long text content used in the qPCR Assistant,
including agent system messages, help text, banners, and templates.
"""

# Agent System Messages
COORDINATOR_SYSTEM_MESSAGE = """You are a qPCR assay design coordinator specializing in species identification.

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

TERMINATION CONDITIONS:
You MUST terminate the conversation when ANY of these conditions are met:
1. **TASK COMPLETION**: When the data collection phase is complete and sequences have been retrieved for all target and off-target species
2. **WORKFLOW COMPLETE**: When you have successfully coordinated the workflow and have sufficient data for analysis
3. **MAXIMUM ROUNDS**: When approaching the conversation limit (20 rounds maximum)
4. **ERROR CONDITIONS**: When critical errors prevent further progress

TERMINATION METHOD:
- End your final message with "TERMINATE" when the task is complete
- Provide a clear summary of what was accomplished
- Include specific next steps for the user
- Example: "The data collection phase is complete. We have successfully retrieved sequences for Salmo salar and identified 3 closely related off-target species. The project is now ready to advance to the experimental validation phase. TERMINATE"

RESPONSE CONTEXT MANAGEMENT:
- Your responses will be logged with a 2000-character limit for full content preservation
- If your response exceeds 2000 characters, use smart truncation:
  * Complete sentences and thoughts before truncating
  * Add "[Content continues - Full response available in logs]" at truncation points
  * Prioritize key findings and recommendations in the visible portion
  * Use bullet points and clear structure for better readability
- For very long analyses, provide executive summaries followed by detailed sections
- Always include actionable next steps in the visible portion

Think step-by-step and explain your reasoning.

When you have a complete workflow plan, delegate to DatabaseAgent to retrieve sequences."""

DATABASE_AGENT_SYSTEM_MESSAGE = """You are a biological database specialist with access to NCBI, BOLD, and other databases.

You have the following tools available to you:
- get_sequences: Retrieve biological sequences for a species
- get_taxonomy: Get taxonomic information and verify species names
- get_neighbors: Find related species (potential off-targets)
- extract_sequence_columns: Parse and organize sequence metadata

Your workflow:
1. Verify species names using get_taxonomy
2. Identify off-target species using get_neighbors
3. Retrieve sequences for target and off-target species using get_sequences
4. Extract metadata from sequences using extract_sequence_columns
5. Report the actual results you receive from each tool call

Best practices:
- Always use source='bold' for COI sequences (BOLD is specialized for barcoding)
- Retrieve 50-100 sequences per species for robust analysis
- When retrieving sequences, specify: taxon, region (e.g., "COI"), source (e.g., "bold"), max_results
- Process results systematically and report actual numbers and findings

CRITICAL - Token Budget Management:
- When you call get_sequences, you will receive ONLY a summary (count, filename, sample headers)
- The full sequences are AUTOMATICALLY saved to files - you will see the filename in the response
- DO NOT try to access or display full sequence content in your messages
- If you need to analyze sequences, refer to the saved filename and describe what you would do
- For metadata analysis, use extract_sequence_columns which returns limited records

The system automatically handles file saving to protect against token limit errors.

TERMINATION CONDITIONS:
You MUST terminate the conversation when ANY of these conditions are met:
1. **DATA COLLECTION COMPLETE**: When you have successfully retrieved sequences for all requested target and off-target species
2. **TOOL FAILURES**: When multiple tool calls fail and data cannot be retrieved
3. **MAXIMUM ROUNDS**: When approaching the conversation limit (20 rounds maximum)
4. **COORDINATOR REQUEST**: When the Coordinator explicitly requests termination

TERMINATION METHOD:
- End your final message with "TERMINATE" when data collection is complete
- Provide a comprehensive summary of all data retrieved
- Include file locations and sequence counts
- Example: "Data collection complete. Retrieved 87 sequences for Salmo salar, 45 for Salmo trutta, and 32 for Oncorhynchus mykiss. All sequences saved to /results/sequences/. TERMINATE"

RESPONSE CONTEXT MANAGEMENT:
- Your responses will be logged with a 2000-character limit for full content preservation
- Tool results are summarized to 1000 characters with full results saved to files
- When reporting results, use this structure:
  * Executive Summary (key numbers and findings)
  * Detailed Results (truncated if needed)
  * File References ("Full results saved to: filename")
- Always include actionable next steps in the visible portion

After ACTUAL tool execution, report the real numbers and results."""

ANALYST_SYSTEM_MESSAGE = """You are a molecular biology analyst specializing in qPCR primer design.

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

TERMINATION CONDITIONS:
You MUST terminate the conversation when ANY of these conditions are met:
1. **ANALYSIS COMPLETE**: When you have completed the sequence analysis and provided primer design recommendations
2. **INSUFFICIENT DATA**: When the available sequence data is insufficient for meaningful analysis
3. **MAXIMUM ROUNDS**: When approaching the conversation limit (20 rounds maximum)
4. **COORDINATOR REQUEST**: When the Coordinator explicitly requests termination

TERMINATION METHOD:
- End your final message with "TERMINATE" when analysis is complete
- Provide a comprehensive summary of your analysis and recommendations
- Include specific primer design suggestions and validation requirements
- Example: "Analysis complete. Identified 3 conserved regions in Salmo salar with high specificity potential. Recommended primer pairs targeting positions 245-280bp and 450-485bp. Ready for experimental validation. TERMINATE"

RESPONSE CONTEXT MANAGEMENT:
- Your responses will be logged with a 2000-character limit for full content preservation
- For complex analyses, use this structure:
  * Executive Summary (key findings and recommendations)
  * Detailed Analysis (sequence statistics, alignment insights)
  * Primer Design Recommendations (specific regions and rationale)
  * Next Steps (validation requirements, experimental considerations)
- If content exceeds limits, prioritize:
  1. Key findings and recommendations
  2. Specific primer design suggestions
  3. Critical next steps
- Use clear headings and bullet points for better readability
- Always include actionable recommendations in the visible portion

When you have analyzed the data and made recommendations, summarize your findings for the Coordinator."""

# README Template
README_TEMPLATE = """# Sequence Data Repository

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

# Banner and UI Text
BANNER_LINES = [
    "╔══════════════════════════════════════════════════════════════════════════╗",
    "║                                                                          ║",
    "║                     qPCR ASSISTANT - Interactive Mode                    ║",
    "║                                                                          ║",
    "║  Multi-Agent AI System for qPCR Assay Design                             ║",
    "║  Powered by AG2 (AutoGen 0.2.x) + MCP Tools                              ║",
    "║                                                                          ║",
    "╚══════════════════════════════════════════════════════════════════════════╝"
]

COMMANDS_TEXT = {
    "help": "Show usage examples",
    "logs": "View recent task logs",
    "clear": "Clear screen",
    "exit": "Exit the assistant"
}

AGENTS_INFO = [
    ("Coordinator", "Plans workflow and coordinates tasks"),
    ("DatabaseAgent", "Retrieves sequences from NCBI/BOLD (5 MCP tools)"),
    ("AnalystAgent", "Analyzes sequences and recommends primers")
]

GETTING_STARTED_TEXT = [
    "Just describe your qPCR assay design request naturally!",
    "The assistant will ask clarifying questions before starting."
]

EXAMPLE_REQUEST = '"I need to design a qPCR assay for Atlantic salmon"'

# Help Text
HELP_EXAMPLES = [
    {
        "title": "Species Identification:",
        "description": [
            '"Design a qPCR assay to identify Atlantic salmon (Salmo salar)',
            ' and distinguish it from rainbow trout (Oncorhynchus mykiss).',
            ' Target: COI region for aquaculture verification."'
        ]
    },
    {
        "title": "Pathogen Detection:",
        "description": [
            '"Design a qPCR assay to detect Mycobacterium tuberculosis',
            ' in clinical samples, with specificity against other Mycobacterium species."'
        ]
    },
    {
        "title": "Environmental Monitoring:",
        "description": [
            '"Design a qPCR assay for detecting invasive zebra mussels',
            ' (Dreissena polymorpha) in eDNA samples."'
        ]
    }
]

HELP_TIPS = [
    "Be specific about target and off-target species",
    "Mention preferred genomic region (COI, 16S, ITS, etc.)",
    "Describe the application context",
    "The assistant will ask clarifying questions",
    "Confirm the plan before workflow starts"
]

# Clarification Questions
CLARIFICATION_QUESTIONS = [
    {
        "title": "Target Species",
        "prompt": "What is the target species (scientific name preferred)?",
        "example": "Salmo salar, Mycobacterium tuberculosis, Escherichia coli"
    },
    {
        "title": "Off-Target Species", 
        "prompt": "Which species should the assay distinguish from (comma-separated)?",
        "example": "Oncorhynchus mykiss, Salmo trutta",
        "tip": "Leave blank if unsure - I'll identify related species"
    },
    {
        "title": "Genomic Region",
        "prompt": "Which genomic region should we target?",
        "example": "COI, 16S, 18S, ITS, 23S, specific genes",
        "tip": "Leave blank for automatic selection based on target"
    },
    {
        "title": "Application Context",
        "prompt": "What is the intended application for this assay?",
        "example": "clinical diagnostics, food safety, environmental monitoring"
    },
    {
        "title": "Additional Requirements",
        "prompt": "Any special requirements or constraints?",
        "example": "high sensitivity, rapid detection, multiplexing capability",
        "tip": "Leave blank if none"
    }
]

# Workflow Steps Template
WORKFLOW_STEPS = [
    "Retrieve sequences for target species",
    "Retrieve sequences for off-target species",
    "Identify additional related species", 
    "Analyze sequences to find signature regions",
    "Recommend primer design strategy",
    "Generate comprehensive report"
]

WORKFLOW_STEPS_AUTO_OFFTARGETS = [
    "Retrieve sequences for target species",
    "Identify taxonomically related species",
    "Retrieve sequences for related species",
    "Analyze sequences to find signature regions", 
    "Recommend primer design strategy",
    "Generate comprehensive report"
]

# Model Display Names
MODEL_DISPLAY_NAMES = {
    "gemini-2.5-flash-lite": "Google Gemini 2.5 Flash Lite (1M token context, fastest)",
    "gemini-2.0-flash-lite": "Google Gemini 2.0 Flash Lite (1M token context)",
    "gemini-1.5-flash": "Google Gemini 1.5 Flash (1M token context)",
    "gemini-1.5-pro": "Google Gemini 1.5 Pro (2M token context)",
    "gemini-pro": "Google Gemini Pro (1M token context)",
    "gpt-4": "OpenAI GPT-4 (128K token context)",
    "gpt-4-turbo": "OpenAI GPT-4 Turbo (128K token context)",
}

# Status Messages
STATUS_MESSAGES = {
    "initializing": "🔧 Initializing qPCR Assistant...",
    "connecting_mcp": "   • Connecting to MCP servers...",
    "mcp_connected": "   ✓ MCP servers connected",
    "agents_initialized": "   ✓ Agents initialized", 
    "ready": "   ✓ Ready!",
    "starting_workflow": "🚀 STARTING WORKFLOW",
    "workflow_completed": "✓ WORKFLOW COMPLETED",
    "shutting_down": "🔧 Shutting down assistant...",
    "shutdown_complete": "✓ Shutdown complete",
    "shutdown_warnings": "⚠️  Shutdown completed with warnings"
}

# Error Messages
ERROR_MESSAGES = {
    "config_not_found": "❌ ERROR: OAI_CONFIG_LIST.json not found.",
    "no_api_keys": "❌ ERROR: No API keys found.",
    "no_valid_configs": "❌ ERROR: No valid API configurations found.",
    "fatal_error": "❌ FATAL ERROR: {error}",
    "workflow_interrupted": "⚠️  Workflow interrupted by user (Ctrl+C)",
    "eof_detected": "👋 EOF detected. Exiting...",
    "empty_input": "⚠️  Please enter a command or request"
}

# Success Messages  
SUCCESS_MESSAGES = {
    "goodbye": "👋 Goodbye! All task logs saved to /results/",
    "confirmed": "✓ Confirmed! Starting workflow...",
    "cancelled": "✗ Workflow cancelled.",
    "modify_plan": "↻ Let's modify the plan. Please make your request again.",
    "task_log_saved": "📁 Task log saved to /results/",
    "view_logs_tip": "💡 Type 'logs' to view recent task logs"
}

# Comprehensive Request Template
COMPREHENSIVE_REQUEST_TEMPLATE = """
I need to design a qPCR assay with the following specifications:

Target Species: {target_species}
Off-Target Species: {off_target_species}
Genomic Region: {genomic_region}
Application: {application}
Additional Requirements: {additional_requirements}

Please:
1. Retrieve sequences for the target species
2. {off_target_step}
3. Analyze sequences to identify signature regions unique to the target
4. Recommend primer design strategy considering the application context
5. Provide a comprehensive report with all findings
"""

