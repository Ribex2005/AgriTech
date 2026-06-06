from django.db import models
from django.contrib.auth.models import User

class ChatMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_messages')
    message = models.TextField()
    reply = models.TextField()
    message_type = models.CharField(
        max_length=20,
        choices=[
            ('general', 'General Question'),
            ('disease_detection', 'Disease Detection'),
            ('market_info', 'Market Information'),
            ('scheme_info', 'Scheme Information'),
        ],
        default='general'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.message[:50]}"