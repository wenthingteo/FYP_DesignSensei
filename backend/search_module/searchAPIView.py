# --- App Setup: search_app/urls.py ---
# This file defines the URL routing specifically for your 'search_app'.
# Assumes myproject/urls.py includes this app's URLs, e.g., path('api/', include('search_app.urls')).

from django.urls import path
from .views import SearchAPIView

urlpatterns = [
    path('search/', SearchAPIView.as_view(), name='search-api'),
]


# --- App Logic: search_app/views.py ---
# This file contains the core logic for your search module, integrating NLP and graph interaction.

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import spacy
from collections import deque # For context-aware search history
# from neo4j import GraphDatabase # Uncomment when integrating with Neo4j
# from your_embedding_service import get_gpt_4_1_nano_embedding # Placeholder for your actual embedding service

# Load spaCy model once when the application starts
# Make sure to run: python -m spacy download en_core_web_sm
try:
    nlp = spacy.load("en_core_web_sm")
    print("spaCy model 'en_core_web_sm' loaded successfully.")
except OSError:
    print("spaCy model 'en_core_web_sm' not found. Please run 'python -m spacy download en_core_web_sm'")
    nlp = None # Handle cases where NLP model is not available

# Global variable to simulate session context for demonstration purposes
# In a real application, this would be managed per-user session (e.g., in a database, Redis cache, or Django session)
# Using a deque to limit history size for context-aware search
session_histories = {} # {session_id: deque(['query1', 'query2'])}

# Neo4j Driver (placeholder)可以看env文件中配置
# NEO4J_URI = "bolt://localhost:7687"
# NEO4J_USERNAME = "neo4j"
# NEO4J_PASSWORD = "password"
# try:
#     neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
#     neo4j_driver.verify_connectivity()
#     print("Successfully connected to Neo4j.")
# except Exception as e:
#     print(f"Failed to connect to Neo4j: {e}")
#     neo4j_driver = None

