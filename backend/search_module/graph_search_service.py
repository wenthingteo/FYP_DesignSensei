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
                WHEN toLower(coalesce(n.description, '')) CONTAINS toLower($searchText) THEN 0.6
                ELSE 0.5 
            END AS fts_score,
            0.0 AS vec_score,
            n.embedding AS embedding,
            [] AS relationships,
            [] AS reverse_relationships
        ORDER BY fts_score DESC
        """
        
        params = {'searchText': user_query_text}
        return query, params

    def _process_neo4j_results(self, raw_results: List[Dict], user_query_embedding: Optional[List[float]]) -> List[Dict]:
        """
        Process Neo4j results - calculate vector similarity here in Python
        """
        processed_data = []
        
        for i, record in enumerate(raw_results):
            try:
                node_data = record.get("n")
                if not node_data:
                    continue
                
                # Handle Neo4j Node objects
                if hasattr(node_data, 'element_id'):
                    node_dict = dict(node_data)
                    node_dict['__id__'] = str(node_data.element_id)
                    node_dict['__labels__'] = list(node_data.labels)
                    node_data = node_dict
                
                # Get FTS score from Neo4j
                fts_score = float(record.get("fts_score", 0.0))
                
                # Calculate vector similarity in Python
                semantic_sim_score = 0.0
                node_embedding = node_data.get("embedding")
                
                if (user_query_embedding and isinstance(node_embedding, list) and 
                    len(user_query_embedding) == len(node_embedding)):
                    semantic_sim_score = self._cosine_similarity(user_query_embedding, node_embedding)
                    logger.debug(f"Calculated semantic similarity: {semantic_sim_score}")
                
                # Combine scores (no misleading vec_score from Neo4j)
                final_relevance_score = (fts_score * 0.7 + semantic_sim_score * 0.3)
                
                # Build result
                node_result = {
                    "name": node_data.get("name", "Unknown"),
                    "description": node_data.get("description", "No description"),
                    "fts_score": round(fts_score, 3),
                    "semantic_score": round(semantic_sim_score, 3),  # Clear naming
                    "relevance_score": round(final_relevance_score, 3),
                    "relationships": record.get("relationships", [])
                }
                
                processed_data.append(node_result)
                
            except Exception as e:
                logger.error(f"Error processing record {i}: {e}")
                continue
        
        return sorted(processed_data, key=lambda x: x['relevance_score'], reverse=True)


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
        Build Cypher query - FTS scoring in Neo4j, vector similarity in Python
        """
        logger.info(f"Building Cypher Query: user_query_text='{user_query_text}', topic_labels={topic_labels}")
        
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
        
        # Add label filtering
        if topic_labels:
            label_conditions = " OR ".join([f"'{label}' IN labels(n)" for label in topic_labels])
            where_conditions.append(f"({label_conditions})")
        
        # Add WHERE clause if we have conditions
        if where_conditions:
            query += "WHERE " + " OR ".join(where_conditions)
        
        # Add FTS scoring (no misleading vec_score)
        query += """
        WITH n,
            CASE 
                WHEN toLower(coalesce(n.name, '')) CONTAINS toLower($searchText) THEN 0.9
                WHEN toLower(coalesce(n.description, '')) CONTAINS toLower($searchText) THEN 0.6
                ELSE 0.5 
            END AS fts_score
        """
        
        # Add relationships and return
        query += """
        OPTIONAL MATCH (n)-[rel]->(target)
        OPTIONAL MATCH (n)<-[rev_rel]-(source)
        RETURN DISTINCT n, 
            fts_score, 
            n.embedding AS embedding,
            collect(DISTINCT {type: type(rel), target_node_name: target.name}) AS relationships,
            collect(DISTINCT {type: type(rev_rel), source_node_name: source.name}) AS reverse_relationships
        ORDER BY fts_score DESC
        """
        
        # Ensure searchText is in params
        if 'searchText' not in params:
            params['searchText'] = user_query_text or ""
        
        return query, params


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
                WHEN toLower(coalesce(n.description, '')) CONTAINS toLower($searchText) THEN 0.6
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
        """
        
        params = {'searchText': user_query_text}
        return query, params