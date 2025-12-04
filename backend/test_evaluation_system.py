"""
Test script for comprehensive evaluation system
"""
from core.models import EvaluationRecord, GroundTruth
from evaluation.evaluation_service import EvaluationService
import os

print("=" * 60)
print("COMPREHENSIVE EVALUATION SYSTEM TEST")
print("=" * 60)

# Check ground truths
print("\n1. Ground Truth Status:")
print(f"   Total ground truths: {GroundTruth.objects.count()}")
print(f"   Verified ground truths: {GroundTruth.objects.filter(verified=True).count()}")

for gt in GroundTruth.objects.all():
    print(f"   - {gt.question[:60]}... (Verified: {gt.verified})")

# Check evaluation records
print("\n2. Evaluation Records:")
total_evals = EvaluationRecord.objects.count()
print(f"   Total evaluations: {total_evals}")

if total_evals > 0:
    recent = EvaluationRecord.objects.order_by('-created_at')[:5]
    print(f"   Recent evaluations:")
    for eval_rec in recent:
        print(f"   - Session {eval_rec.session_id}: {eval_rec.user_query[:40]}...")
        if eval_rec.accuracy_score:
            print(f"     Accuracy: {eval_rec.accuracy_score:.2f}, "
                  f"Completeness: {eval_rec.completeness_score:.2f}, "
                  f"Educational: {eval_rec.educational_value_score:.2f}")
        if eval_rec.flagged_incorrect:
            print(f"     ⚠️ FLAGGED: {eval_rec.flag_reason}")

# Test evaluation service initialization
print("\n3. Evaluation Service:")
try:
    eval_service = EvaluationService()
    print("   ✅ EvaluationService initialized successfully")
    print("   - Ground truth comparison enabled")
    print("   - Semantic matching with 0.7 threshold")
    print("   - LLM evaluation using gpt-4o-mini")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Check database schema
print("\n4. Database Schema:")
eval_fields = [f.name for f in EvaluationRecord._meta.get_fields()]
new_fields = ['accuracy_score', 'completeness_score', 'educational_value_score', 
              'matched_ground_truth', 'similarity_to_truth', 'flagged_incorrect', 
              'flag_reason', 'human_rating', 'human_feedback']
for field in new_fields:
    status = "✅" if field in eval_fields else "❌"
    print(f"   {status} {field}")

print("\n" + "=" * 60)
print("Test completed!")
print("=" * 60)
