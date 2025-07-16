#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
System uczenia się asystenta na podstawie historii rozmów i preferencji użytkownika
"""
import os
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from collections import defaultdict, Counter
from app.models import ChatSession

class LearningSystem:
    """Główna klasa systemu uczenia się"""
    
    def __init__(self):
        self.learning_data_file = 'data/learning_data.json'
        self.patterns_file = 'data/user_patterns.json'
        self.preferences_file = 'data/user_preferences.json'
        self.ensure_directories()
        
    def ensure_directories(self):
        """Tworzy wymagane katalogi"""
        for directory in ['data']:
            os.makedirs(directory, exist_ok=True)
    
    def analyze_conversation_history(self, session_id: str, user_id: int = None) -> Dict:
        """Analizuje historię rozmowy dla danej sesji"""
        chat_session = ChatSession(session_id, user_id)
        history = chat_session.load_history()
        
        if not history:
            return {}
        
        # Filtruj wiadomości dla konkretnego użytkownika jeśli user_id podane
        if user_id:
            history = [msg for msg in history if msg.get('user_id') == user_id]
        
        analysis = {
            'session_id': session_id,
            'user_id': user_id,
            'total_messages': len(history),
            'user_patterns': self._extract_user_patterns(history),
            'response_patterns': self._extract_response_patterns(history),
            'topic_progression': self._analyze_topic_progression(history),
            'question_types': self._categorize_questions(history),
            'timestamp': datetime.now().isoformat()
        }
        
        return analysis
    
    def _extract_user_patterns(self, history: List[Dict]) -> Dict:
        """Wyodrębnia wzorce w pytaniach użytkownika"""
        user_messages = [msg for msg in history if msg['role'] == 'user']
        
        patterns = {
            'common_keywords': self._find_common_keywords(user_messages),
            'question_length': self._analyze_question_length(user_messages),
            'request_types': self._categorize_request_types(user_messages),
            'follow_up_patterns': self._analyze_follow_up_patterns(user_messages),
            'preferred_detail_level': self._detect_detail_preference(user_messages)
        }
        
        return patterns
    
    def _extract_response_patterns(self, history: List[Dict]) -> Dict:
        """Analizuje wzorce w odpowiedziach asystenta"""
        assistant_messages = [msg for msg in history if msg['role'] == 'assistant']
        
        patterns = {
            'response_length': self._analyze_response_length(assistant_messages),
            'structure_types': self._analyze_response_structure(assistant_messages),
            'content_types': self._analyze_content_types(assistant_messages),
            'formatting_patterns': self._analyze_formatting_patterns(assistant_messages)
        }
        
        return patterns
    
    def _find_common_keywords(self, messages: List[Dict]) -> List[Tuple[str, int]]:
        """Znajduje najczęściej używane słowa kluczowe"""
        all_text = ' '.join([msg['content'].lower() for msg in messages])
        
        # Usuń typowe słowa i znaki interpunkcyjne
        stop_words = {
            'jak', 'co', 'czy', 'kiedy', 'gdzie', 'dlaczego', 'który', 'która', 'które',
            'w', 'na', 'do', 'z', 'za', 'o', 'przy', 'dla', 'przez', 'od', 'po',
            'jest', 'są', 'było', 'będzie', 'może', 'można', 'powinien', 'powinna',
            'i', 'a', 'ale', 'lub', 'oraz', 'to', 'ta', 'te', 'ten', 'tej', 'tym'
        }
        
        words = re.findall(r'\b\w+\b', all_text)
        words = [word for word in words if len(word) > 3 and word not in stop_words]
        
        return Counter(words).most_common(20)
    
    def _analyze_question_length(self, messages: List[Dict]) -> Dict:
        """Analizuje długość pytań użytkownika"""
        lengths = [len(msg['content'].split()) for msg in messages]
        
        if not lengths:
            return {'avg_length': 0, 'preferred_range': 'short'}
        
        avg_length = sum(lengths) / len(lengths)
        
        if avg_length < 5:
            preferred_range = 'short'
        elif avg_length < 15:
            preferred_range = 'medium'
        else:
            preferred_range = 'long'
        
        return {
            'avg_length': avg_length,
            'min_length': min(lengths),
            'max_length': max(lengths),
            'preferred_range': preferred_range
        }
    
    def _categorize_request_types(self, messages: List[Dict]) -> Dict:
        """Kategoryzuje typy próśb użytkownika"""
        request_patterns = {
            'examples': r'(przykład|przykłady|np\.|na przykład|pokaż|wzór|wzory)',
            'explanations': r'(jak działa|wyjaśnij|objaśnij|co to jest|czym jest)',
            'procedures': r'(procedura|krok po kroku|jak wykonać|instrukcja)',
            'comparisons': r'(różnica|porównaj|lepszy|gorszy|vs|przeciwko)',
            'calculations': r'(oblicz|wylicz|wzór|formuła|równanie)',
            'definitions': r'(definicja|znaczenie|oznacza|definiuj)',
            'practical': r'(praktyczne|w praktyce|zastosowanie|użycie)',
            'theory': r'(teoria|teoretyczne|podstawy|zasady)'
        }
        
        categories = defaultdict(int)
        
        for msg in messages:
            content = msg['content'].lower()
            for category, pattern in request_patterns.items():
                if re.search(pattern, content):
                    categories[category] += 1
        
        return dict(categories)
    
    def _analyze_follow_up_patterns(self, messages: List[Dict]) -> Dict:
        """Analizuje wzorce w pytaniach następnych"""
        follow_up_indicators = {
            'more_detail': r'(więcej|szczegółowo|dokładniej|szerzej|głębiej)',
            'examples': r'(przykład|przykłady|wzór|wzory|dawaj|pokaż)',
            'simplification': r'(prościej|prostymi słowami|łatwiej|jasniej)',
            'practical': r'(praktyczne|w praktyce|jak zastosować|jak użyć)',
            'related': r'(a co z|jak z|również|także|jeszcze|dodatkowo)'
        }
        
        patterns = defaultdict(int)
        
        for i, msg in enumerate(messages):
            if i > 0:  # Pomijamy pierwsze pytanie
                content = msg['content'].lower()
                for pattern_type, pattern in follow_up_indicators.items():
                    if re.search(pattern, content):
                        patterns[pattern_type] += 1
        
        return dict(patterns)
    
    def _detect_detail_preference(self, messages: List[Dict]) -> str:
        """Wykrywa preferowany poziom szczegółowości"""
        detail_indicators = {
            'high': r'(szczegółowo|dokładnie|precyzyjnie|wszystko|kompletnie|wyczerpująco)',
            'medium': r'(wyjaśnij|objaśnij|opisz|przedstaw)',
            'low': r'(krótko|zwięźle|w skrócie|najważniejsze|podsumuj)'
        }
        
        scores = defaultdict(int)
        
        for msg in messages:
            content = msg['content'].lower()
            for level, pattern in detail_indicators.items():
                matches = len(re.findall(pattern, content))
                scores[level] += matches
        
        if not scores:
            return 'medium'
        
        return max(scores.items(), key=lambda x: x[1])[0]
    
    def _analyze_topic_progression(self, history: List[Dict]) -> List[str]:
        """Analizuje progresję tematów w rozmowie"""
        topics = []
        
        # Słownik tematów lotniczych
        topic_keywords = {
            'aerodynamika': ['siła nośna', 'opór', 'profil', 'skrzydło', 'aerodynamik'],
            'nawigacja': ['gps', 'vor', 'kompas', 'nawigacja', 'kurs', 'pozycja'],
            'meteorologia': ['pogoda', 'wiatr', 'ciśnienie', 'temperatura', 'chmury'],
            'silniki': ['silnik', 'spalanie', 'turbina', 'śmigło', 'moc'],
            'procedury': ['start', 'lądowanie', 'podejście', 'procedura', 'maneuwr'],
            'systemy': ['hydraulika', 'elektryka', 'paliwowy', 'system', 'awionika'],
            'regulacje': ['przepis', 'regulacja', 'prawo', 'icao', 'easa', 'faa']
        }
        
        for msg in history:
            if msg['role'] == 'user':
                content = msg['content'].lower()
                for topic, keywords in topic_keywords.items():
                    if any(keyword in content for keyword in keywords):
                        topics.append(topic)
                        break
                else:
                    topics.append('ogólne')
        
        return topics
    
    def _analyze_response_length(self, messages: List[Dict]) -> Dict:
        """Analizuje długość odpowiedzi asystenta"""
        lengths = [len(msg['content']) for msg in messages]
        
        if not lengths:
            return {'avg_length': 0}
        
        return {
            'avg_length': sum(lengths) / len(lengths),
            'min_length': min(lengths),
            'max_length': max(lengths),
            'word_count_avg': sum(len(msg['content'].split()) for msg in messages) / len(messages)
        }
    
    def _analyze_response_structure(self, messages: List[Dict]) -> Dict:
        """Analizuje strukturę odpowiedzi"""
        structures = {
            'has_headers': 0,
            'has_lists': 0,
            'has_examples': 0,
            'has_formulas': 0,
            'has_summaries': 0
        }
        
        for msg in messages:
            content = msg['content']
            
            if re.search(r'<h[1-6]>', content):
                structures['has_headers'] += 1
            if re.search(r'<[ou]l>', content):
                structures['has_lists'] += 1
            if re.search(r'(przykład|np\.|na przykład)', content, re.IGNORECASE):
                structures['has_examples'] += 1
            if re.search(r'(=|wzór|formuła|równanie)', content):
                structures['has_formulas'] += 1
            if re.search(r'(podsumowanie|wniosek|zakończenie)', content, re.IGNORECASE):
                structures['has_summaries'] += 1
        
        total_messages = len(messages)
        if total_messages > 0:
            for key in structures:
                structures[key] = structures[key] / total_messages
        
        return structures
    
    def _analyze_content_types(self, messages: List[Dict]) -> Dict:
        """Analizuje typy treści w odpowiedziach"""
        content_types = {
            'theoretical': 0,
            'practical': 0,
            'examples': 0,
            'procedures': 0,
            'references': 0
        }
        
        for msg in messages:
            content = msg['content'].lower()
            
            if re.search(r'(teoria|zasada|podstawy|koncepcja)', content):
                content_types['theoretical'] += 1
            if re.search(r'(praktyce|zastosowanie|używa się|stosuje się)', content):
                content_types['practical'] += 1
            if re.search(r'(przykład|np\.|na przykład|ilustracja)', content):
                content_types['examples'] += 1
            if re.search(r'(krok|procedura|instrukcja|sposób)', content):
                content_types['procedures'] += 1
            if re.search(r'(dokument|źródło|strona|sekcja)', content):
                content_types['references'] += 1
        
        return content_types
    
    def _analyze_formatting_patterns(self, messages: List[Dict]) -> Dict:
        """Analizuje wzorce formatowania"""
        formatting = {
            'html_tags': 0,
            'markdown_headers': 0,
            'bullet_points': 0,
            'numbered_lists': 0,
            'bold_text': 0,
            'italic_text': 0
        }
        
        for msg in messages:
            content = msg['content']
            
            formatting['html_tags'] += len(re.findall(r'<[^>]+>', content))
            formatting['markdown_headers'] += len(re.findall(r'^#+\s', content, re.MULTILINE))
            formatting['bullet_points'] += len(re.findall(r'^\*\s|^-\s', content, re.MULTILINE))
            formatting['numbered_lists'] += len(re.findall(r'^\d+\.\s', content, re.MULTILINE))
            formatting['bold_text'] += len(re.findall(r'<strong>|<b>|\*\*', content))
            formatting['italic_text'] += len(re.findall(r'<em>|<i>|\*[^*]', content))
        
        return formatting
    
    def _categorize_questions(self, history: List[Dict]) -> Dict:
        """Kategoryzuje pytania użytkownika"""
        user_messages = [msg for msg in history if msg['role'] == 'user']
        
        categories = {
            'definition': 0,
            'explanation': 0,
            'procedure': 0,
            'comparison': 0,
            'example': 0,
            'calculation': 0,
            'application': 0
        }
        
        patterns = {
            'definition': r'(co to jest|czym jest|definicja|znaczenie)',
            'explanation': r'(jak działa|dlaczego|wyjaśnij|objaśnij)',
            'procedure': r'(jak wykonać|procedura|krok po kroku|instrukcja)',
            'comparison': r'(różnica|porównaj|lepszy|gorszy|vs)',
            'example': r'(przykład|przykłady|wzór|wzory|dawaj|pokaż)',
            'calculation': r'(oblicz|wylicz|ile|jaka wartość)',
            'application': r'(zastosowanie|użycie|praktyce|gdzie używa)'
        }
        
        for msg in user_messages:
            content = msg['content'].lower()
            for category, pattern in patterns.items():
                if re.search(pattern, content):
                    categories[category] += 1
        
        return categories
    
    def save_learning_data(self, analysis: Dict):
        """Zapisuje dane uczenia do pliku"""
        learning_data = []
        
        if os.path.exists(self.learning_data_file):
            try:
                with open(self.learning_data_file, 'r', encoding='utf-8') as f:
                    learning_data = json.load(f)
            except Exception as e:
                print(f"Błąd wczytywania danych uczenia: {e}")
                learning_data = []
        
        learning_data.append(analysis)
        
        # Zachowaj tylko ostatnie 100 analiz
        if len(learning_data) > 100:
            learning_data = learning_data[-100:]
        
        try:
            with open(self.learning_data_file, 'w', encoding='utf-8') as f:
                json.dump(learning_data, f, ensure_ascii=False, indent=2)
            print(f"✅ Zapisano dane uczenia dla sesji {analysis['session_id']}")
        except Exception as e:
            print(f"❌ Błąd zapisywania danych uczenia: {e}")
    
    def get_user_preferences(self, session_id: str, user_id: int = None) -> Dict:
        """Pobiera preferencje użytkownika na podstawie historii"""
        analysis = self.analyze_conversation_history(session_id, user_id)
        
        if not analysis:
            return self._get_default_preferences()
        
        # Sprawdź czy użytkownik często prosi o przykłady
        request_types = analysis['user_patterns'].get('request_types', {})
        
        preferences = {
            'detail_level': analysis['user_patterns'].get('preferred_detail_level', 'medium'),
            'question_types': analysis['question_types'],
            'prefers_examples': request_types.get('examples', 0) > 0,
            'prefers_procedures': request_types.get('procedures', 0) > 0,
            'prefers_theory': request_types.get('theory', 0) > 0,
            'prefers_practical': request_types.get('practical', 0) > 0,
            'common_topics': analysis['topic_progression'],
            'response_structure_preference': self._determine_structure_preference(analysis),
            'session_id': session_id,
            'user_id': user_id,
            'updated_at': datetime.now().isoformat()
        }
        
        return preferences
    
    def _get_default_preferences(self) -> Dict:
        """Zwraca domyślne preferencje"""
        return {
            'detail_level': 'medium',
            'question_types': {},
            'prefers_examples': True,
            'prefers_procedures': True,
            'prefers_theory': True,
            'prefers_practical': True,
            'common_topics': [],
            'response_structure_preference': 'structured',
            'session_id': 'default',
            'updated_at': datetime.now().isoformat()
        }
    
    def _determine_structure_preference(self, analysis: Dict) -> str:
        """Określa preferowaną strukturę odpowiedzi"""
        user_patterns = analysis.get('user_patterns', {})
        request_types = user_patterns.get('request_types', {})
        
        # Jeśli użytkownik często zadaje pytania o przykłady, preferuje strukturę z przykładami
        if request_types.get('examples', 0) > 2:
            return 'with_examples'
        
        # Jeśli często pyta o procedury, preferuje krok po kroku
        if request_types.get('procedures', 0) > 1:
            return 'step_by_step'
        
        # Jeśli często o teorię, preferuje szczegółowe wyjaśnienia
        if request_types.get('theory', 0) > 1:
            return 'detailed_theory'
        
        # Domyślnie strukturowana odpowiedź
        return 'structured'
    
    def generate_learning_prompt(self, session_id: str, current_query: str, user_id: int = None) -> str:
        """Generuje prompt uczenia na podstawie preferencji użytkownika"""
        preferences = self.get_user_preferences(session_id, user_id)
        
        prompt_parts = [
            "KONTEKST UCZENIA UŻYTKOWNIKA:",
            f"Poziom szczegółowości: {preferences['detail_level']}",
        ]
        
        if preferences['prefers_examples']:
            prompt_parts.append("✅ Użytkownik preferuje PRZYKŁADY i WZORY - zawsze dodawaj praktyczne przykłady!")
        
        if preferences['prefers_procedures']:
            prompt_parts.append("✅ Użytkownik preferuje PROCEDURY - przedstawiaj informacje krok po kroku!")
        
        if preferences['prefers_theory']:
            prompt_parts.append("✅ Użytkownik preferuje TEORIĘ - dostarczaj solidne podstawy teoretyczne!")
        
        if preferences['prefers_practical']:
            prompt_parts.append("✅ Użytkownik preferuje PRAKTYKĘ - pokazuj zastosowania w rzeczywistości!")
        
        # Analiza wzorców z poprzednich pytań
        common_topics = preferences.get('common_topics', [])
        if common_topics:
            recent_topics = list(set(common_topics[-5:]))  # Ostatnie 5 unikalnych tematów
            prompt_parts.append(f"Ostatnie tematy: {', '.join(recent_topics)}")
        
        structure_pref = preferences.get('response_structure_preference', 'structured')
        if structure_pref == 'with_examples':
            prompt_parts.append("⚠️ OBOWIĄZKOWE: Zawsze dodawaj konkretne przykłady i wzory!")
        elif structure_pref == 'step_by_step':
            prompt_parts.append("⚠️ OBOWIĄZKOWE: Przedstawiaj informacje w formie kroków!")
        elif structure_pref == 'detailed_theory':
            prompt_parts.append("⚠️ OBOWIĄZKOWE: Dostarczaj szczegółowe wyjaśnienia teoretyczne!")
        
        return "\n".join(prompt_parts)
    
    def update_preferences_from_feedback(self, session_id: str, feedback_data: Dict, user_id: int = None):
        """Aktualizuje preferencje na podstawie feedbacku"""
        preferences = self.get_user_preferences(session_id, user_id)
        
        # Analiza pozytywnego feedbacku
        if feedback_data.get('feedback') == 'positive':
            section_type = feedback_data.get('section_type', '')
            content = feedback_data.get('content', '').lower()
            
            # Jeśli pozytywny feedback na przykłady
            if 'przykład' in content or 'wzór' in content:
                preferences['prefers_examples'] = True
            
            # Jeśli pozytywny feedback na procedury
            if 'krok' in content or 'procedura' in content:
                preferences['prefers_procedures'] = True
            
            # Jeśli pozytywny feedback na teorię
            if 'teoria' in content or 'zasada' in content:
                preferences['prefers_theory'] = True
        
        # Zapisz zaktualizowane preferencje
        self._save_preferences(session_id, preferences)
    
    def _save_preferences(self, session_id: str, preferences: Dict):
        """Zapisuje preferencje użytkownika"""
        all_preferences = {}
        
        if os.path.exists(self.preferences_file):
            try:
                with open(self.preferences_file, 'r', encoding='utf-8') as f:
                    all_preferences = json.load(f)
            except Exception as e:
                print(f"Błąd wczytywania preferencji: {e}")
        
        all_preferences[session_id] = preferences
        
        try:
            with open(self.preferences_file, 'w', encoding='utf-8') as f:
                json.dump(all_preferences, f, ensure_ascii=False, indent=2)
            print(f"✅ Zapisano preferencje dla sesji {session_id}")
        except Exception as e:
            print(f"❌ Błąd zapisywania preferencji: {e}")
    
    def analyze_all_sessions(self) -> Dict:
        """Analizuje wszystkie sesje i generuje globalne wzorce"""
        history_dir = 'history'
        
        if not os.path.exists(history_dir):
            return {}
        
        global_patterns = {
            'total_sessions': 0,
            'common_keywords': Counter(),
            'popular_topics': Counter(),
            'preferred_structures': Counter(),
            'user_behavior_patterns': {},
            'timestamp': datetime.now().isoformat()
        }
        
        for filename in os.listdir(history_dir):
            if filename.endswith('.json'):
                session_id = filename.replace('.json', '')
                analysis = self.analyze_conversation_history(session_id)
                
                if analysis:
                    global_patterns['total_sessions'] += 1
                    
                    # Zbieraj słowa kluczowe
                    keywords = analysis['user_patterns'].get('common_keywords', [])
                    for keyword, count in keywords:
                        global_patterns['common_keywords'][keyword] += count
                    
                    # Zbieraj tematy
                    topics = analysis.get('topic_progression', [])
                    for topic in topics:
                        global_patterns['popular_topics'][topic] += 1
                    
                    # Zbieraj preferencje struktury
                    structure_pref = analysis.get('response_structure_preference', 'structured')
                    global_patterns['preferred_structures'][structure_pref] += 1
        
        return global_patterns
    
    def detect_repeated_questions(self, history: List[Dict]) -> Dict:
        """Wykrywa powtarzające się pytania w historii"""
        user_messages = [msg for msg in history if msg['role'] == 'user']
        
        # Normalizuj pytania (usuń znaki interpunkcyjne, małe litery)
        normalized_questions = []
        for msg in user_messages:
            normalized = re.sub(r'[^\w\s]', '', msg['content'].lower().strip())
            normalized_questions.append({
                'original': msg['content'],
                'normalized': normalized,
                'timestamp': msg['timestamp']
            })
        
        # Znajdź powtarzające się pytania
        question_counts = Counter([q['normalized'] for q in normalized_questions])
        repeated_questions = {q: count for q, count in question_counts.items() if count > 1}
        
        # Przygotuj szczegółowe informacje o powtarzających się pytaniach
        repeated_details = {}
        for normalized_q, count in repeated_questions.items():
            instances = [q for q in normalized_questions if q['normalized'] == normalized_q]
            repeated_details[normalized_q] = {
                'count': count,
                'instances': instances,
                'first_asked': instances[0]['timestamp'],
                'last_asked': instances[-1]['timestamp']
            }
        
        return {
            'total_repeated': len(repeated_questions),
            'repeated_questions': repeated_details,
            'repetition_rate': len(repeated_questions) / len(set(question_counts.keys())) if question_counts else 0
        }
    
    def generate_context_aware_prompt(self, session_id: str, current_question: str, history: List[Dict]) -> str:
        """Generuje prompt uwzględniający kontekst rozmowy"""
        if not history or len(history) < 2:
            return ""
        
        # Wykryj powtarzające się pytania
        repeated_info = self.detect_repeated_questions(history)
        
        # Sprawdź czy obecne pytanie to powtórzenie
        normalized_current = re.sub(r'[^\w\s]', '', current_question.lower().strip())
        
        prompt_parts = []
        
        # Jeśli to powtarzające się pytanie
        if normalized_current in repeated_info['repeated_questions']:
            repeat_info = repeated_info['repeated_questions'][normalized_current]
            prompt_parts.append(f"""
            UWAGA: Użytkownik zadał to pytanie już {repeat_info['count']} razy.
            Pierwsze pytanie: {repeat_info['first_asked']}
            Ostatnie pytanie: {repeat_info['last_asked']}
            
            Powinieneś:
            1. Odwołać się do wcześniejszych odpowiedzi
            2. Zapytać czy potrzebuje więcej szczegółów
            3. Sprawdzić czy coś było niejasne w poprzednich odpowiedziach
            4. Zaproponować inne podejście do tematu
            """)
        
        # Analiza kontekstu rozmowy
        user_messages = [msg for msg in history if msg['role'] == 'user']
        assistant_messages = [msg for msg in history if msg['role'] == 'assistant']
        
        if len(user_messages) > 1:
            prompt_parts.append(f"""
            KONTEKST ROZMOWY:
            - Liczba pytań użytkownika: {len(user_messages)}
            - Liczba odpowiedzi asystenta: {len(assistant_messages)}
            - Ostatnie pytanie: {user_messages[-2]['content'][:100]}...
            """)
        
        # Wykryj wzorce w pytaniach
        topics = self._extract_topics_from_messages(user_messages)
        if topics:
            prompt_parts.append(f"""
            TEMATY ROZMOWY:
            {', '.join(topics)}
            
            Zachowaj spójność tematyczną i rozbuduj wcześniejsze odpowiedzi.
            """)
        
        return '\n'.join(prompt_parts)
    
    def _extract_topics_from_messages(self, messages: List[Dict]) -> List[str]:
        """Wyodrębnia główne tematy z wiadomości"""
        aviation_keywords = {
            'siła nośna': 'aerodynamika',
            'nawigacja': 'nawigacja lotnicza',
            'radar': 'systemy awioniczne',
            'meteorologia': 'meteorologia lotnicza',
            'bezpieczeństwo': 'bezpieczeństwo lotów',
            'silnik': 'napęd lotniczy',
            'skrzydło': 'konstrukcja statku powietrznego',
            'lotnisko': 'operacje lotnicze',
            'pilot': 'pilotaż',
            'kontrola': 'kontrola ruchu lotniczego'
        }
        
        topics = set()
        for msg in messages:
            content = msg['content'].lower()
            for keyword, topic in aviation_keywords.items():
                if keyword in content:
                    topics.add(topic)
        
        return list(topics)
