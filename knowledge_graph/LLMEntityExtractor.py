# LLMEntityExtractor.py
import os
import json
import time
import logging
import re
import base64
from typing import Dict, List, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from json_repair import repair_json
from domain_config import DOMAIN_FOCUS 
import concurrent.futures
from multiprocessing import cpu_count
from neo4j import GraphDatabase
from config import NEO4J_CONFIG

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Anti-overfitting strategy for prompt engineering
ANTI_OVERFITTING_STRATEGY = """
When generating knowledge graph content:
1. Focus on fundamental concepts (75%) over specific implementations (25%)
2. Prioritize relationships between concepts over isolated facts
3. Include cross-domain connections (e.g., how patterns affect quality attributes)
4. Maintain balanced representation across all 6 domains
5. Use abstract descriptions that apply to multiple contexts

Example of good abstraction:
BAD: "In Java, use Spring Boot for dependency injection"
GOOD: "Dependency Injection improves testability by decoupling components"
"""

class LLMEntityExtractor:
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.error_log = []
        self.annotation_data = self._load_annotations()
        
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("Missing OpenAI API key")
            
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url or "https://api.openai.com/v1"
        )
        self.last_request_time = 0
        self.min_request_interval = 1.0
        self.total_tokens = 0  # Track token usage

    def _load_annotations(self) -> Dict[str, Any]:
        """Load PDF annotations if available"""
        annotation_path = "./knowledge_graph/annotations.json"
        if os.path.exists(annotation_path):
            try:
                with open(annotation_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load annotations: {e}")
        return {}

    def _rate_limit(self):
        """Simple rate limiting with dynamic adjustment"""
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        
        # Increase interval if we're approaching rate limits
        if self.total_tokens > 100000:
            self.min_request_interval = max(2.0, self.min_request_interval * 1.1)
            
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
            
        self.last_request_time = time.time()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10), retry=retry_if_exception_type(OpenAI.RateLimitError))
    def extract_entities_and_relationships_batch(self, chunks: List[Dict]) -> List[Dict]:
        """Process 3-5 chunks per request"""
        try:
            self._rate_limit()
            
            # Combine chunks with domain context
            combined_text = "\n\n---\n\n".join([chunk['text'] for chunk in chunks])
            all_domains = list(set([d for chunk in chunks for d in chunk.get('domains', [])]))
            node_types = [DOMAIN_FOCUS["node_types"][d] for d in all_domains if d in DOMAIN_FOCUS["node_types"]]
            
            messages = [
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": self._create_extraction_prompt(
                    combined_text, 
                    all_domains,
                    node_types
                )}
            ]
            
            # Make batched API call
            response = self.client.chat.completions.create(
                model="gpt-4-turbo",
                messages=messages,
                temperature=0.1,
                max_tokens=800,
                timeout=45
            )
            
            self.total_tokens += response.usage.total_tokens
            content = response.choices[0].message.content
            
            # Parse the response for all chunks
            result = self._parse_llm_response(content, {"text": combined_text})
            
            # Distribute results to original chunks
            return [{
                **result,
                "chunk_metadata": chunk
            } for chunk in chunks]
            
        except Exception as e:
            logger.error(f"Batch extraction failed: {e}")
            return [self._create_empty_result(chunk) for chunk in chunks]

    def _get_system_prompt(self) -> str:
        """System prompt with domain focus and anti-overfitting strategy"""
        return f"""
        You are an expert in software design knowledge graph construction. 
        Your task is to extract entities and relationships specifically related to:
        {", ".join(DOMAIN_FOCUS['topics'])}
        
        {ANTI_OVERFITTING_STRATEGY}
        
        Respond in JSON format with this structure:
        {{
            "entities": [
                {{
                    "name": "entity_name",
                    "type": "entity_type",  // Must be one of: {list(DOMAIN_FOCUS['node_types'].values())}
                    "description": "Brief description",
                    "properties": {{}}      // Optional additional properties
                }}
            ],
            "relationships": [
                {{
                    "source": "source_entity_name",
                    "target": "target_entity_name",
                    "type": "relationship_type",  // Use: RELATES_TO, IMPLEMENTS, DEPENDS_ON, CONTAINS, PART_OF
                    "description": "Relationship explanation"
                }}
            ]
        }}
        
        Rules:
        1. Focus ONLY on software design concepts from the target domains
        2. Use EXACT domain node types from: {list(DOMAIN_FOCUS['node_types'].values())}
        3. Escape all double quotes inside strings with \\
        4. No trailing commas or unclosed brackets
        5. Prioritize fundamental concepts over implementation specifics
        """

    def _create_extraction_prompt(self, chunk_text: str, domains: List[str], node_types: List[str]) -> str:
        """Create domain-focused extraction prompt"""
        domain_context = "\n".join([f"- {d}: {', '.join(DOMAIN_FOCUS['keywords'][d][:3])}" for d in domains])
        
        return f"""
        Analyze the following text about software design and extract:
        
        Target Domains:
        {domain_context}
        
        Text to analyze:
        \"\"\"
        {chunk_text[:3000]}
        \"\"\"
        
        Instructions:
        1. Extract ONLY entities relevant to the target domains
        2. Use node types: {', '.join(node_types)}
        3. Include relationships between entities
        4. Add descriptions explaining software design relevance
        5. Use double backslashes for escaped characters (\\" becomes \\\\")
        6. Focus on abstract concepts rather than specific implementations
        
        Respond ONLY with valid JSON.
        """

    def _encode_image(self, image_path: str) -> str:
        """Encode image to base64 for GPT-4 Vision"""
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            logger.error(f"Error encoding image: {e}")
            return ""

    def _parse_llm_response(self, content: str, chunk: Dict) -> Dict:
        """Parse and validate LLM response with domain checks"""
        try:
            # Attempt JSON extraction
            json_match = re.search(r'\{[\s\S]*\}', content, re.DOTALL)
            if not json_match:
                logger.warning("No JSON found in LLM response")
                return self._create_empty_result(chunk)
                
            json_str = json_match.group()
            parsed = json.loads(repair_json(json_str))
            
            # Validate and filter entities
            valid_entities = []
            for entity in parsed.get('entities', []):
                if self._is_valid_entity(entity, chunk['domains']):
                    # Add source metadata
                    entity['source_file'] = chunk.get('source', '')
                    entity['source_page'] = chunk.get('position', '')
                    valid_entities.append(entity)
            
            # Validate relationships
            valid_relationships = []
            for rel in parsed.get('relationships', []):
                if self._is_valid_relationship(rel, valid_entities):
                    valid_relationships.append(rel)
            
            if len(valid_entities) < 2 and len(valid_relationships) < 1:
                logger.info(f"Skipping low-yield chunk: {chunk.get('source', '')}")
                return self._create_empty_result(chunk)
            
            # Generate Cypher queries
            cypher_queries = self._generate_cypher_queries(valid_entities, valid_relationships)
            
            return {
                'entities': valid_entities,
                'relationships': valid_relationships,
                'cypher_queries': cypher_queries,
                'chunk_metadata': chunk,
                'extraction_success': bool(valid_entities)
            }
            
        except Exception as e:
            logger.error(f"Response parsing failed: {e}")
            return self._create_empty_result(chunk)

    def _is_valid_entity(self, entity: Dict, expected_domains: List[str]) -> bool:
        """Check if entity matches domain focus"""
        # Validate node type
        valid_types = list(DOMAIN_FOCUS['node_types'].values())
        if entity.get('type') not in valid_types:
            return False
            
        # Check domain relevance
        entity_name = entity.get('name', '').lower()
        for domain in expected_domains:
            if any(kw in entity_name for kw in DOMAIN_FOCUS['keywords'][domain]):
                return True
        return False

    def _is_valid_relationship(self, relationship: Dict, valid_entities: List[Dict]) -> bool:
        """Validate relationship between existing entities"""
        source_names = {e['name'] for e in valid_entities}
        target_names = {e['name'] for e in valid_entities}
        
        return (
            relationship.get('source') in source_names and
            relationship.get('target') in target_names and
            relationship.get('type') in ['RELATES_TO', 'IMPLEMENTS', 'DEPENDS_ON', 'CONTAINS', 'PART_OF']
        )

    def _generate_cypher_queries(self, entities: List[Dict], relationships: List[Dict]) -> List[str]:
        """Generate optimized Cypher queries with MERGE and constraints"""
        queries = []
        
        # Create nodes with MERGE and constraints
        for entity in entities:
            # Escape special characters for Cypher
            name = entity['name'].replace('"', '\\"').replace("'", "\\'")
            description = entity.get('description', '').replace('"', '\\"').replace("'", "\\'")
            
            props = {
                'name': f'"{name}"',
                'description': f'"{description}"',
                'source': f'"{entity.get("source_file", "")}"',
                'page': entity.get("source_page", "")
            }
            
            # Add any additional properties
            for k, v in entity.get('properties', {}).items():
                if isinstance(v, str):
                    v = v.replace('"', '\\"').replace("'", "\\'")
                    props[k] = f'"{v}"'
                else:
                    props[k] = str(v)
                    
            prop_str = ", ".join(f"{k}: {v}" for k, v in props.items())
            queries.append(
                f"MERGE (:{entity['type']} {{ {prop_str} }});"
            )
        
        # Create relationships with MERGE
        for rel in relationships:
            rel_desc = rel.get('description', '').replace('"', '\\"').replace("'", "\\'")
            queries.append(
                f"MATCH (s {{name: \"{rel['source']}\"}}), (t {{name: \"{rel['target']}\"}})\n"
                f"MERGE (s)-[:{rel['type']} {{description: \"{rel_desc}\"}}]->(t);"
            )
            
        return queries

    def _create_empty_result(self, chunk: Dict) -> Dict:
        return {
            'entities': [],
            'relationships': [],
            'cypher_queries': [],
            'chunk_metadata': chunk,
            'extraction_success': False
        }

    def __del__(self):
        if self.error_log:
            error_file = "extraction_errors.json"
            with open(error_file, 'w') as f:
                json.dump(self.error_log, f)
            logger.info(f"Saved {len(self.error_log)} errors to {error_file}")

