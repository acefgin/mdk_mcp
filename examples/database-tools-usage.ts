/**
 * Database Tools Usage Examples
 *
 * Demonstrates how to use the typed database tools with the MCP client.
 * Shows common workflows for bioinformatics research.
 *
 * Prerequisites:
 * 1. Database MCP server must be running (docker-compose up database)
 * 2. MCP client must be initialized and set globally
 *
 * Usage:
 * ```bash
 * npx tsx examples/database-tools-usage.ts
 * ```
 */

import {
  MCPCodeExecutionClient,
  setMCPClient,
  MCPServerConfig,
} from '../workspace/lib/mcp-client.js';

// Import all database tools
import {
  getSequences,
  ggetRef,
  ggetSearch,
  ggetInfo,
  ggetSeq,
  getNeighbors,
  getTaxonomy,
  searchSraStudies,
  getSraRuninfo,
  extractSequenceColumns,
} from '../workspace/servers/database/index.js';

/**
 * Initialize MCP client
 *
 * Set up connection to database server running in Docker container.
 */
async function initializeClient(): Promise<MCPCodeExecutionClient> {
  console.log('🔧 Initializing MCP client...\n');

  const serverConfigs = new Map<string, MCPServerConfig>([
    [
      'database',
      {
        command: 'docker',
        args: [
          'exec',
          '-i',
          'ndiag-database-server',
          'python3',
          '/app/database_mcp_server.py',
        ],
        env: {
          NCBI_API_KEY: process.env.NCBI_API_KEY || '',
        },
      },
    ],
  ]);

  const client = new MCPCodeExecutionClient(serverConfigs);
  await client.initialize();

  // Set as global client for tool functions
  setMCPClient(client);

  console.log('✅ MCP client initialized\n');
  return client;
}

/**
 * Example 1: Basic sequence retrieval
 *
 * Fetch COI sequences for Atlantic salmon (Salmo salar)
 */
async function example1_basicSequenceRetrieval() {
  console.log('📚 Example 1: Basic Sequence Retrieval');
  console.log('=====================================\n');

  try {
    // Fetch sequences with type-safe parameters
    const result = await getSequences({
      taxon: 'Salmo salar',
      region: 'COI',
      source: 'ncbi',
      max_results: 10,
      format: 'fasta',
    });

    console.log('✓ Retrieved sequences:');
    console.log(`  Count: ${result.count || 'N/A'}`);
    console.log(`  Format: FASTA`);
    console.log(`  First 100 chars: ${result.sequences?.substring(0, 100)}...\n`);
  } catch (error: any) {
    console.error('✗ Error:', error.message, '\n');
  }
}

/**
 * Example 2: Reference genome information
 *
 * Get reference genome data for human from Ensembl
 */
async function example2_referenceGenome() {
  console.log('📚 Example 2: Reference Genome Information');
  console.log('==========================================\n');

  try {
    const result = await ggetRef({
      species: 'homo_sapiens',
      which: 'gtf',
    });

    console.log('✓ Reference genome info:');
    console.log(`  Species: ${result.species || 'N/A'}`);
    console.log(`  Release: ${result.release || 'N/A'}`);
    console.log(`  Available references: ${result.references?.length || 0}\n`);
  } catch (error: any) {
    console.error('✗ Error:', error.message, '\n');
  }
}

/**
 * Example 3: Gene search and information
 *
 * Search for BRAF gene and get detailed information
 */
async function example3_geneSearchAndInfo() {
  console.log('📚 Example 3: Gene Search and Information');
  console.log('=========================================\n');

  try {
    // Step 1: Search for gene
    console.log('Step 1: Searching for BRAF gene...');
    const searchResults = await ggetSearch({
      search_term: 'BRAF',
      species: 'homo_sapiens',
      limit: 5,
    });

    console.log(`✓ Found ${searchResults.results?.length || 0} results`);

    if (searchResults.results && searchResults.results.length > 0) {
      const firstResult = searchResults.results[0];
      console.log(`  Gene: ${firstResult.gene_name}`);
      console.log(`  Ensembl ID: ${firstResult.ensembl_id}\n`);

      // Step 2: Get detailed information
      console.log('Step 2: Getting detailed gene information...');
      const geneInfo = await ggetInfo({
        ensembl_ids: [firstResult.ensembl_id],
      });

      console.log('✓ Gene details:');
      const gene = geneInfo.genes?.[firstResult.ensembl_id];
      if (gene) {
        console.log(`  Name: ${gene.gene_name}`);
        console.log(`  Description: ${gene.description}`);
        console.log(`  Chromosome: ${gene.chromosome || 'N/A'}`);
        console.log(`  Start: ${gene.start || 'N/A'}`);
        console.log(`  End: ${gene.end || 'N/A'}\n`);
      }
    }
  } catch (error: any) {
    console.error('✗ Error:', error.message, '\n');
  }
}