class SearchAPIView(APIView):
    """
    API endpoint for handling natural language search queries against the knowledge graph.
    """

    def post(self, request, *args, **kwargs):
        """
        Processes a user query and returns relevant knowledge graph results.
        """
        user_query = request.data.get('user_query')
        # Expect session_id from frontend for context-aware search
        session_id = request.data.get('session_id', 'default_session')

        if not user_query:
            return Response({"error": "No user query provided."}, status=status.HTTP_400_BAD_REQUEST)

        # Initialize or retrieve session history for the given session_id
        if session_id not in session_histories:
            session_histories[session_id] = deque(maxlen=5) # Keep last 5 queries to maintain context

        # 1. Tokenization and Normalization Processes
        # Convert user input into a normalized form for processing.
        processed_query_tokens = self._process_query_nlp(user_query)
        # Also generate embedding for the original user query for semantic similarity
        user_query_embedding = self._get_embedding(user_query)

        # 2. Context-Aware Search: Consider previous interactions.
        # Combine the current query with the recent history to enrich the search.
        full_context_query_text = self._build_contextual_query(user_query, session_id)
        session_histories[session_id].append(user_query) # Add current query to history after processing

        # 3. Query Expansion: Broaden the search coverage.
        # This can involve synonyms, hyponyms, or related concepts.
        expanded_queries_texts = self._expand_query(full_context_query_text)

        # 4. Semantic Similarity Measures: Match queries to graph concepts using embeddings.
        # Convert expanded queries into parameters suitable for graph traversal.
        graph_search_parameters = self._convert_to_graph_params(
            expanded_queries_texts, user_query_embedding
        )

        # 5. Mechanisms for handling ambiguous queries.
        # Refine query parameters if there are multiple possible interpretations.
        resolved_params = self._handle_ambiguity(graph_search_parameters)

        # 6. Efficient Graph Traversal Mechanisms: Interact with Neo4j.
        # Execute Cypher queries to find relevant knowledge based on resolved parameters.
        raw_graph_results = self._traverse_graph(resolved_params, user_query_embedding)

        # 7. Implement relevance ranking algorithms for search results.
        # Rank the retrieved graph results based on their relevance to the original query.
        ranked_results = self._rank_results(raw_graph_results, user_query, user_query_embedding)

        # 8. Format search results appropriately for the prompt engineering module.
        # Prepare the final output for consumption by the chatbot's prompt engineering component.
        formatted_results = self._format_results(ranked_results)

        return Response({"query": user_query, "results": formatted_results}, status=status.HTTP_200_OK)

    def _process_query_nlp(self, query):
        """
        Performs tokenization, lemmatization, and removes stop words using spaCy.
        Returns a list of processed tokens (lemmas).
        """
        if nlp is None:
            # Fallback for when spaCy model is not loaded
            return query.lower().split()

        doc = nlp(query.lower())
        processed_tokens = [
            token.lemma_ for token in doc if not token.is_stop and not token.is_punct and not token.is_space
        ]
        print(f"Processed tokens for '{query}': {processed_tokens}")
        return processed_tokens

    def _get_embedding(self, text):
        """
        Placeholder for generating embeddings using gpt-4.1-nano.
        In a real implementation, this would call your embedding service.
        """
        # Example: Replace with actual API call to gpt-4.1-nano embedding service
        # try:
        #     embedding = get_gpt_4_1_nano_embedding(text)
        #     return embedding
        # except Exception as e:
        #     print(f"Error getting embedding for '{text}': {e}")
        #     return None # Handle error appropriately

        # Simulate a generic embedding (list of floats) for demonstration
        # In reality, embeddings are high-dimensional vectors (e.g., 1536 for OpenAI)
        import hashlib
        import struct
        # Create a simple, repeatable "embedding" from the text for simulation
        hash_object = hashlib.sha256(text.encode())
        hex_dig = hash_object.hexdigest()
        # Take first few bytes and convert to floats for a simple vector
        simulated_embedding = [float(c) / 255.0 for c in hex_dig[:16].encode()] # Simple simulation
        print(f"Simulated embedding for '{text}': {simulated_embedding[:5]}...") # Print first 5 for brevity
        return simulated_embedding

    def _cosine_similarity(self, vec1, vec2):
        """
        Calculates cosine similarity between two vectors.
        Assumes vectors are non-empty and of same dimension.
        """
        if not vec1 or not vec2:
            return 0.0
        # Ensure same dimension, pad with zeros if not (though ideally they should be same)
        min_len = min(len(vec1), len(vec2))
        vec1_cropped = vec1[:min_len]
        vec2_cropped = vec2[:min_len]

        dot_product = sum(v1 * v2 for v1, v2 in zip(vec1_cropped, vec2_cropped))
        magnitude_vec1 = sum(v1**2 for v1 in vec1_cropped)**0.5
        magnitude_vec2 = sum(v2**2 for v2 in vec2_cropped)**0.5

        if magnitude_vec1 == 0 or magnitude_vec2 == 0:
            return 0.0
        return dot_product / (magnitude_vec1 * magnitude_vec2)

    def _build_contextual_query(self, current_query, session_id):
        """
        Combines the current query with previous queries from the session history
        to create a richer contextual query string.
        """
        history = session_histories.get(session_id, deque())
        # Include the original user_query itself, not just processed tokens, for context
        # This allows query expansion and embedding to work on full sentences.
        contextual_parts = list(history) + [current_query]
        full_context_query_text = " ".join(contextual_parts)
        print(f"Contextual query text for session '{session_id}': '{full_context_query_text}'")
        return full_context_query_text

    def _expand_query(self, query_string):
        """
        Develops methods for query expansion to improve search coverage.
        This could involve:
        - Using a thesaurus (e.g., WordNet) to find synonyms.
        - Leveraging a pre-built knowledge base for related concepts.
        - Using an LLM to generate alternative phrasings or related questions.
        """
        expanded = [query_string] # Always include the original query string

        # Example: Simple rule-based expansion
        if "design pattern" in query_string.lower():
            expanded.append("software pattern")
            expanded.append("architectural style")
            expanded.append("software solution template")
        if "solid" in query_string.lower():
            expanded.append("SRP")
            expanded.append("OCP")
            expanded.append("LSP")
            expanded.append("ISP")
            expanded.append("DIP")
            expanded.append("object-oriented design principles")
        if "microservice" in query_string.lower():
            expanded.append("microservices architecture")
            expanded.append("distributed system design")

        print(f"Expanded queries for '{query_string}': {expanded}")
        return expanded

    def _convert_to_graph_params(self, expanded_queries_texts, user_query_embedding):
        """
        Converts natural language queries into graph search parameters.
        This involves:
        - Identifying potential node labels (e.g., 'Concept', 'DesignPattern', 'Principle').
        - Identifying relationship types (e.g., 'IS_A', 'RELATED_TO', 'APPLIES_TO').
        - Extracting property values (e.g., specific names, attributes).
        - Leveraging semantic similarity of query embeddings to graph concepts.
        """
        graph_params = []

        for query_text in expanded_queries_texts:
            param = {"match_text": query_text} # Default text match for Cypher's CONTAINS/STARTS WITH

            # If spaCy is loaded, use it for entity recognition and pattern matching
            if nlp:
                doc = nlp(query_text)

                # Entity-based mapping to node labels/properties
                for ent in doc.ents:
                    if ent.label_ == "ORG" or ent.label_ == "PRODUCT":
                        param["node_label"] = param.get("node_label", []) + ["Organization", "Technology"]
                        param["properties"] = param.get("properties", {})
                        param["properties"]["name"] = ent.text # Match by name of entity

                if "pattern" in query_text.lower() or "patterns" in query_text.lower():
                    param["node_label"] = param.get("node_label", []) + ["DesignPattern"]
                if "principle" in query_text.lower() or "principles" in query_text.lower():
                    param["node_label"] = param.get("node_label", []) + ["Principle"]
                if "architecture" in query_text.lower():
                    param["node_label"] = param.get("node_label", []) + ["Architecture"]
                if "concept" in query_text.lower():
                    param["node_label"] = param.get("node_label", []) + ["Concept"]

                # Simplified Relationship Type inference
                if "relate" in query_text.lower() or "connected" in query_text.lower():
                    param["relation_type"] = param.get("relation_type", []) + ["RELATED_TO"]
                if "is a" in query_text.lower() or "type of" in query_text.lower():
                    param["relation_type"] = param.get("relation_type", []) + ["IS_A"]
                if "applies to" in query_text.lower():
                    param["relation_type"] = param.get("relation_type", []) + ["APPLIES_TO"]

            # Store the embedding for semantic similarity matching later in Neo4j
            param["query_embedding"] = self._get_embedding(query_text)

            graph_params.append(param)
        print(f"Converted to graph parameters: {graph_params}")
        return graph_params

    def _handle_ambiguity(self, graph_search_parameters):
        """
        Develops mechanisms for handling ambiguous queries.
        This is a critical part where the system might:
        - Analyze confidence scores for different interpretations.
        - Prioritize interpretations based on user's past behavior (context).
        - If high ambiguity, potentially trigger a clarifying question to the user.
        - Use heuristics (e.g., "design" without specific context defaults to "software design").
        """
        # For simplicity, this is a placeholder. A real implementation would be complex.
        # Example heuristic: if "design" is found without "UI" or "UX", assume "SoftwareDesign"
        # You might iterate through parameters and if ambiguity is detected,
        # modify node_label, properties, or relation_type.
        print(f"Handling ambiguity for: {graph_search_parameters}")
        return graph_search_parameters # No change for this example

    def _traverse_graph(self, graph_params, user_query_embedding):
        """
        Designs efficient graph traversal mechanisms to find relevant knowledge in Neo4j.
        This function would:
        - Connect to Neo4j using the `neo4j_driver`.
        - Construct dynamic Cypher queries based on `graph_params`.
        - Use full-text search indexes (e.g., `CALL db.index.fulltext.queryNodes(...)`) for `match_text`.
        - Perform graph traversals (e.g., `MATCH (n)-[r]-(m) WHERE ... RETURN n, r, m`).
        - Utilize vector similarity search in Neo4j (if using Neo4j's vector index)
          e.g., `CALL db.index.vector.queryNodes('concept_embeddings', $k, $embedding)`
        - Implement methods for searching both node content and relationship types.
        """
        # Simulate interaction with a knowledge base for demonstration purposes.
        # In a real application, you would replace this with actual Neo4j queries.

        simulated_knowledge_base = [
            {"id": "node1", "title": "Singleton Design Pattern", "type": "DesignPattern", "content": "Ensures a class has only one instance and provides a global point of access to it.", "embedding": self._get_embedding("Singleton Design Pattern software pattern example")},
            {"id": "node2", "title": "SOLID Principles", "type": "Principle", "content": "Five design principles for object-oriented programming: SRP, OCP, LSP, ISP, DIP.", "embedding": self._get_embedding("SOLID Principles object-oriented design good practices")},
            {"id": "node3", "title": "Factory Method Pattern", "type": "DesignPattern", "content": "Provides an interface for creating objects in a superclass, but allows subclasses to alter the type of objects that will be created.", "embedding": self._get_embedding("Factory Method design pattern object creation")},
            {"id": "node4", "title": "Domain-Driven Design (DDD)", "type": "Approach", "content": "Focuses on developing complex software systems by connecting the implementation to an evolving model of the core business domain.", "embedding": self._get_embedding("Domain-Driven Design software development approach model")},
            {"id": "node5", "title": "Microservices Architecture", "type": "Architecture", "content": "A style of developing a single application as a suite of small services, each running in its own process and communicating with lightweight mechanisms.", "embedding": self._get_embedding("Microservices distributed architecture system")},
            {"id": "node6", "title": "Software Requirements Specification (SRS)", "type": "Document", "content": "A document that describes the nature of a project, software or system.", "embedding": self._get_embedding("Software Requirements Specification document project system")},
            {"id": "node7", "title": "Coupling and Cohesion", "type": "Principle", "content": "Key concepts in software design. Coupling is the degree of interdependence between software modules; cohesion is the degree to which elements within a module belong together.", "embedding": self._get_embedding("Coupling Cohesion software design principles modularity")},
            {"id": "node8", "title": "Observer Pattern", "type": "DesignPattern", "content": "Defines a one-to-many dependency between objects so that when one object changes state, all its dependents are notified and updated automatically.", "embedding": self._get_embedding("Observer Pattern behavioral design publish subscribe")},
            # Example for a relationship (simplified)
            {"id": "rel1", "type": "IS_A", "from": "node1", "to": "node3", "content": "Singleton is a type of DesignPattern"}, # Not a real relation, just for simulation concept
        ]

        raw_graph_results = []
        for param in graph_params:
            match_text = param.get("match_text", "").lower()
            node_labels = param.get("node_label", [])
            properties = param.get("properties", {})
            relation_types = param.get("relation_type", [])
            param_embedding = param.get("query_embedding")

            # Perform a simulated search based on parameters
            for item in simulated_knowledge_base:
                # Check for node content match
                content_match = match_text and (match_text in item["content"].lower() or match_text in item["title"].lower())

                # Check for node label match
                label_match = not node_labels or item["type"] in node_labels

                # Check for property match
                prop_match = all(item.get(k) and item.get(k).lower() == str(v).lower() for k, v in properties.items())

                # Check for semantic similarity with node/relationship embeddings
                semantic_match = False
                if param_embedding and item.get("embedding"):
                    similarity_score = self._cosine_similarity(param_embedding, item["embedding"])
                    if similarity_score > 0.7: # Threshold for semantic match
                        semantic_match = True
                        item["semantic_score"] = similarity_score # Store for ranking

                # If relation_types are specified, simulate finding related nodes
                # In Neo4j, you'd use `MATCH (a)-[r:REL_TYPE]-(b)`
                is_related_match = False
                if relation_types:
                    for rel_type in relation_types:
                        # This is a very simplistic simulation. In Neo4j, you'd traverse.
                        # e.g., If "Singleton" related to "DesignPattern"
                        if rel_type == "RELATED_TO_DESIGN" and item["type"] in ["DesignPattern", "Principle", "Approach"]:
                            is_related_match = True
                            break

                # Combine all match conditions
                if (content_match and label_match and prop_match) or semantic_match or is_related_match:
                    if item not in raw_graph_results: # Avoid duplicates
                        raw_graph_results.append(item)

        print(f"Raw graph results (simulated): {raw_graph_results}")
        return raw_graph_results

    def _rank_results(self, raw_results, original_query, user_query_embedding):
        """
        Implements weighting schemes for different types of information in the graph
        and relevance ranking algorithms for search results.
        This should prioritize semantically similar results.
        """
        if not raw_results:
            return []

        ranked = []
        query_doc = nlp(original_query.lower()) if nlp else None

        for result in raw_results:
            score = 0.0 # Initialize score

            # 1. Base Relevance (if available from source, like our simulation)
            # You might retrieve a "pagerank" or "centrality" score from Neo4j here
            # For simulation, we'll use a placeholder if needed
            # score += result.get("pagerank", 0.1)

            # 2. Direct Keyword Match Boost
            if original_query.lower() in result["title"].lower():
                score += 0.3
            if original_query.lower() in result["content"].lower():
                score += 0.2

            # 3. Semantic Similarity Boost (Crucial for embedding-based search)
            # Compare user query embedding with result embeddings
            result_embedding = result.get("embedding")
            if user_query_embedding and result_embedding:
                similarity = self._cosine_similarity(user_query_embedding, result_embedding)
                score += similarity * 0.4 # Max 0.4 boost based on semantic similarity

            # 4. Weighting based on Node Type (example)
            if result.get("type") == "DesignPattern":
                score += 0.15
            elif result.get("type") == "Principle":
                score += 0.1
            elif result.get("type") == "Architecture":
                score += 0.08

            # 5. Contextual Relevance (if any context-specific matches were made in traversal)
            # Add logic here if specific context led to a result, give it a boost.

            # Ensure score doesn't exceed 1.0 (or whatever max scale you define)
            result_score = min(1.0, score)
            ranked.append({"score": result_score, **result})

        # Sort by score in descending order
        final_ranked_results = sorted(ranked, key=lambda x: x["score"], reverse=True)
        print(f"Ranked results: {final_ranked_results}")
        return final_ranked_results

    def _format_results(self, ranked_results):
        """
        Formats search results appropriately for the prompt engineering module.
        This involves extracting key information (title, snippet, type, score)
        and presenting it in a structured way that the prompt engineering module
        can easily consume to build chatbot responses.
        """
        formatted = []
        for result in ranked_results:
            formatted.append({
                "title": result.get("title", "No Title"),
                "snippet": result.get("content", "No snippet available."),
                "type": result.get("type", "General Concept"),
                "relevance_score": round(result.get("score", 0.0), 2), # Round score for cleaner output
                "id": result.get("id"), # Include ID for potential linking in the graph
                # Add any other fields useful for prompt engineering, e.g.,
                # "related_terms": result.get("related_terms", []),
                # "source_url": result.get("url", None)
            })
        print(f"Formatted results for prompt engineering: {formatted}")
        return formatted
