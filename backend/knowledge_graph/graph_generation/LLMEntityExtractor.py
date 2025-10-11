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
from domain_config import DOMAIN_FOCUS 
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor, as_completed
from multiprocessing import cpu_count
from neo4j import GraphDatabase
from config import NEO4J_CONFIG
import signal
import sys

print("Current Working Directory:", os.getcwd())
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SOFTWARE_DESIGN_CONTEXT = {
    "core_concepts": [
        # Architecture & Design
        "architecture", "architectural", "design", "pattern", "patterns", "style", "styles",
        "component", "components", "module", "modules", "system", "systems", "service", "services",
        "layer", "layers", "tier", "tiers", "boundary", "boundaries",
        
        # Code Structure
        "class", "classes", "interface", "interfaces", "method", "methods", "function", "functions",
        "object", "objects", "entity", "entities", "model", "models", "controller", "controllers",
        "view", "views", "repository", "repositories", "factory", "factories",
        
        # Design Principles
        "principle", "principles", "responsibility", "coupling", "cohesion", "abstraction",
        "encapsulation", "inheritance", "polymorphism", "composition", "dependency", "dependencies",
        "solid", "single responsibility", "open closed", "liskov", "interface segregation",
        "dependency inversion", "dry", "kiss", "yagni",
        
        # Quality Attributes
        "maintainability", "scalability", "performance", "security", "reliability", "testability",
        "modularity", "extensibility", "reusability", "portability", "availability", "usability",
        
        # DDD Concepts
        "domain", "bounded context", "aggregate", "entity", "value object", "domain event",
        "repository", "service", "ubiquitous language", "context map",
        
        # Problems & Solutions
        "problem", "challenge", "issue", "concern", "trade-off", "complexity", "tight coupling",
        "god object", "spaghetti code", "circular dependency",
        
        # Additional concepts
        "refactoring", "testing", "implementation", "specification", "documentation",
        "framework", "frameworks", "library", "libraries", "api", "apis",
        "primitive", "composite", "leaf", "container", "hierarchy", "tree"
    ],
    
    "relationship_indicators": [
        # Problem-Solution
        "solves", "addresses", "mitigates", "fixes", "handles", "deals with", "resolves",
        
        # Principle-Pattern
        "enforces", "violates", "follows", "adheres to", "complies with", "breaks",
        "applies", "implements", "realizes",
        
        # Quality Impact
        "improves", "enhances", "degrades", "reduces", "optimizes", "sacrifices",
        "trades off", "balances", "prioritizes",
        
        # Learning
        "prerequisite", "requires understanding", "builds on", "extends", "specializes",
        "similar to", "contrasts with", "compared to", "example of",
        
        # Structural
        "contains", "part of", "composes", "aggregates", "delegates", "coordinates",
        "encapsulates", "exposes", "hides", "reveals",
        
        # Existing
        "implements", "extends", "uses", "depends", "inherits", "observes",
        "publishes", "subscribes", "manages", "controls", "creates", "builds"
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
        # Original relationships (keep these)
        ("DesignPattern", "QualityAttribute"): "SUPPORTS",
        ("DesignPattern", "DesignPrinciple"): "APPLIES",
        ("DesignPattern", "CodeStructure"): "IMPLEMENTS",
        ("CodeStructure", "DesignPattern"): "USES",
        
        # New complex relationships
        ("DesignPattern", "DesignPrinciple"): ["APPLIES", "ENFORCES", "VIOLATES"],
        ("DesignPattern", "QualityAttribute"): ["SUPPORTS", "IMPROVES", "DEGRADES", "OPTIMIZES_FOR"],
        ("DesignPattern", "Problem"): ["SOLVES", "ADDRESSES", "MITIGATES"],
        ("DesignPattern", "DesignPattern"): ["SIMILAR_TO", "CONTRASTS_WITH", "REPLACES", "EXTENDS"],
        ("CodeStructure", "DesignPrinciple"): ["VIOLATES", "ENFORCES"],
    },
    
    "principles": {
        # Original relationships (keep these)
        ("DesignPrinciple", "QualityAttribute"): "PROMOTES",
        ("DesignPrinciple", "DesignPrinciple"): "RELATES_TO",
        ("DesignPrinciple", "ArchPattern"): "GUIDES",
        
        # New complex relationships
        ("DesignPrinciple", "QualityAttribute"): ["PROMOTES", "IMPROVES", "OPTIMIZES_FOR"],
        ("DesignPrinciple", "DesignPattern"): ["GUIDES", "PREREQUISITE_FOR"],
        ("DesignPrinciple", "DesignPrinciple"): ["RELATES_TO", "BALANCES", "CONTRADICTS", "BUILDS_ON"],
        ("DesignPrinciple", "Problem"): ["ADDRESSES", "SOLVES"],
    },
    
    "architecture": {
        # Original relationships (keep these)
        ("ArchPattern", "QualityAttribute"): "ACHIEVES",
        ("ArchPattern", "DesignPattern"): "USES",
        ("ArchPattern", "CodeStructure"): "ORGANIZES",
        
        # New complex relationships
        ("ArchPattern", "QualityAttribute"): ["ACHIEVES", "IMPROVES", "DEGRADES", "TRADES_OFF", "OPTIMIZES_FOR"],
        ("ArchPattern", "DesignPrinciple"): ["APPLIES", "ENFORCES"],
        ("ArchPattern", "Problem"): ["SOLVES", "ADDRESSES"],
        ("ArchPattern", "ArchPattern"): ["SIMILAR_TO", "CONTRASTS_WITH", "EXTENDS"],
        ("CodeStructure", "ArchPattern"): ["IMPLEMENTS", "EXAMPLE_OF"],
    },
    
    "ddd_concepts": {
        # DDD-specific relationships
        ("DDDConcept", "DesignPrinciple"): ["APPLIES", "ENFORCES"],
        ("DDDConcept", "QualityAttribute"): ["IMPROVES", "SUPPORTS"],
        ("DDDConcept", "DesignPattern"): ["USES", "IMPLEMENTS"],
        ("DDDConcept", "DDDConcept"): ["COORDINATES", "CONTAINS", "PART_OF", "RELATES_TO"],
        ("DDDConcept", "ArchPattern"): ["APPLIES", "IMPLEMENTS"],
    },
    
    "quality_attributes": {
        # Quality attribute relationships
        ("QualityAttribute", "QualityAttribute"): ["TRADES_OFF", "CONFLICTS_WITH", "SUPPORTS", "BALANCES"],
        ("QualityAttribute", "DesignPattern"): ["REQUIRES", "ENABLES"],
        ("QualityAttribute", "ArchPattern"): ["REQUIRES", "GUIDES"],
    },
    
    "code_structure": {
        # Code structure relationships
        ("CodeStructure", "CodeStructure"): ["COMPOSES", "DELEGATES_TO", "COORDINATES", "ENCAPSULATES"],
        ("CodeStructure", "QualityAttribute"): ["IMPROVES", "DEGRADES"],
        ("CodeStructure", "DesignPrinciple"): ["VIOLATES", "ENFORCES", "EXAMPLE_OF"],
    },
    
    "learning_paths": {
        # Pedagogical relationships (cross-domain)
        ("DesignPrinciple", "DesignPattern"): ["PREREQUISITE_FOR"],
        ("DesignPattern", "ArchPattern"): ["PREREQUISITE_FOR", "BUILDS_ON"],
        ("DesignPrinciple", "DDDConcept"): ["GUIDES", "PREREQUISITE_FOR"],
        ("DesignPattern", "DesignPattern"): ["SIMILAR_TO", "CONTRASTS_WITH", "PREREQUISITE_FOR"],
        ("ArchPattern", "ArchPattern"): ["SIMILAR_TO", "CONTRASTS_WITH", "PREREQUISITE_FOR"],
    },
    
    "problems_solutions": {
        # Problem-solution mapping (any domain)
        ("DesignPattern", "Problem"): ["SOLVES", "ADDRESSES", "MITIGATES"],
        ("ArchPattern", "Problem"): ["SOLVES", "ADDRESSES", "MITIGATES"],
        ("DesignPrinciple", "Problem"): ["ADDRESSES", "PREVENTS"],
        ("DDDConcept", "Problem"): ["SOLVES", "ADDRESSES"],
    }
}

