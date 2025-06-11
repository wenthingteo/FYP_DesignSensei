# LLMEntityExtractor.py
import os
import json
import time
import logging
import re
import datetime
import networkx as nx
import itertools
from collections import defaultdict
from typing import Dict, List, Any, Optional, Set, Tuple
from openai import OpenAI, RateLimitError, AsyncOpenAI
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from json_repair import repair_json
from knowledge_graph.graph_generation.domain_config import DOMAIN_FOCUS
import concurrent.futures
from multiprocessing import cpu_count
from neo4j import GraphDatabase # Already present
from config import NEO4J_CONFIG # Assuming you have a config.py with NEO44J_CONFIG

# NEW IMPORTS for orchestration
from knowledge_graph.graph_generation.text_extraction import ResourceProcessor
from knowledge_graph.graph_generation.file_storage import StorageAdapter
from knowledge_graph.graph_generation.resource_db import ResourceDB # Needed for path setup in main

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define your LLM context here as it was in your original file
SOFTWARE_DESIGN_CONTEXT = {
    "core_concepts": [
        "architecture", "architectural", "design", "pattern", "patterns", "style", "styles",
        "component", "components", "module", "modules", "system", "systems", "service", "services",
        "layer", "layers", "tier", "tiers", "boundary", "boundaries",

        "class", "classes", "interface", "interfaces", "method", "methods", "function", "functions",
        "object", "objects", "entity", "entities", "model", "models", "controller", "controllers",
        "view", "views", "repository", "repositories", "factory", "factories",

        "principle", "principles",
    ],
    "relationship_types": [
        "IMPLEMENTS", "CONTAINS", "DEPENDS_ON", "PART_OF", "EXEMPLIFIES", "ENABLES", "GUIDES", "APPLIES_TO",
        "USES", "BUILDS_ON", "ASSOCIATED_WITH", "RELATES_TO" # Include generic ones if LLM might use them
    ],
    "domain_focus_keywords": DOMAIN_FOCUS.get('keywords', {}),
    "node_types_map": DOMAIN_FOCUS.get('node_types', {})
}


