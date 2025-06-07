# LLMEntityExtractor.py
import os
import json
import time
import logging
import re
import datetime
import asyncio
from typing import Dict, List, Any, Optional
from openai import OpenAI, RateLimitError, AsyncOpenAI
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

# Software Design Context - Broader than domain_config but still focused
SOFTWARE_DESIGN_CONTEXT = {
    "core_concepts": [
        # Architectural concepts
        "architecture", "architectural", "design", "pattern", "patterns", "style", "styles",
        "component", "components", "module", "modules", "system", "systems", "service", "services",
        "layer", "layers", "tier", "tiers", "boundary", "boundaries",
        
        # Code structure
        "class", "classes", "interface", "interfaces", "method", "methods", "function", "functions",
        "object", "objects", "entity", "entities", "model", "models", "controller", "controllers",
        "view", "views", "repository", "repositories", "factory", "factories",
        
        # Design principles
        "principle", "principles", "responsibility", "coupling", "cohesion", "abstraction",
        "encapsulation", "inheritance", "polymorphism", "composition", "dependency", "dependencies",
        
        # Quality attributes
        "maintainability", "scalability", "performance", "security", "reliability", "testability",
        "modularity", "extensibility", "reusability", "portability", "availability",
        
        # Process and methodology
        "refactoring", "testing", "implementation", "specification", "documentation",
        "framework", "frameworks", "library", "libraries", "api", "apis",
        
        # Drawing/Graphics patterns (like your Composite/Primitive Artist example)
        "artist", "renderer", "painter", "drawer", "graphics", "visual", "display",
        "primitive", "composite", "leaf", "container", "hierarchy", "tree"
    ],
    
    "relationship_indicators": [
        "implements", "extends", "uses", "contains", "depends", "inherits", "aggregates",
        "composes", "delegates", "observes", "publishes", "subscribes", "manages", "controls",
        "creates", "builds", "constructs", "produces", "generates", "processes", "handles"
    ],
    
    # Exclusion patterns - things that are clearly NOT software design
    "exclusions": [
        "marketing", "sales", "business process", "accounting", "finance", "hr", "human resources",
        "customer service", "support ticket", "invoice", "payment", "billing", "legal", "contract",
        "meeting", "schedule", "calendar", "email", "phone", "address", "location", "geography"
    ]
}

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
        self.min_request_interval = 0.05
        self.total_tokens = 0 

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
        """Simple rate limiting"""
        current_time = time.time()
        elapsed = current_time - self.last_request_time
        
        if elapsed < self.min_request_interval:
            time.sleep(self.min_request_interval - elapsed)
            
        self.last_request_time = time.time()

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=0.5, min=1, max=3))
    def extract_entities_and_relationships_batch(self, chunks: List[Dict]) -> List[Dict]:
        """Simple synchronous batch extraction"""
        try:
            self._rate_limit()
            combined_text = "\n\n---\n\n".join([chunk['text'] for chunk in chunks])
            all_domains = list(set([d for chunk in chunks for d in chunk.get('domains', [])]))
            if not all_domains:
                all_domains = list(DOMAIN_FOCUS['node_types'].keys())

            node_types = [DOMAIN_FOCUS["node_types"][d] for d in all_domains if d in DOMAIN_FOCUS["node_types"]]

            time.sleep(self.min_request_interval)

            messages = [
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": self._create_extraction_prompt(
                    combined_text, all_domains, node_types
                )}
            ]

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.1,
                max_tokens=1000,
                timeout=20
            )

            if hasattr(response, 'usage') and response.usage:
                self.total_tokens += response.usage.total_tokens

            content = response.choices[0].message.content
            context_chunk = {
                "text": combined_text,
                "domains": all_domains,
                "source": chunks[0].get('source', ''),
                "position": chunks[0].get('position', '')
            }
            result = self._parse_llm_response(content, context_chunk)

            return [{**result, "chunk_metadata": chunk} for chunk in chunks]

        except Exception as e:
            logger.error(f"Batch extraction failed: {e}")
            return [self._create_empty_result(chunk) for chunk in chunks]
        
    def _get_system_prompt(self) -> str:
        """Enhanced system prompt focusing on software design with flexibility"""
        return f"""
        You are an expert software architect and design pattern specialist. Extract entities and relationships 
        specifically related to SOFTWARE DESIGN, ARCHITECTURE, and PROGRAMMING CONCEPTS.

        PRIMARY FOCUS AREAS (prioritize these):
        {", ".join(DOMAIN_FOCUS['topics'])}

        SECONDARY FOCUS: Any software design concepts including:
        - Programming patterns and idioms
        - Code organization and structure  
        - Software engineering practices
        - System design and architecture
        - Framework and library concepts
        - Development methodologies
        - Graphics/UI design patterns (like Composite Artist, Primitive Artist)

        VALID NODE TYPES: {list(DOMAIN_FOCUS['node_types'].values())}

        Respond in JSON format:
        {{
            "entities": [
                {{
                    "name": "entity_name",
                    "type": "best_matching_node_type",  
                    "description": "Brief description focusing on software design relevance",
                    "properties": {{"relevance_score": 0.8}}
                }}
            ],
            "relationships": [
                {{
                    "source": "source_entity_name",
                    "target": "target_entity_name", 
                    "type": "relationship_type",  // RELATES_TO, IMPLEMENTS, DEPENDS_ON, CONTAINS, PART_OF
                    "description": "How this relationship is relevant to software design"
                }}
            ]
        }}

        CRITICAL RULES:
        1. ONLY extract software/programming/design-related concepts
        2. Map entities to the closest appropriate node type from the valid list
        3. Include implementation-specific patterns (e.g., "Composite Artist" maps to DesignPattern)
        4. Escape quotes properly with \\
        5. Focus on concepts that would appear in software architecture documentation
        6. Exclude business processes, marketing, or non-technical content
        """

    def _create_extraction_prompt(self, chunk_text: str, domains: List[str], node_types: List[str]) -> str:
        """Create flexible but focused extraction prompt"""
        if not domains:
            domains = list(DOMAIN_FOCUS['keywords'].keys())
            
        domain_context = "\n".join([f"- {d}: {', '.join(DOMAIN_FOCUS['keywords'].get(d, [])[:5])}" for d in domains])
        
        return f"""
        Analyze this text for SOFTWARE DESIGN concepts. Focus on technical and architectural content.

        PRIORITY DOMAINS:
        {domain_context}

        Text to analyze:
        \"\"\"
        {chunk_text[:3000]}
        \"\"\"

        EXTRACTION GUIDELINES:
        1. Look for design patterns, architectural concepts, code structures
        2. Include specific implementations of general patterns (e.g., "Repository Pattern" or "UserRepository")  
        3. Map entities to these node types: {', '.join(node_types) if node_types else ', '.join(DOMAIN_FOCUS['node_types'].values())}
        4. For graphics/UI patterns: use DesignPattern type
        5. For code structures: use CodeStructure type
        6. For architecture concepts: use ArchPattern type
        7. Extract relationships showing how concepts connect
        8. Skip business processes, marketing content, or non-technical topics

        EXAMPLES of what TO extract:
        - "Composite Artist" (DesignPattern) -> implements Composite pattern for graphics
        - "Primitive Artist" (DesignPattern) -> leaf component in Composite pattern
        - "MVC Controller" (ArchPattern) -> manages application flow
        - "Repository Interface" (CodeStructure) -> abstracts data access

        Respond ONLY with valid JSON.
        """

    def _is_software_design_relevant(self, text: str) -> bool:
        """Enhanced relevance checking with lower threshold"""
        text_lower = text.lower()
        
        # Check exclusions first
        for exclusion in SOFTWARE_DESIGN_CONTEXT["exclusions"]:
            if exclusion in text_lower:
                return False
        
        # Check for software design relevance with more flexible scoring
        relevance_score = 0
        
        # Core concepts (weight: 1)
        for concept in SOFTWARE_DESIGN_CONTEXT["core_concepts"]:
            if concept in text_lower:
                relevance_score += 1
        
        # Domain keywords (weight: 2)
        for domain_keywords in DOMAIN_FOCUS['keywords'].values():
            for keyword in domain_keywords:
                if keyword.lower() in text_lower:
                    relevance_score += 2
        
        # Relationship indicators (weight: 0.5)
        for indicator in SOFTWARE_DESIGN_CONTEXT["relationship_indicators"]:
            if indicator in text_lower:
                relevance_score += 0.5
        
        # Lower threshold: accept if score >= 0.4 instead of 1
        return relevance_score >= 0.4

    def _map_to_best_node_type(self, entity_name: str, entity_description: str, suggested_type: str) -> str:
        """Intelligently map entity to the most appropriate node type"""
        text = f"{entity_name} {entity_description}".lower()
        
        # If suggested type is valid, use it
        valid_types = list(DOMAIN_FOCUS['node_types'].values())
        if suggested_type in valid_types:
            return suggested_type
            
        # Smart mapping based on content
        if any(term in text for term in ["pattern", "strategy", "observer", "factory", "singleton", "composite", "adapter", "artist", "renderer"]):
            return "DesignPattern"
        elif any(term in text for term in ["architecture", "layer", "tier", "microservice", "mvc", "client-server"]):
            return "ArchPattern"  
        elif any(term in text for term in ["solid", "dry", "kiss", "principle", "responsibility", "coupling"]):
            return "DesignPrinciple"
        elif any(term in text for term in ["maintainability", "scalability", "performance", "security", "reliability"]):
            return "QualityAttribute"
        elif any(term in text for term in ["bounded", "aggregate", "entity", "value object", "repository", "domain"]):
            return "DDDConcept"
        elif any(term in text for term in ["module", "component", "interface", "class", "package", "namespace"]):
            return "CodeStructure"
        else:
            # Default mapping based on most likely category
            return "DesignPattern"  # Most flexible default

    def _parse_llm_response(self, content: str, chunk: Dict) -> Dict:
        """Parse LLM response with intelligent software design validation"""
        try:
            json_match = re.search(r'\{[\s\S]*\}', content, re.DOTALL)
            if not json_match:
                logger.warning("No JSON found in LLM response")
                return self._create_empty_result(chunk)
                
            json_str = json_match.group()
            parsed = json.loads(repair_json(json_str))
            
            valid_entities = []
            for entity in parsed.get('entities', []):
                if self._is_valid_software_design_entity(entity):
                    # Ensure proper node type mapping
                    entity['type'] = self._map_to_best_node_type(
                        entity.get('name', ''),
                        entity.get('description', ''),
                        entity.get('type', '')
                    )
                    entity['source_file'] = chunk.get('source', '')
                    entity['source_page'] = chunk.get('position', '')
                    valid_entities.append(entity)
                else:
                    logger.debug(f"Filtered out non-software-design entity: {entity.get('name', 'unnamed')}")
            
            valid_relationships = []
            for rel in parsed.get('relationships', []):
                if self._is_valid_relationship(rel, valid_entities):
                    valid_relationships.append(rel)
            
            # Accept if we have meaningful software design content
            if len(valid_entities) < 1 and len(valid_relationships) < 1:
                return self._create_empty_result(chunk)
            
            cypher_queries = self._generate_cypher_queries(valid_entities, valid_relationships)
            
            return {
                'entities': valid_entities,
                'relationships': valid_relationships,
                'cypher_queries': cypher_queries,
                'chunk_metadata': chunk,
                'extraction_success': bool(valid_entities or valid_relationships)
            }
            
        except Exception as e:
            logger.error(f"Response parsing failed: {e}")
            logger.debug(f"Content that failed to parse: {content[:500]}...")
            return self._create_empty_result(chunk)

    def _is_valid_software_design_entity(self, entity: Dict) -> bool:
        """Validate entity for software design relevance with intelligent filtering"""
        # Must have required fields
        if not entity.get('name') or not entity.get('type'):
            return False
            
        entity_text = f"{entity.get('name', '')} {entity.get('description', '')}".lower()
        
        # Check if it's software design relevant
        if not self._is_software_design_relevant(entity_text):
            return False
            
        # Must be mappable to a valid node type (we'll fix the type in _map_to_best_node_type)
        valid_types = list(DOMAIN_FOCUS['node_types'].values())
        if entity.get('type') not in valid_types:
            # Try to map it
            mapped_type = self._map_to_best_node_type(
                entity.get('name', ''),
                entity.get('description', ''),
                entity.get('type', '')
            )
            if mapped_type not in valid_types:
                return False
        
        return True

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
        """Generate Cypher queries with duplicate checking"""
        queries = []
        
        if not hasattr(self, '_existing_entities'):
            self._existing_entities = load_existing_entities_from_neo4j()
        
        for entity in entities:
            # if entity['name'] in self._existing_entities:
            #     continue
                
            name = entity['name'].replace('"', '\\"').replace("'", "\\'")
            description = entity.get('description', '').replace('"', '\\"').replace("'", "\\'")
            
            props = {
                'name': f'"{name}"',
                'description': f'"{description}"',
                'source': f'"{entity.get("source_file", "")}"',
                'page': entity.get("source_page", "")
            }
            
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
            
            self._existing_entities.add(entity['name'])
        
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
    
    BATCH_SIZE = 3 

    def create_batches(self, chunks: List[Dict]) -> List[List[Dict]]:
        return [chunks[i:i + self.BATCH_SIZE] 
                for i in range(0, len(chunks), self.BATCH_SIZE)]

