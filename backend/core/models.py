from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone # Import timezone for default=timezone.now

# Create your models here.

class Conversation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversations')
    title = models.CharField(max_length=255, default='New Conversation')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True) # Added for auto update timestamp

    def get_user(self):
        return self.user.username
   
    def get_title(self):
        return self.title
   
    def __str__(self):
        return f'{self.title} by {self.user.username}'

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.CharField(max_length=10, choices=[('user', 'User'), ('bot', 'Bot')])
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f'{self.sender.capitalize()} at {self.created_at}: {self.content[:30]}'

class Feedback(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Feedback by {self.user.username} at {self.created_at}'

# class Chat(models.Model): # This was commented out in your original code, so keeping it commented.
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     message = models.TextField()
#     response = models.TextField()
#     created_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f'{self.user.username}: {self.message}'

#  kerry evaluation part
class EvaluationResult(models.Model):
    session_id = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    question = models.TextField()
    context = models.TextField(null=True, blank=True)
    llm_answer = models.TextField()
    ground_truth = models.TextField(null=True, blank=True)
    relevance_score = models.FloatField(null=True, blank=True)
    bert_score = models.FloatField(null=True, blank=True)
    llm_rubric_score = models.FloatField(null=True, blank=True)
    combined_score = models.FloatField(null=True, blank=True)
    passed = models.BooleanField(default=False)
    evaluation_timestamp = models.DateTimeField(default=timezone.now)
    evaluation_details = models.JSONField(default=dict, blank=True)
    action_taken = models.CharField(max_length=50, default="none")
    ragas_score = models.FloatField(null=True, blank=True)
    ragas_details = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"Evaluation for session {self.session_id} - {self.question[:40]}"


class GroundTruth(models.Model):
    question = models.TextField()
    context = models.TextField(null=True, blank=True)
    ground_truth = models.TextField()
    created_by = models.CharField(max_length=255, null=True, blank=True)
    verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    verified_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Ground Truth: {self.question[:40]}"
