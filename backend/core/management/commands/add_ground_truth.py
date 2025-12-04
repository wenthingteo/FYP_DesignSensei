from django.core.management.base import BaseCommand
from core.models import GroundTruth


class Command(BaseCommand):
    help = 'Add ground truth entries for evaluation'

    def add_arguments(self, parser):
        parser.add_argument('--question', type=str, required=True, help='The question')
        parser.add_argument('--ground_truth', type=str, required=True, help='The expert answer')
        parser.add_argument('--context', type=str, default='', help='Optional context')
        parser.add_argument('--created_by', type=str, default='admin', help='Creator name')
        parser.add_argument('--verified', action='store_true', help='Mark as verified')

    def handle(self, *args, **options):
        gt = GroundTruth.objects.create(
            question=options['question'],
            ground_truth=options['ground_truth'],
            context=options['context'],
            created_by=options['created_by'],
            verified=options['verified']
        )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Ground truth added: "{gt.question[:50]}..." (ID: {gt.id}, Verified: {gt.verified})'
            )
        )
