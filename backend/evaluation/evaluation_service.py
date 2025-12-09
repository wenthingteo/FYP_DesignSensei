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

            # Find matching ground truth and calculate semantic similarity
            matched_ground_truth, similarity_score, accuracy, completeness, educational_value = self._compare_with_ground_truth(
                user_query, response_text
            )

            # Auto-flag if accuracy is low
            flagged_incorrect = False
            flag_reason = None
            if accuracy is not None and accuracy < 0.6:
                flagged_incorrect = True
                flag_reason = f"Low accuracy score: {accuracy:.2f}. Requires human review."

            EvaluationRecord.objects.create(
                session_id=session_id,
                user_query=user_query,
                ai_response=response_text,
                rag_used=rag_used,
                hybrid_mode=metadata.get("hybrid_mode", "UNKNOWN"),
                confidence_score=confidence_score,
                matched_ground_truth=matched_ground_truth,
                similarity_to_truth=similarity_score,
                accuracy_score=accuracy,
                completeness_score=completeness,
                educational_value_score=educational_value,
                flagged_incorrect=flagged_incorrect,
                flag_reason=flag_reason
            )
            
            logger.info(f"✅ Evaluation record saved: session={session_id}, mode={metadata.get('hybrid_mode')}, rag={rag_used}, score={confidence_score}, accuracy={accuracy}")

        except Exception as e:
            logger.error(f"❌ Error saving evaluation record: {e}", exc_info=True)

    def _compare_with_ground_truth(self, user_query, ai_response):
        """
        Compare AI response with ground truth database
        Returns: (matched_ground_truth, similarity_score, accuracy, completeness, educational_value)
        """
        try:
            # Find matching ground truth by semantic similarity
            ground_truths = GroundTruth.objects.filter(verified=True)
            
            if not ground_truths.exists():
                logger.info("No verified ground truths available for comparison")
                return None, None, None, None, None

            # Initialize embedding model if needed
            if self.embedding_model is None:
                self._ensure_ragas_loaded()

            # Get query embedding
            query_embedding = self.embedding_model.encode([user_query])[0]
            
            # Find best matching ground truth
            best_match = None
            best_similarity = 0.0
            
            for gt in ground_truths:
                gt_embedding = self.embedding_model.encode([gt.question])[0]
                similarity = np.dot(query_embedding, gt_embedding) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(gt_embedding)
                )
                
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = gt
            
            # Only proceed if similarity is high enough (>0.7 means similar questions)
            if best_similarity < 0.7:
                logger.info(f"No ground truth match found (best similarity: {best_similarity:.2f})")
                return None, None, None, None, None
            
            logger.info(f"Found ground truth match with similarity: {best_similarity:.2f}")
            
            # Calculate quality metrics using LLM
            accuracy, completeness, educational_value = self._calculate_quality_metrics(
                user_query, ai_response, best_match.ground_truth
            )
            
            return best_match, best_similarity, accuracy, completeness, educational_value

        except Exception as e:
            logger.error(f"Error comparing with ground truth: {e}", exc_info=True)
            return None, None, None, None, None

    def _calculate_quality_metrics(self, user_query, ai_response, ground_truth_answer):
        """
        Use LLM to evaluate accuracy, completeness, and educational value
        """
        try:
            evaluation_prompt = f"""You are evaluating an AI tutor's response for educational quality.

USER QUESTION: {user_query}

AI RESPONSE: {ai_response}

GROUND TRUTH (CORRECT ANSWER): {ground_truth_answer}

Evaluate the AI response on three dimensions (return scores as decimals 0.0-1.0):

1. ACCURACY: How factually correct is the AI response compared to the ground truth?
   - 1.0: Completely accurate, all facts correct
   - 0.7-0.9: Mostly accurate with minor issues
   - 0.4-0.6: Partially accurate, some errors
   - 0.0-0.3: Inaccurate or misleading

2. COMPLETENESS: How comprehensive is the response?
   - 1.0: Covers all key concepts from ground truth
   - 0.7-0.9: Covers most key concepts
   - 0.4-0.6: Missing important concepts
   - 0.0-0.3: Incomplete or superficial

3. EDUCATIONAL_VALUE: How well does it help students learn?
   - 1.0: Excellent explanation with examples
   - 0.7-0.9: Good explanation, clear
   - 0.4-0.6: Basic explanation
   - 0.0-0.3: Confusing or unhelpful

Return ONLY three numbers separated by commas (e.g., 0.85,0.90,0.88):
"""

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert educational evaluator. Return only three decimal numbers separated by commas."},
                    {"role": "user", "content": evaluation_prompt}
                ],
                max_tokens=20,
                temperature=0
            )

            result = response.choices[0].message.content.strip()
            logger.info(f"Quality metrics raw result: {result}")
            
            # Parse the three scores
            scores = [float(x.strip()) for x in result.split(',')]
            accuracy = scores[0] if len(scores) > 0 else None
            completeness = scores[1] if len(scores) > 1 else None
            educational_value = scores[2] if len(scores) > 2 else None
            
            logger.info(f"Quality metrics: accuracy={accuracy:.2f}, completeness={completeness:.2f}, educational_value={educational_value:.2f}")
            
            return accuracy, completeness, educational_value

        except Exception as e:
            logger.error(f"Error calculating quality metrics: {e}", exc_info=True)
            return None, None, None

    def get_performance_report(self):
        """
        Generate comprehensive performance report for FYP demonstration
        Shows that GraphRAG achieves the objective of accurate answer generation
        """
        from django.db.models import Avg, Count, Q, F
        
        logger.info("Generating FYP performance report...")
        
        # Overall GraphRAG Performance
        graph_rag_stats = EvaluationRecord.objects.filter(
            hybrid_mode="GRAPH_RAG"
        ).aggregate(
            total_queries=Count('id'),
            avg_accuracy=Avg('accuracy_score'),
            avg_completeness=Avg('completeness_score'),
            avg_educational_value=Avg('educational_value_score'),
            avg_confidence=Avg('confidence_score'),
            high_accuracy_count=Count('id', filter=Q(accuracy_score__gte=0.7)),
            low_accuracy_count=Count('id', filter=Q(accuracy_score__lt=0.6))
        )
        
        # Compare: GraphRAG vs LLM-Only vs Hybrid
        mode_comparison = {}
        for mode in ['GRAPH_RAG', 'LLM_ONLY', 'HYBRID_BLEND']:
            stats = EvaluationRecord.objects.filter(hybrid_mode=mode).aggregate(
                count=Count('id'),
                avg_accuracy=Avg('accuracy_score'),
                avg_completeness=Avg('completeness_score'),
                avg_educational_value=Avg('educational_value_score'),
                avg_confidence=Avg('confidence_score')
            )
            
            # Calculate flagged rate safely
            total_count = stats['count'] or 0
            if total_count > 0:
                flagged_count = EvaluationRecord.objects.filter(
                    hybrid_mode=mode, 
                    flagged_incorrect=True
                ).count()
                stats['flagged_rate'] = (flagged_count / total_count) * 100
            else:
                stats['flagged_rate'] = 0.0
                
            mode_comparison[mode] = stats
        
        # Ground Truth Match Statistics
        ground_truth_stats = EvaluationRecord.objects.filter(
            matched_ground_truth__isnull=False
        ).aggregate(
            total_matched=Count('id'),
            avg_similarity=Avg('similarity_to_truth'),
            high_match_count=Count('id', filter=Q(similarity_to_truth__gte=0.8)),
            avg_accuracy_with_gt=Avg('accuracy_score')
        )
        
        # Quality Assurance Statistics
        quality_stats = EvaluationRecord.objects.aggregate(
            total_evaluations=Count('id'),
            flagged_count=Count('id', filter=Q(flagged_incorrect=True)),
            human_reviewed=Count('id', filter=Q(reviewed_at__isnull=False)),
            avg_human_rating=Avg('human_rating'),
            with_ground_truth=Count('id', filter=Q(matched_ground_truth__isnull=False))
        )
        
        # Calculate success metrics
        graph_rag_accuracy = graph_rag_stats.get('avg_accuracy') or 0.0
        llm_only_accuracy = mode_comparison.get('LLM_ONLY', {}).get('avg_accuracy') or 0.0
        
        return {
            'graph_rag_performance': graph_rag_stats,
            'mode_comparison': mode_comparison,
            'ground_truth_accuracy': ground_truth_stats,
            'quality_assurance': quality_stats,
            'objective_achieved': graph_rag_accuracy >= 0.7,
            'graph_rag_improvement': graph_rag_accuracy - llm_only_accuracy if llm_only_accuracy > 0 else None
        }