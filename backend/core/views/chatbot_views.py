from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.utils import timezone
from django.shortcuts import get_object_or_404
import logging
import asyncio
from asgiref.sync import sync_to_async
from openai import OpenAI
import os
from dotenv import load_dotenv
from django.conf import settings

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

# Import Evaluation Service
from evaluation.evaluation_service import EvaluationService

# Configure logging for this view
logger = logging.getLogger(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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
        Generate concise chat title using OpenAI; fallback to truncation.
        Enforces max 10 words and 60 chars.
        """
        logger.info("=== TITLE GENERATION START ===")
        logger.info(f"First 100 chars of message: {message_text[:100]!r}")

        api_key = getattr(settings, "OPENAI_API_KEY", None) or os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error("OPENAI_API_KEY missing, fallback to truncation.")
            return self._fallback_title(message_text)

        system_prompt = (
            "You are a title generator. Create a short title (max 10 words, no punctuation) "
            "that describes the message topic clearly. Return only the title text."
        )
        user_prompt = f"Generate a concise title for: {message_text}"

        try:
            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model="gpt-4.1-nano-2025-04-14",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=30,
                temperature=0.3,
                timeout=10
            )
            title = response.choices[0].message.content.strip().strip(' "\'')
            words = title.split()

            # limit by words and characters
            if len(words) > 10:
                title = " ".join(words[:10])
            if len(title) > 60:
                title = title[:60].rsplit(' ', 1)[0] + "…"

            return title or self._fallback_title(message_text)

        except Exception as e:
            logger.error(f"Error generating title: {e}", exc_info=True)
            return self._fallback_title(message_text)

    def _fallback_title(self, message_text):
        words = message_text.strip().split()
        title = " ".join(words[:10])
        if len(title) > 60:
            title = title[:60].rsplit(" ", 1)[0] + "…"
        return title or "New Conversation"

    async def _process_message_async(self, message_text, session_id, conversation_context):
        """
        Async wrapper for the LLM processing with timeout
        """
        try:
            # Intent classification & Graph Search
            initial_intent_result = self.prompt_manager.intent_classifier.classify_intent(user_query=message_text)
            search_parameters = self.prompt_manager.intent_classifier.get_search_parameters(
                user_query=message_text,
                intent=initial_intent_result
            )

            graphrag_results = {'results': []}
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

            # --- Handle fallback: if graph returns nothing or too weak ---
            graph_results_list = graphrag_results.get('results', [])
            if not graph_results_list or len(graph_results_list) == 0:
                logger.info("No relevant graph results — switching to general LLM response.")
                general_prompt = (
                    "You are DesignSensei, an AI assistant for software design students. "
                    "If the user's question is not related to software design, respond naturally and helpfully like a friendly AI."
                )

                # ✅ Initialize OpenAI client directly (not through PromptManager)
                from openai import OpenAI
                import os
                client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

                fallback_response = client.chat.completions.create(
                    model="gpt-4.1-nano-2025-04-14",
                    messages=[
                        {"role": "system", "content": general_prompt},
                        {"role": "user", "content": message_text}
                    ],
                    max_tokens=300,
                    temperature=0.7
                )

                answer = fallback_response.choices[0].message.content.strip()

                logger.info("✅ Fallback mode triggered — returned general LLM response.")
                return {"response": answer, "metadata": {"mode": "fallback"}}, graphrag_results

            # --- Process query and generate response (normal GraphRAG mode) ---
            user_expertise = UserExpertise.INTERMEDIATE
            response_length = ResponseLength.MEDIUM

            processed_result = self.prompt_manager.process_query(
                user_query=message_text,
                graphrag_results=graphrag_results,
                conversation_context=conversation_context,
                user_expertise=user_expertise,
                response_length=response_length
            )
            
            return processed_result, graphrag_results

        except Exception as e:
            logger.error(f"ChatbotAPIView: Error during async processing: {e}", exc_info=True)
            raise

    def post(self, request):
        """Send message (and trigger AI response)"""
        message_text = request.data.get('content')
        conversation_id = request.data.get('conversation')
        is_regenerate = request.data.get('regenerate', False)

        if not message_text:
            return Response({'error': 'Message is required'}, status=status.HTTP_400_BAD_REQUEST)

        is_new_conversation = False
        conversation = None

        # --- Check if existing conversation or create new one ---
        if conversation_id:
            conversation = get_object_or_404(Conversation, id=conversation_id, user=request.user)
        else:
            logger.info(f"Creating new conversation for user: {request.user.username}")
            conversation = Conversation.objects.create(
                user=request.user,
                title='Generating title...',  # Temporary title
                created_at=timezone.now()
            )
            is_new_conversation = True
            logger.info(f"New conversation created with ID: {conversation.id}")

        # --- Generate AI-powered conversation title for new conversations ---
        if is_new_conversation:
            logger.info("This is a new conversation - generating AI title...")
            smart_title = self._generate_conversation_title(message_text)
            conversation.title = smart_title
            conversation.save()
            logger.info(f"Conversation title saved to database: {smart_title}")

        # --- Handle regeneration: reuse existing user message ---
        # Assumes the caller may provide `is_regenerate` (bool) and optionally `message_id` (UUID/int).
        # `message_text` contains the user's message text (still required).
        is_regenerate = request.data.get("is_regenerate", False)
        regenerate_message_id = request.data.get("message_id")  # optional: prefer this

        if is_regenerate:
            logger.info("Regeneration requested - locating existing user message")

            user_message = None

            # 1) Prefer locating by explicit message_id if provided by client
            if regenerate_message_id:
                try:
                    user_message = Message.objects.filter(
                        id=regenerate_message_id, conversation=conversation, sender='user'
                    ).first()
                    if user_message:
                        logger.info(f"Found user message by id: {user_message.id}")
                except Exception as e:
                    logger.warning(f"Error looking up message by id {regenerate_message_id}: {e}", exc_info=True)

            # 2) Fallback: locate latest user message with matching content (best-effort)
            if not user_message:
                user_message = Message.objects.filter(
                    conversation=conversation,
                    sender='user',
                    content=message_text
                ).order_by('-created_at').first()

                if user_message:
                    logger.info(f"Found user message by text match, id: {user_message.id}")

            # 3) If still not found, create it — but make sure to add it to context afterwards
            if not user_message:
                logger.warning("No existing user message found for regeneration. Creating new one and adding to context.")
                user_message = Message.objects.create(
                    conversation=conversation,
                    sender='user',
                    content=message_text,
                    created_at=timezone.now(),
                    metadata={"regenerated": True}
                )
                # Since we created it now, we must add it to the in-memory context:
                session_id = str(conversation.id)
                self.context_manager.add_message(
                    session_id=session_id,
                    role='user',
                    content=message_text,
                    metadata=user_message.metadata or {}
                )
            else:
                # If message exists, ensure context contains it; add if missing
                session_id = str(conversation.id)
                conversation_context = self.context_manager.get_context(session_id)
                # Implement a heuristic to determine whether to add: e.g., check last message content
                if not conversation_context or not any(
                    (m.get("role") == "user" and m.get("content") == user_message.content) 
                    for m in conversation_context
                ):
                    logger.info("Context missing the original user message; adding it to context.")
                    self.context_manager.add_message(
                        session_id=session_id,
                        role='user',
                        content=user_message.content,
                        metadata=user_message.metadata or {}
                    )

            # Optional: remove or mark previous assistant reply to this user_message
            # (common UX: replace the old bot reply rather than appending another)
            try:
                last_bot_msg = Message.objects.filter(
                    conversation=conversation,
                    sender='bot',
                    created_at__gte=user_message.created_at
                ).order_by('created_at').first()
                if last_bot_msg:
                    # Option A: delete it (uncomment if desired)
                    # last_bot_msg.delete()
                    # logger.info(f"Deleted previous bot reply id={last_bot_msg.id} for regeneration.")

                    # Option B: mark it as superseded in metadata
                    last_bot_msg.metadata = {**(last_bot_msg.metadata or {}), "superseded_by_regen": True}
                    last_bot_msg.save(update_fields=["metadata"])
                    logger.info(f"Marked previous bot reply id={last_bot_msg.id} as superseded.")
            except Exception as e:
                logger.warning(f"Could not find/modify previous bot reply: {e}", exc_info=True)

        else:
            # --- Create and save user's message (normal flow) ---
            user_message = Message.objects.create(
                conversation=conversation,
                sender='user',
                content=message_text,
                created_at=timezone.now(),
                metadata={}
            )
            session_id = str(conversation.id)
            # add the new user message to context
            self.context_manager.add_message(
                session_id=session_id,
                role='user',
                content=message_text,
                metadata={}
            )   

        conversation_context = self.context_manager.get_context(session_id)

        # --- Process with timeout ---
        try:
            # Set timeout to 50 seconds (frontend will timeout at 60s)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            processed_result, graphrag_results = loop.run_until_complete(
                asyncio.wait_for(
                    self._process_message_async(message_text, session_id, conversation_context),
                    timeout=50.0
                )
            )
            loop.close()

        except asyncio.TimeoutError:
            logger.error(f"ChatbotAPIView: Request timed out for message: {message_text}")
            # Don't save AI message to database on timeout
            return Response({
                'error': 'timeout',
                'message': 'Response generation took too long. Please try again.',
                'conversation_id': conversation.id,
                'conversation_title': conversation.title,
                'user_message': MessageSerializer(user_message).data,
            }, status=status.HTTP_408_REQUEST_TIMEOUT)

        except Exception as e:
            logger.error(f"ChatbotAPIView: Error processing message: {e}", exc_info=True)
            return Response({
                'error': 'processing_error',
                'message': 'An error occurred while processing your request.',
                'conversation_id': conversation.id,
                'conversation_title': conversation.title,
                'user_message': MessageSerializer(user_message).data,
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # --- Extract response ---
        draft_answer = processed_result.get('response', "An error occurred generating response.")
        context_text = str(graphrag_results.get('results', []))

        # --- Evaluate BEFORE sending (auto-regenerates up to 3 times) ---
        eval_service = EvaluationService()
        final_answer, score, attempts = eval_service.evaluate_before_send(
            question=message_text,
            context=context_text,
            draft_answer=draft_answer,
            max_attempts=3,
            threshold=0.7
        )

        ai_response_text = final_answer
        logger.info(f"✅ Final evaluation score after {attempts} attempts: {score:.3f}")

        # --- Save evaluation result asynchronously ---
        try:
            current_user_id = request.user.id
            eval_service.evaluate_and_store_async(
                session_id=str(conversation.id),
                user_id=current_user_id,
                question=message_text,
                context=context_text,
                llm_answer=ai_response_text
            )
        except Exception as e:
            logger.error(f"ChatbotAPIView: Evaluation service error: {e}", exc_info=True)

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

        logger.info(f"Sending response with title: {conversation.title}")
        
        # Return response data
        return Response({
            'conversation_id': conversation.id,
            'conversation_title': conversation.title,
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