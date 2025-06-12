from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import logging

# Import components needed for search
from knowledge_graph.connection.neo4j_client import Neo4jClient
from search_module.graph_search_service import GraphSearchService
from prompt_engine.intent_classifier import IntentClassifier # Needed for classifying intent and getting search params

logger = logging.getLogger(__name__)

class SearchAPIView(APIView):
    """
    API endpoint for handling natural language search queries against the knowledge graph.
    This view now orchestrates the intent classification and the graph search.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Initialize IntentClassifier and GraphSearchService once per view instance
        self.intent_classifier = IntentClassifier()
        try:
            self.neo4j_client = Neo4jClient()
            self.graph_search_service = GraphSearchService(self.neo4j_client)
            logger.info("SearchAPIView: Neo4jClient and GraphSearchService initialized successfully.")
        except Exception as e:
            logger.error(f"SearchAPIView: Failed to initialize Neo4jClient or GraphSearchService: {e}", exc_info=True)
            self.neo4j_client = None
            self.graph_search_service = None
            # Decide on fallback behavior: raise exception or log and proceed with limited features
            # If search is critical, you might raise an exception here or during the post method.

    def post(self, request, *args, **kwargs):
        user_query_text = request.data.get("user_query")
        session_id = request.data.get('session_id', 'default_session') # Pass session_id for context

        if not user_query_text or not isinstance(user_query_text, str) or not user_query_text.strip():
            return Response({"error": "No valid user query provided."}, status=status.HTTP_400_BAD_REQUEST)

        graphrag_results = {'results': []} # Initialize empty results

        try:
            # Step 1: Classify user intent to get structured search parameters
            # The classify_intent here does NOT use graphrag_results for refinement yet,
            # as these results are what we are about to fetch.
            initial_intent_result = self.intent_classifier.classify_intent(user_query=user_query_text)
           
            # Step 2: Generate search parameters for the GraphSearchService
            search_parameters = self.intent_classifier.get_search_parameters(
                user_query=user_query_text,
                intent_result=initial_intent_result
            )
           
            # Step 3: Call the GraphSearchService to perform the actual search
            if self.graph_search_service:
                logger.info(f"SearchAPIView: Calling GraphSearchService for '{user_query_text}' with params: {search_parameters}")
                graphrag_results = self.graph_search_service.search(
                    user_query_text=user_query_text, # Original query text for embedding
                    search_params=search_parameters, # Structured parameters from intent classifier
                    session_id=session_id # Session ID for context-aware search
                )
                logger.info(f"SearchAPIView: Received {len(graphrag_results.get('results', []))} results from GraphSearchService.")
            else:
                logger.warning("SearchAPIView: GraphSearchService not available. Returning empty results.")

        except Exception as e:
            logger.error(f"SearchAPIView: Error during search pipeline: {e}", exc_info=True)
            return Response({"error": f"Graph search failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Return the results
        return Response(graphrag_results, status=status.HTTP_200_OK)