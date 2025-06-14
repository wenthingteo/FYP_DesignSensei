from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from core.models import Conversation, Message
from core.serializers import ConversationSerializer, MessageSerializer


class ConversationViewSet(viewsets.ModelViewSet):
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Conversation.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def update(self, request, *args, **kwargs):
        """Handle conversation title updates"""
        conversation = self.get_object()
        title = request.data.get('title')
        
        if not title:
            return Response({'error': 'Title is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        conversation.title = title
        conversation.save()
        
        return conversation.title


class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Change 'conversation_id' to 'conversation_pk'
        conversation_id = self.kwargs.get('conversation_pk')
        return Message.objects.filter(
            conversation__id=conversation_id,
            conversation__user=self.request.user
        )

    def perform_create(self, serializer):
        # Change 'conversation_id' to 'conversation_pk'
        conversation_id = self.kwargs.get('conversation_pk')
        conversation = Conversation.objects.get(
            id=conversation_id, user=self.request.user
        )
        serializer.save(conversation=conversation)