class DocumentProcessor:
    def __init__(self):
        pass

def append_cypher_queries_immediately(queries: List[str], output_file: str = "./knowledge_graph/knowledge_graph.cypher"):
        """Immediately append new cypher queries to file for crash protection"""
        if not queries:
            return
        
        file_exists = os.path.exists(output_file)
        
        try:
            mode = 'a' if file_exists else 'w'
            with open(output_file, mode, encoding='utf-8') as f:
                if not file_exists:
                    # Write header for new file
                    f.write("// Knowledge Graph Creation Script\n")
                    f.write("// Generated from software design documents\n")
                    f.write(f"// Domain Focus: {', '.join(DOMAIN_FOCUS['topics'])}\n\n")
                    
                    # Add constraints
                    for node_type in set(DOMAIN_FOCUS['node_types'].values()):
                        f.write(f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{node_type}) REQUIRE n.name IS UNIQUE;\n")
                    f.write("\n")
                
                # Add timestamp comment for this batch
                f.write(f"\n// Batch saved at {datetime.datetime.now()}\n")
                for query in queries:
                    if not query.strip().endswith(';'):
                        query += ';'
                    f.write(query + '\n')
                f.flush()  # Force write to disk immediately
                
        except Exception as e:
            logger.error(f"Failed to append cypher queries: {e}")

