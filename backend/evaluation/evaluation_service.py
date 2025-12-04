import logging
import os
from typing import List, Dict, Optional
import threading
from core.models import EvaluationRecord, GroundTruth
from openai import OpenAI
import numpy as np

logger = logging.getLogger(__name__)


class EvaluationService:
    """
    Comprehensive Evaluation Service for Educational AI Responses
    - Compares responses with ground truth
    - Evaluates accuracy, completeness, educational value
    - Implements automated feedback and flagging
    - Supports both automated and human assessment
    """

    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.api_key)

        # Lazy load - only initialize when actually evaluating
        self.embedding_model = None
        self._ragas_imported = False

        logger.info("EvaluationService ready with ground truth comparison.")
    
    def _ensure_ragas_loaded(self):
        """Lazy load heavy dependencies only when needed"""
        if not self._ragas_imported:
            logger.info("Loading RAGAS dependencies...")
            global Dataset, evaluate, answer_relevancy, faithfulness, SentenceTransformer
            from datasets import Dataset
            from ragas import evaluate
            from ragas.metrics import answer_relevancy, faithfulness
            from sentence_transformers import SentenceTransformer
            
            logger.info("Initializing SentenceTransformer for embeddings...")
            self.embedding_model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
            self._ragas_imported = True
            logger.info("RAGAS dependencies loaded successfully.")

    # --------------------------
    # LLM CALL (for Ragas)
    # --------------------------
    async def llm_callable(self, prompt: str) -> str:
        """
        RAGAS expects: async fn(prompt) -> string
        """

        response = self.client.chat.completions.create(
            model="gpt-4.1-nano-2025-04-14",
            messages=[{"role": "user", "content": prompt}]
        )

        return response.choices[0].message.content

    # --------------------------
    # EMBEDDING CALL (for Ragas)
    # --------------------------
    async def embed_callable(self, texts: List[str]) -> List[List[float]]:
        """
        RAGAS expects: async fn(list[str]) -> list[list[float]]
        """
        if self.embedding_model is None:
            self._ensure_ragas_loaded()
        return self.embedding_model.encode(texts, convert_to_numpy=False).tolist()

    # --------------------------
    # MAIN EVALUATION METHOD
    # --------------------------
    async def evaluate_answer(self, user_question: str, generated_answer: str, context_chunks: List[str]):
        """
        Runs RAGAS evaluation on LLM result.
        """
        self._ensure_ragas_loaded()

        logger.info("Running RAGAS evaluation (0.3.9)...")

        # Prepare dataset
        ragas_input = Dataset.from_dict({
            "question": [user_question],
            "answer": [generated_answer],
            "contexts": [context_chunks],
        })

        # Run evaluation
        result = await evaluate(
            dataset=ragas_input,
            metrics=[
                answer_relevancy,
                faithfulness
            ],
            llm=self.llm_callable,
            embed=self.embed_callable
        )

        relevancy = result["answer_relevancy"][0]
        faithful = result["faithfulness"][0]

        # Combine (simple weighted average)
        combined = (relevancy * 0.6) + (faithful * 0.4)

        logger.info(f"RAGAS Evaluation => rel={relevancy:.3f} faith={faithful:.3f} combined={combined:.3f}")

        return {
            "relevance": float(relevancy),
            "faithfulness": float(faithful),
            "combined": float(combined)
        }
    
    def evaluate_and_store_async(self, session_id, user_query, response_text, graph_data, metadata):
        """
        Start async thread to save evaluation record without blocking main response.
        """
        logger.info(f"[EVAL] Starting async evaluation storage for session {session_id}")
        thread = threading.Thread(
            target=self._evaluate_and_store_worker,
            args=(session_id, user_query, response_text, graph_data, metadata),
            daemon=True
        )
        thread.start()

    def _evaluate_and_store_worker(self, session_id, user_query, response_text, graph_data, metadata):
        try:
            # Determine if RAG was used based on graph data
            rag_used = bool(graph_data and graph_data.get("results"))
            
            # Calculate confidence score from graph results if available
            confidence_score = None
            if rag_used:
                # Try to get LLM relevance score first
                confidence_score = graph_data.get("average_llm_score", 0.0)
                
                # If that's 0, calculate from graph results relevance scores
                if confidence_score == 0.0:
                    results = graph_data.get("results", [])
                    if results:
                        # Average the top 5 results' relevance scores
                        top_scores = [r.get("relevance_score", 0.0) for r in results[:5]]
                        if top_scores:
                            confidence_score = sum(top_scores) / len(top_scores)
                            logger.info(f"📊 Calculated confidence from top {len(top_scores)} results: {confidence_score:.3f}")

            EvaluationRecord.objects.create(
                session_id=session_id,
                user_query=user_query,
                ai_response=response_text,
                rag_used=rag_used,
                hybrid_mode=metadata.get("hybrid_mode", "UNKNOWN"),
                confidence_score=confidence_score
            )
            
            logger.info(f"✅ Evaluation record saved: session={session_id}, mode={metadata.get('hybrid_mode')}, rag={rag_used}, score={confidence_score}")

        except Exception as e:
            logger.error(f"❌ Error saving evaluation record: {e}", exc_info=True)