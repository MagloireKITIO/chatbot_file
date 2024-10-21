import json
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .forms import FAQFileForm, ChatbotSettingsForm
from .models import FAQFile, ChatbotSettings
from django.conf import settings
import os

@login_required
def upload_faq(request):
    if request.method == 'POST':
        form = FAQFileForm(request.POST, request.FILES)
        if form.is_valid():
            faq_file = form.save()
            
            # Valider et traiter le fichier JSON
            try:
                with faq_file.file.open('r') as file:
                    faq_data = json.load(file)
                
                # Vérifier la structure du fichier JSON
                if not validate_faq_structure(faq_data):
                    faq_file.delete()
                    return JsonResponse({'error': 'Invalid FAQ structure'}, status=400)
                
                # Sauvegarder le fichier JSON traité
                save_path = os.path.join(settings.FAQ_STORAGE_PATH, f'faq_{faq_file.language}.json')
                with open(save_path, 'w', encoding='utf-8') as outfile:
                    json.dump(faq_data, outfile, ensure_ascii=False, indent=2)
                
                return JsonResponse({'success': 'FAQ file uploaded and processed successfully'})
            except json.JSONDecodeError:
                faq_file.delete()
                return JsonResponse({'error': 'Invalid JSON file'}, status=400)
        else:
            return JsonResponse({'error': form.errors}, status=400)
    else:
        form = FAQFileForm()
    
    return render(request, 'backoffice/upload_faq.html', {'form': form})

@login_required
def chatbot_settings(request):
    settings = ChatbotSettings.objects.first()
    if not settings:
        settings = ChatbotSettings()
    
    if request.method == 'POST':
        form = ChatbotSettingsForm(request.POST, request.FILES, instance=settings)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': 'Chatbot settings updated successfully'})
        else:
            return JsonResponse({'error': form.errors}, status=400)
    else:
        form = ChatbotSettingsForm(instance=settings)
    
    return render(request, 'backoffice/chatbot_settings.html', {'form': form})

def validate_faq_structure(data):
    required_keys = ['metadata', 'settings', 'categories']
    if not all(key in data for key in required_keys):
        return False
    
    if not isinstance(data['categories'], list):
        return False
    
    for category in data['categories']:
        if 'name' not in category or 'questions' not in category:
            return False
        
        if not isinstance(category['questions'], list):
            return False
        
        for question in category['questions']:
            if not all(key in question for key in ['id', 'question', 'answer', 'keywords']):
                return False
    
    return True