def process_chunk_batch(extractor: LLMEntityExtractor, chunks: List[Dict]) -> List[Dict]:
    """Process batch and immediately save cypher queries"""
    start_time = time.time()
    try:
        results = extractor.extract_entities_and_relationships_batch(chunks)
        
        processing_time = time.time() - start_time
        logger.info(f"Batch of {len(chunks)} chunks processed in {processing_time:.2f}s")

        # Immediately save cypher queries from successful extractions
        all_queries = []
        successful_chunks = []
        
        for result in results:
            if result.get('extraction_success', False):
                queries = result.get('cypher_queries', [])
                all_queries.extend(queries)
                successful_chunks.append(result)
        
        # Save queries immediately for crash protection
        if all_queries:
            append_cypher_queries_immediately(all_queries)
            logger.debug(f"Saved {len(all_queries)} queries immediately to disk")
        
        return results
        
    except Exception as e:
        logger.error(f"Failed to process batch: {e}")
        return [extractor._create_empty_result(chunk) for chunk in chunks]

def load_processed_chunks() -> set:
    """Load list of already processed chunk IDs to skip them"""
    processed_file = "processed_chunks.json"
    if os.path.exists(processed_file):
        try:
            with open(processed_file, 'r') as f:
                return set(json.load(f))
        except:
            return set()
    return set()

