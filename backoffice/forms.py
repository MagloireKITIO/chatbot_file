from django import forms
from .models import FAQFile, ChatbotSettings

class FAQFileForm(forms.ModelForm):
    class Meta:
        model = FAQFile
        fields = ['language', 'file']

class ChatbotSettingsForm(forms.ModelForm):
    class Meta:
        model = ChatbotSettings
        fields = ['welcome_message', 'farewell_message', 'inactivity_timeout', 'background_image', 'chat_icon']