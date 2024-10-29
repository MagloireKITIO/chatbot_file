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
    """Charge les données FAQ pour toutes les langues"""
    logger.info("Début du chargement des données FAQ")
    for language in ['fr', 'en']:
        try:
            faq_file = FAQFile.objects.filter(language=language).first()
            if faq_file and faq_file.file:
                file_path = os.path.join(settings.MEDIA_ROOT, faq_file.file.name)
                logger.info(f"Tentative de chargement du fichier FAQ pour {language}: {file_path}")
                
                if os.path.exists(file_path):
                    nlp_processors[language].load_faq_data(file_path)
                    logger.info(f"FAQ chargé avec succès pour {language}")
                    
                    # Vérification du chargement
                    if nlp_processors[language].faq_data:
                        logger.info(f"Données FAQ validées pour {language}")
                    else:
                        logger.error(f"Les données FAQ sont None pour {language} après chargement")
                else:
                    logger.error(f"Le fichier FAQ n'existe pas: {file_path}")
        except Exception as e:
            logger.error(f"Erreur lors du chargement du FAQ pour {language}: {str(e)}")

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
        user_message = data.get('message', '').strip()
        language = data.get('language', 'fr')
        
        logger.info(f"Message reçu: '{user_message}', Langue: {language}")
        
        nlp_processor = nlp_processors.get(language)
        if not nlp_processor:
            return JsonResponse({'error': 'Langue non supportée'}, status=400)
            
        if not nlp_processor.faq_data:
            load_faq_data()
            
        response = nlp_processor.find_best_match(user_message)
        suggestions = nlp_processor.get_suggested_questions(user_message)
        
        return JsonResponse({
            'response': response,
            'suggestions': suggestions if 'désolé' in response else []
        })
        
    except Exception as e:
        logger.error(f"Erreur: {str(e)}", exc_info=True)
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