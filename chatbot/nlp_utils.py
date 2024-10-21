import json
from venv import logger
from django.conf import settings
import os
from fuzzywuzzy import fuzz

class NLPProcessor:
    def __init__(self, language):
        self.language = language
        self.faq_data = None

    def load_faq_data(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            self.faq_data = json.load(file)

    def find_best_match(self, user_input):
        if not self.faq_data:
            print("Les données FAQ n'ont pas été chargées.")
            return "Les données FAQ n'ont pas été chargées."

        best_match = None
        best_score = 0

        print(f"Recherche de correspondance pour: '{user_input}'")

        for category in self.faq_data['categories']:
            for question in category['questions']:
                score = fuzz.token_set_ratio(user_input.lower(), question['question'].lower())
                keyword_score = max([fuzz.token_set_ratio(user_input.lower(), keyword.lower()) for keyword in question['keywords']])
                
                combined_score = max(score, keyword_score)
                
                print(f"Question: '{question['question']}', Score: {combined_score}")

                if combined_score > best_score:
                    best_score = combined_score
                    best_match = question['answer']

        if best_score > 70:
            print(f"Meilleure correspondance trouvée avec un score de {best_score}")
            return best_match
        else:
            print(f"Aucune correspondance satisfaisante trouvée. Meilleur score: {best_score}")
            return "Je suis désolé, je n'ai pas trouvé de réponse à votre question. Pouvez-vous reformuler ou poser une autre question ?"

nlp_processors = {
    'fr': NLPProcessor('french'),
    'en': NLPProcessor('english')
}