def save_processed_chunks(processed_chunks: set):
    """Save processed chunk IDs"""
    with open("processed_chunks.json", 'w') as f:
        json.dump(list(processed_chunks), f)

def create_chunk_id(chunk: Dict) -> str:
    """Create unique ID for chunk based on content + source"""
    text_hash = hash(chunk['text'][:100])  # Hash first 100 chars
    return f"{chunk.get('source', 'unknown')}_{chunk.get('position', 0)}_{text_hash}"

def save_checkpoint(processed_chunk_ids: set, extractions_so_far: Dict):
    """Save checkpoint data every N batches"""
    try:
        save_processed_chunks(processed_chunk_ids)
        
        checkpoint_file = "extraction_checkpoint.json"
        with open(checkpoint_file, 'w') as f:
            json.dump(extractions_so_far, f, indent=2)
            
        logger.debug("Checkpoint saved")
    except Exception as e:
        logger.error(f"Failed to save checkpoint: {e}")

def process_all_chunks(all_chunks, extractor, max_workers=None, max_chunks=None):
    """Process chunks with immediate saving and checkpoints"""
    
    processed_chunk_ids = load_processed_chunks()
    logger.info(f"Found {len(processed_chunk_ids)} already processed chunks")
    
    for filename, chunks in all_chunks.items():
        for chunk in chunks:
            if not isinstance(chunk, dict) or 'text' not in chunk:
                logger.error(f"Invalid chunk format in {filename}: {type(chunk)}")
                raise ValueError("Chunks must be dictionaries with 'text' field")
    
    new_chunks = {}
    total_original = 0
    total_new = 0
    
    for filename, chunks in all_chunks.items():
        total_original += len(chunks)
        new_file_chunks = []
        
        for chunk in chunks:
            chunk_id = create_chunk_id(chunk)
            if chunk_id not in processed_chunk_ids:
                new_file_chunks.append(chunk)
        
        if new_file_chunks:
            new_chunks[filename] = new_file_chunks
            total_new += len(new_file_chunks)
    
    logger.info(f"Processing {total_new} new chunks (skipped {total_original - total_new} already processed)")
    
    if not new_chunks:
        logger.info("No new chunks to process!")
        return {}
    
    if max_workers is None:
        max_workers = min(8, cpu_count()*2) 
        
    all_extractions = {}
    total_chunks = sum(len(chunks) for chunks in all_chunks.values())
    
    if max_chunks:
        total_chunks = min(total_chunks, max_chunks)
    
    processed = 0
    newly_processed_ids = set()
    CHECKPOINT_INTERVAL = 100  # Save checkpoint every 100 batches
    batch_count = 0
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        for filename, chunks_list in new_chunks.items():
            logger.info(f"Processing {len(chunks_list)} new chunks from {filename}")
            batches = extractor.create_batches(chunks_list)
            futures = []
            
            for batch in batches:
                if max_chunks and processed >= max_chunks:
                    break
                    
                # Submit batch for processing (which now includes immediate saving)
                future = executor.submit(process_chunk_batch, extractor, batch)
                futures.append((future, batch))
                processed += len(batch)
                batch_count += 1
                
                if processed % 10 == 0:
                    logger.info(f"Processed {processed}/{total_new} new chunks")
            
            file_extractions = []
            for future, batch in futures:
                try:
                    batch_results = future.result()
                    file_extractions.extend(batch_results)
                    
                    # Mark chunks as processed
                    for chunk in batch:
                        newly_processed_ids.add(create_chunk_id(chunk))
                    
                    # Save checkpoint periodically
                    if batch_count % CHECKPOINT_INTERVAL == 0:
                        all_processed = processed_chunk_ids.union(newly_processed_ids)
                        save_checkpoint(all_processed, all_extractions)
                        
                except Exception as e:
                    logger.error(f"Error processing batch: {e}")
            
            all_extractions[filename] = file_extractions

            if max_chunks and processed >= max_chunks:
                break
    
    all_processed = processed_chunk_ids.union(newly_processed_ids)
    save_processed_chunks(all_processed)
    logger.info(f"Saved {len(newly_processed_ids)} newly processed chunk IDs")
                
    return all_extractions

