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
from prompt_engine.intent_classifier import IntentClassifier
from prompt_engine.managers.prompt_manager import PromptManager
from prompt_engine.managers.context_manager import ContextManager
from prompt_engine.templates.base_template import UserExpertise, ResponseLength

# Import GraphRAG integration components
from knowledge_graph.connection.neo4j_client import Neo4jClient
from search_module.graph_search_service import GraphSearchService

# Configure logging for this view
logger = logging.getLogger(__name__)

class ChatbotAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.context_manager = ContextManager()
        self.prompt_manager = PromptManager()

        self.neo4j_client = None
        self.graph_search_service = None
        try:
            self.neo4j_client = Neo4jClient()
            self.graph_search_service = GraphSearchService(self.neo4j_client)
            logger.info("ChatbotAPIView: Neo4jClient and GraphSearchService initialized successfully.")
        except Exception as e:
            logger.error(f"ChatbotAPIView: Failed to initialize Neo4jClient or GraphSearchService: {e}", exc_info=True)

    def _generate_conversation_title(self, message_text):
        """
        Simple helper function to generate a title from the first message.
        You can improve this logic later (e.g. by calling OpenAI).
        """
        try:
            # Example: just take first 8–10 words or 50 chars
            words = message_text.split()
            title = " ".join(words[:10]) if len(words) > 10 else message_text
            return title[:50]
        except Exception as e:
            logger.error(f"Error generating title: {e}")
            return "New Conversation"

    def post(self, request):
        """Send message (and trigger AI response)"""
        message_text = request.data.get('content')
        conversation_id = request.data.get('conversation')

        if not message_text:
            return Response({'error': 'Message is required'}, status=status.HTTP_400_BAD_REQUEST)

        is_new_conversation = False
        conversation = None

        # --- Check if existing conversation or create new one ---
        if conversation_id:
            conversation = get_object_or_404(Conversation, id=conversation_id, user=request.user)
        else:
            conversation = Conversation.objects.create(
                user=request.user,
                title='New Conversation',
                created_at=timezone.now()
            )
            is_new_conversation = True

        # --- Generate conversation title immediately (no Celery) ---
        if is_new_conversation:
            smart_title = self._generate_conversation_title(message_text)
            conversation.title = smart_title
            conversation.save()

        # --- Create and save user's message ---
        user_message = Message.objects.create(
            conversation=conversation,
            sender='user',
            content=message_text,
            created_at=timezone.now(),
            metadata={}
        )

        session_id = str(conversation.id)
        self.context_manager.add_message(
            session_id=session_id,
            role='user',
            content=message_text,
            metadata={}
        )

        conversation_context = self.context_manager.get_context(session_id)
        graphrag_results = {'results': []}

        # --- Intent classification & Graph Search ---
        try:
            initial_intent_result = self.prompt_manager.intent_classifier.classify_intent(user_query=message_text)
            search_parameters = self.prompt_manager.intent_classifier.get_search_parameters(
                user_query=message_text,
                intent_result=initial_intent_result
            )

            if self.graph_search_service:
                logger.info(f"ChatbotAPIView: Calling GraphSearchService for '{message_text}' with params: {search_parameters}")
                graphrag_results = self.graph_search_service.search(
                    user_query_text=message_text,
                    search_params=search_parameters,
                    session_id=session_id
                )
                logger.info(f"ChatbotAPIView: Received {len(graphrag_results.get('results', []))} results from GraphSearchService.")
            else:
                logger.warning("ChatbotAPIView: GraphSearchService not available. Proceeding without GraphRAG results.")
        except Exception as e:
            logger.error(f"ChatbotAPIView: Error during intent classification or graph search: {e}", exc_info=True)
            graphrag_results = {'results': []}

        # --- Process query and generate response ---
        user_expertise = UserExpertise.INTERMEDIATE
        response_length = ResponseLength.MEDIUM

        processed_result = self.prompt_manager.process_query(
            user_query=message_text,
            graphrag_results=graphrag_results,
            conversation_context=conversation_context,
            user_expertise=user_expertise,
            response_length=response_length
        )

        ai_response_text = processed_result.get('response', "An error occurred generating response.")
        ai_response_metadata = {
            'intent': processed_result.get('metadata', {}).get('intent', {}),
            'response_params': processed_result.get('response_params', {}),
            'citations': processed_result.get('citations', []),
            'user_level_after_response': processed_result.get('metadata', {}).get('expertise_level'),
            'context_used': conversation_context
        }

        if not isinstance(ai_response_text, str):
            ai_response_text = str(ai_response_text)
            logger.warning(f"ChatbotAPIView: AI response was not a string. Converted to string: {ai_response_text[:100]}...")

        # --- Save AI response message ---
        ai_message = Message.objects.create(
            conversation=conversation,
            sender='bot',
            content=ai_response_text,
            created_at=timezone.now(),
            metadata=ai_response_metadata
        )

        conversation.save()
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