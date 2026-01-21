from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db.models import Avg, Count, Q
import logging

from evaluation.evaluation_service import EvaluationService
from core.models import EvaluationRecord, GroundTruth

logger = logging.getLogger(__name__)


def is_admin_user(user):
    """Check if user has admin privileges"""
    return user.is_staff or user.is_superuser


class PerformanceReportView(APIView):
    """
    FYP Objective Demonstration: GraphRAG Performance Evaluation
    Endpoint to show that the system achieves accurate answer generation
    Admin-only access.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Generate comprehensive performance report"""
        # Check admin privileges
        if not is_admin_user(request.user):
            return Response(
                {'error': 'Admin privileges required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            eval_service = EvaluationService()
            report = eval_service.get_performance_report()
            
            # Define success criteria for FYP
            graph_rag_accuracy = report['graph_rag_performance'].get('avg_accuracy') or 0.0
            graph_rag_completeness = report['graph_rag_performance'].get('avg_completeness') or 0.0
            graph_rag_educational = report['graph_rag_performance'].get('avg_educational_value') or 0.0
            
            llm_only_accuracy = report['mode_comparison'].get('LLM_ONLY', {}).get('avg_accuracy') or 0.0
            
            success_metrics = {
                "accuracy_target": 0.70,
                "accuracy_achieved": round(graph_rag_accuracy, 3) if graph_rag_accuracy else 0.0,
                "accuracy_met": graph_rag_accuracy >= 0.70,
                
                "completeness_target": 0.75,
                "completeness_achieved": round(graph_rag_completeness, 3) if graph_rag_completeness else 0.0,
                "completeness_met": graph_rag_completeness >= 0.75,
                
                "educational_value_target": 0.80,
                "educational_value_achieved": round(graph_rag_educational, 3) if graph_rag_educational else 0.0,
                "educational_value_met": graph_rag_educational >= 0.80,
                
                "graph_rag_better_than_llm": graph_rag_accuracy > llm_only_accuracy if llm_only_accuracy > 0 else None,
                "improvement_percentage": round((graph_rag_accuracy - llm_only_accuracy) * 100, 2) if llm_only_accuracy > 0 else None
            }
            
            # Overall conclusion
            objectives_met = [
                success_metrics['accuracy_met'],
                success_metrics['graph_rag_better_than_llm'] if success_metrics['graph_rag_better_than_llm'] is not None else True
            ]
            
            conclusion = "OBJECTIVE ACHIEVED ✅" if all(objectives_met) else "NEEDS IMPROVEMENT ⚠️"
            
            return Response({
                "fyp_objective": "Evaluate the performance of the GraphRAG chatbot based on answer accuracy",
                "evaluation_summary": report,
                "success_metrics": success_metrics,
                "conclusion": conclusion,
                "recommendations": self._generate_recommendations(success_metrics, report)
            })
            
        except Exception as e:
            logger.error(f"Error generating performance report: {e}", exc_info=True)
            return Response({
                "error": "Failed to generate performance report",
                "detail": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _generate_recommendations(self, success_metrics, report):
        """Generate actionable recommendations based on performance"""
        recommendations = []
        
        if not success_metrics['accuracy_met']:
            recommendations.append("Expand ground truth database to improve accuracy measurement")
        
        if success_metrics['graph_rag_better_than_llm'] is False:
            recommendations.append("Optimize graph search parameters and relevance scoring")
        
        gt_stats = report.get('ground_truth_accuracy', {})
        if gt_stats.get('total_matched', 0) < 20:
            recommendations.append("Add more verified ground truth questions for better evaluation coverage")
        
        flagged_rate = report['mode_comparison'].get('GRAPH_RAG', {}).get('flagged_rate', 0)
        if flagged_rate > 5:
            recommendations.append(f"High flagged rate ({flagged_rate:.1f}%) - review flagged responses")
        
        if not recommendations:
            recommendations.append("System performing well! Continue monitoring and expanding ground truth database.")
        
        return recommendations


class EvaluationDashboardView(APIView):
    """
    Dashboard view for visualization of evaluation metrics
    Provides data for charts and graphs
    Admin-only access
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get dashboard data for visualization"""
        # Check admin privileges
        if not is_admin_user(request.user):
            return Response(
                {'error': 'Admin privileges required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            # Mode distribution
            mode_distribution = []
            for mode in ['GRAPH_RAG', 'LLM_ONLY', 'HYBRID_BLEND']:
                count = EvaluationRecord.objects.filter(hybrid_mode=mode).count()
                mode_distribution.append({
                    "mode": mode,
                    "count": count
                })
            
            # Accuracy distribution by mode
            accuracy_by_mode = []
            for mode in ['GRAPH_RAG', 'LLM_ONLY', 'HYBRID_BLEND']:
                avg_accuracy = EvaluationRecord.objects.filter(
                    hybrid_mode=mode,
                    accuracy_score__isnull=False
                ).aggregate(avg=Avg('accuracy_score'))['avg']
                
                accuracy_by_mode.append({
                    "mode": mode,
                    "accuracy": round(avg_accuracy, 3) if avg_accuracy else 0.0
                })
            
            # Quality metrics over time (last 30 evaluations)
            recent_evaluations = EvaluationRecord.objects.filter(
                accuracy_score__isnull=False
            ).order_by('-created_at')[:30]
            
            quality_timeline = []
            for eval_record in reversed(list(recent_evaluations)):
                quality_timeline.append({
                    "id": eval_record.id,
                    "accuracy": round(eval_record.accuracy_score, 3) if eval_record.accuracy_score else 0.0,
                    "completeness": round(eval_record.completeness_score, 3) if eval_record.completeness_score else 0.0,
                    "educational_value": round(eval_record.educational_value_score, 3) if eval_record.educational_value_score else 0.0,
                    "mode": eval_record.hybrid_mode
                })
            
            # Flagged vs Passed
            flagged_summary = {
                "flagged": EvaluationRecord.objects.filter(flagged_incorrect=True).count(),
                "passed": EvaluationRecord.objects.filter(flagged_incorrect=False).count(),
                "total": EvaluationRecord.objects.count()
            }
            
            # Ground truth coverage
            ground_truth_coverage = {
                "total_ground_truths": GroundTruth.objects.filter(verified=True).count(),
                "evaluations_with_ground_truth": EvaluationRecord.objects.filter(
                    matched_ground_truth__isnull=False
                ).count(),
                "avg_similarity": EvaluationRecord.objects.filter(
                    matched_ground_truth__isnull=False
                ).aggregate(avg=Avg('similarity_to_truth'))['avg']
            }
            
            return Response({
                "mode_distribution": mode_distribution,
                "accuracy_by_mode": accuracy_by_mode,
                "quality_timeline": quality_timeline,
                "flagged_summary": flagged_summary,
                "ground_truth_coverage": ground_truth_coverage
            })
            
        except Exception as e:
            logger.error(f"Error generating dashboard data: {e}", exc_info=True)
            return Response({
                "error": "Failed to generate dashboard data",
                "detail": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GroundTruthManagementView(APIView):
    """
    Manage ground truth database
    Admin-only access
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """List all ground truths"""
        # Check admin privileges
        if not is_admin_user(request.user):
            return Response(
                {'error': 'Admin privileges required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        ground_truths = GroundTruth.objects.all().order_by('-created_at')
        
        data = []
        for gt in ground_truths:
            data.append({
                "id": gt.id,
                "question": gt.question,
                "ground_truth": gt.ground_truth,
                "verified": gt.verified,
                "created_by": gt.created_by,
                "created_at": gt.created_at.isoformat(),
                "usage_count": gt.evaluations.count()
            })
        
        return Response({
            "ground_truths": data,
            "total": len(data),
            "verified": sum(1 for gt in data if gt['verified'])
        })

    def post(self, request):
        """Add new ground truth"""
        # Check admin privileges
        if not is_admin_user(request.user):
            return Response(
                {'error': 'Admin privileges required'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            question = request.data.get('question')
            ground_truth = request.data.get('ground_truth')
            context = request.data.get('context', '')
            verified = request.data.get('verified', False)
            
            if not question or not ground_truth:
                return Response({
                    "error": "Question and ground_truth are required"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            gt = GroundTruth.objects.create(
                question=question,
                ground_truth=ground_truth,
                context=context,
                verified=verified,
                created_by=request.user.username
            )
            
            return Response({
                "message": "Ground truth created successfully",
                "id": gt.id
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error creating ground truth: {e}", exc_info=True)
            return Response({
                "error": "Failed to create ground truth",
                "detail": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
