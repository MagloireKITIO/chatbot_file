import json
import logging
import unicodedata
import re
from typing import Dict, List, Optional, Union
from fuzzywuzzy import fuzz
from datetime import datetime
import os

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('chatbot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TextProcessor:
    """Gestion du traitement de texte"""
    
    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalise le texte en retirant les accents et caractères spéciaux"""
        if not text:
            return ""
        # Conversion en minuscules
        text = text.lower()
        # Suppression des accents
        text = ''.join(c for c in unicodedata.normalize('NFKD', text)
                      if not unicodedata.combining(c))
        # Suppression de la ponctuation
        text = re.sub(r'[^\w\s]', ' ', text)
        # Suppression des espaces multiples
        text = ' '.join(text.split())
        return text

    @staticmethod
    def calculate_similarity(text1: str, text2: str) -> float:
        """Calcule la similarité entre deux textes"""
        if not text1 or not text2:
            return 0.0
        
        # Normalisation des textes
        text1 = TextProcessor.normalize_text(text1)
        text2 = TextProcessor.normalize_text(text2)
        
        # Différentes méthodes de comparaison
        token_sort = fuzz.token_sort_ratio(text1, text2)
        token_set = fuzz.token_set_ratio(text1, text2)
        partial_ratio = fuzz.partial_ratio(text1, text2)
        
        # Score pondéré
        return (token_sort * 0.4) + (token_set * 0.4) + (partial_ratio * 0.2)

class ResponseFormatter:
    """Gestion du formatage des réponses"""

    @staticmethod
    def format_step_notes(step: Dict) -> List[str]:
        """Formate les notes et informations additionnelles d'une étape"""
        notes = []
        
        if step.get('info'):
            notes.append(f"   ℹ️ {step['info']}")
        if step.get('note'):
            notes.append(f"   💡 {step['note']}")
        if step.get('example'):
            notes.append(f"   Exemple: {step['example']}")
        if step.get('warning'):
            notes.append(f"   ⚠️ {step['warning']}")
        if step.get('tip'):
            notes.append(f"   Conseil: {step['tip']}")
        if step.get('options'):
            for opt in step.get('options', []):
                notes.append(f"   • {opt}")
        
        return notes

    @staticmethod
    def format_steps(steps: List[Dict]) -> str:
        """Formate les étapes d'une réponse"""
        if not steps:
            return ""
            
        formatted_steps = []
        all_notes = []
        
        for i, step in enumerate(steps, 1):
            if not isinstance(step, dict) or 'step' not in step:
                continue
                
            # Formatage de l'étape principale
            step_lines = [f"{i}. {step['step']}"]
            
            # Collecter les notes pour cette étape
            notes = ResponseFormatter.format_step_notes(step)
            
            # Si c'est une étape simple (comme dans la liste des produits),
            # on met la note en bas
            if 'note' in step and len(step) == 2:  # Seulement step et note
                all_notes.append(f"_{step['step']}: {step['note']}_")
            else:
                # Sinon, on ajoute les notes directement après l'étape
                step_lines.extend(notes)
            
            formatted_steps.append("\n".join(step_lines))
        
        # Combiner les étapes et les notes
        result = "\n\n".join(formatted_steps)
        if all_notes:
            result += "\n\n" + "\n".join(all_notes)
        
        return result

    @staticmethod
    def format_answer(answer: Union[str, Dict]) -> str:
        """Formate une réponse complète"""
        try:
            if isinstance(answer, str):
                return answer

            if not isinstance(answer, dict):
                return "Désolé, je ne peux pas formater cette réponse."

            formatted_parts = []
            
            # Titre avec emoji selon le type de réponse
            if answer.get('title'):
                title_prefix = ""
                if "produit" in answer['title'].lower():
                    title_prefix = "🛡️ 💎 "
                elif "contact" in answer['title'].lower():
                    title_prefix = "📞 ✉️ "
                elif "localisation" in answer['title'].lower() or "situé" in answer['title'].lower():
                    title_prefix = "📍 🏢 "
                elif "sinistre" in answer['title'].lower():
                    title_prefix = "⚠️ 🆘 "
                elif "paiement" in answer['title'].lower():
                    title_prefix = "💳 💰 "
                formatted_parts.append(f"{title_prefix}{answer['title']}")
            
            # Introduction non numérotée
            if answer.get('introduction'):
                formatted_parts.append(f"{answer['introduction']}")
            
            # Texte simple si présent
            if answer.get('text'):
                formatted_parts.append(f"{answer['text']}")
            
            # Étapes avec leurs informations
            if answer.get('steps'):
                formatted_steps = ResponseFormatter.format_steps(answer['steps'])
                if formatted_steps:
                    formatted_parts.append(formatted_steps)
            
            # Informations complémentaires
            if answer.get('conclusion'):
                formatted_parts.append(f"\n{answer['conclusion']}")
            
            if answer.get('additional_info'):
                formatted_parts.append(f"\nℹ️ Information complémentaire:\n{answer['additional_info']}")
            
            if answer.get('contact'):
                formatted_parts.append(f"\n📞 Contact: {answer['contact']}")
            
            if answer.get('note'):
                formatted_parts.append(f"\n💡 Note: {answer['note']}")

            formatted_response = "\n\n".join(part.strip() for part in formatted_parts if part.strip())
            return formatted_response if formatted_response else str(answer)
            
        except Exception as e:
            logger.error(f"Erreur lors du formatage de la réponse: {str(e)}")
            return str(answer)

class NLPProcessor:
    """Processeur principal NLP"""
    
    def __init__(self, language: str):
        self.language = language
        self.faq_data = None
        self.text_processor = TextProcessor()
        self.response_formatter = ResponseFormatter()
        self.last_reload = None
        logger.info(f"Initialisation du processeur NLP pour la langue: {language}")

    def load_faq_data(self, file_path: str) -> bool:
        """Charge les données FAQ depuis un fichier"""
        try:
            if not os.path.exists(file_path):
                logger.error(f"Fichier FAQ non trouvé: {file_path}")
                return False

            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                
            if self._validate_faq_data(data):
                self.faq_data = data
                self.last_reload = datetime.now()
                logger.info(f"FAQ chargé avec succès depuis {file_path}")
                return True
            else:
                logger.error("Structure FAQ invalide")
                return False
                
        except Exception as e:
            logger.error(f"Erreur lors du chargement du FAQ: {str(e)}")
            return False

    def _validate_faq_data(self, data: Dict) -> bool:
        """Valide la structure des données FAQ"""
        try:
            if not isinstance(data, dict) or 'categories' not in data:
                return False
                
            categories = data.get('categories', [])
            if not isinstance(categories, list):
                return False

            for category in categories:
                if not isinstance(category, dict):
                    return False
                if 'questions' not in category:
                    return False
                    
                questions = category.get('questions', [])
                if not isinstance(questions, list):
                    return False

                for question in questions:
                    if not all(k in question for k in ['id', 'question', 'answer']):
                        return False

            return True
        except Exception as e:
            logger.error(f"Erreur lors de la validation FAQ: {str(e)}")
            return False

    def find_best_match(self, user_input: str) -> str:
        """Trouve la meilleure correspondance pour une question"""
        try:
            if not self.faq_data or not user_input:
                return "Je ne peux pas traiter votre demande pour le moment."

            logger.info(f"Recherche de correspondance pour: '{user_input}'")
            best_match = None
            best_score = 0

            for category in self.faq_data.get('categories', []):
                for question in category.get('questions', []):
                    current_score = self._calculate_match_score(user_input, question)
                    logger.info(f"Score pour {question.get('id', 'unknown')}: {current_score}")

                    if current_score > best_score:
                        best_score = current_score
                        best_match = question

            logger.info(f"Meilleur score trouvé: {best_score}")

            if best_score > 50 and best_match:
                return self.response_formatter.format_answer(best_match['answer'])
            else:
                suggestions = self.get_suggested_questions(user_input)
                suggestion_text = ""
                if suggestions:
                    suggestion_text = "\n\nVouliez-vous dire :\n" + "\n".join(f"- {s}" for s in suggestions[:3])
                
                return (
                    "Je suis désolé, je n'ai pas trouvé de réponse exacte à votre question. "
                    "Pouvez-vous reformuler ou être plus précis ?" + suggestion_text
                )

        except Exception as e:
            logger.error(f"Erreur lors de la recherche de correspondance: {str(e)}")
            return "Une erreur est survenue lors du traitement de votre question."

    def _calculate_match_score(self, user_input: str, question_data: Dict) -> float:
        """Calcule le score de correspondance pour une question"""
        try:
            if not question_data or 'question' not in question_data:
                return 0.0

            main_question_score = self.text_processor.calculate_similarity(
                user_input,
                question_data['question']
            )

            # Score des questions alternatives
            alt_scores = [
                self.text_processor.calculate_similarity(user_input, alt)
                for alt in question_data.get('alternative_questions', [])
            ]

            # Score des mots-clés
            keyword_scores = [
                self.text_processor.calculate_similarity(user_input, keyword)
                for keyword in question_data.get('keywords', [])
            ]

            # Calcul du score final
            final_score = main_question_score * 0.6  # Question principale
            if alt_scores:
                final_score += max(alt_scores) * 0.25  # Meilleures questions alternatives
            if keyword_scores:
                final_score += max(keyword_scores) * 0.15  # Meilleurs mots-clés

            return final_score

        except Exception as e:
            logger.error(f"Erreur lors du calcul du score: {str(e)}")
            return 0.0

    def get_suggested_questions(self, user_input: str) -> List[str]:
        """Génère des suggestions de questions similaires"""
        try:
            if not self.faq_data or not user_input:
                return []

            suggestions = []
            for category in self.faq_data.get('categories', []):
                for question in category.get('questions', []):
                    if 'question' in question:
                        score = self._calculate_match_score(user_input, question)
                        suggestions.append((question['question'], score))

            # Trier par score et prendre les 3 meilleures suggestions
            suggestions.sort(key=lambda x: x[1], reverse=True)
            return [question for question, _ in suggestions[:3]]

        except Exception as e:
            logger.error(f"Erreur lors de la génération des suggestions: {str(e)}")
            return []

# Initialisation des processeurs par langue
nlp_processors = {
    'fr': NLPProcessor('french'),
    'en': NLPProcessor('english')
}