/**
 * Example 4: Sequence retrieval from Ensembl
 *
 * Get nucleotide and amino acid sequences
 */
async function example4_ensemblSequences() {
  console.log('📚 Example 4: Ensembl Sequence Retrieval');
  console.log('========================================\n');

  try {
    const ensemblId = 'ENSG00000157764'; // BRAF gene

    // Get nucleotide sequence
    console.log('Step 1: Retrieving nucleotide sequence...');
    const nucleotideSeq = await ggetSeq({
      ensembl_ids: [ensemblId],
      translate: false,
      isoforms: false,
    });

    console.log('✓ Nucleotide sequence:');
    console.log(`  Length: ${nucleotideSeq.sequences?.[ensemblId]?.length || 'N/A'}`);
    console.log(
      `  Preview: ${nucleotideSeq.sequences?.[ensemblId]?.substring(0, 60)}...\n`
    );

    // Get amino acid sequence
    console.log('Step 2: Retrieving amino acid sequence...');
    const proteinSeq = await ggetSeq({
      ensembl_ids: [ensemblId],
      translate: true,
      isoforms: false,
    });

    console.log('✓ Amino acid sequence:');
    console.log(`  Length: ${proteinSeq.sequences?.[ensemblId]?.length || 'N/A'}`);
    console.log(
      `  Preview: ${proteinSeq.sequences?.[ensemblId]?.substring(0, 60)}...\n`
    );
  } catch (error: any) {
    console.error('✗ Error:', error.message, '\n');
  }
}

/**
 * Example 5: Taxonomic analysis
 *
 * Get taxonomy and find phylogenetic neighbors
 */
async function example5_taxonomicAnalysis() {
  console.log('📚 Example 5: Taxonomic Analysis');
  console.log('=================================\n');

  try {
    const targetTaxon = 'Salmo salar';

    // Step 1: Get taxonomy information
    console.log(`Step 1: Getting taxonomy for ${targetTaxon}...`);
    const taxonomy = await getTaxonomy({
      taxon: targetTaxon,
      include_lineage: true,
    });

    console.log('✓ Taxonomy:');
    console.log(`  Tax ID: ${taxonomy.taxid}`);
    console.log(`  Scientific name: ${taxonomy.scientific_name}`);
    console.log(`  Lineage: ${taxonomy.lineage?.join(' > ')}\n`);

    // Step 2: Find phylogenetic neighbors
    console.log('Step 2: Finding phylogenetic neighbors...');
    const neighbors = await getNeighbors({
      taxon: targetTaxon,
      include_subspecies: true,
      max_distance: 2, // Family level
      max_results: 5,
    });

    console.log('✓ Phylogenetic neighbors:');
    if (neighbors.neighbors && neighbors.neighbors.length > 0) {
      neighbors.neighbors.forEach((neighbor: any, idx: number) => {
        console.log(`  ${idx + 1}. ${neighbor.taxon} (${neighbor.sequences} sequences)`);
      });
    } else {
      console.log('  No neighbors found');
    }
    console.log();
  } catch (error: any) {
    console.error('✗ Error:', error.message, '\n');
  }
}

/**
 * Example 6: SRA database search
 *
 * Search for RNA-seq studies and get run information
 */
async function example6_sraSearch() {
  console.log('📚 Example 6: SRA Database Search');
  console.log('==================================\n');

  try {
    // Step 1: Search for studies
    console.log('Step 1: Searching SRA studies...');
    const studies = await searchSraStudies({
      query: 'Salmo salar transcriptome',
      max_results: 5,
    });

    console.log('✓ Found studies:');
    if (studies.studies && studies.studies.length > 0) {
      const firstStudy = studies.studies[0];
      console.log(`  Accession: ${firstStudy.accession}`);
      console.log(`  Title: ${firstStudy.title}`);
      console.log(`  Organism: ${firstStudy.organism}\n`);

      // Step 2: Get run information
      console.log('Step 2: Getting run information...');
      const runInfo = await getSraRuninfo({
        accession: firstStudy.accession,
        detailed: true,
      });

      console.log('✓ Run information:');
      if (runInfo.runs && runInfo.runs.length > 0) {
        const firstRun = runInfo.runs[0];
        console.log(`  Run: ${firstRun.run}`);
        console.log(`  Spots: ${firstRun.spots?.toLocaleString()}`);
        console.log(`  Bases: ${firstRun.bases?.toLocaleString()}`);
        console.log(`  Layout: ${firstRun.layout || 'N/A'}\n`);
      }
    } else {
      console.log('  No studies found\n');
    }
  } catch (error: any) {
    console.error('✗ Error:', error.message, '\n');
  }
}