# Metadata for relationship types (for validation and teaching value)
RELATIONSHIP_METADATA = {
    # Problem-Solution (Teaching Value: 10)
    "SOLVES": {"teaching_value": 10, "requires_description": True, "min_strength": 0.7},
    "ADDRESSES": {"teaching_value": 8, "requires_description": True, "min_strength": 0.6},
    "MITIGATES": {"teaching_value": 7, "requires_description": True, "min_strength": 0.5},
    
    # Principle-Pattern (Teaching Value: 9-10)
    "ENFORCES": {"teaching_value": 10, "requires_description": True, "min_strength": 0.7},
    "VIOLATES": {"teaching_value": 9, "requires_description": True, "min_strength": 0.7},
    "APPLIES": {"teaching_value": 8, "requires_description": False, "min_strength": 0.6},
    
    # Quality Attributes (Teaching Value: 9-10)
    "IMPROVES": {"teaching_value": 10, "requires_description": True, "min_strength": 0.6},
    "DEGRADES": {"teaching_value": 9, "requires_description": True, "min_strength": 0.6},
    "TRADES_OFF": {"teaching_value": 10, "requires_description": True, "min_strength": 0.7, "bidirectional": True},
    "OPTIMIZES_FOR": {"teaching_value": 8, "requires_description": True, "min_strength": 0.6},
    
    # Learning (Teaching Value: 8-10)
    "PREREQUISITE_FOR": {"teaching_value": 10, "requires_description": False, "min_strength": 0.7},
    "BUILDS_ON": {"teaching_value": 9, "requires_description": False, "min_strength": 0.6},
    "SIMILAR_TO": {"teaching_value": 7, "requires_description": False, "min_strength": 0.5, "bidirectional": True},
    "CONTRASTS_WITH": {"teaching_value": 8, "requires_description": True, "min_strength": 0.6, "bidirectional": True},
    "EXAMPLE_OF": {"teaching_value": 9, "requires_description": False, "min_strength": 0.7},
    
    # Existing (Teaching Value: 5-8)
    "IMPLEMENTS": {"teaching_value": 7, "requires_description": False, "min_strength": 0.5},
    "SUPPORTS": {"teaching_value": 7, "requires_description": False, "min_strength": 0.5},
    "PROMOTES": {"teaching_value": 7, "requires_description": False, "min_strength": 0.5},
    "ACHIEVES": {"teaching_value": 7, "requires_description": False, "min_strength": 0.5},
    "GUIDES": {"teaching_value": 7, "requires_description": False, "min_strength": 0.5},
    "ORGANIZES": {"teaching_value": 6, "requires_description": False, "min_strength": 0.5},
    "USES": {"teaching_value": 6, "requires_description": False, "min_strength": 0.4},
    "REQUIRES": {"teaching_value": 7, "requires_description": False, "min_strength": 0.5},
    "DEPENDS_ON": {"teaching_value": 6, "requires_description": False, "min_strength": 0.4},
    "CONTAINS": {"teaching_value": 5, "requires_description": False, "min_strength": 0.6},
    "PART_OF": {"teaching_value": 6, "requires_description": False, "min_strength": 0.5},
    "RELATES_TO": {"teaching_value": 3, "requires_description": False, "min_strength": 0.3},
    
    # Architectural (Teaching Value: 7-8)
    "COORDINATES": {"teaching_value": 7, "requires_description": False, "min_strength": 0.5},
    "DELEGATES_TO": {"teaching_value": 7, "requires_description": False, "min_strength": 0.5},
    "ENCAPSULATES": {"teaching_value": 8, "requires_description": False, "min_strength": 0.6},
    "EXPOSES": {"teaching_value": 7, "requires_description": False, "min_strength": 0.5},
    
    # Advanced (Teaching Value: 7-9)
    "BALANCES": {"teaching_value": 8, "requires_description": True, "min_strength": 0.6},
    "CONTRADICTS": {"teaching_value": 8, "requires_description": True, "min_strength": 0.6},
    "REPLACES": {"teaching_value": 7, "requires_description": True, "min_strength": 0.6},
    "EXTENDS": {"teaching_value": 7, "requires_description": False, "min_strength": 0.5},
    "COMPOSES": {"teaching_value": 7, "requires_description": False, "min_strength": 0.5},
}