class DocumentProcessor:
    def __init__(self):
        pass  # Table extraction would be implemented here

def process_chunk_batch(extractor: LLMEntityExtractor, chunks: List[Dict]) -> List[Dict]:
    """Process a batch of chunks together"""
    try:
        return extractor.extract_entities_and_relationships_batch(chunks)
    except Exception as e:
        logger.error(f"Failed to process batch: {e}")
        return [{
            'entities': [],
            'relationships': [],
            'cypher_queries': [],
            'chunk_metadata': chunk,
            'extraction_success': False
        } for chunk in chunks]

def process_all_chunks(
    all_chunks: Dict[str, List[Dict]], 
    extractor: LLMEntityExtractor,
    max_workers: int = None,
    max_chunks: int = None
) -> Dict[str, List[Dict]]:
    """
    Process all chunks with parallel execution
    """
    CHECKPOINT_INTERVAL = 50  # Save every 50 chunks

    processed_files = set()
    if os.path.exists("knowledge_graph_extractions.json"):
        with open("knowledge_graph_extractions.json", 'r') as f:
            existing = json.load(f)
            processed_files = set(existing.keys())

    for filename, chunks in all_chunks.items():
        if filename in processed_files:  # Skip processed files
            logger.info(f"Skipping already processed: {filename}")
            continue

    if max_workers is None:
        max_workers = min(4, cpu_count())  # Conservative default
        
    all_extractions = {}
    total_chunks = sum(len(chunks) for chunks in all_chunks.values())
    
    if max_chunks:
        total_chunks = min(total_chunks, max_chunks)
    
    processed = 0
    logger.info(f"Starting extraction for {total_chunks} chunks with {max_workers} workers...")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        for filename, chunks in all_chunks.items():
            if max_chunks and processed >= max_chunks:
                break
            if processed % CHECKPOINT_INTERVAL == 0:
                save_extractions(all_extractions, "knowledge_graph_extractions_partial.json")
                logger.info(f"Checkpoint saved at {processed} chunks")   

            logger.info(f"Processing chunks from {filename}")
            future_to_chunk = {}
            
            for chunk in chunks:
                if max_chunks and processed >= max_chunks:
                    break
                    
                future = executor.submit(process_chunk_batch, extractor, chunk)
                future_to_chunk[future] = (filename, chunk)
                processed += 1
                
                # Print progress every 10 chunks
                if processed % 10 == 0:
                    logger.info(f"Processed {processed}/{total_chunks} chunks")
            
            # Collect results
            extractions = []
            for future in concurrent.futures.as_completed(future_to_chunk):
                filename, chunk = future_to_chunk[future]
                extraction_result = future.result()
                extractions.append(extraction_result)
                
            all_extractions[filename] = extractions

    return all_extractions

