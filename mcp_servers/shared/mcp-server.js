#!/usr/bin/env node
/**
 * MDK MCP TypeScript Server
 *
 * Main MCP server that provides all 34 bioinformatics tools through the Model Context Protocol.
 *
 * This server uses generated TypeScript modules that bridge to Python MCP servers via Docker.
 *
 * @module mcp-server
 */
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { CallToolRequestSchema, ListToolsRequestSchema, McpError, ErrorCode, } from '@modelcontextprotocol/sdk/types.js';
import { checkContainers } from './mcp-client.js';
/**
 * Tool definitions for all 34 tools across 5 servers
 */
const TOOL_DEFINITIONS = [
    // Database Server (11 tools)
    { name: 'database_getSequences', description: 'Fetch sequences from multiple databases (NCBI, BOLD, SILVA, UNITE)', module: 'database', function: 'getSequences' },
    { name: 'database_ggetRef', description: 'Get reference genome information from Ensembl', module: 'database', function: 'ggetRef' },
    { name: 'database_ggetSearch', description: 'Search for genes in Ensembl database', module: 'database', function: 'ggetSearch' },
    { name: 'database_ggetInfo', description: 'Get detailed information about a gene from Ensembl', module: 'database', function: 'ggetInfo' },
    { name: 'database_ggetSeq', description: 'Retrieve nucleotide or amino acid sequence by Ensembl ID', module: 'database', function: 'ggetSeq' },
    { name: 'database_getNeighbors', description: 'Find taxonomically related species', module: 'database', function: 'getNeighbors' },
    { name: 'database_getTaxonomy', description: 'Get complete taxonomic lineage and classification', module: 'database', function: 'getTaxonomy' },
    { name: 'database_searchSraStudies', description: 'Search SRA/BioProject for sequencing studies', module: 'database', function: 'searchSraStudies' },
    { name: 'database_getSraRuninfo', description: 'Get detailed run information for SRA study', module: 'database', function: 'getSraRuninfo' },
    { name: 'database_searchSraCloud', description: 'Search SRA via cloud SQL (BigQuery/Athena)', module: 'database', function: 'searchSraCloud' },
    { name: 'database_extractSequenceColumns', description: 'Extract metadata columns from FASTA/GenBank sequences', module: 'database', function: 'extractSequenceColumns' },
    // Processing Server (5 tools)
    { name: 'processing_fastaQc', description: 'Quality control for FASTA sequences', module: 'processing', function: 'fastaQc' },
    { name: 'processing_dereplicateSequences', description: 'Remove duplicate or highly similar sequences', module: 'processing', function: 'dereplicateSequences' },
    { name: 'processing_maskLowComplexity', description: 'Mask low-complexity regions in sequences', module: 'processing', function: 'maskLowComplexity' },
    { name: 'processing_detectChimeras', description: 'Detect chimeric sequences using UCHIME algorithm', module: 'processing', function: 'detectChimeras' },
    { name: 'processing_processSequences', description: 'Complete QC pipeline - combines all processing steps', module: 'processing', function: 'processSequences' },
    // Alignment Server (5 tools)
    { name: 'alignment_alignSequences', description: 'Align sequences using MAFFT, MUSCLE, or Clustal Omega', module: 'alignment', function: 'alignSequences' },
    { name: 'alignment_processAlignment', description: 'Clean and assess alignment quality', module: 'alignment', function: 'processAlignment' },
    { name: 'alignment_buildPhylogeny', description: 'Build phylogenetic tree from alignment', module: 'alignment', function: 'buildPhylogeny' },
    { name: 'alignment_calculateDistances', description: 'Calculate pairwise distance matrix from alignment', module: 'alignment', function: 'calculateDistances' },
    { name: 'alignment_alignAndAnalyze', description: 'Complete alignment pipeline - align, clean, build tree, calculate distances', module: 'alignment', function: 'alignAndAnalyze' },
    // Design Server (6 tools)
    { name: 'design_findSignatureRegions', description: 'Find signature regions for specific primer design', module: 'design', function: 'findSignatureRegions' },
    { name: 'design_primer3Design', description: 'Design primers using Primer3', module: 'design', function: 'primer3Design' },
    { name: 'design_analyzeSpecificity', description: 'Analyze target vs off-target specificity for primer design', module: 'design', function: 'analyzeSpecificity' },
    { name: 'design_rankRegions', description: 'Rank candidate regions for primer design', module: 'design', function: 'rankRegions' },
    { name: 'design_oligoQc', description: 'Quality control for oligonucleotides - Tm, secondary structure, dimers', module: 'design', function: 'oligoQc' },
    { name: 'design_designPrimersComplete', description: 'Complete primer design pipeline - find regions, design, and QC', module: 'design', function: 'designPrimersComplete' },
    // Validation Server (7 tools)
    { name: 'validation_ggetBlast', description: 'BLAST search using gget (NCBI BLAST)', module: 'validation', function: 'ggetBlast' },
    { name: 'validation_inSilicoPcr', description: 'Perform in silico PCR with primers', module: 'validation', function: 'inSilicoPcr' },
    { name: 'validation_ggetBlat', description: 'BLAT search using gget for fast alignment', module: 'validation', function: 'ggetBlat' },
    { name: 'validation_blastNt', description: 'BLAST against NCBI nucleotide database', module: 'validation', function: 'blastNt' },
    { name: 'validation_assessCoverage', description: 'Assess taxonomic coverage of primers', module: 'validation', function: 'assessCoverage' },
    { name: 'validation_searchPubmed', description: 'Search PubMed for related literature', module: 'validation', function: 'searchPubmed' },
    { name: 'validation_validatePrimersComplete', description: 'Complete primer validation pipeline - BLAST, in silico PCR, coverage', module: 'validation', function: 'validatePrimersComplete' },
];
/**
 * Create and configure MCP server
 */