def recover_from_checkpoint():
    """Recover processing state from checkpoint files"""
    checkpoint_file = "extraction_checkpoint.json"
    
    if os.path.exists(checkpoint_file):
        try:
            with open(checkpoint_file, 'r') as f:
                partial_extractions = json.load(f)
            
            processed_chunks = load_processed_chunks()
            
            logger.info(f"Found checkpoint with {len(partial_extractions)} files and {len(processed_chunks)} processed chunks")
            return partial_extractions, processed_chunks
            
        except Exception as e:
            logger.error(f"Failed to recover from checkpoint: {e}")
    
    return {}, set()

def process_all_chunks(all_chunks, extractor, max_workers=None, max_chunks=None):
    """Process all chunks with parallel execution"""
    for filename, chunks in all_chunks.items():
        for chunk in chunks:
            if not isinstance(chunk, dict) or 'text' not in chunk:
                logger.error(f"Invalid chunk format in {filename}: {type(chunk)}")
                raise ValueError("Chunks must be dictionaries with 'text' field")

    processed_files = set()
    if os.path.exists("./knowledge_graph/knowledge_graph_extractions.json"):
        with open("./knowledge_graph/knowledge_graph_extractions.json", 'r') as f:
            existing = json.load(f)
            processed_files = set(existing.keys())

    for filename, chunks in all_chunks.items():
        if filename in processed_files:
            logger.info(f"Skipping already processed: {filename}")
            continue

    if max_workers is None:
        max_workers = min(4, cpu_count())
        
    all_extractions = {}
    total_chunks = sum(len(chunks) for chunks in all_chunks.values())
    
    if max_chunks:
        total_chunks = min(total_chunks, max_chunks)
    
    processed = 0
    logger.info(f"Starting extraction for {total_chunks} chunks with {max_workers} workers...")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        for filename, chunks_list in all_chunks.items():
            if filename in processed_files:
                continue
                
            logger.info(f"Processing chunks from {filename}")
            batches = extractor.create_batches(chunks_list)
            futures = []
            for batch in batches:
                if max_chunks and processed >= max_chunks:
                    break
                future = executor.submit(process_chunk_batch, extractor, batch)
                futures.append(future)
                processed += len(batch)
                
                if processed % 10 == 0:
                    logger.info(f"Processed {processed}/{total_chunks} chunks")
            
            file_extractions = []
            for future in concurrent.futures.as_completed(futures):
                try:
                    batch_results = future.result()
                    file_extractions.extend(batch_results)
                except Exception as e:
                    logger.error(f"Error processing batch: {e}")
            all_extractions[filename] = file_extractions

            if max_chunks and processed >= max_chunks:
                break
                
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
    """Save only non-empty extractions"""
    filtered_extractions = {}
    
    for filename, extractions in all_extractions.items():
        # Only keep successful extractions with actual content
        successful_extractions = [
            ext for ext in extractions 
            if ext.get('extraction_success', False) and 
            (len(ext.get('entities', [])) > 0 or len(ext.get('relationships', [])) > 0)
        ]
        
        if successful_extractions:  # Only include files with successful extractions
            filtered_extractions[filename] = successful_extractions
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(filtered_extractions, f, indent=2, ensure_ascii=False)
        logger.info(f"Filtered extractions saved to: {output_file}")
    except Exception as e:
        logger.error(f"Failed to save extractions: {e}")

