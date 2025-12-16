from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from core.models import Feedback


class FeedbackView(APIView):
    permission_classes = []  # Allow anonymous feedback

    def post(self, request):
        comment = request.data.get('feedback') or request.data.get('comment')
        rating = request.data.get('rating', 0)
        feedback_type = request.data.get('feedbackType', 'general')
        name = request.data.get('name', '')
        email = request.data.get('email', '')
        
        if not comment:
            return Response({'error': 'Feedback is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create feedback with optional user (if authenticated)
        feedback_data = {
            'comment': comment,
            'rating': rating,
            'feedback_type': feedback_type,
            'name': name,
            'email': email,
        }
        
        if request.user.is_authenticated:
            feedback_data['user'] = request.user
            
        Feedback.objects.create(**feedback_data)
        return Response({'success': True, 'message': 'Thank you for your feedback!'})


class AdminFeedbackView(APIView):
    """
    Admin-only endpoint to view all feedback submissions.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Get all feedback with user information.
        Only accessible to staff or superuser accounts.
        """
        # Check if user is staff or superuser
        if not (request.user.is_staff or request.user.is_superuser):
            return Response(
                {'error': 'Admin privileges required'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        feedbacks = Feedback.objects.select_related('user').order_by('-created_at')
        
        from django.utils import timezone
        import pytz
        malaysia_tz = pytz.timezone('Asia/Kuala_Lumpur')
        
        feedback_data = [
            {
                'id': fb.id,
                'user': fb.user.username if fb.user else (fb.name or 'Anonymous'),
                'email': fb.email or (fb.user.email if fb.user else 'N/A'),
                'comment': fb.comment,
                'rating': fb.rating,
                'feedback_type': fb.get_feedback_type_display(),
                'created_at': fb.created_at.astimezone(malaysia_tz).strftime('%Y-%m-%d %H:%M:%S')
            }
            for fb in feedbacks
        ]
        
        return Response({
            'success': True,
            'count': len(feedback_data),
            'feedbacks': feedback_data
        })
    
    def delete(self, request, feedback_id):
        """
        Delete a specific feedback by ID.
        Only accessible to staff or superuser accounts.
        """
        # Check if user is staff or superuser
        if not (request.user.is_staff or request.user.is_superuser):
            return Response(
                {'error': 'Admin privileges required'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            feedback = Feedback.objects.get(id=feedback_id)
            feedback.delete()
            return Response({'success': True, 'message': 'Feedback deleted'})
        except Feedback.DoesNotExist:
            return Response({'error': 'Feedback not found'}, status=status.HTTP_404_NOT_FOUND)
