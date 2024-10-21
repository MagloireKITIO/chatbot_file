from django.db import models
from django.core.validators import FileExtensionValidator

class FAQFile(models.Model):
    LANGUAGE_CHOICES = [
        ('fr', 'Français'),
        ('en', 'English'),
    ]
    language = models.CharField(max_length=2, choices=LANGUAGE_CHOICES)
    file = models.FileField(
        upload_to='faq_files/',
        validators=[FileExtensionValidator(allowed_extensions=['json'])]
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['language']

    def __str__(self):
        return f"FAQ {self.get_language_display()} - {self.uploaded_at}"

class ChatbotSettings(models.Model):
    welcome_message = models.TextField()
    farewell_message = models.TextField()
    inactivity_timeout = models.IntegerField(default=600)  # en secondes
    background_image = models.ImageField(upload_to='chatbot_images/', null=True, blank=True)
    chat_icon = models.ImageField(upload_to='chatbot_images/', null=True, blank=True)

    class Meta:
        verbose_name = "Paramètres du Chatbot"
        verbose_name_plural = "Paramètres du Chatbot"

    def __str__(self):
        return "Paramètres du Chatbot"