async function main() {
    // Check Docker containers
    const missingContainers = await checkContainers();
    if (missingContainers.length > 0) {
        console.error(`⚠️  Warning: Missing Docker containers: ${missingContainers.join(', ')}`);
        console.error('   Start containers with: docker-compose -f docker-compose.autogen.yml up -d');
    }
    // Create MCP server
    const server = new Server({
        name: 'mdk-mcp-typescript',
        version: '2.0.0',
    }, {
        capabilities: {
            tools: {},
        },
    });
    // List tools handler
    server.setRequestHandler(ListToolsRequestSchema, async () => {
        return {
            tools: TOOL_DEFINITIONS.map(tool => ({
                name: tool.name,
                description: tool.description,
                inputSchema: {
                    type: 'object',
                    properties: {},
                },
            })),
        };
    });
    // Call tool handler
    server.setRequestHandler(CallToolRequestSchema, async (request) => {
        const { name: toolName, arguments: args } = request.params;
        // Find tool definition
        const toolDef = TOOL_DEFINITIONS.find(t => t.name === toolName);
        if (!toolDef) {
            throw new McpError(ErrorCode.MethodNotFound, `Unknown tool: ${toolName}`);
        }
        try {
            // Try to load generated module
            const modulePath = `./servers/${toolDef.module}/index.js`;
            const module = await import(modulePath);
            const toolFunction = module[toolDef.function];
            if (!toolFunction) {
                throw new Error(`Function ${toolDef.function} not found in module ${toolDef.module}`);
            }
            // Call tool function
            const result = await toolFunction(args || {});
            return {
                content: [
                    {
                        type: 'text',
                        text: typeof result === 'string' ? result : JSON.stringify(result, null, 2),
                    },
                ],
            };
        }
        catch (error) {
            throw new McpError(ErrorCode.InternalError, `Tool execution failed: ${error.message}`);
        }
    });
    // Start server
    const transport = new StdioServerTransport();
    await server.connect(transport);
    console.error('✅ mdk-mcp-typescript v2.0.0 running on stdio');
    console.error(`📊 Tools available: ${TOOL_DEFINITIONS.length}`);
    console.error('🚀 Ready for Claude Desktop');
}
// Run server
main().catch((error) => {
    console.error('Fatal error:', error);
    process.exit(1);
});
//# sourceMappingURL=mcp-server.js.map