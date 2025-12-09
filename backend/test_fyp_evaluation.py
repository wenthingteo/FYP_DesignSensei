"""
Test script to verify FYP evaluation system is working
Tests ground truth matching, quality metrics, and performance reporting
"""
import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from core.models import EvaluationRecord, GroundTruth
from evaluation.evaluation_service import EvaluationService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_ground_truth_database():
    """Test that ground truth database is populated"""
    print("\n" + "="*60)
    print("TEST 1: Ground Truth Database")
    print("="*60)
    
    total = GroundTruth.objects.count()
    verified = GroundTruth.objects.filter(verified=True).count()
    
    print(f"✅ Total ground truths: {total}")
    print(f"✅ Verified ground truths: {verified}")
    
    # Show sample
    sample = GroundTruth.objects.first()
    if sample:
        print(f"\nSample Ground Truth:")
        print(f"  Question: {sample.question[:80]}...")
        print(f"  Answer length: {len(sample.ground_truth)} characters")
        print(f"  Verified: {sample.verified}")
    
    return total >= 25


def test_evaluation_records():
    """Test evaluation records exist"""
    print("\n" + "="*60)
    print("TEST 2: Evaluation Records")
    print("="*60)
    
    total = EvaluationRecord.objects.count()
    with_accuracy = EvaluationRecord.objects.filter(accuracy_score__isnull=False).count()
    with_ground_truth = EvaluationRecord.objects.filter(matched_ground_truth__isnull=False).count()
    
    print(f"✅ Total evaluation records: {total}")
    print(f"✅ Records with accuracy scores: {with_accuracy}")
    print(f"✅ Records matched to ground truth: {with_ground_truth}")
    
    # Show mode distribution
    from django.db.models import Count
    mode_dist = EvaluationRecord.objects.values('hybrid_mode').annotate(count=Count('id'))
    
    print(f"\nMode Distribution:")
    for item in mode_dist:
        print(f"  {item['hybrid_mode']}: {item['count']}")
    
    return total > 0


def test_performance_report():
    """Test performance report generation"""
    print("\n" + "="*60)
    print("TEST 3: Performance Report Generation")
    print("="*60)
    
    try:
        service = EvaluationService()
        report = service.get_performance_report()
        
        print(f"✅ Performance report generated successfully")
        
        # Display key metrics
        graph_rag = report['graph_rag_performance']
        print(f"\nGraphRAG Performance:")
        print(f"  Total queries: {graph_rag.get('total_queries', 0)}")
        print(f"  Avg accuracy: {graph_rag.get('avg_accuracy', 0.0):.3f}" if graph_rag.get('avg_accuracy') else "  Avg accuracy: N/A")
        print(f"  Avg completeness: {graph_rag.get('avg_completeness', 0.0):.3f}" if graph_rag.get('avg_completeness') else "  Avg completeness: N/A")
        print(f"  Avg educational value: {graph_rag.get('avg_educational_value', 0.0):.3f}" if graph_rag.get('avg_educational_value') else "  Avg educational value: N/A")
        
        # Success criteria
        objective_achieved = report.get('objective_achieved', False)
        print(f"\n{'✅' if objective_achieved else '⚠️'} FYP Objective Achieved: {objective_achieved}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error generating report: {e}")
        return False


def test_ground_truth_matching():
    """Test semantic matching of questions to ground truth"""
    print("\n" + "="*60)
    print("TEST 4: Ground Truth Semantic Matching")
    print("="*60)
    
    try:
        service = EvaluationService()
        
        # Test queries that should match ground truths
        test_queries = [
            "explain domain driven design",
            "what is DDD?",
            "tell me about the repository pattern",
            "how does singleton work?"
        ]
        
        for query in test_queries:
            matched_gt, similarity, acc, comp, edu = service._compare_with_ground_truth(
                query, 
                "This is a test answer about the topic."
            )
            
            if matched_gt:
                print(f"\n✅ Query: '{query}'")
                print(f"   Matched: {matched_gt.question[:60]}...")
                print(f"   Similarity: {similarity:.3f}")
            else:
                print(f"\n⚠️ Query: '{query}' - No match found")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing matching: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print(" FYP OBJECTIVE EVALUATION SYSTEM - VERIFICATION TEST")
    print("="*70)
    print("\nObjective: Evaluate GraphRAG chatbot performance based on answer accuracy")
    print("-"*70)
    
    results = []
    
    # Run tests
    results.append(("Ground Truth Database", test_ground_truth_database()))
    results.append(("Evaluation Records", test_evaluation_records()))
    results.append(("Performance Report", test_performance_report()))
    results.append(("Semantic Matching", test_ground_truth_matching()))
    
    # Summary
    print("\n" + "="*70)
    print(" TEST SUMMARY")
    print("="*70)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status:10} | {test_name}")
    
    all_passed = all(result[1] for result in results)
    
    print("\n" + "="*70)
    if all_passed:
        print("🎉 ALL TESTS PASSED - System ready for FYP demonstration!")
    else:
        print("⚠️  Some tests failed - review errors above")
    print("="*70)
    
    print("\n📊 Next steps:")
    print("1. Access performance report: GET /api/evaluation/performance-report/")
    print("2. View dashboard data: GET /api/evaluation/dashboard/")
    print("3. Manage ground truths: GET /api/evaluation/ground-truth/")
    print("\n💡 Generate more evaluation data by chatting with the system!")


if __name__ == '__main__':
    main()