VALID_RELATIONSHIP_TYPES = {
    # Existing relationships (keep these)
    "IMPLEMENTS", "APPLIES", "SUPPORTS", "COMPOSES", "EXTENDS", 
    "REQUIRES", "CONFLICTS_WITH", "SOLVES", "RELATES_TO", "PROMOTES",
    "ENABLES", "ACHIEVES", "ORGANIZES", "GUIDES", "USES", "DEPENDS_ON",
    "CONTAINS", "PART_OF", "SIMILAR_TO", "CONTRIBUTES_TO", "HELPS_ACHIEVE",
    
    # New complex relationships for software design teaching
    "ENFORCES", "VIOLATES", "PREREQUISITE_FOR", "TRADES_OFF", 
    "IMPROVES", "DEGRADES", "BALANCES", "CONTRADICTS",
    "ADDRESSES", "MITIGATES", "INTRODUCES", "REPLACES",
    "PRECEDES", "FOLLOWS", "TRIGGERS",
    "OPTIMIZES_FOR", "DELEGATES_TO", "COORDINATES",
    "ENCAPSULATES", "EXPOSES", "COMMUNICATES_WITH",
    "ANTI_PATTERN_OF", "SMELL_OF", "SYMPTOM_OF", "ROOT_CAUSE_OF",
    "BUILDS_ON", "CONTRASTS_WITH", "EXAMPLE_OF", "SPECIALIZES",
    "GENERALIZES", "ABSTRACTS"
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

        self.valid_node_types = [
            "solide_principle", "design_patterns", "ddd", "architecture", "quality", "code_structure"
        ]
        
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
                model="gpt-4.1-nano-2025-04-14",
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
            # Force-normalize the result to a dict
            if not isinstance(result, dict):
                logger.warning(f"Unexpected LLM parse type {type(result)}. Wrapping into dict.")
                result = {"entities": [], "relationships": [], "metadata": context_chunk, "raw": str(result)}

            return [{**result, "chunk_metadata": chunk} for chunk in chunks]

        except Exception as e:
            logger.error(f"Batch extraction failed: {e}")
            return [self._create_empty_result(chunk) for chunk in chunks]
        
    def _get_enhanced_system_prompt(self) -> str:
        """Enhanced system prompt focusing on relationships and format."""
        return f"""
        You are an expert software architect specializing in extracting ENTITIES and their COMPLEX, SEMANTIC RELATIONSHIPS 
        from software design and architecture documents. Your goal is to generate a comprehensive, high-quality KNOWLEDGE GRAPH 
        dataset with a MAXIMUM VARIETY of relationship types for chatbot training.

        PRIMARY FOCUS: Extract software design concepts AND maximize the use of all valid semantic relationships.

        VALID ENTITY TYPES: {list(self.valid_node_types)}

        VALID RELATIONSHIP TYPES: {', '.join(sorted(VALID_RELATIONSHIP_TYPES))}

        CRITICAL INSTRUCTION: You MUST use the most specific relationship type possible from the list above. AVOID using "RELATES_TO" 
        unless absolutely no other type applies. Focus heavily on Causal, Evaluative, and Hierarchical relationships.

        Response format (STRICT JSON):
        {{
            "entities": [
                {{"name": "Entity Name", "type": "EntityType", "description": "...", "properties": {{"relevance_score": 0.8, "domain": "..."}}}}
            ],
            "relationships": [
                {{"source": "Source Entity Name", "target": "Target Entity Name", "type": "RELATIONSHIP_TYPE", "description": "Detailed explanation of why/how they relate", "strength": 0.9, "context": "..."}}
            ]
        }}

        CRITICAL: Focus on SOFTWARE DESIGN concepts only. Extract meaningful relationships.
        """

    def _create_enhanced_extraction_prompt(self, chunk_text: str, domains: List[str], node_types: List[str]) -> str:
        """Enhanced extraction prompt focusing on the text, context, and complex relationships."""
        if not domains:
            domains = list(DOMAIN_FOCUS['keywords'].keys())
            
        domain_context = "\n".join([f"- {d}: {', '.join(DOMAIN_FOCUS['keywords'].get(d, [])[:5])}" for d in domains])
        
        return f"""
    Extract all relevant SOFTWARE DESIGN entities AND their COMPLEX RELATIONSHIPS from the text below.

    PRIORITY DOMAINS for extraction:
    {domain_context}

    TEXT TO ANALYZE:
    \"\"\"
    {chunk_text[:3500]}
    \"\"\"

    CRITICAL EXTRACTION FOCUS:
    Focus on extracting RICH, MEANINGFUL relationships that explain:
    1. **PROBLEM-SOLUTION**: What problems do patterns/principles solve? (SOLVES, ADDRESSES)
    2. **PRINCIPLE-PATTERN**: How do patterns ENFORCE or VIOLATE principles? (ENFORCES, VIOLATES)
    3. **QUALITY IMPACTS**: How do design choices AFFECT quality attributes? (IMPROVES, DEGRADES, TRADES_OFF)
    4. **LEARNING PATHS**: What concepts are PREREQUISITES or BUILDS_ON others? (PREREQUISITE_FOR, BUILDS_ON)
    5. **TRADE-OFFS**: What qualities are sacrificed for others? (TRADES_OFF, BALANCES)

    RELATIONSHIP TYPES: (Use the MOST SPECIFIC type from the allowed list provided in your system instructions.)

    **Trade-Offs & Quality Impacts (CRITICAL for Chatbot Training):**
    - TRADES_OFF: Sacrifices one quality attribute for another. **(HIGH PRIORITY)**
    - IMPROVES: Enhances a quality attribute (e.g., Microservices IMPROVES Scalability).
    - DEGRADES: Reduces a quality attribute (e.g., Microservices DEGRADES Performance).
    - BALANCES: Attempts to balance two conflicting qualities.

    **Learning & Causal Paths (HIGH PRIORITY):**
    - PREREQUISITE_FOR, BUILDS_ON, SIMILAR_TO, CONTRASTS_WITH, EXAMPLE_OF

    **Structural:**
    - IMPLEMENTS, EXTENDS, COMPOSES, CONTAINS, REQUIRES, DEPENDS_ON, USES.

    **Architectural:**
    - COORDINATES, DELEGATES_TO, ENCAPSULATES, EXPOSES

    EXTRACTION EXAMPLES:

    Example 1 - Problem-Solution:
    - Entity: "Factory Pattern" (DesignPattern)
    - Entity: "Complex Object Creation" (Problem)
    - Relationship: "Factory Pattern" SOLVES "Complex Object Creation" 
    Description: "Encapsulates object creation logic to handle complex instantiation scenarios"

    Example 2 - Principle-Pattern:
    - Entity: "Strategy Pattern" (DesignPattern)
    - Entity: "Open/Closed Principle" (DesignPrinciple)
    - Relationship: "Strategy Pattern" ENFORCES "Open/Closed Principle"
    Description: "Allows adding new strategies without modifying existing code"

    Example 3 - Quality Trade-off:
    - Entity: "Microservices Architecture" (ArchPattern)
    - Entity: "Scalability" (QualityAttribute)
    - Entity: "Performance" (QualityAttribute)
    - Relationship: "Microservices Architecture" IMPROVES "Scalability"
    Description: "Enables independent scaling of services"
    - Relationship: "Microservices Architecture" DEGRADES "Performance"
    Description: "Network overhead from inter-service communication"

    Example 4 - Learning Path:
    - Entity: "SOLID Principles" (DesignPrinciple)
    - Entity: "Design Patterns" (Category)
    - Relationship: "SOLID Principles" PREREQUISITE_FOR "Design Patterns"
    Description: "Understanding SOLID principles is essential before learning design patterns"

    CRITICAL RULES:
    1. Extract BOTH entities AND relationships
    2. Use SPECIFIC relationship types (avoid generic RELATES_TO unless no better fit)
    3. Include detailed relationship descriptions explaining WHY/HOW
    4. Focus on teaching-valuable relationships
    5. Identify quality attribute impacts
    6. Extract learning prerequisites and sequences
    7. Capture trade-offs and contradictions

    CRITICAL RULES:
    1. **MAXIMIZE RELATIONSHIP DIVERSITY**: Use all specific types where context allows. Do not default to "RELATES_TO".
    2. Extract ALL relevant entities AND all possible semantic relationships.

    ENTITY TYPES: {', '.join(node_types) if node_types else 'DesignPattern, DesignPrinciple, ArchPattern, QualityAttribute, CodeStructure, DDDConcept'}

    Return ONLY valid JSON.
    """

    def _parse_enhanced_llm_response(self, content, context_chunk):
        """Parse the LLM response into structured entities/relationships, with JSON repair fallback."""
        try:
            # Try parsing directly
            data = json.loads(content)

        except Exception as e:
            try:
                # Attempt repair if malformed
                repaired = repair_json(content)
                data = json.loads(repaired)
                logger.warning(f"[REPAIRED] Malformed JSON fixed: {e}")
            except Exception as inner_e:
                logger.error(f"Error parsing LLM response: {inner_e}")
                # Create empty fallback result so pipeline continues
                return self._create_empty_result(context_chunk)

        # Ensure output safety
        entities = data.get("entities", []) if isinstance(data, dict) else []
        relationships = data.get("relationships", []) if isinstance(data, dict) else []

        # Optional: sanity filter (prevents None or invalid entries)
        entities = [e for e in entities if isinstance(e, dict) and e.get("name")]
        relationships = [r for r in relationships if isinstance(r, dict)]

        return {"entities": entities, "relationships": relationships}

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
        """Enhanced relationship validation with teaching value assessment"""
        source_names = {e['name'] for e in valid_entities}
        target_names = {e['name'] for e in valid_entities}
        
        # Basic validation
        if not (relationship.get('source') in source_names and 
                relationship.get('target') in target_names):
            return False
        
        # Avoid self-references
        if relationship.get('source') == relationship.get('target'):
            return False
        
        rel_type = relationship.get('type', '')
        if rel_type not in VALID_RELATIONSHIP_TYPES:
            if any(keyword in rel_type.lower() for keyword in 
                ['solve', 'enforce', 'improve', 'prerequisite', 'trade']):
                relationship['type'] = self._map_to_valid_relationship_type(rel_type)
            else:
                relationship['type'] = 'RELATES_TO'  # Fallback
        
        if rel_type in RELATIONSHIP_RULES:
            rule = RELATIONSHIP_RULES[rel_type]
            teaching_value = rule.get('teaching_value', 5)
            
            min_strength = 0.2 if teaching_value >= 8 else 0.3
        else:
            min_strength = 0.3
        
        strength = relationship.get('strength', 0.5)
        min_strength = 0.35 
        
        if relationship['type'] in ['RELATES_TO', 'USES', 'DEPENDS_ON', 'SIMILAR_TO']:
            min_strength = 0.5
            
        if strength < min_strength:
            return False
        
        complex_types = ['SOLVES', 'ENFORCES', 'TRADES_OFF', 'PREREQUISITE_FOR', 'IMPROVES', 'DEGRADES', 'CONTRASTS_WITH']
        if relationship['type'] in complex_types:
            if not relationship.get('description') or len(relationship.get('description', '')) < 15:
                return False
        
        return True

    def _map_to_valid_relationship_type(self, rel_type: str) -> str:
        """Map similar relationship types to valid ones"""
        rel_lower = rel_type.lower()
        
        mapping = {
            'solve': 'SOLVES',
            'fix': 'SOLVES',
            'address': 'ADDRESSES',
            'enforce': 'ENFORCES',
            'follow': 'ENFORCES',
            'violate': 'VIOLATES',
            'break': 'VIOLATES',
            'improve': 'IMPROVES',
            'enhance': 'IMPROVES',
            'degrade': 'DEGRADES',
            'reduce': 'DEGRADES',
            'prerequisite': 'PREREQUISITE_FOR',
            'require': 'REQUIRES',
            'tradeoff': 'TRADES_OFF',
            'sacrifice': 'TRADES_OFF',
            'build': 'BUILDS_ON',
            'extend': 'EXTENDS',
            'similar': 'SIMILAR_TO',
            'contrast': 'CONTRASTS_WITH',
            'example': 'EXAMPLE_OF'
        }
        
        for keyword, valid_type in mapping.items():
            if keyword in rel_lower:
                return valid_type
        
        return 'RELATES_TO'

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
        self.cypher_output = "./cypher_output/new_1005_knowledge_graph.cypher"
        self.entities_file = "entities.json"
        
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
        """Write schema and constraints (ENHANCED)"""
        header = [
            "// Knowledge Graph Creation Script",
            "// Generated from design documents",
            f"// Domain Focus: {', '.join(DOMAIN_FOCUS['topics'])}\n",
            "// --- Schema Constraints ---\n"
        ]
        
        # 1. UNIQUE Constraints on Entity Names (Critical for MERGE operations)
        unique_node_types = set(DOMAIN_FOCUS['node_types'].values())
        for node_type in unique_node_types:
            # Use a full constraint for efficiency with MERGE
            header.append(f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{node_type}) REQUIRE n.name IS UNIQUE;")
        
        header.extend([
            "\n// --- Property Indexes (For faster lookups) ---\n",
            
            # 2. Indexes on frequently filtered properties
            "CREATE INDEX IF NOT EXISTS FOR (n) ON (n.description);",
            "CREATE INDEX IF NOT EXISTS FOR (n) ON (n.domain);",
            "CREATE INDEX IF NOT EXISTS FOR (n) ON (n.source);",
            "CREATE INDEX IF NOT EXISTS FOR (n) ON (n.relevance_score);",
            
            "\n// --- Relationship Indexes (For fast relationship traversal) ---\n",
            
            # 3. Indexes on common relationship properties
            "CREATE INDEX IF NOT EXISTS FOR ()-[r:RELATED_TO]-() ON r.weight;",
            "CREATE INDEX IF NOT EXISTS FOR ()-[r:DEPENDS_ON]-() ON r.strength;",
            "CREATE INDEX IF NOT EXISTS FOR ()-[r:SOLVES]-() ON r.description;",
            "CREATE INDEX IF NOT EXISTS FOR ()-[r:TRADES_OFF]-() ON r.description;",
            
            "\n// --- Begin Data Insertion ---\n"
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
            
            # # Immediate save for crash protection
            # if all_queries:
            #     self.append_cypher_queries(all_queries, {
            #         'document': doc_id,
            #         'chunk_count': len(chunks)
            #     })
            
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
        """
        Load set of processed chunk IDs from disk.
        Returns an empty set if no file or if JSON is corrupted.
        """
        state_file = getattr(self, "processed_state_file", "processed_chunks.json")

        if not os.path.exists(state_file):
            logger.warning(f"No processed state file found at {state_file}, starting fresh.")
            return set()

        try:
            with open(state_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return set(data)
                elif isinstance(data, dict) and "processed" in data:
                    return set(data["processed"])
                else:
                    logger.warning(f"Unexpected format in {state_file}, resetting state.")
                    return set()
        except json.JSONDecodeError as e:
            logger.error(f"Corrupted JSON in {state_file}: {e}. Resetting state.")
            return set()
        except Exception as e:
            logger.error(f"Error loading processed chunks: {e}")
            return set()

    def save_processed_chunks(self, processed_chunk_ids: set):
        """
        Save set of processed chunk IDs to disk.
        Uses atomic write (temp file -> rename) to avoid corruption.
        """
        state_file = getattr(self, "processed_state_file", "processed_chunks.json")
        temp_file = state_file + ".tmp"

        try:
            with open("processed_chunks.json", "w", encoding="utf-8") as f:
                json.dump(list(processed_chunk_ids), f, indent=2)
            logger.info("✅ Checkpoint updated.")
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")

    
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

    def process_all_chunks(self, all_chunks, extractor, max_workers=8, batch_size=20, max_chunks=None):
        """Parallel processing with batching and checkpointing (optimized version)."""
        # Load progress
        processed_chunk_ids = self.load_processed_chunks()
        logger.info(f"Found {len(processed_chunk_ids)} already processed chunks")

        # Flatten all chunks
        chunks_to_process = []
        for source_id, chunks in all_chunks.items():
            for idx, chunk in enumerate(chunks):
                chunk_id = f"{source_id}:{idx}"
                if chunk_id not in processed_chunk_ids:
                    chunks_to_process.append((chunk_id, source_id, chunk))

        if max_chunks:
            chunks_to_process = chunks_to_process[:max_chunks]

        total = len(chunks_to_process)
        logger.info(f"Starting parallel entity extraction for {total} chunks...")

        # --- Graceful shutdown handler ---
        def handle_exit(signum, frame):
            logger.warning("⚠️ Interrupt received. Saving progress before exit...")
            self.save_processed_chunks(processed_chunk_ids)
            sys.exit(0)

        signal.signal(signal.SIGINT, handle_exit)
        signal.signal(signal.SIGTERM, handle_exit)

        # --- Parallel batch execution ---
        BATCH_SAVE_INTERVAL = 20  # ✅ checkpoint every 20 chunks
        processed_since_last_save = 0

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for i in range(0, total, batch_size):
                batch = chunks_to_process[i:i + batch_size]
                futures.append(executor.submit(self._process_batch, batch, extractor))

            for future in as_completed(futures):
                result = future.result()
                if result:
                    for chunk_id, source_id, entities in result:
                        self.save_extracted_entities(chunk_id, source_id, entities)
                        processed_chunk_ids.add(chunk_id)
                        processed_since_last_save += 1

                        # ✅ Save checkpoint every 20 processed chunks
                        if processed_since_last_save >= BATCH_SAVE_INTERVAL:
                            self.save_processed_chunks(processed_chunk_ids)
                            logger.info(f"💾 Checkpoint saved ({len(processed_chunk_ids)}/{total} chunks processed).")
                            processed_since_last_save = 0

        # Final checkpoint at the end
        self.save_processed_chunks(processed_chunk_ids)
        logger.info("✅ Finished processing all chunks.")

    def _process_batch(self, batch, extractor):
        """Handle a single batch of chunks."""
        results = []
        try:
            chunks = [chunk for _, _, chunk in batch]
            batch_entities = extractor.extract_entities_and_relationships_batch(chunks)
            for (chunk_id, source_id, chunk), entities in zip(batch, batch_entities):
                results.append((chunk_id, source_id, entities))
        except Exception as e:
            logger.error(f"Error processing batch: {e}", exc_info=True)
        return results

    def save_extracted_entities(self, chunk_id, source_id, entities):
        """Safely appends or updates entities.json without overwriting previous content."""
        try:
            # Load existing file
            if os.path.exists(self.entities_file):
                with open(self.entities_file, "r", encoding="utf-8") as f:
                    all_entities = json.load(f)
            else:
                all_entities = {}

            # Ensure structure
            if source_id not in all_entities:
                all_entities[source_id] = {}

            # Save or update
            all_entities[source_id][chunk_id] = entities

            # Write updated content back
            tmp_file = self.entities_file + ".tmp"
            with open(tmp_file, "w", encoding="utf-8") as f:
                json.dump(all_entities, f, indent=2)
            os.replace(tmp_file, self.entities_file)

        except Exception as e:
            logger.error(f"Failed to save entities for {chunk_id}: {e}", exc_info=True)

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

    def ensure_cypher_header(self):
        """Creates the output file and writes the full schema header if it doesn't exist."""
        # Ensure directory exists first
        os.makedirs(os.path.dirname(self.cypher_output), exist_ok=True)

        if not os.path.exists(self.cypher_output):
            logger.info(f"Creating new Cypher script file: {self.cypher_output}")
            try:
                with open(self.cypher_output, 'w', encoding='utf-8') as f:
                    self._write_cypher_header(f)
                return True
            except Exception as e:
                logger.error(f"Failed to write initial Cypher header: {e}")
                return False
        return False # File already exists

def append_cypher_queries_immediately(queries: List[str], file_path: str):
    """Append Cypher queries to a file immediately for crash protection."""
    if not queries:
        return
    with open(file_path, 'a', encoding='utf-8') as f:
        for query in queries:
            f.write(query.strip() + "\n")

def process_documents_to_knowledge_graph(
    document_paths: List[str],
    output_dir: str = "./cypher_output",
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
            
            chunks = []
            with open(doc_path, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        chunks.append(json.loads(line))
                    except json.JSONDecodeError:
                        logger.warning(f"Skipping bad JSON line in {doc_path}")
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
                                os.path.join(output_dir, "new_1005_knowledge_graph.cypher")
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

def load_chunked_content_from_disk(chunks_dir: str) -> Dict[str, List[Dict]]:
    """Loads all chunked JSONL files from the specified directory."""
    all_chunks = defaultdict(list)
    if not os.path.exists(chunks_dir):
        logger.error(f"Chunks directory not found: {chunks_dir}")
        return all_chunks

    for filename in os.listdir(chunks_dir):
        # We only care about the chunked JSONL files
        if filename.endswith(".jsonl"):
            file_path = os.path.join(chunks_dir, filename)
            source_id = os.path.splitext(filename)[0]  # Use the filename as the source document ID
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            chunk = json.loads(line)
                            if 'source' not in chunk:
                                chunk['source'] = source_id
                            all_chunks[source_id].append(chunk)
                        except json.JSONDecodeError as e:
                            logger.error(f"Skipping bad line in {filename}: {e}")

            except Exception as e:
                logger.error(f"Error loading chunk file {filename}: {e}")

    return dict(all_chunks)

def write_final_cypher_script(entities_file="./entities.json", output_dir="./cypher_output"):
    """
    Reads entities.json and generates unique Cypher queries directly from the 
    'entities' and 'relationships' keys, which are guaranteed to be present if 
    extraction was successful.
    """
    os.makedirs(output_dir, exist_ok=True)
    cypher_path = os.path.join(output_dir, "new_1005_knowledge_graph.cypher")
    
    if not os.path.exists(entities_file):
        print(f"[WARNING] Entities file not found: {entities_file}. Cannot generate Cypher data.")
        return

    unique_queries = set()
    
    try:
        with open(entities_file, "r", encoding="utf-8") as f:
            all_entities = json.load(f)

        for doc_id, chunk_data in all_entities.items():
            for chunk_id, extraction_result in chunk_data.items():
                
                results_to_process = []
                
                if isinstance(extraction_result, dict):
                    results_to_process.append(extraction_result)
                elif isinstance(extraction_result, list):
                    results_to_process.extend(extraction_result)
                else:
                    logger.warning(
                        f"Skipping corrupt entry for {doc_id}:{chunk_id}. Expected dict or list, got {type(extraction_result).__name__}."
                    )
                    continue 

                # Process all entities and relationships found in the result(s)
                for entry in results_to_process:
                    if not isinstance(entry, dict): continue
                    
                    # --- 1. GENERATE NODE QUERIES ---
                    for entity in entry.get("entities", []):
                        if not isinstance(entity, dict) or not entity.get("name"): continue
                        
                        # 1. Clean and prepare basic properties
                        name = entity["name"].replace('"', '\\"').replace("'", "\\'")
                        etype = entity.get("type", "Unknown")
                        
                        # 2. Extract and sanitize additional properties
                        description = entity.get('description', '').replace('"', '\\"').replace("'", "\\'")
                        domain = entity.get('properties', {}).get('domain', '').replace('"', '\\"').replace("'", "\\'")
                        relevance_score = entity.get('properties', {}).get('relevance_score', 0.5)
                        
                        # 3. Build the full SET clause
                        set_props = []
                        if description: set_props.append(f"n.description = '{description}'")
                        if domain: set_props.append(f"n.domain = '{domain}'")
                        set_props.append(f"n.relevance_score = {relevance_score}")
                        
                        # 4. Construct the MERGE ON CREATE SET query
                        if set_props:
                            query = (
                                f'MERGE (n:{etype} {{name: "{name}"}}) '
                                f'ON CREATE SET {", ".join(set_props)}'
                            )
                        else:
                            # Fallback if somehow only name exists
                            query = f'MERGE (n:{etype} {{name: "{name}"}})'
                            
                        unique_queries.add(query)

                    # --- 2. GENERATE RELATIONSHIP QUERIES ---
                    for rel in entry.get("relationships", []):
                        if not isinstance(rel, dict) or not rel.get("source") or not rel.get("target"): continue
                        
                        # 1. Clean and prepare endpoints
                        src = rel.get("source", "").replace('"', "\\\"").replace("'", "\\'")
                        tgt = rel.get("target", "").replace('"', "\\\"").replace("'", "\\'")
                        rtype = rel.get("type", "RELATES_TO")
                        
                        # 2. Extract and sanitize relationship properties
                        description = rel.get('description', '').replace('"', '\\"').replace("'", "\\'")
                        strength = rel.get('strength', 0.5)
                        context = rel.get('context', '').replace('"', '\\"').replace("'", "\\'")
                        
                        # 3. Build the full ON CREATE SET clause for the relationship
                        set_props = []
                        if description: set_props.append(f"r.description = '{description}'")
                        if context: set_props.append(f"r.context = '{context}'")
                        set_props.append(f"r.strength = {strength}")
                        
                        # 4. Construct the MATCH/MERGE ON CREATE SET query
                        query = (
                            f'MATCH (a {{name: "{src}"}}), (b {{name: "{tgt}"}}) '
                            f'MERGE (a)-[r:{rtype}]->(b)'
                        )
                        if set_props:
                            query += f' ON CREATE SET {", ".join(set_props)}'
                            
                        unique_queries.add(query)
                        
                            
        # Final writing logic (using append 'a')
        with open(cypher_path, "a", encoding="utf-8") as cypher_file:
            cypher_file.write("\n// --- Final Unique Data Insertion (Regenerated from entities.json) ---\n")
            
            # Sort the queries to put MERGE (nodes) before MATCH/MERGE (relationships)
            sorted_queries = sorted(list(unique_queries), 
                                    key=lambda x: 0 if x.startswith("MERGE (:") else 1)
            
            for query in sorted_queries:
                if not query.endswith(';'):
                    query += ';'
                cypher_file.write(query + '\n')
                            
        print(f"[INFO] ✅ Final UNIQUE Cypher script generated at: {cypher_path} ({len(unique_queries)} unique queries written).")

    except Exception as e:
        print(f"[ERROR] Failed to write final Cypher script: {e}")

def main():
    """Main entry point for the knowledge graph builder"""
    load_dotenv()
    
    CHUNKS_DIR = "./chunks"
    OUTPUT_DIR = "./cypher_output"
    cypher_path = os.path.join(OUTPUT_DIR, "new_1005_knowledge_graph.cypher")
    
    # --- 1. FAIL-SAFE EARLY EXIT CHECK ---
    if os.path.exists(cypher_path):
        refiner_available = False
        try:
            # Attempt the import and function call
            from CypherRefiner import refine_cypher_if_exists
            print("[INFO] Cypher file exists. Enhancing it semantically without rerunning extraction...")
            refine_cypher_if_exists()
            refiner_available = True
            
        except ImportError as e:
            # Handle the case where CypherRefiner.py or the function is missing
            print(f"[WARNING] Skipping refinement: Could not import refine_cypher_if_exists. Error: {e}")
            pass # Continue past the return below to skip the extraction logic
        except Exception as e:
            print(f"[ERROR] Refinement failed due to an unexpected error: {e}")
            pass # Continue past the return below to skip the extraction logic

        if refiner_available:
            return # Only exit if refinement actually ran successfully or failed gracefully

    # --- 2. SETUP AND CHUNK LOADING ---
    print(f"[INFO] Loading chunked content from: {CHUNKS_DIR}")
    
    all_chunks = load_chunked_content_from_disk(CHUNKS_DIR)
    if not all_chunks:
        print("[ERROR] No chunked JSON files found. Cannot proceed with extraction.")
        return
    
    extractor = LLMEntityExtractor()
    processor = DocumentProcessor()
    
    total_chunks = sum(len(chunks) for chunks in all_chunks.values())
    
    # --- 3. ENSURE HEADER BEFORE STARTING/SKIPPING ---
    header_written = processor.ensure_cypher_header()
    if header_written:
        print(f"✅ Constraints and indexes written to new file: {cypher_path}")

    # --- 4. RUN EXTRACTION (OR SKIP IF ALL PROCESSED) ---
    processed_chunk_ids = processor.load_processed_chunks()
    chunks_to_process = total_chunks - len(processed_chunk_ids)

    if chunks_to_process > 0:
        print(f"[INFO] Starting entity extraction for {chunks_to_process} chunks...")
        processor.process_all_chunks(all_chunks, extractor)
        print("[INFO] Incremental extraction complete.")
    else:
        print("[INFO] All chunks were previously processed. Skipping LLM extraction.")

    # --- 5. FINALIZATION / ERROR RECOVERY ---
    write_final_cypher_script("./entities.json", "./cypher_output")
    
    print("[INFO] Final Cypher script generation complete. File ready in the output directory.")

if __name__ == "__main__":
    main()