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
from neo4j import GraphDatabase
from config import NEO4J_CONFIG

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SOFTWARE_DESIGN_CONTEXT = {
    "core_concepts": [
        "architecture", "architectural", "design", "pattern", "patterns", "style", "styles",
        "component", "components", "module", "modules", "system", "systems", "service", "services",
        "layer", "layers", "tier", "tiers", "boundary", "boundaries",
        
        "class", "classes", "interface", "interfaces", "method", "methods", "function", "functions",
        "object", "objects", "entity", "entities", "model", "models", "controller", "controllers",
        "view", "views", "repository", "repositories", "factory", "factories",
        
        "principle", "principles", "responsibility", "coupling", "cohesion", "abstraction",
        "encapsulation", "inheritance", "polymorphism", "composition", "dependency", "dependencies",
        
        "maintainability", "scalability", "performance", "security", "reliability", "testability",
        "modularity", "extensibility", "reusability", "portability", "availability",
        
        "refactoring", "testing", "implementation", "specification", "documentation",
        "framework", "frameworks", "library", "libraries", "api", "apis",
        
        "artist", "renderer", "painter", "drawer", "graphics", "visual", "display",
        "primitive", "composite", "leaf", "container", "hierarchy", "tree"
    ],
    
    "relationship_indicators": [
        "implements", "extends", "uses", "contains", "depends", "inherits", "aggregates",
        "composes", "delegates", "observes", "publishes", "subscribes", "manages", "controls",
        "creates", "builds", "constructs", "produces", "generates", "processes", "handles"
    ],
    
    "exclusions": [
        "marketing", "sales", "business process", "accounting", "finance", "hr", "human resources",
        "customer service", "support ticket", "invoice", "payment", "billing", "legal", "contract",
        "meeting", "schedule", "calendar", "email", "phone", "address", "location", "geography"
    ]
}

# Enhanced relationship mapping based on domain knowledge
RELATIONSHIP_RULES = {
    "design_patterns": {
        ("DesignPattern", "QualityAttribute"): "SUPPORTS",
        ("DesignPattern", "DesignPrinciple"): "APPLIES",
        ("DesignPattern", "CodeStructure"): "IMPLEMENTS",
        ("CodeStructure", "DesignPattern"): "USES"
    },
    "principles": {
        ("DesignPrinciple", "QualityAttribute"): "PROMOTES",
        ("DesignPrinciple", "DesignPrinciple"): "RELATES_TO",
        ("DesignPrinciple", "ArchPattern"): "GUIDES"
    },
    "architecture": {
        ("ArchPattern", "QualityAttribute"): "ACHIEVES",
        ("ArchPattern", "DesignPattern"): "USES",
        ("ArchPattern", "CodeStructure"): "ORGANIZES"
    }
}

VALID_RELATIONSHIP_TYPES = {
    "IMPLEMENTS", "APPLIES", "SUPPORTS", "COMPOSES", "EXTENDS", 
    "REQUIRES", "CONFLICTS_WITH", "SOLVES", "RELATES_TO", "PROMOTES",
    "ENABLES", "ACHIEVES", "ORGANIZES", "GUIDES", "USES", "DEPENDS_ON",
    "CONTAINS", "PART_OF", "SIMILAR_TO", "CONTRIBUTES_TO", "HELPS_ACHIEVE"
}

