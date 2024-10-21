from django.contrib import admin
from .models import FAQFile, ChatbotSettings
from .forms import FAQFileForm, ChatbotSettingsForm

@admin.register(FAQFile)
class FAQFileAdmin(admin.ModelAdmin):
    form = FAQFileForm
    list_display = ('language', 'uploaded_at')
    list_filter = ('language',)

@admin.register(ChatbotSettings)
class ChatbotSettingsAdmin(admin.ModelAdmin):
    form = ChatbotSettingsForm

    def has_add_permission(self, request):
        # Empêcher l'ajout de plusieurs instances de paramètres
        return ChatbotSettings.objects.count() == 0