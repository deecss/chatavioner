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
        if not history:
            return {
                'common_keywords': [],
                'question_length': {'avg': 0, 'min': 0, 'max': 0},
                'request_types': {},
                'follow_up_patterns': [],
                'preferred_detail_level': 'medium'
            }
        
        # Filtruj tylko poprawne wiadomości użytkownika
        user_messages = []
        for msg in history:
            if isinstance(msg, dict) and msg.get('role') == 'user' and msg.get('content'):
                user_messages.append(msg)
        
        if not user_messages:
            return {
                'common_keywords': [],
                'question_length': {'avg': 0, 'min': 0, 'max': 0},
                'request_types': {},
                'follow_up_patterns': [],
                'preferred_detail_level': 'medium'
            }
        
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
        if not history:
            return {
                'response_length': {'avg': 0, 'min': 0, 'max': 0},
                'structure_types': {},
                'content_types': {},
                'formatting_patterns': {}
            }
        
        # Filtruj tylko poprawne wiadomości asystenta
        assistant_messages = []
        for msg in history:
            if isinstance(msg, dict) and msg.get('role') == 'assistant' and msg.get('content'):
                assistant_messages.append(msg)
        
        if not assistant_messages:
            return {
                'response_length': {'avg': 0, 'min': 0, 'max': 0},
                'structure_types': {},
                'content_types': {},
                'formatting_patterns': {}
            }
        
        patterns = {
            'response_length': self._analyze_response_length(assistant_messages),
            'structure_types': self._analyze_response_structure(assistant_messages),
            'content_types': self._analyze_content_types(assistant_messages),
            'formatting_patterns': self._analyze_formatting_patterns(assistant_messages)
        }
        
        return patterns
    
    def _find_common_keywords(self, messages: List[Dict]) -> List[Tuple[str, int]]:
        """Znajduje najczęściej używane słowa kluczowe"""
        if not messages:
            return []
        
        try:
            all_text = ' '.join([msg.get('content', '').lower() for msg in messages if msg.get('content')])
            
            if not all_text:
                return []
            
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
        except Exception as e:
            print(f"❌ Błąd w _find_common_keywords: {e}")
            return []
    
    def _analyze_question_length(self, messages: List[Dict]) -> Dict:
        """Analizuje długość pytań użytkownika"""
        try:
            lengths = [len(msg.get('content', '').split()) for msg in messages if msg.get('content')]
            
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
        except Exception as e:
            print(f"❌ Błąd w _analyze_question_length: {e}")
            return {'avg_length': 0, 'preferred_range': 'short'}
    
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
        
        for msg in self._filter_valid_messages(messages):
            content = self._get_safe_content(msg).lower()
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
        """Pobiera preferencje użytkownika na podstawie WSZYSTKICH jego sesji"""
        if user_id:
            # Sprawdź czy istnieją zapisane preferencje użytkownika
            saved_preferences = self.get_saved_user_preferences(user_id)
            if saved_preferences:
                # Sprawdź czy preferencje nie są starsze niż 24 godziny
                saved_time = saved_preferences.get('updated_at')
                if saved_time:
                    try:
                        saved_datetime = datetime.fromisoformat(saved_time.replace('Z', '+00:00'))
                        time_diff = datetime.now() - saved_datetime
                        if time_diff.total_seconds() < 24 * 3600:  # 24 godziny
                            print(f"📋 Używam zapisanych preferencji użytkownika {user_id}")
                            return saved_preferences
                    except Exception as e:
                        print(f"⚠️  Błąd parsowania czasu zapisanych preferencji: {e}")
            
            # Analizuj wszystkie sesje użytkownika
            print(f"🔄 Przeprowadzam pełną analizę sesji użytkownika {user_id}")
            analysis = self.analyze_all_user_sessions(user_id)
        else:
            # Fallback - analizuj tylko bieżącą sesję
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
            'total_sessions_analyzed': analysis.get('total_sessions', 1),
            'updated_at': datetime.now().isoformat()
        }
        
        # Zapisz preferencje dla przyszłego użycia (tylko jeśli to analiza wszystkich sesji)
        if user_id and analysis.get('total_sessions', 1) > 1:
            self._save_user_preferences(user_id, preferences)
        
        return preferences
    
    def analyze_all_user_sessions(self, user_id: int) -> Dict:
        """Analizuje wszystkie sesje danego użytkownika i sumuje dane"""
        print(f"🧠 Analizuję wszystkie sesje użytkownika {user_id}...")
        
        # Pobierz wszystkie sesje użytkownika
        user_sessions = self._get_user_sessions(user_id)
        
        if not user_sessions:
            print(f"⚠️  Brak sesji dla użytkownika {user_id}")
            return {}
        
        print(f"📊 Znaleziono {len(user_sessions)} sesji użytkownika {user_id}")
        
        # Inicjalizuj strukturę do sumowania danych
        aggregated_analysis = {
            'user_id': user_id,
            'total_sessions': len(user_sessions),
            'total_messages': 0,
            'user_patterns': {
                'common_keywords': Counter(),
                'question_length': {'lengths': []},
                'request_types': Counter(),
                'follow_up_patterns': Counter(),
                'preferred_detail_level': Counter()
            },
            'response_patterns': {
                'response_length': {'lengths': []},
                'structure_types': Counter(),
                'content_types': Counter(),
                'formatting_patterns': Counter()
            },
            'topic_progression': [],
            'question_types': Counter(),
            'timestamp': datetime.now().isoformat()
        }
        
        # Analizuj każdą sesję użytkownika
        for session_id in user_sessions:
            try:
                session_analysis = self.analyze_conversation_history(session_id, user_id)
                if session_analysis:
                    self._merge_session_analysis(aggregated_analysis, session_analysis)
                    print(f"✅ Przeanalizowano sesję {session_id}")
            except Exception as e:
                print(f"⚠️  Błąd analizy sesji {session_id}: {e}")
                continue
        
        # Przetwórz zagregowane dane
        aggregated_analysis = self._process_aggregated_data(aggregated_analysis)
        
        print(f"🎯 Analiza użytkownika {user_id} zakończona - {aggregated_analysis['total_sessions']} sesji, {aggregated_analysis['total_messages']} wiadomości")
        
        return aggregated_analysis
    
    def _get_user_sessions(self, user_id: int) -> List[str]:
        """Pobiera listę wszystkich sesji użytkownika"""
        user_sessions = []
        
        # Sprawdź plik sesji użytkownika
        user_sessions_file = f'data/user_sessions/{user_id}.json'
        if os.path.exists(user_sessions_file):
            try:
                with open(user_sessions_file, 'r', encoding='utf-8') as f:
                    sessions_data = json.load(f)
                    if isinstance(sessions_data, list):
                        user_sessions = [session['session_id'] for session in sessions_data if 'session_id' in session]
                        print(f"📋 Znaleziono {len(user_sessions)} sesji w pliku użytkownika")
            except Exception as e:
                print(f"❌ Błąd wczytywania sesji użytkownika {user_id}: {e}")
        
        # Również sprawdź katalog history dla wszystkich sesji (fallback)
        history_dir = 'history'
        if os.path.exists(history_dir):
            try:
                for filename in os.listdir(history_dir):
                    if filename.endswith('.json') and not filename.endswith('_full_context.json'):
                        session_id = filename.replace('.json', '')
                        # Sprawdź czy sesja należy do użytkownika
                        if self._session_belongs_to_user(session_id, user_id):
                            if session_id not in user_sessions:
                                user_sessions.append(session_id)
            except Exception as e:
                print(f"❌ Błąd skanowania katalogu history: {e}")
        
        return user_sessions
    
    def _session_belongs_to_user(self, session_id: str, user_id: int) -> bool:
        """Sprawdza czy sesja należy do danego użytkownika"""
        try:
            history_file = f'history/{session_id}.json'
            if os.path.exists(history_file):
                with open(history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
                    # Sprawdź czy w historii są wiadomości tego użytkownika
                    for msg in history:
                        if isinstance(msg, dict) and msg.get('user_id') == user_id:
                            return True
            return False
        except Exception as e:
            print(f"⚠️  Błąd sprawdzania przynależności sesji {session_id}: {e}")
            return False
    
    def _merge_session_analysis(self, aggregated: Dict, session_analysis: Dict):
        """Łączy analizę pojedynczej sesji z zagregowanymi danymi"""
        try:
            # Sumuj całkowitą liczbę wiadomości
            aggregated['total_messages'] += session_analysis.get('total_messages', 0)
            
            # Łącz wzorce użytkownika
            user_patterns = session_analysis.get('user_patterns', {})
            
            # Słowa kluczowe
            keywords = user_patterns.get('common_keywords', [])
            for keyword, count in keywords:
                aggregated['user_patterns']['common_keywords'][keyword] += count
            
            # Długości pytań
            question_length = user_patterns.get('question_length', {})
            if 'avg_length' in question_length:
                aggregated['user_patterns']['question_length']['lengths'].append(question_length['avg_length'])
            
            # Typy zapytań
            request_types = user_patterns.get('request_types', {})
            for req_type, count in request_types.items():
                aggregated['user_patterns']['request_types'][req_type] += count
            
            # Wzorce follow-up
            follow_up = user_patterns.get('follow_up_patterns', {})
            for pattern_type, count in follow_up.items():
                aggregated['user_patterns']['follow_up_patterns'][pattern_type] += count
            
            # Poziom szczegółowości
            detail_level = user_patterns.get('preferred_detail_level', 'medium')
            aggregated['user_patterns']['preferred_detail_level'][detail_level] += 1
            
            # Wzorce odpowiedzi
            response_patterns = session_analysis.get('response_patterns', {})
            
            # Długości odpowiedzi
            response_length = response_patterns.get('response_length', {})
            if 'avg_length' in response_length:
                aggregated['response_patterns']['response_length']['lengths'].append(response_length['avg_length'])
            
            # Typy struktur
            structure_types = response_patterns.get('structure_types', {})
            for struct_type, count in structure_types.items():
                aggregated['response_patterns']['structure_types'][struct_type] += count
            
            # Typy treści
            content_types = response_patterns.get('content_types', {})
            for content_type, count in content_types.items():
                aggregated['response_patterns']['content_types'][content_type] += count
            
            # Formatowanie
            formatting = response_patterns.get('formatting_patterns', {})
            for format_type, count in formatting.items():
                aggregated['response_patterns']['formatting_patterns'][format_type] += count
            
            # Progresja tematów
            topics = session_analysis.get('topic_progression', [])
            aggregated['topic_progression'].extend(topics)
            
            # Typy pytań
            question_types = session_analysis.get('question_types', {})
            for q_type, count in question_types.items():
                aggregated['question_types'][q_type] += count
                
        except Exception as e:
            print(f"❌ Błąd łączenia analizy sesji: {e}")
    
    def _process_aggregated_data(self, aggregated: Dict) -> Dict:
        """Przetwarza zagregowane dane do finalnej postaci"""
        try:
            # Przetwórz słowa kluczowe na listę top 20
            aggregated['user_patterns']['common_keywords'] = aggregated['user_patterns']['common_keywords'].most_common(20)
            
            # Oblicz średnią długość pytań
            lengths = aggregated['user_patterns']['question_length']['lengths']
            if lengths:
                avg_length = sum(lengths) / len(lengths)
                aggregated['user_patterns']['question_length'] = {
                    'avg': avg_length,
                    'min': min(lengths),
                    'max': max(lengths),
                    'preferred_range': 'short' if avg_length < 5 else 'medium' if avg_length < 15 else 'long'
                }
            else:
                aggregated['user_patterns']['question_length'] = {'avg': 0, 'preferred_range': 'medium'}
            
            # Konwertuj Countery na słowniki
            aggregated['user_patterns']['request_types'] = dict(aggregated['user_patterns']['request_types'])
            aggregated['user_patterns']['follow_up_patterns'] = dict(aggregated['user_patterns']['follow_up_patterns'])
            
            # Wybierz najczęstszy poziom szczegółowości
            detail_counter = aggregated['user_patterns']['preferred_detail_level']
            if detail_counter:
                aggregated['user_patterns']['preferred_detail_level'] = detail_counter.most_common(1)[0][0]
            else:
                aggregated['user_patterns']['preferred_detail_level'] = 'medium'
            
            # Przetwórz długości odpowiedzi
            response_lengths = aggregated['response_patterns']['response_length']['lengths']
            if response_lengths:
                aggregated['response_patterns']['response_length'] = {
                    'avg_length': sum(response_lengths) / len(response_lengths),
                    'min_length': min(response_lengths),
                    'max_length': max(response_lengths)
                }
            else:
                aggregated['response_patterns']['response_length'] = {'avg_length': 0}
            
            # Konwertuj pozostałe Countery
            aggregated['response_patterns']['structure_types'] = dict(aggregated['response_patterns']['structure_types'])
            aggregated['response_patterns']['content_types'] = dict(aggregated['response_patterns']['content_types'])
            aggregated['response_patterns']['formatting_patterns'] = dict(aggregated['response_patterns']['formatting_patterns'])
            aggregated['question_types'] = dict(aggregated['question_types'])
            
            return aggregated
            
        except Exception as e:
            print(f"❌ Błąd przetwarzania zagregowanych danych: {e}")
            return aggregated

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
        """Generuje prompt uczenia na podstawie preferencji użytkownika z WSZYSTKICH sesji"""
        preferences = self.get_user_preferences(session_id, user_id)
        
        prompt_parts = [
            "KONTEKST UCZENIA UŻYTKOWNIKA (na podstawie WSZYSTKICH sesji):",
            f"Poziom szczegółowości: {preferences['detail_level']}",
        ]
        
        # Informacja o liczbie analizowanych sesji
        total_sessions = preferences.get('total_sessions_analyzed', 1)
        if total_sessions > 1:
            prompt_parts.append(f"📊 Analiza oparta na {total_sessions} sesjach użytkownika")
        
        if preferences['prefers_examples']:
            prompt_parts.append("✅ Użytkownik preferuje PRZYKŁADY i WZORY - zawsze dodawaj praktyczne przykłady!")
        
        if preferences['prefers_procedures']:
            prompt_parts.append("✅ Użytkownik preferuje PROCEDURY - przedstawiaj informacje krok po kroku!")
        
        if preferences['prefers_theory']:
            prompt_parts.append("✅ Użytkownik preferuje TEORIĘ - dostarczaj solidne podstawy teoretyczne!")
        
        if preferences['prefers_practical']:
            prompt_parts.append("✅ Użytkownik preferuje PRAKTYKĘ - pokazuj zastosowania w rzeczywistości!")
        
        # Analiza wzorców z poprzednich pytań (ze wszystkich sesji)
        common_topics = preferences.get('common_topics', [])
        if common_topics:
            # Weź 10 najczęstszych tematów ze wszystkich sesji
            topic_counter = Counter(common_topics)
            most_common_topics = [topic for topic, count in topic_counter.most_common(10)]
            if most_common_topics:
                prompt_parts.append(f"🎯 Najczęstsze tematy ze wszystkich sesji: {', '.join(most_common_topics[:5])}")
        
        structure_pref = preferences.get('response_structure_preference', 'structured')
        if structure_pref == 'with_examples':
            prompt_parts.append("⚠️ OBOWIĄZKOWE: Zawsze dodawaj konkretne przykłady i wzory!")
        elif structure_pref == 'step_by_step':
            prompt_parts.append("⚠️ OBOWIĄZKOWE: Przedstawiaj informacje w formie kroków!")
        elif structure_pref == 'detailed_theory':
            prompt_parts.append("⚠️ OBOWIĄZKOWE: Dostarczaj szczegółowe wyjaśnienia teoretyczne!")
        
        # Dodaj informację o wzorcach pytań ze wszystkich sesji
        question_types = preferences.get('question_types', {})
        if question_types:
            top_question_types = sorted(question_types.items(), key=lambda x: x[1], reverse=True)[:3]
            if top_question_types:
                types_str = ', '.join([f"{qtype}({count})" for qtype, count in top_question_types])
                prompt_parts.append(f"📋 Najczęstsze typy pytań: {types_str}")
        
        return "\n".join(prompt_parts)
    
    def update_preferences_from_feedback(self, session_id: str, feedback_data: Dict, user_id: int = None):
        """Aktualizuje preferencje na podstawie feedbacku (analizuje wszystkie sesje użytkownika)"""
        # Pobierz preferencje na podstawie wszystkich sesji użytkownika
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
        
        # Zapisz zaktualizowane preferencje (dla użytkownika, nie sesji)
        if user_id:
            self._save_user_preferences(user_id, preferences)
        else:
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
    
    def _save_user_preferences(self, user_id: int, preferences: Dict):
        """Zapisuje preferencje użytkownika na podstawie wszystkich jego sesji"""
        user_preferences_file = f'data/user_preferences_{user_id}.json'
        
        try:
            with open(user_preferences_file, 'w', encoding='utf-8') as f:
                json.dump(preferences, f, ensure_ascii=False, indent=2)
            print(f"✅ Zapisano preferencje użytkownika {user_id} bazujące na {preferences.get('total_sessions_analyzed', 1)} sesjach")
        except Exception as e:
            print(f"❌ Błąd zapisywania preferencji użytkownika {user_id}: {e}")
    
    def get_saved_user_preferences(self, user_id: int) -> Dict:
        """Pobiera zapisane preferencje użytkownika"""
        user_preferences_file = f'data/user_preferences_{user_id}.json'
        
        if os.path.exists(user_preferences_file):
            try:
                with open(user_preferences_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"❌ Błąd wczytywania preferencji użytkownika {user_id}: {e}")
        
        return None

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
    
    def analyze_and_cache_all_users(self):
        """Analizuje i cachuje preferencje dla wszystkich użytkowników"""
        print("👥 Analizuję preferencje wszystkich użytkowników...")
        
        users_analyzed = 0
        
        # Sprawdź katalog user_sessions
        user_sessions_dir = 'data/user_sessions'
        if os.path.exists(user_sessions_dir):
            for filename in os.listdir(user_sessions_dir):
                if filename.endswith('.json') and filename != 'admin.json':
                    try:
                        # Wyodrębnij user_id z nazwy pliku (może być UUID lub nazwa)
                        user_id_str = filename.replace('.json', '')
                        
                        # Sprawdź czy to jest user admin (specjalny przypadek)
                        if user_id_str == 'admin':
                            # Znajdź ID użytkownika admin
                            user_id = self._get_admin_user_id()
                            if user_id:
                                self._analyze_and_cache_user(user_id)
                                users_analyzed += 1
                        else:
                            # Sprawdź czy w pliku są sesje użytkownika
                            sessions_file = os.path.join(user_sessions_dir, filename)
                            with open(sessions_file, 'r', encoding='utf-8') as f:
                                sessions_data = json.load(f)
                                if sessions_data and len(sessions_data) > 0:
                                    # Spróbuj pobrać user_id z pierwszej sesji
                                    first_session_id = sessions_data[0].get('session_id')
                                    if first_session_id:
                                        actual_user_id = self._get_user_id_from_session(first_session_id)
                                        if actual_user_id:
                                            self._analyze_and_cache_user(actual_user_id)
                                            users_analyzed += 1
                                        
                    except Exception as e:
                        print(f"⚠️  Błąd analizy użytkownika z pliku {filename}: {e}")
                        continue
        
        print(f"✅ Przeanalizowano i zachowano preferencje dla {users_analyzed} użytkowników")
    
    def _get_admin_user_id(self) -> int:
        """Pobiera ID użytkownika admin"""
        try:
            users_file = 'data/users.json'
            if os.path.exists(users_file):
                with open(users_file, 'r', encoding='utf-8') as f:
                    users_data = json.load(f)
                    for user in users_data:
                        if user.get('username') == 'admin':
                            return user.get('id')
            return None
        except Exception as e:
            print(f"❌ Błąd pobierania ID użytkownika admin: {e}")
            return None
    
    def _get_user_id_from_session(self, session_id: str) -> int:
        """Pobiera user_id z pierwszej wiadomości w sesji"""
        try:
            history_file = f'history/{session_id}.json'
            if os.path.exists(history_file):
                with open(history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
                    for msg in history:
                        if isinstance(msg, dict) and 'user_id' in msg:
                            return msg['user_id']
            return None
        except Exception as e:
            print(f"⚠️  Błąd pobierania user_id z sesji {session_id}: {e}")
            return None
    
    def _analyze_and_cache_user(self, user_id: int):
        """Analizuje i cachuje preferencje pojedynczego użytkownika"""
        try:
            print(f"🔍 Analizuję użytkownika {user_id}...")
            preferences = self.get_user_preferences("", user_id)
            if preferences.get('total_sessions_analyzed', 0) > 0:
                print(f"✅ Przeanalizowano użytkownika {user_id}: {preferences['total_sessions_analyzed']} sesji")
            else:
                print(f"⚠️  Brak sesji dla użytkownika {user_id}")
        except Exception as e:
            print(f"❌ Błąd analizy użytkownika {user_id}: {e}")

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
    
    def _get_safe_content(self, msg: Dict) -> str:
        """Bezpiecznie pobiera content z wiadomości"""
        if not isinstance(msg, dict):
            return ''
        return msg.get('content', '')
    
    def _filter_valid_messages(self, messages: List[Dict], role: str = None) -> List[Dict]:
        """Filtruje tylko poprawne wiadomości"""
        valid_messages = []
        for msg in messages:
            if isinstance(msg, dict) and msg.get('content'):
                if role is None or msg.get('role') == role:
                    valid_messages.append(msg)
        return valid_messages
