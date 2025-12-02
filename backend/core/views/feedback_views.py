from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from core.models import Feedback


class FeedbackView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        comment = request.data.get('comment')
        if comment:
            Feedback.objects.create(user=request.user, comment=comment)
            return Response({'success': True})
        return Response({'error': 'No comment provided'}, status=status.HTTP_400_BAD_REQUEST)


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
        
        feedback_data = [
            {
                'id': fb.id,
                'username': fb.user.username,
                'email': fb.user.email,
                'comment': fb.comment,
                'created_at': fb.created_at.isoformat(),
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