class LLMEntityExtractor:
    def __init__(self, model_name: str = "gpt-4o", api_key: Optional[str] = None):
        self.client = OpenAI(api_key=api_key or os.getenv("OPENAI_API_KEY"))
        self.model_name = model_name
        self.total_tokens = 0
        self.system_prompt = self._build_system_prompt()
        self.base_node_id_prefix = "n"
        self.base_rel_id_prefix = "r"
        # These sets are for deduplication *within a single extraction run*.
        # For cross-run deduplication, Neo4j's MERGE is key.
        self.seen_nodes_in_run = set()
        self.seen_relationships_in_run = set()

    def _build_system_prompt(self) -> str:
        # This prompt should guide the LLM to output precise JSON with relevant labels
        return """
        You are an expert in software engineering, architecture, and design patterns. Your task is to extract concepts (nodes) and their relationships (edges) from provided text related to software design.

        **Node Labels:** Assign one or more relevant labels to each concept from this list:
        - DesignPrinciple
        - DesignPattern
        - DDDConcept (Domain-Driven Design Concept)
        - CodeStructure
        - ArchPattern (Architectural Pattern)
        - QualityAttribute
        - SoftwareConcept (Use this as a fallback if none of the above fit perfectly)

        **Node Properties:** Each node MUST have a 'id' (unique hash for the concept), 'name', 'description'.
        Additionally, add 'source_file', 'chunk_id', and 'resource_id' as properties to each node for traceability.

        **Relationship Types:** Use specific relationship types where possible from this list:
        - IMPLEMENTS
        - CONTAINS
        - DEPENDS_ON
        - PART_OF
        - EXEMPLIFIES
        - ENABLES
        - GUIDES
        - APPLIES_TO
        - USES
        - BUILDS_ON
        - ASSOCIATED_WITH
        - RELATES_TO (Use as a generic fallback if no specific type fits)

        **Relationship Properties:** Each relationship MUST have 'source_id', 'target_id', 'type'.
        Additionally, add 'description', 'strength', 'confidence', 'source_file', 'chunk_id', and 'resource_id' as properties for traceability.

        Output Format (Strict JSON):
        ```json
        {
          "nodes": [
            {"id": "unique_node_id_1", "name": "Concept A", "labels": ["DesignPrinciple", "SoftwareConcept"], "description": "...", "source_file": "...", "chunk_id": "...", "resource_id": 1},
            {"id": "unique_node_id_2", "name": "Concept B", "labels": ["CodeStructure"], "description": "...", "source_file": "...", "chunk_id": "...", "resource_id": 1}
          ],
          "relationships": [
            {"source_id": "unique_node_id_1", "target_id": "unique_node_id_2", "type": "IMPLEMENTS", "description": "Concept A implements Concept B", "strength": "strong", "confidence": 0.9, "source_file": "...", "chunk_id": "...", "resource_id": 1}
          ]
        }
        ```
        Ensure 'id' for nodes and relationships are unique and deterministic (e.g., hash-based on name/source-target-type).
        """

    @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=4, max=20), retry=retry_if_exception_type(RateLimitError))
    def _call_openai_api(self, prompt: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"} # Ensure JSON response
            )
            self.total_tokens += response.usage.total_tokens
            content = response.choices[0].message.content
            return repair_json(content) # Robust JSON parsing
        except RateLimitError:
            logger.warning("Rate limit hit. Retrying...")
            raise
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")
            raise

    def _parse_llm_response(self, response_text: str) -> Dict[str, List[Dict]]:
        try:
            data = json.loads(response_text)
            nodes_raw = data.get('nodes', [])
            relationships_raw = data.get('relationships', [])

            processed_nodes = []
            for node in nodes_raw:
                # Basic validation and default values
                if 'name' not in node or not node['name']:
                    logger.warning(f"Node without 'name' found: {node}. Skipping.")
                    continue
                
                # Ensure 'id' is present or generate it
                if 'id' not in node or not node['id']:
                    node['id'] = self._generate_node_id(node['name'])
                
                # Ensure labels are a list of strings
                if 'labels' not in node:
                    # If LLM gave 'label' as a string, convert to 'labels' list
                    if 'label' in node and isinstance(node['label'], str):
                        node['labels'] = [node['label']]
                    else:
                        node['labels'] = ['SoftwareConcept'] # Default fallback label
                
                # Filter out invalid labels or non-string labels
                node['labels'] = [l for l in node['labels'] if l and isinstance(l, str)]
                if not node['labels']:
                    node['labels'] = ['SoftwareConcept'] # Ensure at least one label

                # Deduplicate nodes based on ID for this specific extraction run
                if node['id'] not in self.seen_nodes_in_run:
                    processed_nodes.append(node)
                    self.seen_nodes_in_run.add(node['id'])
                else:
                    logger.debug(f"Skipping duplicate node ID from LLM response: {node['id']}")

            processed_relationships = []
            for rel in relationships_raw:
                # Basic validation
                if not all(k in rel for k in ['source_id', 'target_id', 'type']):
                    logger.warning(f"Malformed relationship (missing source_id, target_id, or type): {rel}. Skipping.")
                    continue
                
                # Ensure 'id' is present or generate it
                if 'id' not in rel or not rel['id']:
                    rel['id'] = self._generate_relationship_id(rel['source_id'], rel['target_id'], rel['type'])
                
                # Ensure relationship type is clean
                if 'type' in rel and isinstance(rel['type'], str):
                    rel['type'] = re.sub(r'[^a-zA-Z0-9_]', '', rel['type']).upper()
                    if not rel['type']: rel['type'] = 'RELATES_TO' # Fallback
                else:
                    rel['type'] = 'RELATES_TO' # Default

                # Deduplicate relationships based on (source, target, type) for this run
                rel_tuple = (rel['source_id'], rel['target_id'], rel['type'])
                if rel_tuple not in self.seen_relationships_in_run:
                    processed_relationships.append(rel)
                    self.seen_relationships_in_run.add(rel_tuple)
                else:
                    logger.debug(f"Skipping duplicate relationship from LLM response: {rel_tuple}")

            return {"nodes": processed_nodes, "relationships": processed_relationships}
        except json.JSONDecodeError as e:
            logger.error(f"JSON decoding error: {e} - Raw response: {response_text[:500]}...")
            return {"nodes": [], "relationships": []}
        except Exception as e:
            logger.error(f"Error parsing LLM response: {e}")
            return {"nodes": [], "relationships": []}

    def _generate_node_id(self, name: str) -> str:
        # Use hashlib for more robust ID generation than simple hash()
        import hashlib
        if not name:
            return f"{self.base_node_id_prefix}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')}"

        clean_name = re.sub(r'[^a-zA-Z0-9]', '', name).lower()
        if not clean_name:
             return f"{self.base_node_id_prefix}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')}"

        hash_obj = hashlib.md5(clean_name.encode('utf-8'))
        return f"{self.base_node_id_prefix}_{hash_obj.hexdigest()[:8]}"


    def _generate_relationship_id(self, source_id: str, target_id: str, rel_type: str) -> str:
        import hashlib
        unique_string = f"{source_id}-{rel_type}-{target_id}"
        hash_obj = hashlib.md5(unique_string.encode('utf-8'))
        return f"{self.base_rel_id_prefix}_{hash_obj.hexdigest()[:8]}"

    def _format_cypher_for_node(self, node: Dict) -> str:
        # Ensures labels are properly formatted and properties are JSON-escaped
        labels = node.get('labels', ['SoftwareConcept']) # Default to SoftwareConcept
        clean_labels = [f":`{label}`" for label in labels if label and isinstance(label, str)]
        if not clean_labels: clean_labels = [":`SoftwareConcept`"] # Fallback if labels list becomes empty

        label_clause = "".join(clean_labels)

        props = {k: v for k, v in node.items() if k not in ['id', 'labels', 'label']}
        
        # Build property string for ON CREATE and ON MATCH
        # Use json.dumps to handle string escaping correctly
        props_str = ', '.join([f"n.{k} = {json.dumps(v)}" for k, v in props.items()])
        
        # Ensure name property is always set/updated
        name_prop_str = f"n.name = {json.dumps(node.get('name', ''))}"
        
        full_props_str = f"{name_prop_str}, {props_str}" if props_str else name_prop_str

        return (
            f"MERGE (n{label_clause} {{id: {json.dumps(node['id'])}}}) "
            f"ON CREATE SET {full_props_str} "
            f"ON MATCH SET {full_props_str};" # Update existing nodes with new properties
        )

    def _format_cypher_for_relationship(self, rel: Dict) -> str:
        rel_type = rel.get('type', 'RELATES_TO')
        clean_rel_type = re.sub(r'[^a-zA-Z0-9_]', '', rel_type).upper()
        if not clean_rel_type: clean_rel_type = 'RELATES_TO'

        props = {k: v for k, v in rel.items() if k not in ['source_id', 'target_id', 'type', 'id']} # 'id' if it exists in rel
        props_str = ', '.join([f"r.{k} = {json.dumps(v)}" for k, v in props.items()])

        return (
            f"MATCH (sourceNode {{id: {json.dumps(rel['source_id'])}}}), "
            f"(targetNode {{id: {json.dumps(rel['target_id'])}}}) "
            f"MERGE (sourceNode)-[r:`{clean_rel_type}`]->(targetNode) "
            f"ON CREATE SET {props_str} "
            f"ON MATCH SET {props_str};" # Update relationship properties if it already exists
        )

    def extract_entities_and_relationships_from_chunk(self, chunk_text_content: str, resource_id: int, chunk_id: str, source_file_name: str) -> Dict:
        """
        Extracts entities and relationships from a single chunk of text
        and adds traceability properties.
        """
        try:
            prompt = f"Given the following text related to software design, extract concepts (nodes) and their relationships. Ensure each extracted concept has a unique 'id' and a descriptive 'name', and assign a relevant label. For relationships, ensure 'source_id', 'target_id', and 'type' are present. Add 'source_file', 'chunk_id', and 'resource_id' as properties to both nodes and relationships. The original file is '{source_file_name}'.\n\nText:\n{chunk_text_content}"
            response_text = self._call_openai_api(prompt)
            extracted_data = self._parse_llm_response(response_text)

            # Add traceability properties to all extracted nodes and relationships
            for item_list in [extracted_data['nodes'], extracted_data['relationships']]:
                for item in item_list:
                    item['source_file'] = source_file_name
                    item['chunk_id'] = chunk_id
                    item['resource_id'] = resource_id

            return extracted_data
        except Exception as e:
            logger.error(f"Error during entity extraction from chunk '{chunk_id}' of '{source_file_name}': {e}")
            return {"nodes": [], "relationships": []}

    # NEW METHOD: generate_cypher_for_chunk - this is the core of incremental update
    def generate_cypher_for_chunk(self, chunk: Dict, resource_id: int, source_file_name: str) -> str:
        """
        Generates Cypher MERGE statements for a single chunk's entities and relationships.
        This is a core method for the incremental update process, using direct LLM extraction.
        """
        # Clear seen nodes/relationships for this *chunk* processing, as we are looking at a new chunk
        # If this is called per-chunk, the seen sets should reset for each chunk for unique IDs
        # within that chunk's context. Global deduplication happens via MERGE in Neo4j.
        self.seen_nodes_in_run = set()
        self.seen_relationships_in_run = set()

        extracted_data = self.extract_entities_and_relationships_from_chunk(
            chunk['text'], resource_id, chunk['chunk_id'], source_file_name
        )

        cypher_statements = []

        # Generate node MERGE statements
        for node_data in extracted_data.get('nodes', []):
            cypher_statements.append(self._format_cypher_for_node(node_data))

        # Generate relationship MERGE statements
        for rel_data in extracted_data.get('relationships', []):
            cypher_statements.append(self._format_cypher_for_relationship(rel_data))

        return "\n".join(cypher_statements)


