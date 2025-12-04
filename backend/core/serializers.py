from rest_framework import serializers
from .models import Conversation, Message

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = '__all__'

class ConversationSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = ['id', 'user', 'title', 'created_at', 'messages', 'updated_at']

# kerry evaluation part
from .models import EvaluationRecord, GroundTruth

class EvaluationResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = EvaluationRecord
        fields = '__all__'


class GroundTruthSerializer(serializers.ModelSerializer):
    class Meta:
        model = GroundTruth
        fields = '__all__'