def repair_json(json_str: str) -> str:
    """Basic JSON repair for common issues"""
    json_str = re.sub(r',\s*}', '}', json_str)
    json_str = re.sub(r',\s*]', ']', json_str)
    json_str = re.sub(r'(["\'])\s*:\s*(["\'])', r'\1: \2', json_str)
    return json_str

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
        """Enhanced batch extraction with relationship enrichment"""
        try:
            self._rate_limit()
            combined_text = "\n\n---\n\n".join([chunk['text'] for chunk in chunks])
            all_domains = list(set([d for chunk in chunks for d in chunk.get('domains', [])]))
            if not all_domains:
                all_domains = list(DOMAIN_FOCUS['node_types'].keys())

            node_types = [DOMAIN_FOCUS["node_types"][d] for d in all_domains if d in DOMAIN_FOCUS["node_types"]]

            time.sleep(self.min_request_interval)

            messages = [
                {"role": "system", "content": self._get_enhanced_system_prompt()},
                {"role": "user", "content": self._create_enhanced_extraction_prompt(
                    combined_text, all_domains, node_types
                )}
            ]

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.1,
                max_tokens=1500,  # Increased for relationship extraction
                timeout=25
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
            result = self._parse_enhanced_llm_response(content, context_chunk)

            return [{**result, "chunk_metadata": chunk} for chunk in chunks]

        except Exception as e:
            logger.error(f"Batch extraction failed: {e}")
            return [self._create_empty_result(chunk) for chunk in chunks]
        
    def _get_enhanced_system_prompt(self) -> str:
        """Enhanced system prompt focusing on relationships"""
        return f"""
        You are an expert software architect specializing in extracting ENTITIES and their RELATIONSHIPS 
        from software design and architecture documents.

        PRIMARY FOCUS: Extract software design concepts AND their semantic relationships.

        VALID ENTITY TYPES: {list(set(DOMAIN_FOCUS['node_types'].values()))}

        VALID RELATIONSHIP TYPES: {', '.join(sorted(VALID_RELATIONSHIP_TYPES))}

        RELATIONSHIP EXTRACTION RULES:
        1. IMPLEMENTS: Concrete implementations of abstractions
        2. APPLIES: Principles applied to patterns/structures  
        3. SUPPORTS/PROMOTES: Patterns supporting quality attributes
        4. USES/DEPENDS_ON: Dependencies between components
        5. RELATES_TO: General semantic connections
        6. ENABLES/ACHIEVES: Causal relationships
        7. CONTAINS/PART_OF: Composition relationships

        Response format (STRICT JSON):
        {{
            "entities": [
                {{
                    "name": "Entity Name",
                    "type": "EntityType",
                    "description": "Brief description",
                    "properties": {{"relevance_score": 0.8, "domain": "design_patterns"}}
                }}
            ],
            "relationships": [
                {{
                    "source": "Source Entity Name",
                    "target": "Target Entity Name",
                    "type": "RELATIONSHIP_TYPE",
                    "description": "Why this relationship exists",
                    "strength": 0.8,
                    "context": "When/where this applies"
                }}
            ]
        }}

        CRITICAL: Focus on SOFTWARE DESIGN concepts only. Extract meaningful relationships.
        """

    def _create_enhanced_extraction_prompt(self, chunk_text: str, domains: List[str], node_types: List[str]) -> str:
        """Enhanced extraction prompt with relationship focus"""
        if not domains:
            domains = list(DOMAIN_FOCUS['keywords'].keys())
            
        domain_context = "\n".join([f"- {d}: {', '.join(DOMAIN_FOCUS['keywords'].get(d, [])[:5])}" for d in domains])
        
        return f"""
        Extract SOFTWARE DESIGN entities AND their relationships from this text:

        PRIORITY DOMAINS:
        {domain_context}

        TEXT TO ANALYZE:
        \"\"\"
        {chunk_text[:3500]}
        \"\"\"

        EXTRACTION REQUIREMENTS:
        1. ENTITIES: Identify design patterns, principles, architectures, code structures, quality attributes
        2. RELATIONSHIPS: Extract HOW entities connect (not just that they do)
        3. ENTITY TYPES: Use these types: {', '.join(node_types) if node_types else ', '.join(set(DOMAIN_FOCUS['node_types'].values()))}
        4. RELATIONSHIP TYPES: Use semantic types like IMPLEMENTS, SUPPORTS, APPLIES, ENABLES, etc.

        EXAMPLES:
        - "Observer Pattern" (DesignPattern) SUPPORTS "Loose Coupling" (QualityAttribute)
        - "Single Responsibility Principle" (DesignPrinciple) PROMOTES "Maintainability" (QualityAttribute)
        - "Factory Pattern" (DesignPattern) APPLIES "Open/Closed Principle" (DesignPrinciple)

        CRITICAL: 
        - Extract BOTH entities AND relationships
        - Use meaningful relationship types, not generic "RELATES_TO"
        - Include relationship descriptions explaining WHY the connection exists
        - Focus on software architecture and design concepts only

        Return ONLY valid JSON.
        """

    def _parse_enhanced_llm_response(self, content: str, chunk: Dict) -> Dict:
        """Enhanced parsing with relationship enrichment"""
        try:
            json_match = re.search(r'\{[\s\S]*\}', content, re.DOTALL)
            if not json_match:
                logger.warning("No JSON found in LLM response")
                return self._create_empty_result(chunk)
                
            json_str = json_match.group()
            parsed = json.loads(repair_json(json_str))
            
            # Validate and clean entities
            valid_entities = []
            for entity in parsed.get('entities', []):
                if self._is_valid_software_design_entity(entity):
                    entity['type'] = self._map_to_best_node_type(
                        entity.get('name', ''),
                        entity.get('description', ''),
                        entity.get('type', '')
                    )
                    entity['source_file'] = chunk.get('source', '')
                    entity['source_page'] = chunk.get('position', '')
                    valid_entities.append(entity)
            
            # Validate relationships
            valid_relationships = []
            for rel in parsed.get('relationships', []):
                if self._is_valid_relationship(rel, valid_entities):
                    # Ensure relationship type is valid
                    if rel.get('type') not in VALID_RELATIONSHIP_TYPES:
                        rel['type'] = 'RELATES_TO'  # Fallback
                    valid_relationships.append(rel)
            
            if len(valid_entities) < 1 and len(valid_relationships) < 1:
                return self._create_empty_result(chunk)
            
            cypher_queries = self._generate_enhanced_cypher_queries(valid_entities, valid_relationships)
            
            return {
                'entities': valid_entities,
                'relationships': valid_relationships,
                'cypher_queries': cypher_queries,
                'chunk_metadata': chunk,
                'extraction_success': bool(valid_entities or valid_relationships)
            }
            
        except Exception as e:
            logger.error(f"Enhanced response parsing failed: {e}")
            logger.debug(f"Content that failed to parse: {content[:500]}...")
            return self._create_empty_result(chunk)

    def _generate_enhanced_cypher_queries(self, entities: List[Dict], relationships: List[Dict]) -> List[str]:
        """Generate enhanced Cypher with meaningful relationships"""
        queries = []
        
        # Create nodes with rich properties
        for entity in entities:
            name = entity['name'].replace('"', '\\"').replace("'", "\\'")
            description = entity.get('description', '').replace('"', '\\"').replace("'", "\\'")
            
            props = {
                'name': f'"{name}"',
                'description': f'"{description}"',
                'source': f'"{entity.get("source_file", "")}"',
                'page': entity.get("source_page", ""),
                'domain': f'"{entity.get("domain", "")}"',
                'relevance_score': entity.get('properties', {}).get('relevance_score', 0.5)
            }
            
            prop_str = ", ".join(f"{k}: {v}" for k, v in props.items() if v not in ['""', ''])
            queries.append(f"MERGE (:{entity['type']} {{ {prop_str} }});")
        
        # Create relationships with semantic properties
        for rel in relationships:
            source_clean = rel['source'].replace('"', '\\"')
            target_clean = rel['target'].replace('"', '\\"')
            rel_desc = rel.get('description', '').replace('"', '\\"')
            
            rel_props = {
                'strength': rel.get('strength', 0.5),
                'context': f'"{rel.get("context", "")}"',
                'description': f'"{rel_desc}"',
                'source_type': f'"{rel.get("source_type", "llm_extraction")}"'
            }
            
            props_str = ", ".join(f"{k}: {v}" for k, v in rel_props.items() if v not in ['""'])
            
            queries.append(f"""MATCH (s {{name: "{source_clean}"}})
MATCH (t {{name: "{target_clean}"}})
MERGE (s)-[:{rel['type']} {{ {props_str} }}]->(t);""")
            
        return queries

    def _is_software_design_relevant(self, text: str) -> bool:
        """Enhanced relevance checking"""
        text_lower = text.lower()
        
        # Check exclusions first
        for exclusion in SOFTWARE_DESIGN_CONTEXT["exclusions"]:
            if exclusion in text_lower:
                return False
        
        relevance_score = 0
        
        for concept in SOFTWARE_DESIGN_CONTEXT["core_concepts"]:
            if concept in text_lower:
                relevance_score += 1
        
        for domain_keywords in DOMAIN_FOCUS['keywords'].values():
            for keyword in domain_keywords:
                if keyword.lower() in text_lower:
                    relevance_score += 2
        
        for indicator in SOFTWARE_DESIGN_CONTEXT["relationship_indicators"]:
            if indicator in text_lower:
                relevance_score += 0.5
        
        return relevance_score >= 0.4

    def _map_to_best_node_type(self, entity_name: str, entity_description: str, suggested_type: str) -> str:
        """Intelligently map entity to the most appropriate node type"""
        text = f"{entity_name} {entity_description}".lower()
        
        valid_types = list(set(DOMAIN_FOCUS['node_types'].values()))
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
            return "DesignPattern" 

    def _is_valid_software_design_entity(self, entity: Dict) -> bool:
        """Validate entity for software design relevance"""
        if not entity.get('name') or not entity.get('type'):
            return False
            
        entity_text = f"{entity.get('name', '')} {entity.get('description', '')}".lower()
        
        if not self._is_software_design_relevant(entity_text):
            return False
            
        valid_types = list(set(DOMAIN_FOCUS['node_types'].values()))
        if entity.get('type') not in valid_types:
            mapped_type = self._map_to_best_node_type(
                entity.get('name', ''),
                entity.get('description', ''),
                entity.get('type', '')
            )
            if mapped_type not in valid_types:
                return False
        
        return True

    def _is_valid_relationship(self, relationship: Dict, valid_entities: List[Dict]) -> bool:
        """Enhanced relationship validation"""
        source_names = {e['name'] for e in valid_entities}
        target_names = {e['name'] for e in valid_entities}
        
        # Basic validation
        if not (relationship.get('source') in source_names and 
                relationship.get('target') in target_names):
            return False
        
        # Avoid self-references
        if relationship.get('source') == relationship.get('target'):
            return False
            
        # Validate relationship type
        rel_type = relationship.get('type', '')
        if rel_type not in VALID_RELATIONSHIP_TYPES:
            relationship['type'] = 'RELATES_TO'  # Fallback
        
        # Check minimum strength
        strength = relationship.get('strength', 0.5)
        if strength < 0.3:
            return False
            
        return True

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
        self.processed_chunks_file = "processed_chunks.json"
        self.checkpoint_file = "extraction_checkpoint.json"
        self.cypher_output = "./knowledge_graph/knowledge_graph.cypher"
        
        # Relationship strengthening
        self.document_context = {}  # Track entities across chunks
        self.existing_entities = self._load_existing_entities()

    def _load_existing_entities(self) -> Set[str]:
        """Load existing entity names from Neo4j to avoid duplicates"""
        try:
            driver = GraphDatabase.driver(
                NEO4J_CONFIG['uri'],
                auth=(NEO4J_CONFIG['user'], NEO4J_CONFIG['password'])
            )
            with driver.session() as session:
                result = session.run("MATCH (n) RETURN DISTINCT n.name AS name")
                return {record["name"] for record in result if record["name"]}
        except Exception as e:
            logger.warning(f"Couldn't load existing entities: {e}")
            return set()

    def append_cypher_queries(self, queries: List[str], batch_metadata: Dict = None):
        """Enhanced query writer with relationship optimization"""
        if not queries:
            return

        try:
            file_exists = os.path.exists(self.cypher_output)
            mode = 'a' if file_exists else 'w'
            
            with open(self.cypher_output, mode, encoding='utf-8') as f:
                if not file_exists:
                    self._write_cypher_header(f)
                
                # Add batch metadata comment
                f.write(f"\n// Batch: {batch_metadata or datetime.datetime.now()}\n")
                
                # Optimized query writing
                for query in self._optimize_queries(queries):
                    if not query.strip().endswith(';'):
                        query += ';'
                    f.write(query + '\n')
                
                f.flush()
                
        except Exception as e:
            logger.error(f"Failed to save queries: {e}")

    def _write_cypher_header(self, file_handle):
        """Write schema and constraints"""
        header = [
            "// Knowledge Graph Creation Script",
            "// Generated from design documents",
            f"// Domain Focus: {', '.join(DOMAIN_FOCUS['topics'])}\n",
            "// Schema Constraints"
        ]
        
        for node_type in set(DOMAIN_FOCUS['node_types'].values()):
            header.append(f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{node_type}) REQUIRE n.name IS UNIQUE;")
        
        header.extend([
            "\n// Relationship Indexes",
            "CREATE INDEX IF NOT EXISTS FOR ()-[r:INTERACTS_WITH]-() ON r.type;",
            "CREATE INDEX IF NOT EXISTS FOR ()-[r:DEPENDS_ON]-() ON r.weight;\n"
        ])
        
        file_handle.write("\n".join(header))

    def _optimize_queries(self, queries: List[str]) -> List[str]:
        """Deduplicate and optimize Cypher queries"""
        unique_queries = list(set(queries))
        
        # Sort to create nodes before relationships
        return sorted(unique_queries, 
                    key=lambda x: ("CREATE" in x, "MERGE" in x, "SET" in x))

    def process_chunk_batch(self, extractor, chunks: List[Dict]) -> List[Dict]:
        """Enhanced batch processing with relationship strengthening"""
        try:
            # Standard extraction
            results = extractor.extract_entities_and_relationships_batch(chunks)
            
            # Document-level context tracking
            doc_id = chunks[0]['source']
            if doc_id not in self.document_context:
                self.document_context[doc_id] = {
                    'entities': set(),
                    'relationships': set()
                }
            
            # Process results
            successful_results = []
            all_queries = []
            
            for result in results:
                if result.get('extraction_success'):
                    # Strengthen relationships
                    strengthened = self._strengthen_relationships(result)
                    queries = strengthened.get('cypher_queries', [])
                    
                    all_queries.extend(queries)
                    successful_results.append(strengthened)
                    
                    # Update document context
                    self._update_document_context(doc_id, strengthened)
            
            # Immediate save for crash protection
            if all_queries:
                self.append_cypher_queries(all_queries, {
                    'document': doc_id,
                    'chunk_count': len(chunks)
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            return [extractor._create_empty_result(chunk) for chunk in chunks]

    def _strengthen_relationships(self, extraction: Dict) -> Dict:
        """Enhance relationships using domain knowledge and co-occurrence"""
        entities = extraction.get('entities', [])
        relationships = extraction.get('relationships', [])
        
        # Add implicit relationships from domain rules
        for rule in DOMAIN_FOCUS.get('relationship_rules', []):
            for e1, e2 in self._find_matching_entities(entities, rule):
                relationships.append({
                    'source': e1['name'],
                    'target': e2['name'],
                    'type': rule[1],
                    'evidence': 'Domain rule'
                })
        
        # Add co-occurrence relationships
        if len(entities) >= 2:
            relationships.extend(self._generate_co_occurrence_rels(entities))
        
        extraction['relationships'] = relationships
        extraction['cypher_queries'] = self._generate_cypher(extraction)
        
        return extraction

    def _find_matching_entities(self, entities: List[Dict], rule: tuple) -> List[tuple]:
        """Find entity pairs matching domain relationship rules"""
        source_type, rel_type, target_type = rule
        sources = [e for e in entities if e['type'] == source_type]
        targets = [e for e in entities if e['type'] == target_type]
        
        return [(s, t) for s in sources for t in targets 
                if s['name'] != t['name']]

    def _generate_co_occurrence_rels(self, entities: List[Dict]) -> List[Dict]:
        """Create relationships based on entity co-occurrence"""
        return [{
            'source': e1['name'],
            'target': e2['name'],
            'type': 'RELATED_TO',
            'weight': 0.5,  # Default weight
            'evidence': 'Co-occurrence'
        } for e1, e2 in itertools.combinations(entities, 2) 
          if e1['type'] != e2['type']]

    def _update_document_context(self, doc_id: str, extraction: Dict):
        """Track entities across chunks in the same document"""
        ctx = self.document_context[doc_id]
        ctx['entities'].update(e['name'] for e in extraction.get('entities', []))
        ctx['relationships'].update(
            (r['source'], r['type'], r['target']) 
            for r in extraction.get('relationships', [])
        )

    def load_processed_chunks(self) -> set:
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
            DocumentProcessor.save_processed_chunks(processed_chunk_ids)
            
            checkpoint_file = "extraction_checkpoint.json"
            with open(checkpoint_file, 'w') as f:
                json.dump(extractions_so_far, f, indent=2)
                
            logger.debug("Checkpoint saved")
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")

    def process_all_chunks(all_chunks, extractor, max_workers=None, max_chunks=None):
        """Process chunks with immediate saving and checkpoints"""
        
        processed_chunk_ids = DocumentProcessor.load_processed_chunks()
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
                chunk_id = DocumentProcessor.create_chunk_id(chunk)
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
                    future = executor.submit(DocumentProcessor.process_chunk_batch, extractor, batch)
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
                            newly_processed_ids.add(DocumentProcessor.create_chunk_id(chunk))
                        
                        # Save checkpoint periodically
                        if batch_count % CHECKPOINT_INTERVAL == 0:
                            all_processed = processed_chunk_ids.union(newly_processed_ids)
                            DocumentProcessor.save_checkpoint(all_processed, all_extractions)
                            
                    except Exception as e:
                        logger.error(f"Error processing batch: {e}")
                
                all_extractions[filename] = file_extractions

                if max_chunks and processed >= max_chunks:
                    break
        
        all_processed = processed_chunk_ids.union(newly_processed_ids)
        DocumentProcessor.save_processed_chunks(all_processed)
        logger.info(f"Saved {len(newly_processed_ids)} newly processed chunk IDs")
                    
        return all_extractions

    def recover_from_checkpoint():
        """Recover processing state from checkpoint files"""
        checkpoint_file = "extraction_checkpoint.json"
        
        if os.path.exists(checkpoint_file):
            try:
                with open(checkpoint_file, 'r') as f:
                    partial_extractions = json.load(f)
                
                processed_chunks = DocumentProcessor.load_processed_chunks()
                
                logger.info(f"Found checkpoint with {len(partial_extractions)} files and {len(processed_chunks)} processed chunks")
                return partial_extractions, processed_chunks
                
            except Exception as e:
                logger.error(f"Failed to recover from checkpoint: {e}")
        
        return {}, set()

    def generate_cypher_script(self, extractions: Dict[str, List[Dict]]):
        """Final script generation with schema validation"""
        queries = []
        
        # Add schema validation
        queries.extend([
            "CALL apoc.schema.assert(",
            "  {",
            "    " + ", ".join(
                f"{node_type}: ['name']"
                for node_type in set(DOMAIN_FOCUS['node_types'].values())
            ) + 
            "  },",
            "  {}",
            ");\n"
        ])
        
        # Process extractions
        for filename, chunk_extractions in extractions.items():
            for extraction in chunk_extractions:
                if extraction.get('extraction_success'):
                    queries.extend(extraction.get('cypher_queries', []))
        
        self.append_cypher_queries(queries, {'final': True})

def append_cypher_queries_immediately(queries: List[str], file_path: str):
    """Append Cypher queries to a file immediately for crash protection."""
    if not queries:
        return
    with open(file_path, 'a', encoding='utf-8') as f:
        for query in queries:
            f.write(query.strip() + "\n")

def process_documents_to_knowledge_graph(
    document_paths: List[str],
    output_dir: str = "./knowledge_graph",
    api_key: Optional[str] = None,
    neo4j_config: Optional[Dict] = None
) -> Dict:
    """
    Main function to process documents and build knowledge graph
    
    Args:
        document_paths: List of paths to documents
        output_dir: Directory to save outputs
        api_key: OpenAI API key
        neo4j_config: Neo4j connection configuration
    
    Returns:
        Dictionary with processing results and statistics
    """
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize components
    processor = DocumentProcessor()
    extractor = LLMEntityExtractor(api_key=api_key)
    
    # Process each document
    all_extractions = []
    all_cypher_queries = []
    processing_stats = {
        'documents_processed': 0,
        'chunks_created': 0,
        'entities_extracted': 0,
        'relationships_extracted': 0,
        'errors': []
    }
    
    for doc_path in document_paths:
        try:
            logger.info(f"Processing document: {doc_path}")
            
            # Process document into chunks
            chunks = processor.process_document(doc_path)
            processing_stats['chunks_created'] += len(chunks)
            
            # Create batches for extraction
            batches = extractor.create_batches(chunks)
            
            # Extract entities and relationships from each batch
            for batch in batches:
                try:
                    batch_results = extractor.extract_entities_and_relationships_batch(batch)
                    
                    for result in batch_results:
                        if result.get('extraction_success', False):
                            all_extractions.append(result)
                            all_cypher_queries.extend(result.get('cypher_queries', []))
                            
                            # Update stats
                            processing_stats['entities_extracted'] += len(result.get('entities', []))
                            processing_stats['relationships_extracted'] += len(result.get('relationships', []))
                            
                            # Save queries immediately for crash protection
                            append_cypher_queries_immediately(
                                result.get('cypher_queries', []),
                                os.path.join(output_dir, "knowledge_graph.cypher")
                            )
                
                except Exception as e:
                    error_msg = f"Batch extraction failed for {doc_path}: {e}"
                    logger.error(error_msg)
                    processing_stats['errors'].append(error_msg)
            
            processing_stats['documents_processed'] += 1
            
        except Exception as e:
            error_msg = f"Document processing failed for {doc_path}: {e}"
            logger.error(error_msg)
            processing_stats['errors'].append(error_msg)
    
    # Save all extractions to JSON
    extractions_file = os.path.join(output_dir, "extractions.json")
    try:
        with open(extractions_file, 'w', encoding='utf-8') as f:
            json.dump(all_extractions, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved extractions to {extractions_file}")
    except Exception as e:
        logger.error(f"Failed to save extractions: {e}")
        processing_stats['errors'].append(f"Failed to save extractions: {e}")
    
    # Save processing stats
    stats_file = os.path.join(output_dir, "processing_stats.json")
    try:
        processing_stats['total_tokens_used'] = extractor.total_tokens
        processing_stats['timestamp'] = datetime.datetime.now().isoformat()
        
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(processing_stats, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved processing stats to {stats_file}")
    except Exception as e:
        logger.error(f"Failed to save stats: {e}")
    
    return processing_stats


def main():
    """Main entry point for the knowledge graph builder"""
    load_dotenv()
    
    OUTPUT_DIR = "./knowledge_graph/graph_generation"
    cypher_path = os.path.join(OUTPUT_DIR, "knowledge_graph.cypher")
    
    if os.path.exists(cypher_path):
        from CypherRefiner import refine_cypher_if_exists
        print("[INFO] Cypher file exists. Enhancing it semantically without rerunning extraction...")
        refine_cypher_if_exists()
        return

    DOCUMENTS_DIR = "./knowledge_graph/resources"
    document_paths = []
    if os.path.exists(DOCUMENTS_DIR):
        for file in os.listdir(DOCUMENTS_DIR):
            if any(file.lower().endswith(ext) for ext in ['.pdf', '.txt', '.md', '.docx']):
                document_paths.append(os.path.join(DOCUMENTS_DIR, file))
    
    print(f"Found {len(document_paths)} documents to process")
    print("Run your chunking process first, then use LLMEntityExtractor for extraction.")

if __name__ == "__main__":
    main()