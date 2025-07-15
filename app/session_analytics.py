#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analityka sesji użytkowników dla panelu administratora
"""
import os
import json
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from typing import Dict, List, Optional
from app.models import ChatSession, User, UserSession

class SessionAnalytics:
    """Klasa do analizy sesji użytkowników"""
    
    def __init__(self):
        self.sessions_data = {}
        self.users_data = {}
        self.load_all_data()
    
    def load_all_data(self):
        """Ładuje wszystkie dane sesji i użytkowników"""
        self.sessions_data = {}
        self.users_data = {}
        
        # Ładuj sesje z katalogu history
        if os.path.exists('history'):
            for filename in os.listdir('history'):
                if filename.endswith('.json') and not filename.endswith('_context.json') and not filename.endswith('_full_context.json'):
                    session_id = filename.replace('.json', '')
                    try:
                        with open(f'history/{filename}', 'r', encoding='utf-8') as f:
                            history = json.load(f)
                        
                        self.sessions_data[session_id] = {
                            'history': history,
                            'session_id': session_id,
                            'user_id': self._extract_user_id(history),
                            'start_time': history[0]['timestamp'] if history else None,
                            'end_time': history[-1]['timestamp'] if history else None,
                            'message_count': len(history),
                            'user_messages': len([m for m in history if m['role'] == 'user']),
                            'assistant_messages': len([m for m in history if m['role'] == 'assistant']),
                            'duration': self._calculate_duration(history),
                            'feedback_count': self._count_feedback(session_id),
                            'topics': self._extract_topics(history),
                            'repeated_questions': self._find_repeated_questions(history),
                            'response_quality': self._analyze_response_quality(session_id),
                            'engagement_score': self._calculate_engagement_score(history, session_id)
                        }
                    except Exception as e:
                        print(f"Błąd ładowania sesji {session_id}: {e}")
                        continue
    
    def _extract_user_id(self, history):
        """Próbuje wyodrębnić user_id z historii"""
        for message in history:
            if 'user_id' in message:
                return message['user_id']
        return None
    
    def _calculate_duration(self, history):
        """Oblicza czas trwania sesji"""
        if len(history) < 2:
            return 0
        
        try:
            start = datetime.fromisoformat(history[0]['timestamp'])
            end = datetime.fromisoformat(history[-1]['timestamp'])
            return int((end - start).total_seconds())
        except:
            return 0
    
    def _count_feedback(self, session_id):
        """Liczy ilość feedbacków dla sesji"""
        feedback_count = 0
        
        # Nowy format - katalog sesji w feedback
        feedback_dir = f'feedback/{session_id}'
        if os.path.exists(feedback_dir):
            for filename in os.listdir(feedback_dir):
                if filename.endswith('.json'):
                    try:
                        with open(f'{feedback_dir}/{filename}', 'r', encoding='utf-8') as f:
                            feedback_data = json.load(f)
                        if isinstance(feedback_data, list):
                            feedback_count += len(feedback_data)
                        else:
                            feedback_count += 1
                    except:
                        pass
        
        # Stary format - plik w głównym katalogu feedback
        old_feedback_file = f'feedback/{session_id}.json'
        if os.path.exists(old_feedback_file):
            try:
                with open(old_feedback_file, 'r', encoding='utf-8') as f:
                    feedback_data = json.load(f)
                if isinstance(feedback_data, list):
                    feedback_count += len(feedback_data)
                else:
                    feedback_count += 1
            except:
                pass
        
        return feedback_count
    
    def _extract_topics(self, history):
        """Wyodrębnia główne tematy z historii"""
        aviation_keywords = {
            'siła nośna': 'Aerodynamika',
            'nawigacja': 'Nawigacja',
            'radar': 'Systemy',
            'meteorologia': 'Meteorologia',
            'bezpieczeństwo': 'Bezpieczeństwo',
            'silnik': 'Napęd',
            'skrzydło': 'Konstrukcja',
            'lotnisko': 'Operacje',
            'pilot': 'Pilotaż',
            'kontrola': 'Kontrola ruchu',
            'prawo': 'Przepisy',
            'turbulencja': 'Meteorologia',
            'avionika': 'Systemy',
            'komunikacja': 'Komunikacja'
        }
        
        topics = set()
        user_messages = [m for m in history if m['role'] == 'user']
        
        for message in user_messages:
            content = message['content'].lower()
            for keyword, topic in aviation_keywords.items():
                if keyword in content:
                    topics.add(topic)
        
        return list(topics)
    
    def _find_repeated_questions(self, history):
        """Znajduje powtarzające się pytania"""
        user_messages = [m for m in history if m['role'] == 'user']
        
        # Normalizuj pytania
        normalized_questions = []
        for msg in user_messages:
            normalized = msg['content'].lower().strip()
            # Usuń znaki interpunkcyjne
            import re
            normalized = re.sub(r'[^\w\s]', '', normalized)
            normalized_questions.append(normalized)
        
        # Znajdź powtórzenia
        question_counts = Counter(normalized_questions)
        repeated = {q: count for q, count in question_counts.items() if count > 1}
        
        return {
            'total_repeated': len(repeated),
            'repetition_rate': len(repeated) / len(set(normalized_questions)) if normalized_questions else 0,
            'repeated_questions': repeated
        }
    
    def _analyze_response_quality(self, session_id):
        """Analizuje jakość odpowiedzi na podstawie feedbacku"""
        feedback_dir = f'feedback/{session_id}'
        positive_feedback = 0
        negative_feedback = 0
        
        if os.path.exists(feedback_dir):
            for filename in os.listdir(feedback_dir):
                if filename.endswith('.json'):
                    try:
                        with open(f'{feedback_dir}/{filename}', 'r', encoding='utf-8') as f:
                            feedback_data = json.load(f)
                        
                        if isinstance(feedback_data, list):
                            for fb in feedback_data:
                                if fb.get('feedback_type') == 'positive':
                                    positive_feedback += 1
                                elif fb.get('feedback_type') == 'negative':
                                    negative_feedback += 1
                        else:
                            if feedback_data.get('feedback_type') == 'positive':
                                positive_feedback += 1
                            elif feedback_data.get('feedback_type') == 'negative':
                                negative_feedback += 1
                    except:
                        pass
        
        total_feedback = positive_feedback + negative_feedback
        quality_score = (positive_feedback / total_feedback * 100) if total_feedback > 0 else 0
        
        return {
            'positive_feedback': positive_feedback,
            'negative_feedback': negative_feedback,
            'total_feedback': total_feedback,
            'quality_score': quality_score
        }
    
    def _calculate_engagement_score(self, history, session_id):
        """Oblicza wskaźnik zaangażowania użytkownika"""
        if not history:
            return 0
        
        user_messages = [m for m in history if m['role'] == 'user']
        assistant_messages = [m for m in history if m['role'] == 'assistant']
        
        # Podstawowe metryki
        message_ratio = len(user_messages) / len(assistant_messages) if assistant_messages else 0
        avg_message_length = sum(len(m['content']) for m in user_messages) / len(user_messages) if user_messages else 0
        
        # Punkty za różne aktywności
        engagement_score = 0
        
        # Punkty za ilość wiadomości (maksymalnie 40 punktów)
        engagement_score += min(len(user_messages) * 2, 40)
        
        # Punkty za długość wiadomości (maksymalnie 20 punktów)
        engagement_score += min(avg_message_length / 10, 20)
        
        # Punkty za feedbacki (maksymalnie 25 punktów)
        feedback_count = self._count_feedback(session_id)
        engagement_score += min(feedback_count * 5, 25)
        
        # Punkty za różnorodność tematów (maksymalnie 15 punktów)
        topics_count = len(self._extract_topics(history))
        engagement_score += min(topics_count * 3, 15)
        
        return min(engagement_score, 100)  # Maksymalnie 100 punktów
    
    def get_user_statistics(self, user_id):
        """Pobiera statystyki dla konkretnego użytkownika"""
        user_sessions = [s for s in self.sessions_data.values() if s['user_id'] == user_id]
        
        if not user_sessions:
            return {
                'total_sessions': 0,
                'total_messages': 0,
                'total_time': 0,
                'avg_session_duration': 0,
                'total_feedback': 0,
                'avg_engagement': 0,
                'favorite_topics': [],
                'quality_score': 0,
                'productivity_score': 0
            }
        
        total_time = sum(s['duration'] for s in user_sessions)
        total_messages = sum(s['user_messages'] for s in user_sessions)
        total_feedback = sum(s['feedback_count'] for s in user_sessions)
        
        # Ulubione tematy
        all_topics = []
        for session in user_sessions:
            all_topics.extend(session['topics'])
        favorite_topics = Counter(all_topics).most_common(5)
        
        # Średnia jakość odpowiedzi
        quality_scores = [s['response_quality']['quality_score'] for s in user_sessions if s['response_quality']['total_feedback'] > 0]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        # Wskaźnik produktywności (pytania na minutę)
        productivity = (total_messages / (total_time / 60)) if total_time > 0 else 0
        
        return {
            'total_sessions': len(user_sessions),
            'total_messages': total_messages,
            'total_time': total_time,
            'avg_session_duration': total_time / len(user_sessions),
            'total_feedback': total_feedback,
            'avg_engagement': sum(s['engagement_score'] for s in user_sessions) / len(user_sessions),
            'favorite_topics': favorite_topics,
            'quality_score': avg_quality,
            'productivity_score': productivity,
            'recent_sessions': sorted(user_sessions, key=lambda x: x['end_time'], reverse=True)[:10]
        }
    
    def get_session_details(self, session_id):
        """Pobiera szczegółowe informacje o sesji"""
        if session_id not in self.sessions_data:
            return None
        
        session = self.sessions_data[session_id]
        
        # Dodatkowo załaduj kontekst pełny jeśli istnieje
        full_context_file = f'history/{session_id}_full_context.json'
        full_context = None
        if os.path.exists(full_context_file):
            try:
                with open(full_context_file, 'r', encoding='utf-8') as f:
                    full_context = json.load(f)
            except:
                pass
        
        # Załaduj szczegółowe feedbacki
        detailed_feedback = self._load_detailed_feedback(session_id)
        
        return {
            **session,
            'full_context': full_context,
            'detailed_feedback': detailed_feedback,
            'performance_metrics': self._calculate_performance_metrics(session)
        }
    
    def _load_detailed_feedback(self, session_id):
        """Ładuje szczegółowe feedbacki dla sesji"""
        feedback_list = []
        
        # Nowy format - katalog sesji
        feedback_dir = f'feedback/{session_id}'
        if os.path.exists(feedback_dir):
            for filename in os.listdir(feedback_dir):
                if filename.endswith('.json'):
                    try:
                        with open(f'{feedback_dir}/{filename}', 'r', encoding='utf-8') as f:
                            feedback_data = json.load(f)
                        
                        if isinstance(feedback_data, list):
                            feedback_list.extend(feedback_data)
                        else:
                            feedback_list.append(feedback_data)
                    except:
                        pass
        
        return feedback_list
    
    def _calculate_performance_metrics(self, session):
        """Oblicza metryki wydajności sesji"""
        history = session['history']
        
        # Średni czas odpowiedzi asystenta
        response_times = []
        for i in range(len(history) - 1):
            if history[i]['role'] == 'user' and history[i+1]['role'] == 'assistant':
                try:
                    user_time = datetime.fromisoformat(history[i]['timestamp'])
                    assistant_time = datetime.fromisoformat(history[i+1]['timestamp'])
                    response_time = (assistant_time - user_time).total_seconds()
                    response_times.append(response_time)
                except:
                    pass
        
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        # Aktywność w czasie (wiadomości na godzinę)
        duration_hours = session['duration'] / 3600 if session['duration'] > 0 else 0
        messages_per_hour = session['user_messages'] / duration_hours if duration_hours > 0 else 0
        
        return {
            'avg_response_time': avg_response_time,
            'messages_per_hour': messages_per_hour,
            'completion_rate': (session['assistant_messages'] / session['user_messages']) if session['user_messages'] > 0 else 0,
            'interaction_quality': session['engagement_score'] / 100
        }
    
    def get_global_statistics(self):
        """Pobiera globalne statystyki systemu"""
        if not self.sessions_data:
            return {}
        
        all_sessions = list(self.sessions_data.values())
        
        # Podstawowe statystyki
        total_sessions = len(all_sessions)
        total_messages = sum(s['message_count'] for s in all_sessions)
        total_time = sum(s['duration'] for s in all_sessions)
        total_feedback = sum(s['feedback_count'] for s in all_sessions)
        
        # Statystyki czasowe
        today = datetime.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        sessions_today = sessions_week = sessions_month = 0
        
        for session in all_sessions:
            if session['end_time']:
                try:
                    end_date = datetime.fromisoformat(session['end_time']).date()
                    if end_date == today:
                        sessions_today += 1
                    if end_date >= week_ago:
                        sessions_week += 1
                    if end_date >= month_ago:
                        sessions_month += 1
                except:
                    pass
        
        # Najpopularniejsze tematy
        all_topics = []
        for session in all_sessions:
            all_topics.extend(session['topics'])
        popular_topics = Counter(all_topics).most_common(10)
        
        # Średnie wskaźniki
        avg_engagement = sum(s['engagement_score'] for s in all_sessions) / len(all_sessions)
        avg_session_duration = total_time / len(all_sessions)
        
        return {
            'total_sessions': total_sessions,
            'total_messages': total_messages,
            'total_time': total_time,
            'total_feedback': total_feedback,
            'sessions_today': sessions_today,
            'sessions_week': sessions_week,
            'sessions_month': sessions_month,
            'avg_engagement': avg_engagement,
            'avg_session_duration': avg_session_duration,
            'popular_topics': popular_topics,
            'active_users': len(set(s['user_id'] for s in all_sessions if s['user_id'])),
            'feedback_rate': (total_feedback / total_sessions) if total_sessions > 0 else 0
        }
    
    def get_active_users_today(self):
        """Pobierz aktywnych użytkowników dzisiaj"""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            active_users = []
            
            for session in ChatSession.query.filter(ChatSession.started_at.startswith(today)).all():
                if session.user_id and session.user_id not in active_users:
                    active_users.append(session.user_id)
            
            return len(active_users)
        except Exception as e:
            logger.error(f"Błąd pobierania aktywnych użytkowników: {e}")
            return 0

    def get_top_performing_users(self):
        """Pobierz najlepszych użytkowników"""
        try:
            users = []
            for user in User.query.all():
                user_stats = self.get_user_basic_stats(user.id)
                if user_stats['total_sessions'] > 0:
                    users.append({
                        'username': user.username,
                        'engagement': user_stats['engagement_score'],
                        'sessions': user_stats['total_sessions']
                    })
            
            return sorted(users, key=lambda x: x['engagement'], reverse=True)[:5]
        except Exception as e:
            logger.error(f"Błąd pobierania top użytkowników: {e}")
            return []

    def calculate_system_health(self):
        """Oblicz zdrowie systemu"""
        try:
            # Podstawowe metryki zdrowia
            total_sessions = ChatSession.query.count()
            active_sessions = ChatSession.query.filter(
                ChatSession.started_at >= datetime.now() - timedelta(hours=1)
            ).count()
            
            # Wskaźnik zdrowia (0-100)
            health_score = min(100, (active_sessions / max(1, total_sessions)) * 1000)
            
            return {
                'score': health_score,
                'status': 'healthy' if health_score > 80 else 'warning' if health_score > 50 else 'critical',
                'active_sessions': active_sessions,
                'total_sessions': total_sessions
            }
        except Exception as e:
            logger.error(f"Błąd obliczania zdrowia systemu: {e}")
            return {'score': 0, 'status': 'unknown', 'active_sessions': 0, 'total_sessions': 0}

    def get_daily_statistics(self):
        """Pobierz dzienne statystyki"""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            
            # Sesje dzisiaj
            today_sessions = ChatSession.query.filter(
                ChatSession.started_at.startswith(today)
            ).all()
            
            # Oblicz podstawowe statystyki
            total_sessions = len(today_sessions)
            total_messages = sum(s.user_messages for s in today_sessions if s.user_messages)
            avg_duration = sum(s.duration for s in today_sessions if s.duration) / max(1, total_sessions)
            
            return {
                'date': today,
                'total_sessions': total_sessions,
                'total_messages': total_messages,
                'avg_duration': avg_duration,
                'active_users': self.get_active_users_today()
            }
        except Exception as e:
            logger.error(f"Błąd pobierania dziennych statystyk: {e}")
            return {'date': datetime.now().strftime('%Y-%m-%d'), 'total_sessions': 0, 'total_messages': 0, 'avg_duration': 0, 'active_users': 0}

    def get_top_users_detailed(self):
        """Pobierz szczegółowe dane top użytkowników"""
        try:
            users_data = []
            
            for user in User.query.all():
                user_stats = self.get_user_basic_stats(user.id)
                if user_stats['total_sessions'] > 0:
                    users_data.append({
                        'id': user.id,
                        'username': user.username,
                        'total_sessions': user_stats['total_sessions'],
                        'total_messages': user_stats['total_messages'],
                        'avg_engagement': user_stats['engagement_score'],
                        'avg_session_duration': user_stats['avg_session_duration'],
                        'feedback_count': user_stats.get('feedback_count', 0),
                        'productivity_score': user_stats.get('productivity_score', 0),
                        'overall_rating': user_stats.get('overall_rating', 0)
                    })
            
            return sorted(users_data, key=lambda x: x['avg_engagement'], reverse=True)
        except Exception as e:
            logger.error(f"Błąd pobierania szczegółowych danych użytkowników: {e}")
            return []

    def analyze_topics_distribution(self):
        """Analizuj rozkład tematów"""
        try:
            topics = {}
            
            # Pobierz wszystkie sesje z ostatnich 30 dni
            cutoff_date = datetime.now() - timedelta(days=30)
            recent_sessions = ChatSession.query.filter(
                ChatSession.started_at >= cutoff_date
            ).all()
            
            for session in recent_sessions:
                session_topics = self.extract_topics_from_session(session)
                for topic in session_topics:
                    topics[topic] = topics.get(topic, 0) + 1
            
            # Sortuj i formatuj
            sorted_topics = sorted(topics.items(), key=lambda x: x[1], reverse=True)[:10]
            total = sum(topics.values())
            
            return [{
                'name': topic,
                'count': count,
                'percentage': (count / total * 100) if total > 0 else 0
            } for topic, count in sorted_topics]
        except Exception as e:
            logger.error(f"Błąd analizy tematów: {e}")
            return []

    def extract_topics_from_session(self, session):
        """Wyodrębnij tematy z sesji"""
        try:
            # Podstawowa analiza tematów na podstawie wiadomości
            topics = []
            
            # Pobierz historię z pliku
            history_file = f"/home/dee/chatavioner/history/{session.session_id}.json"
            if os.path.exists(history_file):
                with open(history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
                    
                # Analizuj wiadomości użytkownika
                for message in history:
                    if message.get('role') == 'user':
                        content = message.get('content', '').lower()
                        
                        # Podstawowe słowa kluczowe
                        if any(word in content for word in ['lot', 'samolot', 'pilot']):
                            topics.append('Lotnictwo')
                        if any(word in content for word in ['prawo', 'przepis', 'regulacja']):
                            topics.append('Prawo lotnicze')
                        if any(word in content for word in ['pogoda', 'wiatr', 'chmury']):
                            topics.append('Meteorologia')
                        if any(word in content for word in ['silnik', 'mechanika', 'awaria']):
                            topics.append('Technika')
                        if any(word in content for word in ['licencja', 'egzamin', 'szkolenie']):
                            topics.append('Szkolenie')
            
            return list(set(topics))  # Usuń duplikaty
        except Exception as e:
            logger.error(f"Błąd wyodrębniania tematów: {e}")
            return []

    def get_user_basic_stats(self, user_id):
        """Pobierz podstawowe statystyki użytkownika"""
        try:
            user_sessions = ChatSession.query.filter_by(user_id=user_id).all()
            
            if not user_sessions:
                return {
                    'total_sessions': 0,
                    'total_messages': 0,
                    'avg_session_duration': 0,
                    'engagement_score': 0,
                    'feedback_count': 0,
                    'productivity_score': 0,
                    'overall_rating': 0
                }
            
            total_sessions = len(user_sessions)
            total_messages = sum(s.user_messages for s in user_sessions if s.user_messages)
            total_duration = sum(s.duration for s in user_sessions if s.duration)
            
            # Oblicz engagement
            engagement_scores = []
            for session in user_sessions:
                if session.engagement_score:
                    engagement_scores.append(session.engagement_score)
            
            avg_engagement = sum(engagement_scores) / len(engagement_scores) if engagement_scores else 0
            
            return {
                'total_sessions': total_sessions,
                'total_messages': total_messages,
                'avg_session_duration': total_duration / total_sessions if total_sessions > 0 else 0,
                'engagement_score': avg_engagement,
                'feedback_count': sum(s.feedback_count for s in user_sessions if s.feedback_count),
                'productivity_score': total_messages / total_sessions if total_sessions > 0 else 0,
                'overall_rating': 4.0  # Domyślna ocena
            }
        except Exception as e:
            logger.error(f"Błąd pobierania podstawowych statystyk użytkownika {user_id}: {e}")
            return {'total_sessions': 0, 'total_messages': 0, 'avg_session_duration': 0, 'engagement_score': 0, 'feedback_count': 0, 'productivity_score': 0, 'overall_rating': 0}

    def get_quick_stats(self):
        """Pobierz szybkie statystyki dla API"""
        try:
            now = datetime.now()
            today = now.strftime('%Y-%m-%d')
            
            # Aktywne sesje (ostatnia godzina)
            active_sessions = ChatSession.query.filter(
                ChatSession.started_at >= now - timedelta(hours=1)
            ).count()
            
            # Sesje dzisiaj
            today_sessions = ChatSession.query.filter(
                ChatSession.started_at.startswith(today)
            ).count()
            
            return {
                'active_sessions': active_sessions,
                'today_sessions': today_sessions,
                'system_status': 'OK'
            }
        except Exception as e:
            logger.error(f"Błąd pobierania szybkich statystyk: {e}")
            return {'active_sessions': 0, 'today_sessions': 0, 'system_status': 'ERROR'}

    def get_users_current_status(self):
        """Pobierz aktualny status użytkowników"""
        try:
            users_status = []
            now = datetime.now()
            
            for user in User.query.all():
                # Sprawdź ostatnią aktywność
                last_session = ChatSession.query.filter_by(user_id=user.id).order_by(ChatSession.started_at.desc()).first()
                
                is_active = False
                if last_session:
                    last_activity = datetime.fromisoformat(last_session.started_at.replace('Z', '+00:00'))
                    is_active = (now - last_activity).total_seconds() < 3600  # Aktywny jeśli ostatnia sesja w ciągu godziny
                
                users_status.append({
                    'id': user.id,
                    'is_active': is_active
                })
            
            return users_status
        except Exception as e:
            logger.error(f"Błąd pobierania statusu użytkowników: {e}")
            return []

# Dodaj import os na początku pliku
import os
