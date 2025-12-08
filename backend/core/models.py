from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone # Import timezone for default=timezone.now
import uuid
from datetime import timedelta

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

#  kerry evaluation part,updated
class EvaluationRecord(models.Model):
    session_id = models.CharField(max_length=255)
    user_query = models.TextField()
    ai_response = models.TextField()
    rag_used = models.BooleanField(default=False)
    hybrid_mode = models.CharField(max_length=50)
    
    # Evaluation Metrics
    confidence_score = models.FloatField(null=True, blank=True)
    accuracy_score = models.FloatField(null=True, blank=True)  # Compared to ground truth
    completeness_score = models.FloatField(null=True, blank=True)  # How complete the answer is
    educational_value_score = models.FloatField(null=True, blank=True)  # Educational quality
    
    # Ground Truth Comparison
    matched_ground_truth = models.ForeignKey('GroundTruth', null=True, blank=True, on_delete=models.SET_NULL, related_name='evaluations')
    similarity_to_truth = models.FloatField(null=True, blank=True)  # Semantic similarity 0-1
    
    # Automatic Feedback
    flagged_incorrect = models.BooleanField(default=False)
    flag_reason = models.TextField(null=True, blank=True)
    
    # Human Assessment
    human_rating = models.IntegerField(null=True, blank=True, choices=[(1,'Poor'),(2,'Fair'),(3,'Good'),(4,'Very Good'),(5,'Excellent')])
    human_feedback = models.TextField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.CharField(max_length=255, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'core'
        indexes = [
            models.Index(fields=['session_id']),
            models.Index(fields=['flagged_incorrect']),
            models.Index(fields=['created_at']),
        ]

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

class PasswordResetToken(models.Model):
    """Model for password reset tokens"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_reset_tokens')
    token = models.CharField(max_length=100, unique=True, default=uuid.uuid4)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    class Meta:
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['expires_at']),
        ]
        ordering = ['-created_at']
    
    def save(self, *args, **kwargs):
        # Set expiry time to 1 hour from creation if not set
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=1)
        super().save(*args, **kwargs)
    
    def is_valid(self):
        """Check if token is valid (not expired and not used)"""
        return not self.is_used and timezone.now() < self.expires_at
    
    def __str__(self):
        return f"Reset token for {self.user.username} - {'Valid' if self.is_valid() else 'Invalid'}"
