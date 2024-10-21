from venv import logger
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
from .nlp_utils import nlp_processors
from backoffice.models import ChatbotSettings, FAQFile
from django.conf import settings
import os

def load_faq_data():
    for language in ['fr', 'en']:
        faq_file = FAQFile.objects.filter(language=language).first()
        if faq_file and faq_file.file:
            file_path = os.path.join(settings.MEDIA_ROOT, faq_file.file.name)
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as file:
                        faq_data = json.load(file)
                    nlp_processors[language].faq_data = faq_data
                    print(f"FAQ chargé pour {language}: {faq_data}")
                except Exception as e:
                    print(f"Erreur lors du chargement du FAQ pour {language}: {str(e)}")
            else:
                print(f"Le fichier FAQ pour {language} n'existe pas: {file_path}")
        else:
            print(f"Aucun fichier FAQ trouvé pour la langue: {language}")

# Assurez-vous d'appeler cette fonction au démarrage de l'application
load_faq_data()

def chatbot_interface(request):
    settings = ChatbotSettings.objects.first()
    return render(request, 'chatbot.html', {'settings': settings})

@csrf_exempt
@require_POST
def chatbot_message(request):
    try:
        data = json.loads(request.body)
        user_message = data.get('message')
        language = data.get('language', 'fr')
        
        logger.info(f"Message reçu: '{user_message}', Langue: {language}")

        if not user_message:
            logger.warning("Message vide reçu")
            return JsonResponse({'error': 'Message is required'}, status=400)
        
        nlp_processor = nlp_processors.get(language)
        if not nlp_processor:
            logger.error(f"Langue non supportée: {language}")
            return JsonResponse({'error': 'Unsupported language'}, status=400)
        
        response = nlp_processor.find_best_match(user_message)
        
        logger.info(f"Réponse du chatbot: '{response}'")
        return JsonResponse({'response': response})
    except json.JSONDecodeError:
        logger.error("JSON invalide reçu")
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.exception("Erreur inattendue lors du traitement du message")
        return JsonResponse({'error': str(e)}, status=500)

def get_chatbot_settings(request):
    settings = ChatbotSettings.objects.first()
    if not settings:
        return JsonResponse({'error': 'Chatbot settings not found'}, status=404)
    
    return JsonResponse({
        'welcome_message': settings.welcome_message,
        'farewell_message': settings.farewell_message,
        'inactivity_timeout': settings.inactivity_timeout,
        'background_image': settings.background_image.url if settings.background_image else None,
        'chat_icon': settings.chat_icon.url if settings.chat_icon else None,
    })

def reload_faq(request):
    load_faq_data()
    return JsonResponse({'status': 'FAQ reloaded successfully'})