/**
 * Example 7: Metadata extraction
 *
 * Parse FASTA sequences and extract metadata
 */
async function example7_metadataExtraction() {
  console.log('📚 Example 7: Metadata Extraction');
  console.log('==================================\n');

  try {
    // Step 1: Fetch sequences
    console.log('Step 1: Fetching sequences...');
    const sequences = await getSequences({
      taxon: 'Mus musculus',
      region: 'COI',
      source: 'ncbi',
      max_results: 5,
      format: 'fasta',
    });

    console.log(`✓ Retrieved ${sequences.count} sequences\n`);

    // Step 2: Extract metadata
    console.log('Step 2: Extracting metadata...');
    const metadata = await extractSequenceColumns({
      sequences: sequences.sequences,
      format: 'fasta',
      output_format: 'json',
      columns: ['accession', 'organism', 'length', 'country', 'collection_date'],
    });

    console.log('✓ Extracted metadata:');
    if (metadata.records && metadata.records.length > 0) {
      metadata.records.slice(0, 3).forEach((record: any, idx: number) => {
        console.log(`  ${idx + 1}. ${record.accession}`);
        console.log(`     Organism: ${record.organism || 'N/A'}`);
        console.log(`     Length: ${record.length || 'N/A'} bp`);
        console.log(`     Country: ${record.country || 'N/A'}`);
        console.log(`     Date: ${record.collection_date || 'N/A'}`);
      });
      if (metadata.records.length > 3) {
        console.log(`  ... and ${metadata.records.length - 3} more`);
      }
    }
    console.log();
  } catch (error: any) {
    console.error('✗ Error:', error.message, '\n');
  }
}

/**
 * Example 8: Complete workflow
 *
 * Comprehensive workflow combining multiple tools
 */
async function example8_completeWorkflow() {
  console.log('📚 Example 8: Complete Workflow');
  console.log('================================\n');
  console.log('Workflow: Design qPCR primers for pathogen detection\n');

  try {
    const targetSpecies = 'Vibrio cholerae';
    const targetRegion = '16S';

    // Step 1: Get taxonomy
    console.log('Step 1: Taxonomic identification...');
    const taxonomy = await getTaxonomy({
      taxon: targetSpecies,
      include_lineage: true,
    });
    console.log(`✓ Confirmed: ${taxonomy.scientific_name} (taxid: ${taxonomy.taxid})\n`);

    // Step 2: Fetch target sequences
    console.log('Step 2: Fetching target sequences...');
    const targetSeqs = await getSequences({
      taxon: targetSpecies,
      region: targetRegion,
      source: 'ncbi',
      max_results: 20,
      format: 'fasta',
    });
    console.log(`✓ Retrieved ${targetSeqs.count} target sequences\n`);

    // Step 3: Extract metadata
    console.log('Step 3: Extracting sequence metadata...');
    const metadata = await extractSequenceColumns({
      sequences: targetSeqs.sequences,
      format: 'fasta',
      output_format: 'json',
      columns: ['accession', 'organism', 'length', 'country'],
    });
    console.log(`✓ Extracted metadata for ${metadata.records?.length || 0} records\n`);

    // Step 4: Find phylogenetic neighbors (for specificity checking)
    console.log('Step 4: Finding phylogenetic neighbors...');
    const neighbors = await getNeighbors({
      taxon: targetSpecies,
      max_distance: 2,
      max_results: 10,
    });
    console.log(`✓ Found ${neighbors.neighbors?.length || 0} neighbor taxa\n`);

    // Step 5: Literature search (SRA studies)
    console.log('Step 5: Searching for related SRA studies...');
    const sraStudies = await searchSraStudies({
      query: `${targetSpecies} ${targetRegion}`,
      max_results: 5,
    });
    console.log(`✓ Found ${sraStudies.studies?.length || 0} SRA studies\n`);

    console.log('✅ Workflow complete!');
    console.log('Next steps:');
    console.log('  - Align target sequences');
    console.log('  - Find signature regions');
    console.log('  - Design primers with Primer3');
    console.log('  - Validate with BLAST\n');
  } catch (error: any) {
    console.error('✗ Error:', error.message, '\n');
  }
}