def generate_cypher_script(all_extractions: Dict[str, List[Dict]], output_file: str = "knowledge_graph.cypher") -> None:
    """Append new cypher queries to existing file"""
    file_exists = os.path.exists(output_file)
    
    new_queries = []
    query_count = 0
    
    for filename, extractions in all_extractions.items():
        new_queries.append(f"\n// New queries from {filename} - {datetime.datetime.now()}")
        
        for extraction in extractions:
            if extraction.get('extraction_success', False):
                for query in extraction.get('cypher_queries', []):
                    if not query.strip().endswith(';'):
                        query += ';'
                    new_queries.append(query)
                    query_count += 1
    
    if not new_queries:
        logger.info("No new queries to add")
        return
    
    mode = 'a' if file_exists else 'w'
    try:
        with open(output_file, mode, encoding='utf-8') as f:
            if not file_exists:
                f.write("// Knowledge Graph Creation Script\n")
                f.write("// Generated from software design documents\n")
                f.write(f"// Domain Focus: {', '.join(DOMAIN_FOCUS['topics'])}\n\n")
                
                for node_type in set(DOMAIN_FOCUS['node_types'].values()):
                    f.write(f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{node_type}) REQUIRE n.name IS UNIQUE;\n")
                f.write("\n")
            else:
                f.write(f"\n// === INCREMENTAL UPDATE {datetime.datetime.now()} ===\n")
            
            f.write("\n".join(new_queries))
            
        logger.info(f"{'Appended' if file_exists else 'Created'} {query_count} queries to {output_file}")
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
                
                for entity in extraction.get('entities', []):
                    for domain, node_type in DOMAIN_FOCUS['node_types'].items():
                        if entity.get('type') == node_type:
                            stats['domains'][domain] += 1
                
                chunk_meta = extraction.get('chunk_metadata', {})
                stats['token_estimate'] += chunk_meta.get('token_estimate', 0)
    
    print("\n" + "="*50)
    print("SOFTWARE DESIGN KNOWLEDGE GRAPH EXTRACTION SUMMARY")
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

