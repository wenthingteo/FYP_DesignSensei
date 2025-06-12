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
   
    # --- ADDED METADATA FIELD ---
    # This field will store additional structured data (e.g., intent, citations, search params).
    # JSONField is suitable for storing dictionary-like data.
    # default=dict ensures new messages have an empty dictionary if no metadata is provided.
    # blank=True allows this field to be optional in forms.
    metadata = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f'{self.sender.capitalize()} at {self.created_at}: {self.content[:30]}'

class Feedback(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        # Corrected: Use created_at instead of submitted_at
        return f'Feedback by {self.user.username} at {self.created_at}'

# class Chat(models.Model): # This was commented out in your original code, so keeping it commented.
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     message = models.TextField()
#     response = models.TextField()
#     created_at = models.DateTimeField(auto_now_add=True)

#     def __str__(self):
#         return f'{self.user.username}: {self.message}'