def load_chunks_from_directory(chunk_dir: str) -> Dict[str, List[Dict]]:
    """Load chunked JSONL files from directory"""
    all_chunks = {}
    
    if not os.path.exists(chunk_dir):
        logger.error(f"Chunk directory not found: {chunk_dir}")
        return {}
    
    for filename in os.listdir(chunk_dir):
        if filename.endswith("_chunks.jsonl"):
            file_path = os.path.join(chunk_dir, filename)
            chunks = []
            try:
                with open(file_path, 'r') as f:
                    for line in f:
                        chunks.append(json.loads(line))
                all_chunks[filename] = chunks
                logger.info(f"Loaded {len(chunks)} chunks from {filename}")
            except Exception as e:
                logger.error(f"Error loading {file_path}: {e}")
    
    return all_chunks

def save_extractions(all_extractions: Dict[str, List[Dict]], output_file: str) -> None:
    """Save extractions with pretty JSON formatting"""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_extractions, f, indent=2, ensure_ascii=False)
        logger.info(f"Extractions saved to: {output_file}")
    except Exception as e:
        logger.error(f"Failed to save extractions: {e}")

def generate_cypher_script(all_extractions: Dict[str, List[Dict]], output_file: str) -> None:
    """Generate optimized Cypher script with validation"""
    cypher_lines = [
        "// Knowledge Graph Creation Script",
        "// Generated from software design documents",
        "// Domain Focus: " + ", ".join(DOMAIN_FOCUS['topics']),
        ""
    ]
    
    # Add constraints
    for node_type in set(DOMAIN_FOCUS['node_types'].values()):
        cypher_lines.append(
            f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{node_type}) REQUIRE n.name IS UNIQUE;"
        )
    cypher_lines.append("")
    
    # Add MERGE queries
    query_count = 0
    for filename, extractions in all_extractions.items():
        cypher_lines.append(f"\n// Queries from {filename}")
        
        for extraction in extractions:
            if extraction.get('extraction_success', False):
                for query in extraction.get('cypher_queries', []):
                    # Ensure query ends with semicolon
                    if not query.strip().endswith(';'):
                        query += ';'
                    cypher_lines.append(query)
                    query_count += 1
    
    # Add statistics
    cypher_lines[3] = f"// Total queries: {query_count}"
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("\n".join(cypher_lines))
        logger.info(f"Cypher script saved to: {output_file} with {query_count} queries")
    except Exception as e:
        logger.error(f"Failed to save Cypher script: {e}")