def load_existing_entities_from_neo4j():
    """Load existing entity names from Neo4j to avoid duplicates"""
    try:
        driver = GraphDatabase.driver(
            NEO4J_CONFIG['uri'],
            auth=(NEO4J_CONFIG['user'], NEO4J_CONFIG['password'])
        )
        existing_entities = set()
        with driver.session() as session:
            result = session.run("MATCH (n) RETURN DISTINCT n.name as name")
            for record in result:
                if record["name"]:
                    existing_entities.add(record["name"])
        driver.close()
        return existing_entities
    except Exception as e:
        logger.warning(f"Could not load existing entities: {e}")
        return set()
    
def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--force-reprocess', action='store_true', 
                       help='Force reprocess all chunks (ignore processed_chunks.json)')
    parser.add_argument('--recover', action='store_true',
                       help='Recover from checkpoint and continue processing')
    parser.add_argument('--max-chunks', type=int, help='Limit number of chunks to process')
    args = parser.parse_args()

    if args.recover:
        partial_extractions, processed_chunks = recover_from_checkpoint()
        logger.info("Recovered from checkpoint - continuing where left off")

    if args.force_reprocess:
        # Clean slate
        for file in ["processed_chunks.json", "extraction_checkpoint.json", "knowledge_graph.cypher"]:
            if os.path.exists(file):
                os.remove(file)
        logger.info("Removed all checkpoint files - starting fresh")

    load_dotenv(override=True)

    extractor = LLMEntityExtractor()
    doc_processor = DocumentProcessor()

    CHUNK_DIR = "./knowledge_graph/chunks"
    all_chunks = load_chunks_from_directory(CHUNK_DIR)

    if not all_chunks:
        logger.error("No chunks found. Check chunking pipeline.")
        exit(1)

    # Process only new chunks
    all_extractions = process_all_chunks(
        all_chunks,
        extractor,
        max_workers=cpu_count(),
        max_chunks=args.max_chunks
    )

    if all_extractions:
        save_extractions(all_extractions, "./knowledge_graph/knowledge_graph_extractions.json")
        generate_cypher_script(all_extractions)  # generate but DO NOT run
        print_extraction_summary(all_extractions)
    else:
        logger.info("No new extractions to process")

if __name__ == "__main__":
    main()