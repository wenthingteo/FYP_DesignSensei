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
        """
        Send message (normal or regenerate), process AI, evaluate, regenerate if needed,
        save message, return final assistant response.
        """
        message_text = request.data.get("content")
        conversation_id = request.data.get("conversation")
        is_regenerate = request.data.get("is_regenerate", False)
        regenerate_message_id = request.data.get("message_id")

        if not message_text:
            return Response({"error": "Message is required"}, status=400)

        # ------------------------------------------------------------------
        # 1. Create or fetch conversation
        # ------------------------------------------------------------------
        if conversation_id:
            conversation = get_object_or_404(
                Conversation,
                id=conversation_id,
                user=request.user
            )
            is_new_conversation = False
        else:
            conversation = Conversation.objects.create(
                user=request.user,
                title="Generating title...",
                created_at=timezone.now(),
            )
            is_new_conversation = True

        # Generate AI Conversation Title
        if is_new_conversation:
            smart_title = self._generate_conversation_title(message_text)
            conversation.title = smart_title
            conversation.save()

        session_id = str(conversation.id)

        # ------------------------------------------------------------------
        # 2. Handle normal message OR regenerate flow
        # ------------------------------------------------------------------
        if is_regenerate:
            # -----------------------------------------
            # REGENERATE: find original user message
            # -----------------------------------------
            user_message = None

            # Priority 1: a specific message_id
            if regenerate_message_id:
                user_message = Message.objects.filter(
                    id=regenerate_message_id,
                    conversation=conversation,
                    sender="user"
                ).first()

            # Priority 2: match by content
            if user_message is None:
                user_message = Message.objects.filter(
                    conversation=conversation,
                    sender="user",
                    content=message_text
                ).order_by("-created_at").first()

            # Priority 3: recreate if truly missing
            if user_message is None:
                user_message = Message.objects.create(
                    conversation=conversation,
                    sender="user",
                    content=message_text,
                    created_at=timezone.now(),
                    metadata={"regenerated": True},
                )
                # Add newly created msg to context
                self.context_manager.add_message(
                    session_id=session_id,
                    role="user",
                    content=message_text,
                    metadata=user_message.metadata,
                )
            else:
                # Ensure context contains the original message
                ctx = self.context_manager.get_context(session_id)
                if not any(m.get("role") == "user" and m.get("content") == user_message.content for m in ctx):
                    self.context_manager.add_message(
                        session_id=session_id,
                        role="user",
                        content=user_message.content,
                        metadata=user_message.metadata,
                    )

            # Mark previous bot reply as superseded
            try:
                last_bot = Message.objects.filter(
                    conversation=conversation,
                    sender="bot",
                    created_at__gte=user_message.created_at
                ).order_by("created_at").first()

                if last_bot:
                    last_bot.metadata = {**(last_bot.metadata or {}), "superseded_by_regen": True}
                    last_bot.save(update_fields=["metadata"])

            except Exception:
                pass

        else:
            # ---------------------------
            # NORMAL CHAT MESSAGE
            # ---------------------------
            user_message = Message.objects.create(
                conversation=conversation,
                sender="user",
                content=message_text,
                created_at=timezone.now(),
                metadata={},
            )
            self.context_manager.add_message(
                session_id=session_id,
                role="user",
                content=message_text,
                metadata={},
            )

        # ------------------------------------------------------------------
        # 3. AI processing (async with timeout)
        # ------------------------------------------------------------------
        conversation_context = self.context_manager.get_context(session_id)

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            processed_result, graphrag_results = loop.run_until_complete(
                asyncio.wait_for(
                    self._process_message_async(
                        message_text,
                        session_id,
                        conversation_context
                    ),
                    timeout=50
                )
            )
            loop.close()

        except asyncio.TimeoutError:
            return Response({
                "error": "timeout",
                "message": "AI generation timed out.",
                "conversation_id": conversation.id,
                "conversation_title": conversation.title,
                "user_message": MessageSerializer(user_message).data,
            }, status=408)

        except Exception as e:
            logger.exception("Chatbot AI processing error:")
            return Response({
                "error": "processing_error",
                "message": "Error while processing your request.",
                "conversation_id": conversation.id,
                "conversation_title": conversation.title,
                "user_message": MessageSerializer(user_message).data,
            }, status=500)

        # Extract AI draft
        draft_answer = processed_result.get("response", "")
        context_text = str(graphrag_results.get("results", []))

        # ------------------------------------------------------------------
        # 4. Evaluate BEFORE sending (hybrid score + RAGAS factuality)
        # ------------------------------------------------------------------
        eval_service = EvaluationService()

        final_answer, score, attempts = eval_service.evaluate_before_send(
            question=message_text,
            context=context_text,
            draft_answer=draft_answer,
            max_attempts=3,
            threshold=0.7
        )

        ai_response_text = final_answer

        # ------------------------------------------------------------------
        # 5. Save evaluation asynchronously
        # ------------------------------------------------------------------
        try:
            eval_service.evaluate_and_store_async(
                session_id=session_id,
                user_id=request.user.id,
                question=message_text,
                context=context_text,
                llm_answer=ai_response_text
            )
        except Exception as e:
            logger.error("Eval async save error: %s", e)

        # ------------------------------------------------------------------
        # 6. Save AI response message
        # ------------------------------------------------------------------
        ai_metadata = {
            "intent": processed_result.get("metadata", {}).get("intent"),
            "response_params": processed_result.get("response_params"),
            "citations": processed_result.get("citations"),
            "user_level_after_response": processed_result.get("metadata", {}).get("expertise_level"),
            "context_used": conversation_context,
        }

        ai_message = Message.objects.create(
            conversation=conversation,
            sender="bot",
            content=ai_response_text,
            created_at=timezone.now(),
            metadata=ai_metadata,
        )

        self.context_manager.add_message(
            session_id=session_id,
            role="assistant",
            content=ai_response_text,
            metadata=ai_metadata,
        )

        # ------------------------------------------------------------------
        # 7. Return final structured response
        # ------------------------------------------------------------------
        return Response({
            "conversation_id": conversation.id,
            "conversation_title": conversation.title,
            "user_message": MessageSerializer(user_message).data,
            "ai_response": MessageSerializer(ai_message).data,
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