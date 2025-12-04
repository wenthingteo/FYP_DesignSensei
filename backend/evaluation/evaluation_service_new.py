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
    
    Features:
    - Compares responses with ground truth created by experts
    - Evaluates accuracy, completeness, and educational value
    - Implements automated feedback and flagging mechanisms
    - Supports both automated and human assessment
    - Tracks system performance over time
    - Identifies potentially incorrect information
    """

    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.api_key)

        logger.info("EvaluationService ready with ground truth comparison.")
    
    def evaluate_and_store_async(self, session_id, user_query, response_text, graph_data, metadata):
        """
        Start async thread to evaluate and save evaluation record without blocking main response.
        """
        logger.info(f"[EVAL] Starting async evaluation storage for session {session_id}")
        thread = threading.Thread(
            target=self._evaluate_and_store_worker,
            args=(session_id, user_query, response_text, graph_data, metadata),
            daemon=True
        )
        thread.start()

    def _evaluate_and_store_worker(self, session_id, user_query, response_text, graph_data, metadata):
        """
        Comprehensive evaluation worker that:
        1. Finds matching ground truth
        2. Evaluates accuracy, completeness, educational value
        3. Flags potentially incorrect information
        4. Stores detailed evaluation record
        """
        try:
            # Determine if RAG was used
            rag_used = bool(graph_data and graph_data.get("results"))
            
            # Calculate basic confidence score from graph results
            confidence_score = self._calculate_confidence(graph_data, rag_used)
            
            # Find matching ground truth
            ground_truth_match = self._find_matching_ground_truth(user_query)
            
            # Evaluate against ground truth if found
            accuracy_score = None
            completeness_score = None
            educational_value_score = None
            similarity_to_truth = None
            flagged_incorrect = False
            flag_reason = None
            
            if ground_truth_match:
                logger.info(f"📚 Found ground truth match for query: '{user_query[:50]}...'")
                
                # Evaluate response quality
                eval_results = self._evaluate_against_ground_truth(
                    user_query=user_query,
                    ai_response=response_text,
                    ground_truth=ground_truth_match.ground_truth,
                    context=ground_truth_match.context
                )
                
                accuracy_score = eval_results.get('accuracy')
                completeness_score = eval_results.get('completeness')
                educational_value_score = eval_results.get('educational_value')
                similarity_to_truth = eval_results.get('similarity')
                
                # Flag if accuracy is too low
                if accuracy_score and accuracy_score < 0.6:
                    flagged_incorrect = True
                    flag_reason = f"Low accuracy score: {accuracy_score:.2f}. Response may contain incorrect information."
                    logger.warning(f"⚠️ Flagged response for low accuracy: {accuracy_score:.2f}")
            
            # Create evaluation record
            EvaluationRecord.objects.create(
                session_id=session_id,
                user_query=user_query,
                ai_response=response_text,
                rag_used=rag_used,
                hybrid_mode=metadata.get("hybrid_mode", "UNKNOWN"),
                confidence_score=confidence_score,
                accuracy_score=accuracy_score,
                completeness_score=completeness_score,
                educational_value_score=educational_value_score,
                matched_ground_truth=ground_truth_match,
                similarity_to_truth=similarity_to_truth,
                flagged_incorrect=flagged_incorrect,
                flag_reason=flag_reason
            )
            
            logger.info(f"✅ Evaluation record saved: session={session_id}, accuracy={accuracy_score}, flagged={flagged_incorrect}")
            
        except Exception as e:
            logger.error(f"❌ Error in evaluation worker: {e}", exc_info=True)
    
    def _calculate_confidence(self, graph_data, rag_used):
        """Calculate confidence score from graph results"""
        confidence_score = None
        if rag_used and graph_data:
            confidence_score = graph_data.get("average_llm_score", 0.0)
            
            if confidence_score == 0.0:
                results = graph_data.get("results", [])
                if results:
                    top_scores = [r.get("relevance_score", 0.0) for r in results[:5]]
                    if top_scores:
                        confidence_score = sum(top_scores) / len(top_scores)
                        logger.info(f"📊 Calculated confidence from top {len(top_scores)} results: {confidence_score:.3f}")
        return confidence_score
    
    def _find_matching_ground_truth(self, user_query: str) -> Optional[GroundTruth]:
        """
        Find the most relevant ground truth entry for a given query
        Uses semantic similarity with embeddings
        """
        try:
            # Get all verified ground truths
            ground_truths = GroundTruth.objects.filter(verified=True)
            
            if not ground_truths.exists():
                logger.info("No verified ground truths available")
                return None
            
            # Get embedding for user query
            query_embedding = self._get_embedding(user_query)
            
            best_match = None
            best_similarity = 0.0
            
            for gt in ground_truths:
                # Get embedding for ground truth question
                gt_embedding = self._get_embedding(gt.question)
                
                # Calculate cosine similarity
                similarity = self._cosine_similarity(query_embedding, gt_embedding)
                
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = gt
            
            # Only return if similarity is above threshold
            if best_similarity > 0.7:  # 70% similarity threshold
                logger.info(f"✅ Ground truth match found: similarity={best_similarity:.3f}")
                return best_match
            else:
                logger.info(f"No strong ground truth match (best: {best_similarity:.3f})")
                return None
                
        except Exception as e:
            logger.error(f"Error finding ground truth: {e}")
            return None
    
    def _evaluate_against_ground_truth(self, user_query: str, ai_response: str, ground_truth: str, context: str = None) -> Dict:
        """
        Use LLM to evaluate AI response against ground truth
        Returns: accuracy, completeness, educational_value, similarity
        """
        try:
            evaluation_prompt = f"""You are an expert evaluator for educational AI responses.

