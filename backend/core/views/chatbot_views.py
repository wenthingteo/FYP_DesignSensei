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
        Async LLM processing:
        - Intent classification
        - GraphRAG graph search
        - Fallback if graph not useful
        - Main answer generation
        - Stronger hallucination protection
        """
        try:
            # ---------------------------------------------------------
            # 1. INTENT CLASSIFICATION (fast, synchronous)
            # ---------------------------------------------------------
            intent = self.prompt_manager.intent_classifier.classify_intent(
                user_query=message_text
            )
            search_params = self.prompt_manager.intent_classifier.get_search_parameters(
                user_query=message_text,
                intent=intent
            )

            # ---------------------------------------------------------
            # 2. GRAPH SEARCH (GraphRAG)
            # ---------------------------------------------------------
            graphrag_results = {'results': []}
            graph_results_list = []

            logger.info(f"🔍 Graph search service status: {self.graph_search_service is not None}")
            if self.graph_search_service:
                try:
                    logger.info(f"[GraphRAG] 🔎 Starting search for query: '{message_text}'")
                    logger.info(f"[GraphRAG] 📋 Search params: {search_params}")

                    graphrag_results = self.graph_search_service.search(
                        user_query_text=message_text,
                        search_params=search_params,
                        session_id=session_id
                    )

                    graph_results_list = graphrag_results.get("results", [])
                    logger.info(f"[GraphRAG] ✅ Received {len(graph_results_list)} results")
                    
                    if len(graph_results_list) == 0:
                        logger.warning(f"[GraphRAG] ⚠️ No results found for query: '{message_text[:50]}...'")
                        logger.warning(f"[GraphRAG] ⚠️ Full graphrag_results: {graphrag_results}")
                except Exception as e:
                    logger.error(f"[GraphRAG] ❌ Search error: {e}", exc_info=True)
            else:
                logger.error(f"[GraphRAG] ❌ Graph search service is None! Check Neo4j initialization.")

            # ---------------------------------------------------------
            # 3. HYBRID MODE — Evaluate Graph Quality using LLM Score
            # ---------------------------------------------------------
            HYBRID_THRESHOLD = 0.55  # Higher threshold for quality graph results only
            llm_relevance_score = 0.0

            if graph_results_list:
                # Build structured summary with top results (more context, better formatting)
                top_results = graph_results_list[:8]  # Increased from 6 to 8
                
                # Extract detected topics for context
                detected_topics = search_params.get('topic_filter_labels', [])[:3]
                topic_context = f"Detected topics: {', '.join(detected_topics)}" if detected_topics else ""
                
                # Format results with clear structure (name + description, not full text)
                formatted_results = []
                for i, r in enumerate(top_results, 1):
                    name = r.get('name', 'Unknown')
                    desc = r.get('description', r.get('text', ''))[:200]  # First 200 chars
                    formatted_results.append(f"{i}. {name}: {desc}")
                
                knowledge_summary = "\n".join(formatted_results)

                # Improved scoring prompt with clear criteria and examples
                scoring_prompt = (
                    "You are evaluating whether knowledge graph results can answer the user's question.\n\n"
                    f"USER QUESTION: \"{message_text}\"\n"
                    f"{topic_context}\n\n"
                    "KNOWLEDGE GRAPH RESULTS:\n"
                    f"{knowledge_summary}\n\n"
                    "SCORING CRITERIA:\n"
                    "• 0.8-1.0: Results directly answer the question with detailed, relevant information\n"
                    "• 0.5-0.7: Results contain related concepts but lack completeness\n"
                    "• 0.2-0.4: Results are tangentially related but don't address the question\n"
                    "• 0.0-0.1: Results are irrelevant or off-topic\n\n"
                    "IMPORTANT:\n"
                    "- If question asks about 'DDD' and results contain DDD concepts → HIGH score (0.7-1.0)\n"
                    "- If results provide definitions, examples, or explanations for the asked topic → HIGH score\n"
                    "- Only give LOW scores if results don't match the question topic at all\n\n"
                    "Output ONLY a single decimal number (e.g., 0.85):"
                )

                relevance_response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are an expert relevance evaluator. Analyze carefully and output only a decimal score."},
                        {"role": "user", "content": scoring_prompt}
                    ],
                    max_tokens=10,
                    temperature=0
                )

                try:
                    raw_score = relevance_response.choices[0].message.content.strip()
                    logger.info(f"🔍 LLM raw relevance response: '{raw_score}'")
                    
                    # Extract first number found in response
                    import re
                    match = re.search(r'0\.[0-9]+|1\.0+|0\.0+', raw_score)
                    if match:
                        llm_relevance_score = float(match.group())
                        logger.info(f"✅ Extracted LLM relevance score: {llm_relevance_score}")
                    else:
                        # Fallback: calculate based on FTS scores if available
                        avg_fts = sum(r.get('fts_score', 0.5) for r in top_results) / len(top_results)
                        llm_relevance_score = min(0.7, avg_fts)  # Cap at 0.7 for fallback
                        logger.warning(f"⚠️ No number found in LLM response, using FTS average: {llm_relevance_score:.2f}")
                except Exception as e:
                    # Better fallback: use average of FTS scores from graph results
                    avg_fts = sum(r.get('fts_score', 0.5) for r in top_results) / len(top_results)
                    llm_relevance_score = min(0.7, avg_fts)
                    logger.error(f"❌ Failed to parse LLM relevance score: {e}, using FTS average: {llm_relevance_score:.2f}")

                graphrag_results["average_llm_score"] = llm_relevance_score
                logger.info(f"📊 Relevance scoring: {len(top_results)} results analyzed, final score: {llm_relevance_score:.2f}")

            # ---------------------------------------------------------
            # 4. HYBRID ROUTING: Decide LLM only / Blend / Graph Mode
            # ---------------------------------------------------------
            if not graph_results_list:
                mode = "LLM_ONLY"
                logger.info(f"[MODE: LLM_ONLY] No graph results available")
            elif llm_relevance_score < HYBRID_THRESHOLD:
                mode = "HYBRID_BLEND"
                logger.info(f"[MODE: HYBRID_BLEND] Score {llm_relevance_score:.2f} < threshold {HYBRID_THRESHOLD}")
            else:
                mode = "GRAPH_RAG"
                logger.info(f"[MODE: GRAPH_RAG] Score {llm_relevance_score:.2f} >= threshold {HYBRID_THRESHOLD}")

            logger.info(f"🎯 HYBRID MODE DECISION: {mode} (Score={llm_relevance_score:.2f}, Threshold={HYBRID_THRESHOLD})")

            # ----------------- MODE: LLM ONLY -----------------------
            if mode == "LLM_ONLY":
                system_prompt = (
                    "You are DesignSensei, an AI tutor specializing in software design.\n"
                    "Provide clear, factual, concise responses.\n"
                    "If unsure, say 'I might be mistaken.'\n"
                    "IMPORTANT: Use the conversation history to understand context and references like 'it', 'that', 'this concept', etc."
                )

                # Build conversation history for context
                messages = [{"role": "system", "content": system_prompt}]
                
                # Add recent conversation history (last 3 exchanges)
                if conversation_context and isinstance(conversation_context, dict):
                    previous_messages = conversation_context.get('previous_messages', [])
                    logger.info(f"📝 LLM_ONLY mode: Found {len(previous_messages)} previous messages in context")
                    if previous_messages:
                        recent_history = previous_messages[-6:]  # Last 3 user+assistant pairs
                        logger.info(f"📝 Adding {len(recent_history)} messages to LLM context")
                        for msg in recent_history:
                            messages.append({
                                "role": msg.get("role", "user"),
                                "content": msg.get("content", "")
                            })
                    else:
                        logger.warning(f"⚠️ No previous messages found in conversation_context!")
                else:
                    logger.warning(f"⚠️ conversation_context is not a dict or is None: {type(conversation_context)}")
                
                # Add current user message
                messages.append({"role": "user", "content": message_text})
                
                logger.info(f"📤 Sending {len(messages)} messages to LLM (including system prompt)")

                fallback_response = client.chat.completions.create(
                    model="gpt-4.1-nano-2025-04-14",
                    messages=messages,
                    max_tokens=350,
                    temperature=0.2
                )
                answer = fallback_response.choices[0].message.content.strip()
                return (
                    {"response": answer, "metadata": {"mode": mode, "score": llm_relevance_score, "intent": intent}},
                    graphrag_results
                )

            # ----------------- MODE: HYBRID BLEND (LLM + graph summary) -----------------------
            if mode == "HYBRID_BLEND":
                graph_summary = "\n".join([f"- {r.get('text', '')}" for r in graph_results_list[:4]])

                blend_prompt = (
                    "You are DesignSensei, an AI tutor specializing in software design.\n"
                    "Below is partial but not fully confident knowledge graph info. "
                    "Use it ONLY as supporting hints.\n\n"
                    f"Graph Insights:\n{graph_summary}\n\n"
                    "Answer the user's question clearly.\n"
                    "IMPORTANT: Use conversation history to understand references like 'it', 'that', 'this', etc."
                )

                # Build messages with conversation history
                messages = [{"role": "system", "content": blend_prompt}]
                
                # Add recent conversation history
                if conversation_context and isinstance(conversation_context, dict):
                    previous_messages = conversation_context.get('previous_messages', [])
                    if previous_messages:
                        recent_history = previous_messages[-6:]  # Last 3 exchanges
                        for msg in recent_history:
                            messages.append({
                                "role": msg.get("role", "user"),
                                "content": msg.get("content", "")
                            })
                
                messages.append({"role": "user", "content": message_text})

                hybrid_response = client.chat.completions.create(
                    model="gpt-4.1-nano-2025-04-14",
                    messages=messages,
                    max_tokens=380,
                    temperature=0.25
                )

                answer = hybrid_response.choices[0].message.content.strip()
                return (
                    {"response": answer, "metadata": {"mode": mode, "score": llm_relevance_score, "intent": intent}},
                    graphrag_results
                )

            # ----------------- MODE: GRAPH RAG (strong results) -----------------------
            processed_result = self.prompt_manager.process_query(
                user_query=message_text,
                graphrag_results=graphrag_results,
                conversation_context=conversation_context,
                user_expertise=UserExpertise.INTERMEDIATE,
                response_length=ResponseLength.MEDIUM
            )

            processed_result.setdefault("metadata", {})
            processed_result["metadata"].update({"mode": mode, "score": llm_relevance_score, "intent": intent})

            return processed_result, graphrag_results

        except Exception as e:
            logger.error(f"[ERROR] During async message processing: {e}", exc_info=True)
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
            user_message = None

            if regenerate_message_id:
                user_message = Message.objects.filter(
                    id=regenerate_message_id,
                    conversation=conversation,
                    sender="user"
                ).first()

            if user_message is None:
                user_message = Message.objects.filter(
                    conversation=conversation,
                    sender="user",
                    content=message_text
                ).order_by("-created_at").first()

            if user_message is None:
                user_message = Message.objects.create(
                    conversation=conversation,
                    sender="user",
                    content=message_text,
                    created_at=timezone.now(),
                    metadata={"regenerated": True},
                )
                self.context_manager.add_message(
                    session_id=session_id,
                    role="user",
                    content=message_text,
                    metadata=user_message.metadata,
                )
            else:
                ctx = self.context_manager.get_context(session_id)
                if not any(m.get("role") == "user" and m.get("content") == user_message.content for m in ctx):
                    self.context_manager.add_message(
                        session_id=session_id,
                        role="user",
                        content=user_message.content,
                        metadata=user_message.metadata,
                    )

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

        draft_answer = processed_result.get("response", "")
        context_text = str(graphrag_results.get("results", []))

        # ------------------------------------------------------------------
        # 4. NEW RAGAS EVALUATION PIPELINE (correct for ragas 0.3.9)
        # ------------------------------------------------------------------
        eval_service = EvaluationService()

        # Extract final answer from processed_result
        final_answer = processed_result.get("response", "")
        hybrid_mode = processed_result.get("metadata", {}).get("mode", "UNKNOWN")

        # Save evaluation asynchronously
        try:
            eval_service.evaluate_and_store_async(
                session_id=session_id,
                user_query=message_text,
                response_text=final_answer,
                graph_data=graphrag_results,
                metadata={"hybrid_mode": hybrid_mode}
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
            content=final_answer,
            created_at=timezone.now(),
            metadata=ai_metadata,
        )

        self.context_manager.add_message(
            session_id=session_id,
            role="assistant",
            content=final_answer,
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