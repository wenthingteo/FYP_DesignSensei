# LLMEntityExtractor.py
import os
import json
import time
import logging
import re
from typing import Dict, List, Tuple, Optional
from openai import OpenAI
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential
from json_repair import repair_json

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMEntityExtractor:
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        # Initialize error log
        self.error_log = []

        if api_key is None:
            api_key = os.getenv("OPENAI_API_KEY")  # Get from environment if not provided
            
        if not api_key:
            raise ValueError("Missing OpenAI API key")
            
        self.client = OpenAI(
            api_key=api_key,  # Use the validated API key
            base_url=base_url or "https://api.openai.com/v1"
        )

        try:
            print(self.client.models.list())
        except Exception as e:
            print("Key validation failed:", e)
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 1.0  # Minimum seconds between requests
        
    def _rate_limit(self):
        """Simple rate limiting to avoid hitting API limits."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)
        self.last_request_time = time.time()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def extract_entities_and_relationships(self, chunk_text: str, chunk_metadata: Dict) -> Dict:
        """
        Extract entities and relationships from a text chunk.
        
        Args:
            chunk_text: The text to analyze
            chunk_metadata: Metadata about the chunk (source, id, etc.)
            
        Returns:
            Dictionary containing entities, relationships, and cypher queries
        """
        prompt = self._create_extraction_prompt(chunk_text)
        
        try:
            self._rate_limit()
            
            response = self.client.chat.completions.create(
                model="gpt-4.1-nano-2025-04-14",
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": self._create_extraction_prompt(chunk_text)}
                ],
                temperature=0.1,
                max_tokens=1500,
                timeout=30
            )
            
            content = response.choices[0].message.content
            return self._parse_llm_response(content, chunk_metadata)
            
        except Exception as e:
            logger.error(f"Error extracting from chunk {chunk_metadata.get('chunk_id', 'unknown')}: {e}")
            return self._create_empty_result(chunk_metadata)
    
    def _get_system_prompt(self) -> str:
        """System prompt for the LLM."""
        return """You are an expert in software engineering and knowledge graph construction. 
            Your task is to extract software design entities and their relationships from educational content.

            Focus on:
            - Software design principles (SOLID, DRY, KISS, etc.)
            - Design patterns (Singleton, Factory, Observer, etc.)
            - Architectural concepts (layers, components, modules, etc.)
            - Software engineering practices (testing, refactoring, etc.)
            - Programming concepts (inheritance, polymorphism, encapsulation, etc.)

            Respond in JSON format with EXACTLY this structure:
            {
                "entities": [
                    {"name": "entity_name", "type": "entity_type", "description": "brief_description"}
                ],
                "relationships": [
                    {"source": "entity1", "target": "entity2", "relationship": "relationship_type", "description": "brief_description"}
                ],
                "cypher_queries": [
                    "VALID CYPHER QUERY"
                ]
            }

            JSON RULES:
            1. Escape all double quotes inside strings with \\
            2. No trailing commas
            3. No unescaped newlines
            4. All brackets must be properly closed"""

    def _create_extraction_prompt(self, chunk_text: str) -> str:
        """Create the extraction prompt for a specific chunk."""
        return f"""
Analyze the following text about software engineering and extract:

1. **Entities**: Key concepts, principles, patterns, or practices mentioned
2. **Relationships**: How these entities connect to each other
3. **Cypher Queries**: Neo4j queries to create the knowledge graph

Entity types to focus on:
- Principle (design principles like SRP, OCP)
- Pattern (design patterns like Singleton, Factory)
- Concept (general software concepts like modularity, abstraction)
- Practice (methodologies like TDD, refactoring)
- Component (architectural elements like layers, modules)

Relationship types to use:
- IMPLEMENTS, SUPPORTS, DEPENDS_ON, IS_PART_OF, SIMILAR_TO, CONFLICTS_WITH, ENABLES

Text to analyze:
\"\"\"
{chunk_text[:2000]}
\"\"\"

Respond only with the JSON structure. Be precise and focus on software engineering concepts.