Question: {user_query}

Ground Truth Answer (Expert Reference):
{ground_truth}

AI Generated Answer:
{ai_response}

Evaluate the AI answer on these dimensions (score 0.0-1.0):

1. ACCURACY: How factually correct is the AI answer compared to ground truth?
   - 1.0 = Perfectly accurate, all facts correct
   - 0.5 = Some inaccuracies or misconceptions
   - 0.0 = Major errors or incorrect information

2. COMPLETENESS: How complete is the AI answer?
   - 1.0 = Covers all key points from ground truth
   - 0.5 = Covers some but misses important points
   - 0.0 = Significantly incomplete

3. EDUCATIONAL_VALUE: How well does it teach the concept?
   - 1.0 = Clear, well-explained, good examples
   - 0.5 = Acceptable but could be clearer
   - 0.0 = Confusing or unhelpful

Output ONLY a JSON object with scores:
{{"accuracy": 0.X, "completeness": 0.X, "educational_value": 0.X}}"""

            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an evaluation expert. Output only JSON."},
                    {"role": "user", "content": evaluation_prompt}
                ],
                max_tokens=100,
                temperature=0
            )
            
            result_text = response.choices[0].message.content.strip()
            logger.info(f"🔍 LLM evaluation response: {result_text}")
            
            # Parse JSON
            import json
            import re
            # Extract JSON from response
            json_match = re.search(r'\{[^}]+\}', result_text)
            if json_match:
                scores = json.loads(json_match.group())
                
                # Calculate semantic similarity
                ai_embedding = self._get_embedding(ai_response)
                truth_embedding = self._get_embedding(ground_truth)
                similarity = self._cosine_similarity(ai_embedding, truth_embedding)
                
                scores['similarity'] = similarity
                
                logger.info(f"✅ Evaluation scores: accuracy={scores.get('accuracy'):.2f}, "
                          f"completeness={scores.get('completeness'):.2f}, "
                          f"educational={scores.get('educational_value'):.2f}")
                
                return scores
            else:
                logger.warning("Failed to parse evaluation JSON")
                return {'accuracy': 0.5, 'completeness': 0.5, 'educational_value': 0.5, 'similarity': 0.5}
                
        except Exception as e:
            logger.error(f"Error evaluating against ground truth: {e}", exc_info=True)
            return {'accuracy': None, 'completeness': None, 'educational_value': None, 'similarity': None}
    
    def _get_embedding(self, text: str) -> list:
        """Get OpenAI embedding for text"""
        try:
            response = self.client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error getting embedding: {e}")
            return [0.0] * 1536  # Return zero vector on error
    
    def _cosine_similarity(self, vec1: list, vec2: list) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            vec1 = np.array(vec1)
            vec2 = np.array(vec2)
            
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return float(dot_product / (norm1 * norm2))
        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {e}")
            return 0.0
    
    def get_performance_report(self, start_date=None, end_date=None) -> Dict:
        """
        Generate performance report for tracking system quality
        """
        try:
            from django.db.models import Avg, Count, Q
            from datetime import datetime, timedelta
            
            # Default to last 7 days if no dates provided
            if not end_date:
                end_date = datetime.now()
            if not start_date:
                start_date = end_date - timedelta(days=7)
            
            # Get all evaluations in date range
            evals = EvaluationRecord.objects.filter(
                created_at__range=(start_date, end_date)
            )
            
            # Calculate aggregates
            stats = evals.aggregate(
                total_responses=Count('id'),
                avg_accuracy=Avg('accuracy_score'),
                avg_completeness=Avg('completeness_score'),
                avg_educational_value=Avg('educational_value_score'),
                avg_confidence=Avg('confidence_score'),
                flagged_count=Count('id', filter=Q(flagged_incorrect=True))
            )
            
            # Get mode distribution
            mode_distribution = {}
            for mode in ['LLM_ONLY', 'HYBRID_BLEND', 'GRAPH_RAG']:
                mode_distribution[mode] = evals.filter(hybrid_mode=mode).count()
            
            report = {
                'period': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                },
                'overview': stats,
                'mode_distribution': mode_distribution,
                'quality_flags': {
                    'flagged_responses': stats['flagged_count'],
                    'flag_rate': stats['flagged_count'] / stats['total_responses'] if stats['total_responses'] > 0 else 0
                }
            }
            
            logger.info(f"📊 Performance report generated: {stats['total_responses']} responses analyzed")
            return report
            
        except Exception as e:
            logger.error(f"Error generating performance report: {e}", exc_info=True)
            return {}
