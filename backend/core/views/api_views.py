from rest_framework import viewsets, status  # Import 'status' here
from rest_framework.response import Response  # Import 'Response' here
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
        """Handle conversation title updates - supports both PUT and PATCH"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        # Ensure the user owns this conversation
        if instance.user != request.user:
            return Response(
                {'error': 'You do not have permission to modify this conversation'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get the title from request data
        title = request.data.get('title')
        if not title or not title.strip():
            return Response(
                {'error': 'Title is required and cannot be empty'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update the title
        instance.title = title.strip()
        instance.save()

        # Return the updated conversation data
        serializer = self.get_serializer(instance)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def partial_update(self, request, *args, **kwargs):
        """Handle PATCH requests for partial update"""
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)


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