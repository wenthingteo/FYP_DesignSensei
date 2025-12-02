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
                    min_score = 0.35
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
        OR toLower(coalesce(n.domain, '')) CONTAINS toLower($searchText)
        RETURN n,
            CASE 
                WHEN toLower(coalesce(n.name, '')) CONTAINS toLower($searchText) THEN 0.9
                WHEN toLower(coalesce(n.domain, '')) CONTAINS toLower($searchText) THEN 0.8
                WHEN toLower(coalesce(n.description, '')) CONTAINS toLower($searchText) THEN 0.7
                ELSE 0.6
            END AS fts_score,
            0.0 AS vec_score,
            n.embedding AS embedding,
            [] AS relationships,
            [] AS reverse_relationships
        ORDER BY fts_score DESC
        """
        
        params = {'searchText': user_query_text}
        return query, params

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
        Build Cypher query with cleaned + fuzzy search support
        """
        logger.info(f"Building Cypher Query: user_query_text='{user_query_text}', topic_labels={topic_labels}")

        params = {}
        query = "MATCH (n) "
        where_conditions = []

        # ✅ 1. Clean punctuation and lowercase
        cleaned_text = re.sub(r"[^a-zA-Z0-9\s]", "", user_query_text).strip().lower()

        # ✅ 2. Split into words for flexible matching
        words = [w for w in cleaned_text.split() if w]

        # ✅ 3. Build flexible OR conditions
        for i, word in enumerate(words):
            param_name = f"word_{i}"
            where_conditions.append(
                f"(toLower(coalesce(n.name, '')) CONTAINS ${param_name} "
                f"OR toLower(coalesce(n.description, '')) CONTAINS ${param_name} "
                f"OR toLower(coalesce(n.domain, '')) CONTAINS ${param_name})"
            )
            params[param_name] = word

        # ✅ Combine conditions with OR
        if where_conditions:
            query += "WHERE " + " OR ".join(where_conditions)

        # ✅ Keep your FTS + relationship logic
        query += f"""
            WITH n,
                CASE 
                    WHEN toLower(coalesce(n.name, '')) CONTAINS '{cleaned_text}' THEN 1.0
                    WHEN toLower(coalesce(n.domain, '')) CONTAINS '{cleaned_text}' THEN 0.9
                    WHEN toLower(coalesce(n.description, '')) CONTAINS '{cleaned_text}' THEN 0.7
                    ELSE 0.5
                END AS fts_score
            WHERE n.embedding IS NOT NULL

            OPTIONAL MATCH path=(n)-[:RELATED_TO*1..{search_depth}]-(m)
            WITH n, collect(DISTINCT m.name) AS neighbors, fts_score
            RETURN DISTINCT n, fts_score, n.embedding AS node_embedding, neighbors
            ORDER BY fts_score DESC
            LIMIT 100
        """

        return query, params

    def _process_neo4j_results(self, raw_results: List[Dict], user_query_embedding: Optional[List[float]]) -> List[Dict]:
        """
        Clean + stable scoring for GraphRAG.
        - Normalized FTS
        - Normalized semantic similarity
        - Combined final relevance score
        """
        processed = []

        for record in raw_results:
            try:
                node = record.get("n")
                if not node:
                    continue

                # Convert Neo4j node object into dict
                if hasattr(node, "element_id"):
                    node_dict = dict(node)
                    node_dict["__labels__"] = list(node.labels)
                else:
                    node_dict = node

                # -----------------------------
                # Extract partial scores
                # -----------------------------
                fts = float(record.get("fts_score", 0.0))
                node_embedding = record.get("node_embedding")

                # Normalize FTS to 0–1
                # your current FTS is between 0.5 and 1.0
                fts_norm = (fts - 0.5) / (1.0 - 0.5)
                fts_norm = max(0.0, min(fts_norm, 1.0))

                # Compute semantic similarity
                semantic = 0.0
                if user_query_embedding and isinstance(node_embedding, list):
                    try:
                        semantic = self._cosine_similarity(user_query_embedding, node_embedding)
                    except:
                        semantic = 0.0

                # Normalize semantic 0–1 (cosine range = -1 → 1)
                semantic_norm = (semantic + 1.0) / 2.0

                # -----------------------------
                # Final Combined Score
                # -----------------------------
                combined_score = (0.6 * fts_norm) + (0.4 * semantic_norm)

                processed.append({
                    "name": node_dict.get("name", "Unknown"),
                    "description": node_dict.get("description", "No description"),
                    "domain": node_dict.get("domain", ""),
                    "labels": node_dict.get("__labels__", []),
                    "fts_score": round(fts, 3),
                    "semantic_score": round(semantic, 3),
                    "relevance_score": round(combined_score, 3),
                })

            except Exception as e:
                logger.error(f"Error processing result: {e}")

        # Sort highest first
        processed.sort(key=lambda x: x["relevance_score"], reverse=True)

        # Remove extremely low-confidence results
        return [p for p in processed if p["relevance_score"] >= 0.35]

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
                # print(f"   Sample record: {sample}")
                # print(f"   Node type: {type(node)}")
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
            OR toLower(coalesce(n.domain, '')) CONTAINS toLower($searchText)
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
                OR toLower(coalesce(n.domain, '')) CONTAINS toLower($searchText)
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
            OR toLower(coalesce(n.domain, '')) CONTAINS toLower($searchText)
        WITH n,
            CASE 
                WHEN toLower(coalesce(n.name, '')) CONTAINS toLower($searchText)
                    THEN 1.0 - abs(size(n.name) - size($searchText)) * 0.01
                WHEN toLower(coalesce(n.domain, '')) CONTAINS toLower($searchText)
                    THEN 0.9 - abs(size(n.domain) - size($searchText)) * 0.01
                WHEN toLower(coalesce(n.description, '')) CONTAINS toLower($searchText)
                    THEN 0.6
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
    
    # add vector similarity,  on 21/10/2025
    def build_search_query_with_embeddings(self, user_query_text, query_embedding, topic_labels=None, concepts=None):
        """
        Build Cypher query that combines:
        1. Full-text search (FTS)
        2. Vector similarity using embeddings
        """
        
        # Base WHERE clause
        where_conditions = []
        
        # Text matching conditions
        text_conditions = [
            "toLower(coalesce(n.name, '')) CONTAINS toLower($searchText)",
            "toLower(coalesce(n.description, '')) CONTAINS toLower($searchText)"
        ]
        
        # Add concept matching
        if concepts:
            for i, concept in enumerate(concepts):
                text_conditions.append(f"toLower(coalesce(n.name, '')) CONTAINS toLower($concept_{i})")
                text_conditions.append(f"toLower(coalesce(n.description, '')) CONTAINS toLower($concept_{i})")
        
        where_conditions.append(f"({' OR '.join(text_conditions)})")
        
        # Add label filter if provided
        if topic_labels:
            label_conditions = " OR ".join([f"'{label}' IN labels(n)" for label in topic_labels])
            where_conditions.append(f"({label_conditions})")
        
        where_clause = " OR ".join(where_conditions)
        
        # Build complete query with vector similarity
        query = f"""
        MATCH (n)
        WHERE {where_clause}
        
        // Calculate FTS score (text matching)
        WITH n,
            CASE 
                WHEN toLower(coalesce(n.name, '')) CONTAINS toLower($searchText) THEN 0.9
                WHEN toLower(coalesce(n.domain, '')) CONTAINS toLower($concept_0) THEN 0.8
                WHEN toLower(coalesce(n.description, '')) CONTAINS toLower($searchText) THEN 0.7
                ELSE 0.6
            END AS fts_score
        
        // Calculate vector similarity score (if embedding exists)
        WITH n, fts_score,
            CASE 
                WHEN n.embedding IS NOT NULL AND $query_embedding IS NOT NULL THEN
                    gds.similarity.cosine(n.embedding, $query_embedding)
                ELSE 0.0
            END AS vector_score
        
        // Combine scores: 40% FTS + 60% Vector
        WITH n, fts_score, vector_score,
            (fts_score * 0.4 + vector_score * 0.6) AS combined_score
        
        // Filter by minimum score
        WHERE combined_score >= $min_score
        
        // Get relationships
        OPTIONAL MATCH (n)-[rel]->(target)
        OPTIONAL MATCH (n)<-[rev_rel]-(source)
        
        RETURN DISTINCT n, 
            combined_score AS relevance_score,
            fts_score,
            vector_score,
            collect(DISTINCT {{type: type(rel), target_node_name: target.name}}) AS relationships,
            collect(DISTINCT {{type: type(rev_rel), source_node_name: source.name}}) AS reverse_relationships
        ORDER BY combined_score DESC
        LIMIT 50
        """
        
        return query


    # Example usage in your GraphSearchService
    def search_graph(self, user_query_text, search_params):
        """
        Execute graph search with embeddings
        """
        # Generate query embedding
        query_embedding = self.generate_embedding(user_query_text)
        
        # Extract parameters
        topic_labels = search_params.get('topic_filter_labels', [])
        extracted_concepts = search_params.get('extracted_concepts', [])
        min_score = search_params.get('min_relevance_score', 0.5)
        
        # Build query
        query = self.build_search_query_with_embeddings(
            user_query_text=user_query_text,
            query_embedding=query_embedding,
            topic_labels=topic_labels,
            extracted_concepts=extracted_concepts
        )
        
        # Prepare parameters
        params = {
            'searchText': user_query_text,
            'query_embedding': query_embedding,  # ← ADD THIS!
            'min_score': min_score
        }
        
        # Add concept parameters
        if extracted_concepts:
            for i, concept in enumerate(extracted_concepts):
                params[f'concept_{i}'] = concept
        
        # Execute query
        with self.neo4j_client.driver.session() as session:
            result = session.run(query, params)
            records = list(result)
        
        return records


    def generate_embedding(self, text):
        """
        Generate embedding for query text
        """
        from openai import OpenAI
        
        client = OpenAI(api_key="your_api_key")
        
        response = client.embeddings.create(
            input=text,
            model="text-embedding-3-small"
        )
        
        return response.data[0].embedding