from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.utils import timezone
from django.shortcuts import get_object_or_404
import logging 

from core.models import Conversation, Message
from core.serializers import MessageSerializer, ConversationSerializer

# Import prompt engine components
from prompt_engine.intent_classifier import IntentClassifier # Still needed for type hints, though instance is via PromptManager
from prompt_engine.managers.prompt_manager import PromptManager
from prompt_engine.managers.context_manager import ContextManager
from prompt_engine.templates.base_template import UserExpertise, ResponseLength

# Import GraphRAG integration components
from knowledge_graph.connection.neo4j_client import Neo4jClient
from search_module.graph_search_service import GraphSearchService # Assuming this is the correct path and class

# Configure logging for this view
logger = logging.getLogger(__name__)

class ChatbotAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # --- CRITICAL FIXES: Initialize components ONCE per APIView instance ---
        # This prevents creating new expensive objects (like DB connections) on every request.
        self.context_manager = ContextManager()
        self.prompt_manager = PromptManager() # PromptManager contains an IntentClassifier instance internally.
       
        # Initialize Neo4jClient and GraphSearchService here
        self.neo4j_client = None
        self.graph_search_service = None
        try:
            self.neo4j_client = Neo4jClient()
            # Ensure GraphSearchService constructor correctly accepts Neo4jClient
            self.graph_search_service = GraphSearchService(self.neo4j_client)
            logger.info("ChatbotAPIView: Neo4jClient and GraphSearchService initialized successfully.")
        except Exception as e:
            logger.error(f"ChatbotAPIView: Failed to initialize Neo4jClient or GraphSearchService: {e}", exc_info=True)
            # Decide on fallback behavior:
            # For now, we'll log the error and proceed without graph search
            # You could also raise an exception here to immediately stop if search is critical
            # raise Exception("Critical: Could not initialize graph search services.")


    def post(self, request):
        """Send message (and trigger AI response)"""
        message_text = request.data.get('message')
        conversation_id = request.data.get('cid')

        if not message_text:
            return Response({'error': 'Message is required'}, status=status.HTTP_400_BAD_REQUEST)

        conversation = None
        if conversation_id:
            conversation = get_object_or_404(Conversation, id=conversation_id, user=request.user)
        else:
            conversation = Conversation.objects.create(
                user=request.user,
                title='New Conversation', # Default title
                created_at=timezone.now()
            )

        # Set conversation title based on the first message if it's still the default
        if conversation.title == 'New Conversation' or conversation.title.strip() == '':
            conversation.title = message_text[:50] # Use first 50 chars of message
            conversation.save()

        # Create and save user's message
        user_message = Message.objects.create(
            conversation=conversation,
            sender=request.user.username,
            content=message_text,
            created_at=timezone.now(),
            metadata={} # This is now valid due to core/models.py fix
        )
       
        session_id = str(conversation.id)
       
        # Add the user's message to the context manager
        self.context_manager.add_message(
            session_id=session_id,
            role='user',
            content=message_text,
            metadata={} # This is now valid due to core/models.py fix
        )

        # Get conversation context for the prompt engine from the context manager
        conversation_context = self.context_manager.get_context(session_id)
       
        graphrag_results = {'results': []} # Initialize empty, will be populated by search module

        try:
            # --- Step 1: Initial Intent Classification ---
            # Use the IntentClassifier instance owned by PromptManager
            initial_intent_result = self.prompt_manager.intent_classifier.classify_intent(user_query=message_text)
           
            # --- Step 2: Generate Search Parameters based on Initial Intent ---
            search_parameters = self.prompt_manager.intent_classifier.get_search_parameters(
                user_query=message_text,
                intent_result=initial_intent_result
            )
           
            # --- Step 3: Call the Graph Search Module with structured parameters ---
            # Ensure graph_search_service was successfully initialized in __init__
            if self.graph_search_service:
                logger.info(f"ChatbotAPIView: Calling GraphSearchService for '{message_text}' with params: {search_parameters}")
                # Pass the full search_parameters dictionary, NOT just a string from it.
                graphrag_results = self.graph_search_service.search(
                    user_query_text=message_text, # Original query text for embedding
                    search_params=search_parameters, # The structured parameters dictionary
                    session_id=session_id # Session ID for context-aware search
                )
                logger.info(f"ChatbotAPIView: Received {len(graphrag_results.get('results', []))} results from GraphSearchService.")
            else:
                logger.warning("ChatbotAPIView: GraphSearchService not available. Proceeding without GraphRAG results.")
                # graphrag_results remains {'results': []}
           
        except Exception as e:
            logger.error(f"ChatbotAPIView: Error during intent classification or graph search: {e}", exc_info=True)
            # Ensure graphrag_results is still a dict even on error
            graphrag_results = {'results': []}
            # Depending on criticality, you might want to return an error to user here
            # return Response({"error": f"Failed to retrieve knowledge: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # --- Step 4: Determine User Expertise and Response Length ---
        # These can be dynamically determined based on user profile or conversation history.
        user_expertise = UserExpertise.INTERMEDIATE
        response_length = ResponseLength.MEDIUM
       
        # --- Step 5: Process the user's query using the PromptManager ---
        # PromptManager's process_query will internally call classify_intent again,
        # this time *with* the actual graphrag_results for refinement.
        processed_result = self.prompt_manager.process_query(
            user_query=message_text,
            graphrag_results=graphrag_results, # Pass the results from the search module
            conversation_context=conversation_context, # Pass the conversation history
            user_expertise=user_expertise,
            response_length=response_length
        )
       
        # Safely get response text and metadata
        ai_response_text = processed_result.get('response', "An error occurred generating response.")
        ai_response_metadata = {
            'intent': processed_result.get('metadata', {}).get('intent', {}),
            'response_params': processed_result.get('response_params', {}),
            'citations': processed_result.get('citations', []),
            'user_level_after_response': processed_result.get('metadata', {}).get('expertise_level'),
            'context_used': conversation_context # Store context snapshot if needed
        }
       
        # Ensure AI response text is a string before saving
        if not isinstance(ai_response_text, str):
            ai_response_text = str(ai_response_text)
            logger.warning(f"ChatbotAPIView: AI response was not a string. Converted to string: {ai_response_text[:100]}...")

        # Create and save AI's response message
        ai_message = Message.objects.create(
            conversation=conversation,
            sender='AI Chatbot',
            content=ai_response_text,
            created_at=timezone.now(),
            metadata=ai_response_metadata # This is now valid due to core/models.py fix
        )
       
        # Add the AI's response to the context manager
        self.context_manager.add_message(
            session_id=session_id,
            role='assistant',
            content=ai_response_text,
            metadata=ai_response_metadata
        )

        return Response({
            'conversation_id': conversation.id,
            'user_message': MessageSerializer(user_message).data,
            'ai_response': MessageSerializer(ai_message).data
        })

    def get(self, request):
        """Get all conversations and optionally messages from one"""
        conversation_id = request.query_params.get('cid')

        conversations = Conversation.objects.filter(user=request.user).order_by('-created_at')
        serialized_conversations = ConversationSerializer(conversations, many=True).data

        if conversation_id:
            conversation = get_object_or_404(Conversation, id=conversation_id, user=request.user)
            messages = Message.objects.filter(conversation=conversation).order_by('created_at')
            serialized_messages = MessageSerializer(messages, many=True).data

            return Response({
                'conversations': serialized_conversations,
                'current_conversation': ConversationSerializer(conversation).data,
                'messages': serialized_messages
            })

        return Response({
            'conversations': serialized_conversations,
            'current_conversation': None,
            'messages': []
        })

    def put(self, request):
        """Rename conversation"""
        conversation_id = request.data.get('cid')
        new_title = request.data.get('title')

        if not conversation_id or not new_title:
            return Response({'error': 'Conversation ID and new title are required'}, status=400)

        conversation = get_object_or_404(Conversation, id=conversation_id, user=request.user)
        conversation.title = new_title
        conversation.save()

        return Response({'message': 'Conversation renamed successfully', 'title': new_title})

    def delete(self, request):
        """Delete conversation"""
        conversation_id = request.query_params.get('cid')

        if not conversation_id:
            return Response({'error': 'Conversation ID is required'}, status=400)

        conversation = get_object_or_404(Conversation, id=conversation_id, user=request.user)
        conversation.delete()

        return Response({'message': 'Conversation deleted successfully'})