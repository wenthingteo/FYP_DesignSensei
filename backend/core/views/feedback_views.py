from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
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