IMPORTANT: Use DOUBLE BACKSLASHES for all escaped characters (\\" becomes \\\\")
Example of valid JSON:
{{
    "entities": [
        {{"name": "SOLID", "type": "Principle", "description": "Object-oriented design principles"}}
    ],
    "relationships": [
        {{"source": "SOLID", "target": "SRP", "relationship": "CONTAINS", "description": "SRP is part of SOLID"}}
    ],
    "cypher_queries": [
        "CREATE (:Principle {{name: 'SOLID', description: 'Object-oriented design principles'}})"
    ]
}}
"""

    def _parse_llm_response(self, content: str, chunk_metadata: Dict) -> Dict:
        try:
            # Preprocess content
            content = content.strip()
            content = content.replace("\\n", "\\\\n")  # Preserve newlines in strings
            content = re.sub(r'(?<!\\)"(?!\s*[:}\]])', r'\\"', content)  # Only escape unclosed quotes
            content = re.sub(r',(\s*[}\]])', r'\1', content)  # Remove trailing commas  

            # Try multiple JSON extraction patterns
            json_str = None
            # Change patterns to:
            patterns = [
                r'```json\n?(.+?)```',  # Code blocks
                r'\{[\s\S]*\}',  # Greedy match
                r'\{(?:[^{}]|(\{.*?\}))*?\}'  # Non-recursive nested match
            ]
            
            for pattern in patterns:
                try:
                    match = re.search(pattern, content, re.DOTALL)
                    if match:
                        json_str = match.group()
                        try:
                            parsed = json.loads(json_str)
                            if all(key in parsed for key in ['entities', 'relationships', 'cypher_queries']):
                                parsed['chunk_metadata'] = chunk_metadata
                                parsed['extraction_success'] = True
                                
                                # Validate individual fields
                                for entity in parsed['entities']:
                                    if 'name' not in entity:
                                        logger.warning(f"Entity missing name in chunk {chunk_metadata.get('chunk_id')}")
                                        continue  # Skip invalid entities but keep others
                                    entity.setdefault('type', 'Concept')
                                    entity.setdefault('description', 'No description provided')

                                for rel in parsed['relationships']:
                                    if not all(key in rel for key in ['source', 'target', 'relationship']):
                                        logger.warning(f"Invalid relationship structure in chunk {chunk_metadata.get('chunk_id')}")
                                        parsed['relationships'].remove(rel)  # Remove invalid relationships
                                return parsed
                        except:
                            continue

                except re.error as e:
                    logger.warning(f"Regex error with pattern {pattern}: {str(e)}")
                    continue

            # If all patterns fail, attempt JSON repair
            try:
                repaired = repair_json(json_str)
                parsed = json.loads(repaired)
                parsed['chunk_metadata'] = chunk_metadata
                parsed['extraction_success'] = True
                return parsed
            except Exception as e:
                logger.error(f"JSON repair failed: {str(e)}")
                return self._create_empty_result(chunk_metadata)
                
        except Exception as e:
            self.error_log.append({
                'content': content,
                'error': str(e),
                'chunk_id': chunk_metadata.get('chunk_id')
            })
            logger.error(f"Saved error to log (total errors: {len(self.error_log)})")
            return self._create_empty_result(chunk_metadata)
    
    def __del__(self):
        if self.error_log:
            with open("extraction_errors.json", "w") as f:
                json.dump(self.error_log, f)
            logger.info(f"Saved {len(self.error_log)} errors to extraction_errors.json")
            
    def _create_empty_result(self, chunk_metadata: Dict) -> Dict:
        """Create an empty result structure."""
        return {
            'entities': [],
            'relationships': [],
            'cypher_queries': [],
            'chunk_metadata': chunk_metadata,
            'extraction_success': False
        }

def load_chunks_from_file(chunks_file: str) -> Dict[str, List[Dict]]:
    all_chunks = {}
    current_source = None
    current_chunks = []
    
    try:
        with open(chunks_file, 'r', encoding='utf-8-sig') as f:
            content = f.read()

            # Split into document blocks
            blocks = re.split(r'\n={80}\n', content)
            
            for block in blocks:
                # Extract source from block header
                if block.startswith('SOURCE: '):
                    source_match = re.match(r'SOURCE: (.+?)\nTOTAL CHUNKS: \d+', block)
                    if source_match:
                        current_source = source_match.group(1).strip()
                        current_chunks = []
                
                # Process chunks in subsequent blocks
                elif current_source:
                    chunks = []
                    chunk_matches = re.finditer(
                        r'--- Chunk (\d+) ---\n'
                        r'Tokens: (\d+)\n'
                        r'Type: (.+?)\n'
                        r'Text:\n(.*?)(?=\n--- Chunk|\Z)',
                        block, re.DOTALL
                    )
                    
                    for match in chunk_matches:
                        chunks.append({
                            'chunk_id': int(match.group(1)),
                            'tokens': int(match.group(2)),
                            'type': match.group(3).strip(),
                            'text': ' '.join(match.group(4).split()),
                            'source': current_source
                        })
                    
                    if chunks:
                        all_chunks[current_source] = chunks
                        current_source = None  # Reset for next document

        logger.info(f"Loaded {sum(len(c) for c in all_chunks.values())} total chunks")
        return all_chunks
        
    except Exception as e:
        logger.error(f"Error loading chunks: {str(e)}", exc_info=True)
        return {}

def process_all_chunks(all_chunks: Dict[str, List[Dict]], 
                      extractor: LLMEntityExtractor,
                      max_chunks: Optional[int] = None) -> Dict[str, List[Dict]]:
    """
    Process all chunks with the LLM extractor.
    
    Args:
        all_chunks: Dictionary of filename -> list of chunks
        extractor: LLMEntityExtractor instance
        max_chunks: Maximum number of chunks to process (for testing)
        
    Returns:
        Dictionary of filename -> list of extraction results
    """
    all_extractions = {}
    total_chunks = sum(len(chunks) for chunks in all_chunks.values())
    
    if max_chunks:
        total_chunks = min(total_chunks, max_chunks)
    
    processed = 0
    
    logger.info(f"Starting extraction for {total_chunks} chunks...")
    
    for filename, chunks in all_chunks.items():
        if max_chunks and processed >= max_chunks:
            break
            
        logger.info(f"Processing chunks from {filename}")
        extractions = []
        
        for chunk in chunks:
            if max_chunks and processed >= max_chunks:
                break
                
            processed += 1
            logger.info(f"Processing chunk {processed}/{total_chunks}")
            
            extraction_result = extractor.extract_entities_and_relationships(
                chunk['text'], 
                chunk
            )
            extractions.append(extraction_result)
        
        all_extractions[filename] = extractions
        # After chunk extraction
        logger.debug(f"Sample chunk text: {chunks[0]['text'][:200]}..." if chunks else "No text extracted")

    return all_extractions

def save_extractions(all_extractions: Dict[str, List[Dict]], 
                    output_file: str = "knowledge_graph_extractions.json"):
    """Save all extractions to a JSON file."""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_extractions, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Extractions saved to: {output_file}")

def generate_cypher_script(all_extractions: Dict[str, List[Dict]], 
                          output_file: str = "knowledge_graph.cypher"):
    """Generate a consolidated Cypher script for Neo4j."""
    all_cypher_queries = []
    
    # Add constraint queries first
    constraints = [
        "CREATE CONSTRAINT entity_name IF NOT EXISTS FOR (n:Entity) REQUIRE n.name IS UNIQUE;",
        "CREATE CONSTRAINT principle_name IF NOT EXISTS FOR (n:Principle) REQUIRE n.name IS UNIQUE;",
        "CREATE CONSTRAINT pattern_name IF NOT EXISTS FOR (n:Pattern) REQUIRE n.name IS UNIQUE;",
        "CREATE CONSTRAINT concept_name IF NOT EXISTS FOR (n:Concept) REQUIRE n.name IS UNIQUE;",
        "CREATE CONSTRAINT practice_name IF NOT EXISTS FOR (n:Practice) REQUIRE n.name IS UNIQUE;",
        "CREATE CONSTRAINT component_name IF NOT EXISTS FOR (n:Component) REQUIRE n.name IS UNIQUE;"
    ]
    all_cypher_queries.extend(constraints)
    
    # Collect all Cypher queries from extractions
    query_count = 0
    for filename, extractions in all_extractions.items():
        all_cypher_queries.append(f"\n// Queries from {filename}")
        
        for extraction in extractions:
            if extraction.get('extraction_success', False):
                cypher_queries = extraction.get('cypher_queries', [])
                if cypher_queries:
                    all_cypher_queries.extend(cypher_queries)
                    query_count += len(cypher_queries)
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("// Knowledge Graph Creation Script\n")
        f.write("// Generated from software design documents\n")
        f.write(f"// Total queries: {query_count}\n\n")
        f.write("\n".join(all_cypher_queries))
    
    logger.info(f"Cypher script saved to: {output_file} with {query_count} queries")

def print_extraction_summary(all_extractions: Dict[str, List[Dict]]):
    """Print a summary of the extraction results."""
    total_extractions = sum(len(extractions) for extractions in all_extractions.values())
    successful_extractions = sum(
        sum(1 for extraction in extractions if extraction.get('extraction_success', False))
        for extractions in all_extractions.values()
    )
    
    total_entities = sum(
        sum(len(extraction.get('entities', [])) for extraction in extractions)
        for extractions in all_extractions.values()
    )
    
    total_relationships = sum(
        sum(len(extraction.get('relationships', [])) for extraction in extractions)
        for extractions in all_extractions.values()
    )
    
    total_cypher_queries = sum(
        sum(len(extraction.get('cypher_queries', [])) for extraction in extractions)
        for extractions in all_extractions.values()
    )
    
    print("\n" + "="*50)
    print("EXTRACTION SUMMARY")
    print("="*50)
    print(f"Total chunks processed: {total_extractions}")
    print(f"Successful extractions: {successful_extractions}")
    print(f"Success rate: {successful_extractions/total_extractions*100:.1f}%")
    print(f"Total entities extracted: {total_entities}")
    print(f"Total relationships extracted: {total_relationships}")
    print(f"Total Cypher queries generated: {total_cypher_queries}")
    print("="*50)
if __name__ == "__main__":
    load_dotenv(override=True)
    try:
        # Get absolute path to chunks file
        chunks_path = os.path.abspath(os.path.join("knowledge_graph", "chunks_output.txt"))
        print(f"Loading chunks from: {chunks_path}")
        
        # Add file existence check
        if not os.path.exists(chunks_path):
            print(f"Error: File not found at {chunks_path}")
            exit(1)

        # Load chunks with debug info
        all_chunks = load_chunks_from_file(chunks_path)
        
        if not all_chunks:
            print("No chunks found! Check:")
            print(f"1. File exists: {chunks_path}")
            print("2. File format matches the sample")
            exit(1)
        
        print(f"Loaded {sum(len(chunks) for chunks in all_chunks.values())} chunks from {len(all_chunks)} files")
        
        print("Creating LLM extractor...")
        print(f"Using API Key: {os.getenv('OPENAI_API_KEY')[:8]}...{os.getenv('OPENAI_API_KEY')[-4:]}")  # Show first/last chars
        extractor = LLMEntityExtractor()
        
        # Fix API connection test
        print("Testing API connection...")
        test_response = extractor.client.chat.completions.create(
            model="gpt-4.1-nano-2025-04-14",
            messages=[{"role": "user", "content": "Connection test"}],
            max_tokens=5
        )
        print("API connection successful!")
        
        # Process chunks
        print("Processing chunks (limited to 5 for testing)...")
        all_extractions = process_all_chunks(all_chunks, extractor, max_chunks=5)

        # Save results
        save_extractions(all_extractions)
        generate_cypher_script(all_extractions)
        print_extraction_summary(all_extractions)
        
        print("\nFiles generated:")
        print("- knowledge_graph_extractions.json (raw extractions)")
        print("- knowledge_graph.cypher (Neo4j script)")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

def generate_cypher_script(all_extractions: Dict[str, List[Dict]], 
    output_file: str = "knowledge_graph.cypher"):
    """
    Generate a Cypher script to import the extracted entities and relationships into Neo4j.

    Args:
        all_extractions: Dictionary of filename -> list of extraction results
        output_file: Path to the output .cypher file
    """
    try:
        cypher_lines = []

        for file_results in all_extractions.values():
            for result in file_results:
                if result.get("extraction_success", False):
                    cypher_lines.extend(result.get("cypher_queries", []))
        
        # Remove duplicates
        cypher_lines = list(dict.fromkeys(cypher_lines))

        with open(output_file, "w", encoding="utf-8") as f:
            for line in cypher_lines:
                f.write(line.strip() + "\n")

        logger.info(f"Cypher script saved to: {output_file}")
        # # Try reading with different encoding
        # with open(output_file, 'r', encoding='utf-8-sig') as f:
        #     for line in cypher_lines:
        #         f.write(line.strip() + "\n")
        
        # logger.info(f"Cypher script saved to: {output_file}")
        
    except Exception as e:
        logger.error(f"Error generating Cypher script: {e}")

if __name__ == "__main__":
    chunks = load_chunks_from_file("knowledge_graph/chunks_output.txt")
    extractor = LLMEntityExtractor()
    all_extractions = process_all_chunks(chunks, extractor, max_chunks=20)  # Adjust max_chunks as needed
    sample_error_response = '''
    {
        "entities": [
            {"name": "SOLID", "type": "Principle", "description": "OOP design principles}
        ],
        relationships: [
            {source: "SOLID", target: "SRP", relationship: "CONTAINS"}
        ],
        "cypher_queries": [
            "CREATE (:Principle {name: 'SOLID'})"
        ]
    }
    '''
    extractor._parse_llm_response(sample_error_response, {})
    save_extractions(all_extractions, "knowledge_graph_extractions.json")
    generate_cypher_script(all_extractions, "knowledge_graph.cypher")
