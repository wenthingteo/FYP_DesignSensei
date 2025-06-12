from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.utils import timezone
from django.shortcuts import get_object_or_404

from core.models import Conversation, Message
from core.serializers import MessageSerializer, ConversationSerializer
# from core.services.openai_services import ask_openai # Removed as PromptManager handles AI interaction

# Import prompt engine components
from backend.prompt_engine.managers.prompt_manager import PromptManager
from backend.prompt_engine.managers.context_manager import ContextManager
from backend.prompt_engine.templates.base_template import UserExpertise, ResponseLength
from backend.prompt_engine.test.mock_graph_results import get_mock_search_results # Using mock data for GraphRAG results
# halo看这边  for上面这个mock的数据，实际项目中需要替换为真实的GraphRAG集成
# replaced with actual calls to your GraphSearch module, dynamically generating results based on the user's query and the extracted intent.

# If actual GraphRAG integration is desired, uncomment and configure these:
# from knowledge_graph.connection.neo4j_client import Neo4jClient
# from search_module.graph_search import GraphSearch

class ChatbotAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Initialize the prompt engine components
        self.context_manager = ContextManager()
        self.prompt_manager = PromptManager()
        
        # For actual GraphRAG integration, you would initialize Neo4jClient and GraphSearch here.
        # Note: Instantiating Neo4jClient per request is not optimal for production.
        # Consider a singleton pattern or Django app lifecycle management for connections.
        # self.neo4j_client = Neo4jClient()
        # self.graph_search = GraphSearch(self.neo4j_client)

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
                title='New Conversation',
                created_at=timezone.now()
            )

        if not conversation.title or conversation.title.strip() == '':
            # Set conversation title based on the first message
            conversation.title = message_text[:50]
            conversation.save()

        # Create and save user's message
        user_message = Message.objects.create(
            conversation=conversation,
            sender=request.user.username,
            content=message_text,
            created_at=timezone.now(),
        )
        
        session_id = str(conversation.id)
        
        # Add the user's message to the context manager
        self.context_manager.add_message(
            session_id=session_id,
            role='user',
            content=message_text,
            metadata={} # No specific metadata for user input yet
        )

        # Get conversation context for the prompt engine from the context manager
        conversation_context = self.context_manager.get_context(session_id)
        
        #哈咯哈咯还有这边 intent classifier我已经放在prompt engine里面了，可以在PromptManager中使用
        # You can also extract topics discussed in the conversation if needed < copilot给你的建议
        # --- GraphRAG Integration (using mock data for demonstration) ---
        # In a real scenario, you would use your GraphSearch module here.
        # The prompt_manager's intent classifier could guide the graph search.
        # Example of how you might dynamically get graphrag_results:
        # intent_result = self.prompt_manager.intent_classifier.classify_intent(message_text)
        # search_params = self.prompt_manager.intent_classifier.get_search_parameters(intent_result)
        # graphrag_results = self.graph_search.perform_search(search_params) # This method would need to be implemented
        
        # For this integration, we'll use a hardcoded mock result. 这边也是
        # You would replace "singleton" with a key determined by your application logic.
        graphrag_results = get_mock_search_results("singleton") 
        
        # Determine user expertise and response length.
        # These could be retrieved from user profiles, conversation history, or set as defaults.
        # The PromptManager also adapts the user_level internally.
        user_expertise = UserExpertise.INTERMEDIATE
        response_length = ResponseLength.MEDIUM
        
        # Process the user's query using the PromptManager
        processed_result = self.prompt_manager.process_query(
            user_query=message_text,
            graphrag_results=graphrag_results,
            conversation_context=conversation_context,
            user_expertise=user_expertise,
            response_length=response_length
        )
        
        ai_response_text = processed_result['response']
        # Extract additional metadata to store with the AI's message
        ai_response_metadata = {
            'intent': processed_result.get('intent'),
            'response_params': processed_result.get('response_params'),
            'citations': processed_result.get('citations'),
            'user_level_after_response': processed_result.get('user_level'),
            'context_used': processed_result.get('context_used')
        }

        # Create and save AI's response message
        ai_message = Message.objects.create(
            conversation=conversation,
            sender='AI Chatbot',
            content=ai_response_text,
            created_at=timezone.now(),
            metadata=ai_response_metadata # Store the detailed metadata
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