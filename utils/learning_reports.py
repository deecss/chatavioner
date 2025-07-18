#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
System raportów uczenia się modelu
Generuje raporty o aktywności użytkowników, pytaniach, feedbackach i wzorcach uczenia się
"""
import os
import json
import uuid
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from typing import Dict, List, Any, Optional
import glob

class LearningReportsSystem:
    """System generowania raportów uczenia się"""
    
    def __init__(self):
        self.reports_dir = "reports/learning"
        self.data_dir = "data"
        self.history_dir = "history"
        self.feedback_dir = "feedback"
        self.learning_data_file = "data/learning_data.json"
        self.users_file = "data/users.json"
        
        # Utwórz katalogi jeśli nie istnieją
        os.makedirs(self.reports_dir, exist_ok=True)
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.history_dir, exist_ok=True)
        os.makedirs(self.feedback_dir, exist_ok=True)
        
        # Załaduj dane użytkowników
        self.users_data = self._load_users_data()
    
    def generate_daily_report(self, date: datetime = None) -> Dict[str, Any]:
        """Generuje dzienny raport aktywności"""
        if date is None:
            date = datetime.now()
        
        report_date = date.strftime('%Y-%m-%d')
        start_time = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(days=1)
        
        print(f"📊 Generuję raport dzienny za {report_date}")
        
        # Zbierz dane z różnych źródeł
        user_activity = self._analyze_user_activity(start_time, end_time)
        questions_analysis = self._analyze_questions(start_time, end_time)
        feedback_analysis = self._analyze_feedback(start_time, end_time)
        learning_insights = self._analyze_learning_patterns(start_time, end_time)
        topic_distribution = self._analyze_topic_distribution(start_time, end_time)
        
        report = {
            "report_id": str(uuid.uuid4()),
            "report_type": "daily",
            "date": report_date,
            "generated_at": datetime.now().isoformat(),
            "period": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat()
            },
            "summary": {
                "total_users": len(user_activity),
                "total_questions": questions_analysis["total_questions"],
                "total_feedback": feedback_analysis["total_feedback"],
                "avg_questions_per_user": questions_analysis["avg_per_user"],
                "feedback_ratio": feedback_analysis["feedback_ratio"]
            },
            "user_activity": user_activity,
            "questions_analysis": questions_analysis,
            "feedback_analysis": feedback_analysis,
            "learning_insights": learning_insights,
            "topic_distribution": topic_distribution
        }
        
        # Zapisz raport
        report_filename = f"daily_report_{report_date}.json"
        report_path = os.path.join(self.reports_dir, report_filename)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Raport dzienny zapisany: {report_path}")
        return report
    
    def _analyze_user_activity(self, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
        """Analizuje aktywność użytkowników"""
        user_stats = defaultdict(lambda: {
            "user_id": "",
            "username": "",
            "role": "",
            "sessions_count": 0,
            "questions_count": 0,
            "responses_received": 0,
            "feedback_given": 0,
            "topics_discussed": set(),
            "session_duration_total": 0,
            "first_activity": None,
            "last_activity": None,
            "learning_profile": {},
            "detailed_activity": []
        })
        
        # Analizuj pliki historii
        if os.path.exists(self.history_dir):
            for filename in os.listdir(self.history_dir):
                if filename.endswith('.json'):
                    session_id = filename.replace('.json', '')
                    filepath = os.path.join(self.history_dir, filename)
                    
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            history = json.load(f)
                        
                        session_users = set()
                        session_questions = 0
                        session_topics = set()
                        
                        # Filtruj wiadomości z danego okresu
                        for message in history:
                            if not isinstance(message, dict):
                                continue
                            
                            msg_time = self._parse_timestamp(message.get('timestamp'))
                            if not msg_time or not (start_time <= msg_time < end_time):
                                continue
                            
                            user_id = message.get('user_id', 'unknown')
                            if user_id == 'unknown':
                                continue
                            
                            session_users.add(user_id)
                            stats = user_stats[user_id]
                            
                            # Pobierz informacje o użytkowniku
                            if not stats["user_id"]:
                                user_info = self._get_user_info(user_id)
                                stats["user_id"] = user_id
                                stats["username"] = user_info["username"]
                                stats["role"] = user_info["role"]
                            
                            # Aktualizuj statystyki
                            if message.get('role') == 'user':
                                stats["questions_count"] += 1
                                session_questions += 1
                                
                                # Wykryj temat
                                content = message.get('content', '').lower()
                                topic = self._detect_topic(content)
                                if topic:
                                    stats["topics_discussed"].add(topic)
                                    session_topics.add(topic)
                                
                                # Dodaj szczegółową aktywność
                                stats["detailed_activity"].append({
                                    "timestamp": msg_time.isoformat(),
                                    "type": "question",
                                    "topic": topic,
                                    "content_preview": content[:100] + "..." if len(content) > 100 else content,
                                    "session_id": session_id
                                })
                            
                            elif message.get('role') == 'assistant':
                                stats["responses_received"] += 1
                            
                            # Aktualizuj czasy aktywności
                            if not stats["first_activity"] or msg_time < datetime.fromisoformat(stats["first_activity"]):
                                stats["first_activity"] = msg_time.isoformat()
                            
                            if not stats["last_activity"] or msg_time > datetime.fromisoformat(stats["last_activity"]):
                                stats["last_activity"] = msg_time.isoformat()
                        
                        # Zwiększ licznik sesji dla użytkowników aktywnych w tej sesji
                        for user_id in session_users:
                            user_stats[user_id]["sessions_count"] += 1
                    
                    except Exception as e:
                        print(f"⚠️  Błąd analizy historii {filename}: {e}")
        
        # Analizuj feedback
        if os.path.exists(self.feedback_dir):
            for user_dir in os.listdir(self.feedback_dir):
                user_path = os.path.join(self.feedback_dir, user_dir)
                if os.path.isdir(user_path):
                    feedback_files = glob.glob(os.path.join(user_path, "*.json"))
                    for feedback_file in feedback_files:
                        try:
                            with open(feedback_file, 'r', encoding='utf-8') as f:
                                feedback_data = json.load(f)
                            
                            feedback_time = self._parse_timestamp(feedback_data.get('timestamp'))
                            if feedback_time and start_time <= feedback_time < end_time:
                                user_id = feedback_data.get('user_id', user_dir)
                                if user_id in user_stats:
                                    user_stats[user_id]["feedback_given"] += 1
                                    
                                    # Dodaj szczegółową aktywność
                                    user_stats[user_id]["detailed_activity"].append({
                                        "timestamp": feedback_time.isoformat(),
                                        "type": "feedback",
                                        "feedback_type": feedback_data.get('type', 'unknown'),
                                        "rating": feedback_data.get('rating', 0),
                                        "comment": feedback_data.get('comment', '')[:50] + "..." if len(feedback_data.get('comment', '')) > 50 else feedback_data.get('comment', '')
                                    })
                        
                        except Exception as e:
                            print(f"⚠️  Błąd analizy feedback {feedback_file}: {e}")
        
        # Wzbogać o szczegółowe profile uczenia się
        for user_id, stats in user_stats.items():
            try:
                stats["learning_profile"] = self._get_user_learning_profile(user_id)
            except Exception as e:
                print(f"⚠️  Błąd tworzenia profilu uczenia dla {user_id}: {e}")
                # Domyślny profil w przypadku błędu
                stats["learning_profile"] = {
                    'learning_level': 'beginner',
                    'preferred_detail_level': 'medium',
                    'learning_progress': {},
                    'preferences': {
                        'topics': [],
                        'question_style': 'direct',
                        'response_length': 'medium'
                    },
                    'statistics': {
                        'total_sessions': stats.get('sessions_count', 0),
                        'total_messages': stats.get('questions_count', 0),
                        'avg_session_length': 0,
                        'learning_streak': 0,
                        'mastered_topics': []
                    },
                    'recent_activity': {
                        'last_session': None,
                        'recent_topics': list(stats.get('topics_discussed', [])),
                        'improvement_areas': []
                    }
                }
        
        # Konwertuj sets na listy dla JSON i posortuj aktywność
        result = []
        for user_id, stats in user_stats.items():
            stats["topics_discussed"] = list(stats["topics_discussed"])
            # Sortuj szczegółową aktywność chronologicznie
            stats["detailed_activity"].sort(key=lambda x: x["timestamp"])
            # Ogranicz do ostatnich 10 aktywności
            stats["detailed_activity"] = stats["detailed_activity"][-10:]
            
            # Przenieś dane z learning_profile na główny poziom dla kompatybilności z szablonem
            if "learning_profile" in stats:
                profile = stats["learning_profile"]
                stats["learning_level"] = profile.get("learning_level", "beginner")
                stats["preferred_detail_level"] = profile.get("preferred_detail_level", "medium")
                stats["preferences"] = profile.get("preferences", {})
            
            result.append(stats)
        
        return result
    
    def _analyze_questions(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Analizuje pytania zadane w danym okresie"""
        questions = []
        question_types = Counter()
        question_complexity = Counter()
        
        if os.path.exists(self.history_dir):
            for filename in os.listdir(self.history_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(self.history_dir, filename)
                    
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            history = json.load(f)
                        
                        for message in history:
                            if not isinstance(message, dict) or message.get('role') != 'user':
                                continue
                            
                            msg_time = self._parse_timestamp(message.get('timestamp'))
                            if not msg_time or not (start_time <= msg_time < end_time):
                                continue
                            
                            content = message.get('content', '')
                            if not content:
                                continue
                            
                            # Analiza pytania
                            question_analysis = self._analyze_question(content)
                            questions.append({
                                "content": content[:200] + "..." if len(content) > 200 else content,
                                "length": len(content),
                                "type": question_analysis["type"],
                                "complexity": question_analysis["complexity"],
                                "topic": question_analysis["topic"],
                                "timestamp": msg_time.isoformat(),
                                "user_id": message.get('user_id')
                            })
                            
                            question_types[question_analysis["type"]] += 1
                            question_complexity[question_analysis["complexity"]] += 1
                    
                    except Exception as e:
                        print(f"⚠️  Błąd analizy pytań {filename}: {e}")
        
        total_questions = len(questions)
        unique_users = len(set(q["user_id"] for q in questions if q["user_id"]))
        
        # Sortuj pytania chronologicznie
        questions_sorted = sorted(questions, key=lambda x: x["timestamp"])
        
        return {
            "total_questions": total_questions,
            "unique_users": unique_users,
            "avg_per_user": total_questions / unique_users if unique_users > 0 else 0,
            "questions_by_type": dict(question_types),
            "questions_by_complexity": dict(question_complexity),
            "avg_question_length": sum(q["length"] for q in questions) / total_questions if total_questions > 0 else 0,
            "sample_questions": questions_sorted[:15],  # Pierwsze 15 pytań chronologicznie
            "recent_questions": questions_sorted[-10:] if questions_sorted else [],  # Ostatnie 10 pytań
            "questions_by_topic": self._group_questions_by_topic(questions_sorted)
        }
    
    def _group_questions_by_topic(self, questions: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Grupuje pytania według tematów"""
        topics_questions = defaultdict(list)
        
        for question in questions:
            topic = question.get("topic", "inne")
            if topic:
                topics_questions[topic].append({
                    "content": question["content"],
                    "user_id": question["user_id"],
                    "timestamp": question["timestamp"],
                    "complexity": question["complexity"]
                })
        
        # Ograniczenie do 5 pytań na temat
        for topic in topics_questions:
            topics_questions[topic] = topics_questions[topic][:5]
        
        return dict(topics_questions)
    
    def _normalize_datetime(self, dt):
        """Zwraca offset-naive datetime (usuwa strefę czasową jeśli jest)"""
        if dt is None:
            return None
        if dt.tzinfo is not None:
            return dt.replace(tzinfo=None)
        return dt
    
    def _safe_feedback_entry(self, entry):
        """Zwraca pojedynczy feedback jako dict lub None"""
        if isinstance(entry, dict):
            return entry
        elif isinstance(entry, list):
            # Jeśli entry to lista, spróbuj wziąć pierwszy element
            if len(entry) > 0 and isinstance(entry[0], dict):
                return entry[0]
        return None
    
    def _analyze_feedback(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Analizuje feedback użytkowników"""
        feedback_data = []
        positive_feedback = 0
        negative_feedback = 0
        start_time = self._normalize_datetime(start_time)
        end_time = self._normalize_datetime(end_time)
        
        if os.path.exists(self.feedback_dir):
            for user_dir in os.listdir(self.feedback_dir):
                user_path = os.path.join(self.feedback_dir, user_dir)
                if os.path.isdir(user_path):
                    feedback_files = glob.glob(os.path.join(user_path, "*.json"))
                    for feedback_file in feedback_files:
                        try:
                            with open(feedback_file, 'r', encoding='utf-8') as f:
                                feedback = json.load(f)
                            
                            # Obsługa listy feedbacków w pliku
                            if isinstance(feedback, list):
                                feedback_entries = [self._safe_feedback_entry(e) for e in feedback if isinstance(e, dict)]
                            elif isinstance(feedback, dict):
                                feedback_entries = [feedback]
                            else:
                                feedback_entries = []
                            
                            for fb in feedback_entries:
                                if not fb:  # Pomiń None entries
                                    continue
                                    
                                feedback_time = self._parse_timestamp(fb.get('timestamp'))
                                feedback_time = self._normalize_datetime(feedback_time)
                                
                                # Sprawdź czy feedback_time jest prawidłowy
                                if not feedback_time:
                                    continue
                                
                                # Porównaj tylko offset-naive datetimes
                                try:
                                    if not (start_time <= feedback_time < end_time):
                                        continue
                                except TypeError:
                                    # Jeśli nadal problem z porównaniem, pomiń
                                    print(f"⚠️  Błąd porównania czasu dla feedback: {fb.get('timestamp')}")
                                    continue
                                
                                feedback_data.append({
                                    "user_id": fb.get('user_id', user_dir),
                                    "type": fb.get('type', 'unknown'),
                                    "rating": fb.get('rating', 0),
                                    "comment": fb.get('comment', ''),
                                    "timestamp": feedback_time.isoformat()
                                })
                                if fb.get('type') == 'positive':
                                    positive_feedback += 1
                                elif fb.get('type') == 'negative':
                                    negative_feedback += 1
                        except Exception as e:
                            print(f"⚠️  Błąd analizy feedback {feedback_file}: {e}")
        
        total_feedback = len(feedback_data)
        
        return {
            "total_feedback": total_feedback,
            "positive_feedback": positive_feedback,
            "negative_feedback": negative_feedback,
            "feedback_ratio": positive_feedback / total_feedback if total_feedback > 0 else 0,
            "avg_rating": sum(f["rating"] for f in feedback_data) / total_feedback if total_feedback > 0 else 0,
            "recent_feedback": feedback_data[-10:] if feedback_data else []
        }
    
    def _analyze_learning_patterns(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Analizuje wzorce uczenia się"""
        learning_patterns = {
            "user_preferences": {},
            "topic_progression": {},
            "question_evolution": {},
            "common_misconceptions": []
        }
        
        try:
            if os.path.exists(self.learning_data_file):
                with open(self.learning_data_file, 'r', encoding='utf-8') as f:
                    learning_data = json.load(f)
                
                # Obsługa listy lub słownika
                if isinstance(learning_data, dict):
                    items = learning_data.items()
                elif isinstance(learning_data, list):
                    items = [(entry.get('user_id', f'unknown_{i}'), entry) for i, entry in enumerate(learning_data) if isinstance(entry, dict)]
                else:
                    items = []
                for user_id, data in items:
                    if isinstance(data, dict):
                        preferences = data.get('preferences', {})
                        learning_patterns["user_preferences"][user_id] = {
                            "detail_level": preferences.get('detail_level', 'medium'),
                            "preferred_topics": preferences.get('preferred_topics', []),
                            "learning_speed": preferences.get('learning_speed', 'normal'),
                            "question_style": preferences.get('question_style', 'direct')
                        }
        
        except Exception as e:
            print(f"⚠️  Błąd analizy wzorców uczenia: {e}")
        
        return learning_patterns
    
    def _analyze_topic_distribution(self, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Analizuje rozkład tematów"""
        topic_counter = Counter()
        topic_by_user = defaultdict(set)
        
        if os.path.exists(self.history_dir):
            for filename in os.listdir(self.history_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(self.history_dir, filename)
                    
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            history = json.load(f)
                        
                        for message in history:
                            if not isinstance(message, dict) or message.get('role') != 'user':
                                continue
                            
                            msg_time = self._parse_timestamp(message.get('timestamp'))
                            if not msg_time or not (start_time <= msg_time < end_time):
                                continue
                            
                            content = message.get('content', '').lower()
                            topic = self._detect_topic(content)
                            
                            if topic:
                                topic_counter[topic] += 1
                                user_id = message.get('user_id')
                                if user_id:
                                    topic_by_user[user_id].add(topic)
                    
                    except Exception as e:
                        print(f"⚠️  Błąd analizy tematów {filename}: {e}")
        
        # Konwertuj sets na listy
        topic_by_user_list = {user_id: list(topics) for user_id, topics in topic_by_user.items()}
        
        # Konwertuj most_popular_topics na format z obiektem
        most_popular = []
        for topic, count in topic_counter.most_common(10):
            most_popular.append({
                "topic": topic,
                "count": count
            })
        
        return {
            "topic_distribution": dict(topic_counter),
            "most_popular_topics": most_popular,
            "most_popular": most_popular,  # Dodaj też w tym formacie dla kompatybilności
            "topics_by_user": topic_by_user_list,
            "unique_topics": len(topic_counter),
            "avg_topics_per_user": sum(len(topics) for topics in topic_by_user.values()) / len(topic_by_user) if topic_by_user else 0
        }
    
    def _enrich_with_learning_data(self, user_stats: Dict[str, Dict[str, Any]]) -> None:
        """Wzbogaca statystyki użytkowników o dane z systemu uczenia"""
        try:
            if os.path.exists(self.learning_data_file):
                with open(self.learning_data_file, 'r', encoding='utf-8') as f:
                    learning_data = json.load(f)
                
                for user_id, stats in user_stats.items():
                    if user_id in learning_data:
                        user_learning = learning_data[user_id]
                        
                        # Dodaj informacje o uczeniu się
                        stats["learning_level"] = user_learning.get('level', 'beginner')
                        stats["preferred_detail_level"] = user_learning.get('preferences', {}).get('detail_level', 'medium')
                        stats["learning_progress"] = user_learning.get('progress', {})
                        
                        # Dodaj informacje o preferencjach
                        preferences = user_learning.get('preferences', {})
                        stats["preferences"] = {
                            "topics": preferences.get('preferred_topics', []),
                            "question_style": preferences.get('question_style', 'direct'),
                            "response_length": preferences.get('response_length', 'medium')
                        }
        
        except Exception as e:
            print(f"⚠️  Błąd wzbogacania danych uczenia: {e}")
    
    def _detect_topic(self, content: str) -> str:
        """Wykrywa temat pytania"""
        content_lower = content.lower()
        
        # Słownik tematów lotniczych
        topics = {
            'aerodynamika': ['aerodynamika', 'siła nośna', 'siła ciągu', 'opór', 'profil skrzydła', 'kąt natarcia', 'przeciągnięcie'],
            'nawigacja': ['nawigacja', 'gps', 'kompas', 'kurs', 'namierzanie', 'pozycja', 'współrzędne'],
            'meteorologia': ['pogoda', 'wiatr', 'chmury', 'burza', 'oblodzenie', 'turbulencje', 'widoczność'],
            'przepisy': ['przepisy', 'regulacje', 'icao', 'certyfikacja', 'licencja', 'prawo lotnicze'],
            'bezpieczeństwo': ['bezpieczeństwo', 'awaria', 'procedury awaryjne', 'lądowanie awaryjne', 'ryzyko'],
            'awionika': ['awionika', 'radar', 'autopilot', 'instrumenty', 'systemy pokładowe'],
            'silniki': ['silnik', 'turbina', 'spalanie', 'paliwo', 'moc', 'ciąg'],
            'struktury': ['konstrukcja', 'materiały', 'wytrzymałość', 'kadłub', 'skrzydła'],
            'pilotaż': ['pilotaż', 'sterowanie', 'manewr', 'start', 'lądowanie', 'lot']
        }
        
        for topic, keywords in topics.items():
            if any(keyword in content_lower for keyword in keywords):
                return topic
        
        return 'ogólne'
    
    def _analyze_question(self, content: str) -> Dict[str, str]:
        """Analizuje typ i złożoność pytania"""
        content_lower = content.lower()
        
        # Określ typ pytania
        if any(word in content_lower for word in ['jak', 'w jaki sposób', 'dlaczego', 'czemu']):
            q_type = 'proceduralne'
        elif any(word in content_lower for word in ['co to', 'czym jest', 'definicja', 'znaczenie']):
            q_type = 'definicyjne'
        elif any(word in content_lower for word in ['kiedy', 'gdzie', 'ile', 'która']):
            q_type = 'faktyczne'
        elif '?' in content:
            q_type = 'pytające'
        else:
            q_type = 'inne'
        
        # Określ złożoność
        if len(content) < 50:
            complexity = 'proste'
        elif len(content) < 150:
            complexity = 'średnie'
        else:
            complexity = 'złożone'
        
        return {
            'type': q_type,
            'complexity': complexity,
            'topic': self._detect_topic(content)
        }
    
    def _parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """Parsuje timestamp z różnych formatów"""
        if not timestamp_str:
            return None
        
        try:
            # Spróbuj różne formaty
            formats = [
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%dT%H:%M:%S.%f',
                '%Y-%m-%d %H:%M:%S.%f',
                '%Y-%m-%dT%H:%M:%S%z',
                '%Y-%m-%dT%H:%M:%S.%f%z'
            ]
            
            for fmt in formats:
                try:
                    dt = datetime.strptime(timestamp_str, fmt)
                    # Zawsze zwróć offset-naive datetime
                    return self._normalize_datetime(dt)
                except ValueError:
                    continue
            
            # Jeśli żaden format nie zadziałał, spróbuj ISO format
            try:
                dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                return self._normalize_datetime(dt)
            except ValueError:
                pass
            
            # Ostatnia próba - usuń wszystkie znaki stref czasowych i spróbuj ponownie
            cleaned = timestamp_str.split('+')[0].split('Z')[0]
            for fmt in formats[:4]:  # Tylko formaty bez strefy czasowej
                try:
                    return datetime.strptime(cleaned, fmt)
                except ValueError:
                    continue
        
        except Exception as e:
            print(f"⚠️  Błąd parsowania timestamp '{timestamp_str}': {e}")
        
        return None
    
    def get_available_reports(self) -> List[Dict[str, Any]]:
        """Pobiera listę dostępnych raportów"""
        reports = []
        
        if os.path.exists(self.reports_dir):
            for filename in os.listdir(self.reports_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(self.reports_dir, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            report_data = json.load(f)
                        
                        reports.append({
                            "filename": filename,
                            "report_id": report_data.get('report_id'),
                            "date": report_data.get('date'),
                            "type": report_data.get('report_type'),
                            "generated_at": report_data.get('generated_at'),
                            "summary": report_data.get('summary', {}),
                            "filepath": filepath
                        })
                    
                    except Exception as e:
                        print(f"⚠️  Błąd odczytu raportu {filename}: {e}")
        
        # Sortuj według daty
        reports.sort(key=lambda x: x['date'], reverse=True)
        return reports
    
    def get_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        """Pobiera konkretny raport"""
        reports = self.get_available_reports()
        
        for report in reports:
            if report['report_id'] == report_id:
                try:
                    with open(report['filepath'], 'r', encoding='utf-8') as f:
                        return json.load(f)
                except Exception as e:
                    print(f"⚠️  Błąd odczytu raportu {report_id}: {e}")
        
        return None
    
    def cleanup_old_reports(self, days_to_keep: int = 30) -> None:
        """Usuwa stare raporty"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        if os.path.exists(self.reports_dir):
            for filename in os.listdir(self.reports_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(self.reports_dir, filename)
                    try:
                        # Sprawdź datę z nazwy pliku
                        if 'daily_report_' in filename:
                            date_str = filename.replace('daily_report_', '').replace('.json', '')
                            file_date = datetime.strptime(date_str, '%Y-%m-%d')
                            
                            if file_date < cutoff_date:
                                os.remove(filepath)
                                print(f"🗑️  Usunięto stary raport: {filename}")
                    
                    except Exception as e:
                        print(f"⚠️  Błąd podczas usuwania raportu {filename}: {e}")
    
    def _load_users_data(self) -> Dict[str, Dict[str, Any]]:
        """Ładuje dane użytkowników z pliku"""
        users_dict = {}
        try:
            if os.path.exists(self.users_file):
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    users_list = json.load(f)
                
                # Konwertuj listę na słownik z ID jako kluczem
                for user in users_list:
                    if isinstance(user, dict) and 'id' in user:
                        users_dict[user['id']] = user
        
        except Exception as e:
            print(f"⚠️  Błąd ładowania danych użytkowników: {e}")
        
        return users_dict
    
    def _get_user_info(self, user_id: str) -> Dict[str, Any]:
        """Pobiera informacje o użytkowniku"""
        if user_id in self.users_data:
            user = self.users_data[user_id]
            return {
                'id': user_id,
                'username': user.get('username', 'Unknown'),
                'role': user.get('role', 'user'),
                'created_at': user.get('created_at', 'Unknown')
            }
        else:
            return {
                'id': user_id,
                'username': f'User_{user_id[:8]}',
                'role': 'user',
                'created_at': 'Unknown'
            }
    
    def _get_user_learning_profile(self, user_id: str) -> Dict[str, Any]:
        """Pobiera szczegółowy profil uczenia się użytkownika"""
        profile = {
            'learning_level': 'beginner',
            'preferred_detail_level': 'medium',
            'learning_progress': {},
            'preferences': {
                'topics': [],
                'question_style': 'direct',
                'response_length': 'medium'
            },
            'statistics': {
                'total_sessions': 0,
                'total_messages': 0,
                'avg_session_length': 0,
                'learning_streak': 0,
                'mastered_topics': []
            },
            'recent_activity': {
                'last_session': None,
                'recent_topics': [],
                'improvement_areas': []
            }
        }
        
        try:
            if os.path.exists(self.learning_data_file):
                with open(self.learning_data_file, 'r', encoding='utf-8') as f:
                    learning_data = json.load(f)
                
                # Szukaj danych dla tego użytkownika
                user_sessions = []
                if isinstance(learning_data, list):
                    for entry in learning_data:
                        if isinstance(entry, dict) and entry.get('user_id') == user_id:
                            user_sessions.append(entry)
                elif isinstance(learning_data, dict):
                    # Jeśli learning_data to słownik, sprawdź czy user_id jest kluczem
                    if user_id in learning_data:
                        user_data = learning_data[user_id]
                        if isinstance(user_data, dict):
                            user_sessions.append(user_data)
                
                if user_sessions:
                    # Analizuj dane uczenia się
                    profile['statistics']['total_sessions'] = len(user_sessions)
                    profile['statistics']['total_messages'] = sum(
                        session.get('total_messages', 0) for session in user_sessions
                    )
                    
                    # Znajdź najnowszą sesję
                    latest_session = user_sessions[0]
                    if len(user_sessions) > 1:
                        latest_session = max(user_sessions, key=lambda x: x.get('session_id', ''))
                    
                    # Wyciągnij preferencje z najnowszej sesji
                    if 'user_patterns' in latest_session:
                        patterns = latest_session['user_patterns']
                        profile['preferred_detail_level'] = patterns.get('preferred_detail_level', 'medium')
                        
                        # Analiza długości pytań
                        question_length = patterns.get('question_length', {})
                        preferred_range = question_length.get('preferred_range', 'medium')
                        profile['preferences']['question_style'] = preferred_range
                    
                    # Analiza progresji tematów
                    all_topics = []
                    for session in user_sessions:
                        topics = session.get('topic_progression', [])
                        if isinstance(topics, list):
                            all_topics.extend(topics)
                    
                    # Najczęstsze tematy
                    if all_topics:
                        from collections import Counter
                        topic_counts = Counter(all_topics)
                        profile['preferences']['topics'] = [topic for topic, count in topic_counts.most_common(5)]
                        profile['recent_activity']['recent_topics'] = list(topic_counts.keys())[-3:]
                    
                    # Określ poziom na podstawie liczby sesji i tematów
                    session_count = profile['statistics']['total_sessions']
                    if session_count > 10:
                        profile['learning_level'] = 'advanced'
                    elif session_count > 5:
                        profile['learning_level'] = 'intermediate'
                    else:
                        profile['learning_level'] = 'beginner'
        
        except Exception as e:
            print(f"⚠️  Błąd ładowania profilu uczenia dla {user_id}: {e}")
            # W przypadku błędu, zwróć domyślny profil
        
        return profile
    
    def delete_report(self, report_id: str) -> bool:
        """Usuwa raport o podanym ID"""
        try:
            report_file = os.path.join(self.reports_dir, f"{report_id}.json")
            
            if os.path.exists(report_file):
                os.remove(report_file)
                print(f"✅ Usunięto raport: {report_id}")
                return True
            else:
                print(f"⚠️  Raport {report_id} nie istnieje")
                return False
                
        except Exception as e:
            print(f"❌ Błąd usuwania raportu {report_id}: {e}")
            return False