/**
 * Example 9: Error handling
 *
 * Demonstrates proper error handling patterns
 */
async function example9_errorHandling() {
  console.log('📚 Example 9: Error Handling');
  console.log('============================\n');

  // Invalid taxon
  console.log('Test 1: Invalid taxon name');
  try {
    await getSequences({
      taxon: 'NonexistentSpeciesXYZ',
      region: 'COI',
      max_results: 10,
    });
    console.log('✓ Request succeeded (unexpected)\n');
  } catch (error: any) {
    console.log('✗ Expected error caught:');
    console.log(`  ${error.message.substring(0, 100)}...\n`);
  }

  // Invalid Ensembl ID
  console.log('Test 2: Invalid Ensembl ID');
  try {
    await ggetInfo({
      ensembl_ids: ['INVALID_ID_123'],
    });
    console.log('✓ Request succeeded (unexpected)\n');
  } catch (error: any) {
    console.log('✗ Expected error caught:');
    console.log(`  ${error.message.substring(0, 100)}...\n`);
  }

  // Empty search
  console.log('Test 3: Empty search query');
  try {
    await searchSraStudies({
      query: '',
      max_results: 10,
    });
    console.log('✓ Request succeeded\n');
  } catch (error: any) {
    console.log('✗ Error caught:');
    console.log(`  ${error.message}\n`);
  }
}

/**
 * Example 10: Type safety demonstration
 *
 * Shows TypeScript type checking benefits
 */
function example10_typeSafety() {
  console.log('📚 Example 10: Type Safety');
  console.log('==========================\n');

  console.log('TypeScript ensures type safety at compile time:\n');

  console.log('✓ Valid code (will compile):');
  console.log('  getSequences({ taxon: "Salmo salar", region: "COI" })');
  console.log('  ggetSearch({ search_term: "BRAF", species: "homo_sapiens" })');
  console.log('  extractSequenceColumns({ sequences: "...", format: "fasta" })\n');

  console.log('✗ Invalid code (will NOT compile):');
  console.log('  getSequences({ })  // Error: missing required "taxon"');
  console.log('  getSequences({ taxon: "test", region: "INVALID" })  // Error: invalid enum');
  console.log('  ggetSeq({ ensembl_ids: "string" })  // Error: should be string[]\n');

  console.log('💡 Benefits:');
  console.log('  - Catch errors at compile time, not runtime');
  console.log('  - IDE autocomplete for all parameters');
  console.log('  - Self-documenting API with inline types');
  console.log('  - Refactoring safety\n');
}

/**
 * Main function
 */
async function main() {
  console.log('\n═══════════════════════════════════════════════════');
  console.log('    DATABASE TOOLS USAGE EXAMPLES');
  console.log('═══════════════════════════════════════════════════\n');

  let client: MCPCodeExecutionClient | null = null;

  try {
    // Initialize MCP client
    client = await initializeClient();

    // Run examples
    await example1_basicSequenceRetrieval();
    await example2_referenceGenome();
    await example3_geneSearchAndInfo();
    await example4_ensemblSequences();
    await example5_taxonomicAnalysis();
    await example6_sraSearch();
    await example7_metadataExtraction();
    await example8_completeWorkflow();
    await example9_errorHandling();
    example10_typeSafety();

    console.log('═══════════════════════════════════════════════════');
    console.log('    ALL EXAMPLES COMPLETED');
    console.log('═══════════════════════════════════════════════════\n');
  } catch (error: any) {
    console.error('\n❌ Fatal error:', error.message);
    process.exit(1);
  } finally {
    // Clean up
    if (client) {
      await client.close();
    }
  }
}

// Run if called directly
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((error) => {
    console.error('Unhandled error:', error);
    process.exit(1);
  });
}

export {
  example1_basicSequenceRetrieval,
  example2_referenceGenome,
  example3_geneSearchAndInfo,
  example4_ensemblSequences,
  example5_taxonomicAnalysis,
  example6_sraSearch,
  example7_metadataExtraction,
  example8_completeWorkflow,
  example9_errorHandling,
  example10_typeSafety,
};
