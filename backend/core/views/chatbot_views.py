from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.utils import timezone
from django.shortcuts import get_object_or_404
import logging 

# Import your Django models and serializers
from core.models import Conversation, Message
from core.serializers import MessageSerializer, ConversationSerializer

# Import prompt engine components
from prompt_engine.managers.prompt_manager import PromptManager
from prompt_engine.managers.context_manager import ContextManager
from prompt_engine.templates.base_template import UserExpertise, ResponseLength
from prompt_engine.expertise_classifier import ExpertiseClassifier
from prompt_engine.intent_classifier import IntentClassifier # Needed for search params

# Import GraphRAG integration components
from knowledge_graph.connection.neo4j_client import Neo4jClient
from search_module.graph_search_service import GraphSearchService # Assuming this is the correct path and class

# Configure logging for this view
logger = logging.getLogger(__name__)

class ChatbotAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.context_manager = ContextManager()
        self.prompt_manager = PromptManager()
        self.expertise_classifier = ExpertiseClassifier()
        self.intent_classifier = IntentClassifier() # Initialize IntentClassifier for search params
       
        self.neo4j_client = None
        self.graph_search_service = None
        try:
            # Initialize Neo4j client and graph search service
            self.neo4j_client = Neo4jClient()
            self.graph_search_service = GraphSearchService(self.neo4j_client)
            logger.info("ChatbotAPIView: Neo4jClient and GraphSearchService initialized successfully.")
        except Exception as e:
            logger.error(f"ChatbotAPIView: Failed to initialize Neo4jClient or GraphSearchService: {e}", exc_info=True)
            self.neo4j_client = None
            self.graph_search_service = None
    
    def post(self, request):
        """Handle incoming chat messages."""
        user_query = request.data.get('message')
        session_id = request.data.get('session_id') # This 'session_id' will correspond to Conversation.id
        response_length_str = request.data.get('response_length', 'medium').upper()

        if not user_query or not session_id:
            return Response({'error': 'Message and session_id are required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Ensure the Conversation object exists or create a new one
            # Use request.user to link conversations to authenticated users
            conversation, created = Conversation.objects.get_or_create(
                id=session_id,
                user=request.user,
                defaults={'title': f'New Chat {timezone.now().strftime("%Y-%m-%d %H:%M")}'}
            )
            if created:
                logger.info(f"New conversation created with ID: {session_id}")
            else:
                logger.info(f"Existing conversation retrieved with ID: {session_id}")

            # 1. Get conversation history from the context manager
            # We'll use the Django messages to build the history for context manager too
            # Fetch messages associated with this conversation
            db_messages = Message.objects.filter(conversation=conversation).order_by('timestamp')
            
            # Populate context_manager's history from DB messages for inference
            # Ensure context_manager reflects the latest state, including what's in DB
            self.context_manager.clear_session(session_id) # Clear to rebuild from DB
            for msg in db_messages:
                # Assuming metadata can be stored/retrieved from Message model if needed
                self.context_manager.add_message(session_id, sender=msg.sender, text=msg.text)
            
            # Add current user query to context manager for inference
            self.context_manager.add_message(session_id, sender='user', text=user_query)
            
            # Get the full conversation context (including the new user query)
            conversation_history_for_inference = self.context_manager.get_history(session_id)

            # 2. Dynamically infer user expertise based on the query and history
            inferred_expertise = self.expertise_classifier.infer_expertise(user_query, conversation_history_for_inference)
            
            # 3. Update the context manager with the new expertise level
            self.context_manager.set_user_expertise(session_id, inferred_expertise)

            # 4. Perform Graph RAG search (using logic similar to SearchAPIView)
            graphrag_results = {}
            if self.graph_search_service:
                # Classify intent for search parameters
                initial_intent_result = self.intent_classifier.classify_intent(user_query)
                search_parameters = self.intent_classifier.get_search_parameters(
                    user_query=user_query,
                    intent_result=initial_intent_result
                )
                logger.info(f"ChatbotAPIView: Calling GraphSearchService for '{user_query}' with params: {search_parameters}")
                graphrag_results = self.graph_search_service.search(
                    user_query_text=user_query,
                    search_params=search_parameters,
                    session_id=session_id
                )
                logger.info(f"ChatbotAPIView: Received {len(graphrag_results.get('results', []))} results from GraphSearchService.")
            else:
                logger.warning("ChatbotAPIView: GraphSearchService not available. Proceeding without RAG results.")
            
            # 5. Determine the response length
            response_length = ResponseLength[response_length_str]

            # 6. Process the query using the prompt manager with all gathered context
            response_data = self.prompt_manager.process_query(
                user_query=user_query,
                session_id=session_id,
                graphrag_results=graphrag_results, # Pass actual RAG results
                conversation_context=conversation_history_for_inference, # Full history for LLM
                user_expertise=inferred_expertise,
                response_length=response_length
            )
            
            bot_response_text = response_data.get('response', 'An error occurred or no response was generated.')
            bot_metadata = response_data.get('metadata', {})

            # 7. Save user message to the database
            Message.objects.create(
                conversation=conversation,
                sender='user',
                text=user_query,
                timestamp=timezone.now()
            )

            # 8. Save bot response to the database
            Message.objects.create(
                conversation=conversation,
                sender='bot',
                text=bot_response_text,
                timestamp=timezone.now(),
                metadata=bot_metadata # Store any relevant metadata
            )
            
            # Update conversation last_updated timestamp
            conversation.last_updated = timezone.now()
            conversation.save()

            return Response(response_data, status=status.HTTP_200_OK)

        except KeyError:
            return Response({'error': f'Invalid response length: {response_length_str}. Must be SHORT, MEDIUM, or DETAILED.'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"ChatbotAPIView: Error processing query: {e}", exc_info=True)
            return Response({'error': f'An internal error occurred: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request):
        """Retrieve conversation history or a specific conversation."""
        session_id = request.query_params.get('cid')
        user = request.user

        if session_id:
            # Retrieve a specific conversation and its messages
            conversation = get_object_or_404(Conversation, id=session_id, user=user)
            messages = Message.objects.filter(conversation=conversation).order_by('timestamp')
            
            serialized_conversation = ConversationSerializer(conversation).data
            serialized_messages = MessageSerializer(messages, many=True).data
            
            # Also populate ContextManager for this session from DB for continuity
            self.context_manager.clear_session(session_id)
            for msg in messages:
                self.context_manager.add_message(session_id, sender=msg.sender, text=msg.text) # Assuming no complex metadata needed for history here

            return Response({
                'current_conversation': serialized_conversation,
                'messages': serialized_messages
            }, status=status.HTTP_200_OK)
        else:
            # Retrieve all conversations for the user
            conversations = Conversation.objects.filter(user=user).order_by('-updated_at')
            serialized_conversations = ConversationSerializer(conversations, many=True).data
            
            return Response({'conversations': serialized_conversations}, status=status.HTTP_200_OK)
        
    def put(self, request):
        """Rename conversation"""
        conversation_id = request.data.get('cid')
        new_title = request.data.get('title')
        user = request.user

        if not conversation_id or not new_title:
            return Response({'error': 'Conversation ID and new title are required'}, status=status.HTTP_400_BAD_REQUEST)

        conversation = get_object_or_404(Conversation, id=conversation_id, user=user)
        conversation.title = new_title
        conversation.save()

        return Response({'message': 'Conversation renamed successfully', 'title': new_title}, status=status.HTTP_200_OK)

    def delete(self, request):
        """Delete conversation"""
        conversation_id = request.query_params.get('cid')
        user = request.user

        if not conversation_id:
            return Response({'error': 'Conversation ID is required'}, status=status.HTTP_400_BAD_REQUEST)

        conversation = get_object_or_404(Conversation, id=conversation_id, user=user)
        conversation.delete()
        
        # Clear the session from the ContextManager as well
        self.context_manager.clear_session(session_id=conversation_id)

        return Response({'message': 'Conversation deleted successfully'}, status=status.HTTP_204_NO_CONTENT)