def print_extraction_summary(all_extractions: Dict[str, List[Dict]]) -> None:
    """Enhanced summary with domain breakdown"""
    stats = {
        'total_chunks': 0,
        'successful': 0,
        'entities': 0,
        'relationships': 0,
        'domains': {domain: 0 for domain in DOMAIN_FOCUS['topics']},
        'token_estimate': 0
    }
    
    for extractions in all_extractions.values():
        for extraction in extractions:
            stats['total_chunks'] += 1
            if extraction.get('extraction_success'):
                stats['successful'] += 1
                stats['entities'] += len(extraction.get('entities', []))
                stats['relationships'] += len(extraction.get('relationships', []))
                
                # Count entities by domain
                for entity in extraction.get('entities', []):
                    for domain, node_type in DOMAIN_FOCUS['node_types'].items():
                        if entity.get('type') == node_type:
                            stats['domains'][domain] += 1
                
                # Estimate token usage
                chunk_meta = extraction.get('chunk_metadata', {})
                stats['token_estimate'] += chunk_meta.get('token_estimate', 0)
    
    print("\n" + "="*50)
    print("KNOWLEDGE GRAPH EXTRACTION SUMMARY")
    print("="*50)
    print(f"Total chunks processed: {stats['total_chunks']}")
    print(f"Successful extractions: {stats['successful']} ({stats['successful']/stats['total_chunks']*100:.1f}%)")
    print(f"Total entities extracted: {stats['entities']}")
    print(f"Total relationships extracted: {stats['relationships']}")
    print(f"Estimated token usage: {stats['token_estimate']:,}")
    print("\nDomain Distribution:")
    for domain, count in stats['domains'].items():
        print(f"  {domain}: {count} entities")
    print("="*50)

def run_cypher_on_neo4j(cypher_script: str):
    driver = GraphDatabase.driver(
        NEO4J_CONFIG['uri'],
        auth=(NEO4J_CONFIG['user'], NEO4J_CONFIG['password'])
    )
    with driver.session() as session:
        queries = [q.strip() for q in cypher_script.split(';') if q.strip()]
        for query in queries:
            session.run(query)
    driver.close()

if __name__ == "__main__":
    load_dotenv(override=True)
    
    # Create required instances
    extractor = LLMEntityExtractor()
    doc_processor = DocumentProcessor()
    
    # Load chunks from directory
    CHUNK_DIR = "./knowledge_graph/chunks"
    all_chunks = load_chunks_from_directory(CHUNK_DIR)
    
    if not all_chunks:
        logger.error("No chunks found. Check chunking pipeline.")
        exit(1)
    
    total_chunks = sum(len(chunks) for chunks in all_chunks.values())
    logger.info(f"Loaded {total_chunks} chunks from {len(all_chunks)} files")
    
    # Process chunks with parallel execution
    all_extractions = process_all_chunks(
        all_chunks, 
        extractor,
        max_workers=min(8, cpu_count()),  # Optimal for API limits
        max_chunks=total_chunks  # Process all chunks
    )
    
    # Save results
    save_extractions(all_extractions, "knowledge_graph_extractions.json")
    generate_cypher_script(all_extractions, "knowledge_graph.cypher")
    with open("knowledge_graph.cypher", "r") as f:
        cypher_script = f.read()
    run_cypher_on_neo4j(cypher_script)
    print_extraction_summary(all_extractions)