# Main function to orchestrate the incremental update
def main():
    """
    Main entry point for the knowledge graph builder.
    Orchestrates processing new documents and incrementally updating the Neo4j graph.
    """
    load_dotenv() # Load environment variables from .env file

    # --- Configuration ---
    # STORAGE_CONFIG should come from your main config setup, potentially via environment variables
    # Example for local storage:
    STORAGE_CONFIG = {
        'storage_type': os.getenv('STORAGE_TYPE', 'local'),
        'base_path': os.getenv('LOCAL_STORAGE_PATH', './knowledge_graph/resources')
    }
    # Example for S3 (uncomment and configure if using):
    # STORAGE_CONFIG = {
    #     'storage_type': 's3',
    #     'bucket_name': os.getenv('S3_BUCKET_NAME'),
    #     'access_key': os.getenv('AWS_ACCESS_KEY_ID'),
    #     'secret_key': os.getenv('AWS_SECRET_ACCESS_KEY'),
    #     'region': os.getenv('AWS_REGION')
    # }
    # ... similarly for Azure/GCP

    DB_PATH = "knowledge_graph/graph_generation/resources.db" # Path to your SQLite resource DB

    # --- Initialization ---
    processor = ResourceProcessor(STORAGE_CONFIG, DB_PATH)
    llm_extractor = LLMEntityExtractor() # API key loaded from .env by load_dotenv()

    # Initialize Neo4j Driver
    driver = None
    try:
        driver = GraphDatabase.driver(NEO4J_CONFIG["uri"], auth=(NEO4J_CONFIG["user"], NEO4J_CONFIG["password"]))
        driver.verify_connectivity() # Test connection
        logger.info("Successfully connected to Neo4j database.")
    except Exception as e:
        logger.critical(f"Failed to connect to Neo4j database. Please check NEO4J_CONFIG in config.py or environment variables: {e}")
        return # Exit if DB connection fails

    # --- Main Processing Loop ---
    try:
        logger.info("Starting knowledge graph incremental update process...")

        # Step 1: Discover and register new local files (if using local storage)
        # For cloud storage, files must be pre-registered (e.g., via a separate upload utility)
        if STORAGE_CONFIG['storage_type'] == 'local':
            local_resources_path = STORAGE_CONFIG['base_path']
            if os.path.exists(local_resources_path):
                for file_name in os.listdir(local_resources_path):
                    file_path = os.path.join(local_resources_path, file_name)
                    # Exclude directories and hidden files (e.g., .DS_Store)
                    if os.path.isfile(file_path) and not file_name.startswith('.'):
                        file_type = 'pdf' if file_name.lower().endswith('.pdf') else \
                                    'pptx' if file_name.lower().endswith('.pptx') else 'unknown'
                        if file_type != 'unknown':
                            try:
                                # add_new_resource registers in DB; file_data is not passed here as it's already on disk
                                processor.add_new_resource(file_name, file_type) # No file_data needed here
                            except Exception as e:
                                logger.error(f"Error registering local file '{file_name}': {e}")
                        else:
                            logger.warning(f"Skipping unsupported local file type: {file_name}")
            else:
                logger.warning(f"Local resource directory not found: {local_resources_path}. Skipping local file registration.")


        # Step 2: Process all pending resources (from local scan or prior registration)
        pending_resources = processor.db.get_pending_resources()
        if not pending_resources:
            logger.info("No new or pending resources to process. Graph is up-to-date with known resources.")
            return

        for resource in pending_resources:
            resource_id = resource['id']
            file_name = resource['file_name'] # Original file name from resource_db
            file_type = resource['file_type']

            logger.info(f"Processing new resource: {file_name} (ID: {resource_id})")

            try:
                processor.db.update_processing_status(resource_id, 'processing')

                # --- Extract Text and Chunk ---
                file_data = processor.storage.download_file(file_name) # Downloads from local or cloud storage

                extracted_sections = [] # List of dicts {text, section, type, etc.}
                if file_type == 'pdf':
                    extracted_sections = processor.extract_text_from_pdf(file_data)
                elif file_type == 'pptx':
                    extracted_sections = processor.extract_text_from_pptx(file_data)
                else:
                    logger.warning(f"Unsupported file type for extraction: {file_name}")
                    processor.db.update_processing_status(resource_id, 'failed')
                    continue

                if not extracted_sections:
                    logger.warning(f"No text extracted from {file_name}. Skipping chunking and entity extraction.")
                    processor.db.update_processing_status(resource_id, 'failed')
                    continue

                # Perform chunking and save chunks to the internal SQLite DB
                # This returns the chunks that were just saved to the DB
                processed_chunks_from_resource = processor.chunk_and_save_resource_chunks(
                    resource_id, file_name, extracted_sections
                )

                if not processed_chunks_from_resource:
                    logger.warning(f"No chunks generated for resource: {file_name}. Skipping entity extraction.")
                    processor.db.update_processing_status(resource_id, 'failed')
                    continue

                # --- Extract Entities from Chunks and Merge to Neo4j ---
                with driver.session() as session:
                    for chunk in processed_chunks_from_resource:
                        logger.info(f"Extracting and merging entities from chunk '{chunk.get('chunk_id', 'N/A')}' of {file_name}")
                        try:
                            # Pass original file name for LLM context and properties
                            cypher_for_current_chunk = llm_extractor.generate_cypher_for_chunk(
                                chunk, resource_id, file_name
                            )

                            if cypher_for_current_chunk.strip():
                                session.run(cypher_for_current_chunk)
                            logger.info(f"Successfully processed and merged chunk '{chunk.get('chunk_id', 'N/A')}' to Neo4j.")
                        except Exception as e:
                            logger.error(f"Error processing chunk '{chunk.get('chunk_id', 'N/A')}' from {file_name}: {e}. Skipping this chunk.")

                # Step 4: Mark resource as completed in resource_db
                processor.db.update_processing_status(resource_id, 'completed')
                logger.info(f"Successfully processed and updated graph for resource: {file_name}")

            except Exception as e:
                logger.error(f"Failed to process resource {file_name}: {e}")
                processor.db.update_processing_status(resource_id, 'failed')

    except Exception as e:
        logger.critical(f"An unhandled error occurred in the main process: {e}")
    finally:
        if driver:
            driver.close()
        logger.info("Knowledge graph incremental update process finished.")

if __name__ == "__main__":
    main()