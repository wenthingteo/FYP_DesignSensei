# search_module/graph_search_service.py
from typing import Dict, List, Any, Tuple, Optional
import logging
import re
from neo4j import GraphDatabase 
from neo4j.graph import Node, Relationship  # Add these imports
from knowledge_graph.connection.neo4j_client import Neo4jClient 
from search_module.embedding_service import get_embedding
from prompt_engine.intent_classifier import QuestionType

logger = logging.getLogger(__name__)

# ... (keep your existing Neo4j driver initialization code) ...

class GraphSearchService:
    def __init__(self, neo4j_client: Neo4jClient):
        self.neo4j_client = neo4j_client
        self.session_histories = {} 

    # Updated search method with better debugging:
    def search(self, user_query_text: str, search_params: Dict, session_id: str) -> Dict:
        """
        Performs a graph search based on the user query and structured search parameters.
        Enhanced with better debugging and error handling.
        """
        logger.info(f"GraphSearchService: Received user_query_text='{user_query_text}', search_params={search_params}, session_id='{session_id}'")

        # Early exit for non-graph intents
        if not search_params or search_params.get('question_type') in [QuestionType.GREETING.value, QuestionType.OUT_OF_SCOPE_GENERAL.value]:
            logger.info("GraphSearchService: Intent is greeting or general out-of-scope, returning empty results.")
            return {'results': []}

        # Check Neo4j client connection
        if not self.neo4j_client or not self.neo4j_client._driver: 
            logger.error("Neo4j client or its driver not initialized. Cannot perform graph search.")
            return {'results': []}

        # Generate Embedding for the user_query_text (for semantic search)
        user_query_embedding = None
        try:
            user_query_embedding = get_embedding(user_query_text)
            if user_query_embedding is None:
                logger.warning(f"Embedding service returned None for query: '{user_query_text}'")
        except Exception as e:
            logger.error(f"Failed to generate embedding for '{user_query_text}': {e}", exc_info=True)

        # Extract parameters from search_params dictionary
        topic_labels = search_params.get('topic_filter_labels', [])
        search_depth = search_params.get('search_depth', 2)
        relationship_types = search_params.get('relationship_types', [])
        extracted_concepts = search_params.get('extracted_concepts', [])
        min_relevance_score = search_params.get('min_relevance_score', 0.7)
        keywords_from_intent = search_params.get('keywords', [])

        # Debug the query execution
        self.debug_query_execution(user_query_text, search_params)

        # Build and execute query with progressive fallback
        try:
            # Try progressively more permissive queries
            for attempt in range(3):
                if attempt == 0:
                    # Full query with all constraints
                    cypher_query, cypher_params = self._build_cypher_query(
                        user_query_text, user_query_embedding, topic_labels,
                        search_depth, relationship_types, extracted_concepts,
                        min_relevance_score, keywords_from_intent
                    )
                elif attempt == 1:
                    # Remove label constraints
                    cypher_query, cypher_params = self._build_cypher_query(
                        user_query_text, user_query_embedding, [],  # No label filtering
                        search_depth, relationship_types, extracted_concepts,
                        min_relevance_score, keywords_from_intent
                    )
                else:
                    # Simple text search only
                    cypher_query, cypher_params = self.create_simple_search_query(user_query_text)

                logger.info(f"Attempt {attempt + 1}: Executing query")
                logger.debug(f"Query: {cypher_query}")
                logger.debug(f"Params: {cypher_params}")

                raw_graph_results = self.neo4j_client.run_cypher(cypher_query, cypher_params)
                logger.info(f"Raw results count: {len(raw_graph_results)}")

                # Add debugging for raw results
                if raw_graph_results:
                    self.debug_raw_results(raw_graph_results)
                    
                    processed_results = self._process_neo4j_results(raw_graph_results, user_query_embedding)
                    logger.info(f"Processed results count: {len(processed_results)}")
                    
                    # Apply minimum relevance score filter
                    min_score = min_relevance_score if attempt == 0 else 0.3
                    final_results = [
                        res for res in processed_results 
                        if res.get('relevance_score', 0.0) >= min_score
                    ]
                    
                    logger.info(f"Final results after relevance filter (>= {min_score}): {len(final_results)}")
                    
                    if final_results:
                        logger.info(f"GraphSearchService: Retrieved {len(final_results)} results from Neo4j.")
                        return {'results': final_results}
                
                logger.warning(f"Attempt {attempt + 1} returned no results, trying next strategy...")

            logger.warning("No results found in Neo4j database")
            return {'results': []}

        except Exception as e:
            logger.error(f"Error during Cypher query execution or processing: {e}", exc_info=True)
            return {'results': []}

    def create_simple_search_query(self, user_query_text: str) -> Tuple[str, Dict]:
        """
        Create a very simple search query for fallback
        """
        query = """
        MATCH (n)
        WHERE toLower(coalesce(n.name, '')) CONTAINS toLower($searchText)
        OR toLower(coalesce(n.description, '')) CONTAINS toLower($searchText)
        RETURN n,
            CASE 
                WHEN toLower(coalesce(n.name, '')) CONTAINS toLower($searchText) THEN 0.9
                WHEN toLower(coalesce(n.description, '')) CONTAINS toLower($searchText) THEN 0.7
                ELSE 0.5 
            END AS fts_score,
            0.0 AS vec_score,
            n.embedding AS embedding,
            [] AS relationships,
            [] AS reverse_relationships
        ORDER BY fts_score DESC
        LIMIT 20
        """
        
        params = {'searchText': user_query_text}
        return query, params

    def _process_neo4j_results(self, raw_results: List[Dict], user_query_embedding: Optional[List[float]]) -> List[Dict]:
        """
        FIXED: Processes raw results from Neo4j handling both Node objects and dictionaries
        More robust processing with better error handling and debugging
        """
        processed_data = []
        
        logger.info(f"Processing {len(raw_results)} raw results...")
        
        for i, record in enumerate(raw_results):
            try:
                logger.debug(f"Processing record {i}: {record}")
                
                # Handle Neo4j Node objects vs dictionaries
                node_data_from_record = record.get("n")
                
                if node_data_from_record is None:
                    logger.warning(f"Skipping record {i} due to missing 'n' key: {record}")
                    continue
                
                # FIX: Don't skip valid Neo4j Node objects!
                # The isinstance check was wrong - Neo4j Node objects are valid
                logger.debug(f"Got node of type: {type(node_data_from_record)}")
                
                # Convert Neo4j Node object to dictionary if needed
                if hasattr(node_data_from_record, 'element_id'):  # This is a Neo4j Node object
                    # Neo4j Node object - extract properties
                    node_dict = dict(node_data_from_record)  # Get all properties
                    node_dict['__id__'] = str(node_data_from_record.element_id)
                    node_dict['__labels__'] = list(node_data_from_record.labels)
                    node_data_from_record = node_dict
                    logger.debug(f"Converted Neo4j Node to dict: {list(node_dict.keys())}")
                elif isinstance(node_data_from_record, dict):
                    # Already a dictionary - use as is
                    logger.debug(f"Using existing dict with keys: {list(node_data_from_record.keys())}")
                else:
                    logger.warning(f"Unexpected node type: {type(node_data_from_record)}")
                    # Don't skip - try to work with whatever we have
                    logger.warning(f"Attempting to process anyway: {node_data_from_record}")

                # Extract scores - with fallbacks
                fts_score = float(record.get("fts_score", 0.0))
                vec_score = float(record.get("vec_score", 0.0))
                
                logger.debug(f"Scores - FTS: {fts_score}, VEC: {vec_score}")
                
                # Handle embedding with better error handling
                node_embedding = node_data_from_record.get("embedding")
                if node_embedding and not isinstance(node_embedding, list):
                    try:
                        node_embedding = list(node_embedding) if hasattr(node_embedding, '__iter__') else None
                    except Exception as e:
                        logger.warning(f"Failed to convert embedding to list: {e}")
                        node_embedding = None

                # Calculate semantic similarity
                semantic_sim_score = 0.0
                if (user_query_embedding and isinstance(node_embedding, list) and 
                    isinstance(user_query_embedding, list) and len(user_query_embedding) == len(node_embedding)):
                    semantic_sim_score = self._cosine_similarity(user_query_embedding, node_embedding)
                    logger.debug(f"Semantic similarity: {semantic_sim_score}")
                
                # Calculate final relevance score properly
                calculated_relevance_score = (fts_score * 0.7 + semantic_sim_score * 0.3)
                
                # Get node properties with robust fallbacks
                node_name = (node_data_from_record.get("name") or 
                            node_data_from_record.get("title") or 
                            node_data_from_record.get("concept_name") or 
                            "Unknown Concept")
                
                node_description = (node_data_from_record.get("description") or 
                                node_data_from_record.get("content") or 
                                node_data_from_record.get("summary") or 
                                "No description available")
                
                # Get labels with fallback
                node_labels = node_data_from_record.get('__labels__', [])
                if not node_labels:
                    # Try to get labels from Neo4j Node object if available
                    if hasattr(node_data_from_record, 'labels'):
                        node_labels = list(node_data_from_record.labels)
                    else:
                        node_labels = ['Unknown']
                
                primary_label = node_labels[0] if node_labels else 'Unknown'
                
                # Build processed node data
                node_data = {
                    "node_id": node_data_from_record.get('__id__', f"node_{i}"),
                    "name": node_name,
                    "description": node_description,
                    "label": primary_label,
                    "relevance_score": round(calculated_relevance_score, 2),
                    "source": node_data_from_record.get("source", "Neo4j Database"),
                    "page": node_data_from_record.get("page", "N/A"),
                    "relationships": record.get("relationships", []) + record.get("reverse_relationships", [])
                }
                
                logger.debug(f"Created node data: {node_data}")
                
                # More lenient filtering - only exclude if we have no meaningful content at all
                if (node_data["name"] and 
                    node_data["name"] not in ["Unknown Concept", ""] and
                    node_data["relevance_score"] > 0):
                    processed_data.append(node_data)
                    logger.debug(f"Added node: {node_data['name']} (score: {node_data['relevance_score']})")
                else:
                    logger.warning(f"Filtered out node: name='{node_data['name']}', score={node_data['relevance_score']}")
                    
            except Exception as e:
                logger.error(f"Error processing record {i}: {record}")
                logger.error(f"Exception: {e}", exc_info=True)
                continue
        
        # Sort by relevance score
        processed_data.sort(key=lambda x: x.get('relevance_score', 0.0), reverse=True)
        
        logger.info(f"Successfully processed {len(processed_data)} nodes from {len(raw_results)} raw results")
        
        # Debug: log the first few results
        for i, node in enumerate(processed_data[:3]):
            logger.info(f"Result {i+1}: {node['name']} (score: {node['relevance_score']}, label: {node['label']})")
        
        return processed_data


    # Also add this debugging method to help identify the issue:
    def debug_raw_results(self, raw_results: List[Dict]):
        """
        Debug method to inspect what we're actually getting from Neo4j
        """
        logger.info(f"🔍 DEBUGGING RAW RESULTS ({len(raw_results)} records)")
        logger.info("=" * 50)
        
        for i, record in enumerate(raw_results[:3]):  # Just first 3 for debugging
            logger.info(f"Record {i}:")
            logger.info(f"  Type: {type(record)}")
            logger.info(f"  Keys: {list(record.keys())}")
            
            node = record.get('n')
            if node:
                logger.info(f"  Node type: {type(node)}")
                if hasattr(node, 'labels'):
                    logger.info(f"  Node labels: {list(node.labels)}")
                if hasattr(node, 'keys'):
                    logger.info(f"  Node keys: {list(node.keys())}")
                if isinstance(node, dict):
                    logger.info(f"  Node dict keys: {list(node.keys())}")
                    logger.info(f"  Node name: {node.get('name', 'N/A')}")
                    logger.info(f"  Node description: {node.get('description', 'N/A')[:100]}...")
            
            # Check scores
            logger.info(f"  FTS Score: {record.get('fts_score', 'N/A')}")
            logger.info(f"  VEC Score: {record.get('vec_score', 'N/A')}")
            logger.info("-" * 30)
    
    def _build_cypher_query(self, user_query_text: str, user_embedding: Optional[List[float]],
                            topic_labels: List[str], search_depth: int,
                            relationship_types: List[str], extracted_concepts: List[str],
                            min_relevance_score: float, keywords_from_intent: List[str]) -> Tuple[str, Dict]:
        """
        Build Cypher query with better error handling and proper scoring
        """
        logger.info(f"Building Cypher Query: user_query_text='{user_query_text}', topic_labels={topic_labels}, extracted_concepts={extracted_concepts}")
        
        params = {}
        
        # Start with base query
        query = "MATCH (n) "
        
        # Build WHERE conditions
        where_conditions = []
        
        # Add text search conditions
        if user_query_text:
            where_conditions.extend([
                "toLower(coalesce(n.name, '')) CONTAINS toLower($searchText)",
                "toLower(coalesce(n.description, '')) CONTAINS toLower($searchText)"
            ])
            params['searchText'] = user_query_text
        
        # Add concept matching
        if extracted_concepts:
            for i, concept in enumerate(extracted_concepts):
                concept_param = f'concept_{i}'
                where_conditions.extend([
                    f"toLower(coalesce(n.name, '')) CONTAINS toLower(${concept_param})",
                    f"toLower(coalesce(n.description, '')) CONTAINS toLower(${concept_param})"
                ])
                params[concept_param] = concept
        
        # Add label filtering (only if labels exist)
        if topic_labels:
            label_conditions = " OR ".join([f"'{label}' IN labels(n)" for label in topic_labels])
            where_conditions.append(f"({label_conditions})")
        
        # Add WHERE clause if we have conditions
        if where_conditions:
            query += "WHERE " + " OR ".join(where_conditions)
        
        # Add scoring logic
        query += """
        WITH n,
            CASE 
                WHEN toLower(coalesce(n.name, '')) CONTAINS toLower($searchText) THEN 0.9
                WHEN toLower(coalesce(n.description, '')) CONTAINS toLower($searchText) THEN 0.7
                ELSE 0.5 
            END AS fts_score,
            0.0 AS vec_score
        """
        
        # Add relationships
        query += """
        OPTIONAL MATCH (n)-[rel]->(target)
        OPTIONAL MATCH (n)<-[rev_rel]-(source)
        RETURN DISTINCT n, 
            fts_score, 
            vec_score, 
            n.embedding AS embedding,
            collect(DISTINCT {type: type(rel), target_node_name: target.name, target_labels: labels(target), target_id: elementId(target)}) AS relationships,
            collect(DISTINCT {type: type(rev_rel), source_node_name: source.name, source_labels: labels(source), source_id: elementId(source)}) AS reverse_relationships
        ORDER BY fts_score DESC
        LIMIT 20
        """
        
        # Ensure searchText is in params even if not used in WHERE
        if 'searchText' not in params:
            params['searchText'] = user_query_text or ""
        
        logger.debug(f"Final Query: {query}")
        logger.debug(f"Final Params: {params}")
        return query, params

    # Add this debugging method to your GraphSearchService class
    def debug_graph_contents(self):
        """
        Debug method to check what's actually in your knowledge graph
        """
        try:
            # Check total node count
            count_query = "MATCH (n) RETURN count(n) as total_nodes"
            result = self.neo4j_client.run_cypher(count_query, {})
            logger.info(f"Total nodes in graph: {result[0]['total_nodes'] if result else 0}")
            
            # Check available labels
            labels_query = "CALL db.labels() YIELD label RETURN label ORDER BY label"
            labels_result = self.neo4j_client.run_cypher(labels_query, {})
            available_labels = [r['label'] for r in labels_result]
            logger.info(f"Available labels: {available_labels}")
            
            # Check for quality-related nodes
            quality_query = """
            MATCH (n) 
            WHERE toLower(coalesce(n.name, '')) CONTAINS 'quality' 
            OR toLower(coalesce(n.description, '')) CONTAINS 'quality'
            RETURN n.name as name, labels(n) as labels, n.description as description
            LIMIT 10
            """
            quality_result = self.neo4j_client.run_cypher(quality_query, {})
            logger.info(f"Quality-related nodes found: {len(quality_result)}")
            for node in quality_result:
                logger.info(f"  - {node['name']} ({node['labels']}): {node['description'][:100]}...")
                
            # Check sample nodes
            sample_query = "MATCH (n) RETURN n.name as name, labels(n) as labels LIMIT 10"
            sample_result = self.neo4j_client.run_cypher(sample_query, {})
            logger.info("Sample nodes in graph:")
            for node in sample_result:
                logger.info(f"  - {node['name']} ({node['labels']})")
                
        except Exception as e:
            logger.error(f"Error during graph debugging: {e}")

    def search_with_fallback(self, user_query_text: str, search_params: Dict, session_id: str) -> Dict:
        """
        Enhanced search with progressive fallback strategies
        """
        logger.info(f"GraphSearchService: Received user_query_text='{user_query_text}', search_params={search_params}, session_id='{session_id}'")

        # Early exit for non-graph intents
        if not search_params or search_params.get('question_type') in [QuestionType.GREETING.value, QuestionType.OUT_OF_SCOPE_GENERAL.value]:
            logger.info("GraphSearchService: Intent is greeting or general out-of-scope, returning empty results.")
            return {'results': []}

        if not self.neo4j_client or not self.neo4j_client._driver: 
            logger.error("Neo4j client or its driver not initialized. Cannot perform graph search.")
            logger.warning("No results found in Neo4j database")
            return {'results': []}

        # Generate embedding
        user_query_embedding = None
        try:
            user_query_embedding = get_embedding(user_query_text)
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")

        # Extract parameters
        topic_labels = search_params.get('topic_filter_labels', [])
        extracted_concepts = search_params.get('extracted_concepts', [])
        min_relevance_score = search_params.get('min_relevance_score', 0.7)

        # Progressive search strategy
        search_strategies = [
            # Strategy 1: Full constraints
            {
                'use_labels': True,
                'use_concepts': True,
                'description': 'full constraints'
            },
            # Strategy 2: Remove label constraints
            {
                'use_labels': False,
                'use_concepts': True,
                'description': 'without label filtering'
            },
            # Strategy 3: Just text search
            {
                'use_labels': False,
                'use_concepts': False,
                'description': 'text search only'
            }
        ]

        for strategy in search_strategies:
            try:
                logger.info(f"Trying search strategy: {strategy['description']}")
                
                # Modify search params based on strategy
                modified_params = search_params.copy()
                if not strategy['use_labels']:
                    modified_params['topic_filter_labels'] = []
                if not strategy['use_concepts']:
                    modified_params['extracted_concepts'] = []
                
                cypher_query, cypher_params = self._build_cypher_query(
                    user_query_text,
                    user_query_embedding,
                    modified_params.get('topic_filter_labels', []),
                    modified_params.get('search_depth', 2),
                    modified_params.get('relationship_types', []),
                    modified_params.get('extracted_concepts', []),
                    min_relevance_score,
                    modified_params.get('keywords', [])
                )
                
                raw_graph_results = self.neo4j_client.run_cypher(cypher_query, cypher_params)
                processed_results = self._process_neo4j_results(raw_graph_results, user_query_embedding)
                
                if processed_results:
                    logger.info(f"Found {len(processed_results)} results with strategy: {strategy['description']}")
                    final_results = [res for res in processed_results if res.get('relevance_score', 0.0) >= 0.3]  # Lower threshold for fallback
                    return {'results': final_results}
                else:
                    logger.info(f"No results with strategy: {strategy['description']}")
                    
            except Exception as e:
                logger.error(f"Error with search strategy '{strategy['description']}': {e}")
                continue
        
        logger.warning("No results found in Neo4j database")
        return {'results': []}

    def _process_neo4j_results(self, raw_results: List[Dict], user_query_embedding: Optional[List[float]]) -> List[Dict]:
        """
        Processes raw results from Neo4j (dictionaries returned by run_cypher) into a standardized dictionary format.
        Calculates a relevance score combining FTS, vector similarity, and node properties.
        """
        processed_data = []
        for record in raw_results:
            node_data_from_record = record.get("n")
            if not node_data_from_record or not isinstance(node_data_from_record, dict):
                logger.warning(f"Skipping record due to missing or invalid 'n' key: {record}")
                continue

            fts_score = record.get("fts_score", 0.0)
            vec_score = record.get("vec_score", 0.0)
            
            node_embedding = node_data_from_record.get("embedding") # Get embedding directly from the node properties
            # Ensure node_embedding is a list, convert if it's a Neo4j Vector object or None
            if not isinstance(node_embedding, list) and node_embedding is not None:
                 node_embedding = list(node_embedding) if hasattr(node_embedding, '__iter__') else None


            semantic_sim_score = 0.0
            if user_query_embedding and isinstance(node_embedding, list) and isinstance(user_query_embedding, list):
                if len(user_query_embedding) == len(node_embedding):
                    semantic_sim_score = self._cosine_similarity(user_query_embedding, node_embedding)
                else:
                    logger.warning(f"Embedding dimension mismatch for node {node_data_from_record.get('__id__', 'N/A')}. User: {len(user_query_embedding)}, Node: {len(node_embedding) if node_embedding else 'None'})")
            
            calculated_relevance_score = record.get("relevance_score", 0.0) 
            
            node_data = {
                "node_id": node_data_from_record.get('__id__', 'N/A'),
                "name": node_data_from_record.get("name") or node_data_from_record.get("title", "Untitled Concept"), 
                "description": node_data_from_record.get("description") or node_data_from_record.get("content", ""), 
                "label": node_data_from_record.get('__labels__', ['Unknown'])[0], 
                "relevance_score": round(calculated_relevance_score, 2),
                "source": node_data_from_record.get("source", "N/A"),
                "page": node_data_from_record.get("page", "N/A"),
                "relationships": record.get("relationships", []) + record.get("reverse_relationships", []) 
            }
            processed_data.append(node_data)
        
        return sorted(processed_data, key=lambda x: x.get('relevance_score', 0.0), reverse=True)

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
            """Calculates cosine similarity between two vectors."""
            if not vec1 or not vec2:
                return 0.0
            min_len = min(len(vec1), len(vec2))
            if min_len == 0:
                return 0.0
            
            vec1_cropped = vec1[:min_len]
            vec2_cropped = vec2[:min_len]

            dot_product = sum(v1 * v2 for v1, v2 in zip(vec1_cropped, vec2_cropped))
            magnitude_vec1 = sum(v1**2 for v1 in vec1_cropped)**0.5
            magnitude_vec2 = sum(v2**2 for v2 in vec2_cropped)**0.5

            if magnitude_vec1 == 0 or magnitude_vec2 == 0:
                return 0.0
            return dot_product / (magnitude_vec1 * magnitude_vec2)

    def debug_query_execution(self, user_query_text: str, search_params: Dict):
        """Enhanced debugging with better Neo4j object handling"""
        print("🔍 DEBUGGING QUERY EXECUTION")
        print("=" * 50)
        
        topic_labels = search_params.get('topic_filter_labels', [])
        extracted_concepts = search_params.get('extracted_concepts', [])
        
        print(f"🎯 Search Parameters:")
        print(f"   - Query text: '{user_query_text}'")
        print(f"   - Topic labels: {topic_labels}")
        print(f"   - Extracted concepts: {extracted_concepts}")
        
        # Test what we actually get from Neo4j
        print(f"\n📝 Testing Neo4j result structure:")
        try:
            test_query = "MATCH (n) RETURN n LIMIT 1"
            raw_result = self.neo4j_client.run_cypher(test_query, {})
            if raw_result:
                sample = raw_result[0]
                node = sample.get('n')
                print(f"   Sample record: {sample}")
                print(f"   Node type: {type(node)}")
                if hasattr(node, 'labels'):
                    print(f"   Node labels: {list(node.labels)}")
                if hasattr(node, 'keys'):
                    print(f"   Node properties: {list(node.keys())}")
                    
        except Exception as e:
            print(f"   ❌ Test failed: {e}")

        # Test basic search
        print(f"\n📝 Testing basic text search:")
        try:
            basic_query = """
            MATCH (n)
            WHERE toLower(coalesce(n.name, '')) CONTAINS toLower($searchText)
            OR toLower(coalesce(n.description, '')) CONTAINS toLower($searchText)
            RETURN count(n) as count
            """
            result = self.neo4j_client.run_cypher(basic_query, {'searchText': user_query_text})
            count = result[0]['count'] if result else 0
            print(f"   ✅ Found {count} nodes matching '{user_query_text}'")
            
            if count > 0:
                # Get a sample
                sample_query = """
                MATCH (n)
                WHERE toLower(coalesce(n.name, '')) CONTAINS toLower($searchText)
                OR toLower(coalesce(n.description, '')) CONTAINS toLower($searchText)
                RETURN n.name as name, labels(n) as labels
                LIMIT 3
                """
                samples = self.neo4j_client.run_cypher(sample_query, {'searchText': user_query_text})
                print(f"   📋 Sample matches:")
                for sample in samples:
                    print(f"     - {sample.get('name', 'No name')} ({sample.get('labels', [])})")
                    
        except Exception as e:
            print(f"   ❌ Basic search failed: {e}")

    def test_neo4j_client_directly(self):
            """
            Test if the Neo4j client is working properly
            """
            print("🔧 TESTING NEO4J CLIENT")
            print("=" * 30)
            
            try:
                # Test 1: Simple count
                result = self.neo4j_client.run_cypher("MATCH (n) RETURN count(n) as count", {})
                print(f"✅ Neo4j client working. Total nodes: {result[0]['count'] if result else 'Error'}")
                
                # Test 2: Simple quality search
                quality_result = self.neo4j_client.run_cypher(
                    "MATCH (n) WHERE toLower(coalesce(n.name, '')) CONTAINS 'quality' RETURN n.name as name LIMIT 3", 
                    {}
                )
                print(f"✅ Quality nodes found: {len(quality_result)}")
                for node in quality_result:
                    print(f"   - {node.get('name', 'No name')}")
                    
                # Test 3: Check what the client actually returns
                raw_test = self.neo4j_client.run_cypher("MATCH (n) RETURN n LIMIT 1", {})
                if raw_test:
                    sample_node = raw_test[0]['n']
                    print(f"✅ Sample node structure: {type(sample_node)}")
                    print(f"   Properties: {list(sample_node.keys()) if hasattr(sample_node, 'keys') else 'No keys method'}")
                    if hasattr(sample_node, 'labels'):
                        print(f"   Labels: {list(sample_node.labels)}")
                    else:
                        print(f"   Labels: Not accessible")
                
            except Exception as e:
                print(f"❌ Neo4j client test failed: {e}")
                import traceback
                traceback.print_exc()

        # Quick fix method - try this if the above reveals the issue
    def create_permissive_search_query(self, user_query_text: str) -> Tuple[str, Dict]:
        """
        Create a very permissive search query that should definitely find results
        """
        query = """
        MATCH (n)
        WHERE toLower(coalesce(n.name, '')) CONTAINS toLower($searchText)
        OR toLower(coalesce(n.description, '')) CONTAINS toLower($searchText)
        OR toLower(coalesce(n.title, '')) CONTAINS toLower($searchText)
        WITH n,
            CASE 
                WHEN toLower(coalesce(n.name, '')) CONTAINS toLower($searchText) THEN 0.9
                WHEN toLower(coalesce(n.description, '')) CONTAINS toLower($searchText) THEN 0.7
                ELSE 0.5 
            END AS fts_score,
            0.0 AS vec_score
        RETURN DISTINCT n, 
            fts_score, 
            vec_score, 
            n.embedding AS embedding,
            (fts_score * 0.5 + vec_score * 0.5) AS relevance_score,
            [] AS relationships,
            [] AS reverse_relationships
        ORDER BY relevance_score DESC
        LIMIT 20
        """
        
        params = {'searchText': user_query_text}
        return query, params