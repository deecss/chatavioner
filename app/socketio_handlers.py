#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Obsługa WebSocket dla aplikacji Aero-Chat
"""
import os
import json
import time
import asyncio
import markdown
from datetime import datetime
from flask import session, request
from flask_socketio import emit, disconnect
from flask_login import current_user
from app.models import ChatSession
from utils.openai_rag import OpenAIRAG
from utils.learning_system import LearningSystem

def markdown_to_html(text):
    """Konwertuje markdown do HTML"""
    if not text:
        return ""
    
    # Konfiguracja markdown z rozszerzeniami
    md = markdown.Markdown(extensions=[
        'extra',     # Dodatkowe funkcje markdown
        'codehilite', # Podświetlanie kodu
        'toc'        # Spis treści
    ])
    
    return md.convert(text)

def register_socketio_handlers(socketio):
    """Rejestruje handlery WebSocket"""
    
    @socketio.on('connect')
    def handle_connect():
        """Obsługuje połączenie WebSocket"""
        if not current_user.is_authenticated:
            print("⚠️  Nieautoryzowane połączenie WebSocket")
            disconnect()
            return
        
        current_session_id = session.get('current_session_id', 'brak')
        print(f"🔌 Użytkownik {current_user.username} połączony: {current_session_id}")
        print(f"🔗 Socket SID: {request.sid}")
        emit('connected', {
            'message': 'Połączono z serwerem', 
            'session_id': current_session_id,
            'user_id': current_user.id,
            'username': current_user.username
        })
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Obsługuje rozłączenie WebSocket"""
        if current_user.is_authenticated:
            print(f"Użytkownik {current_user.username} rozłączony")
        else:
            print("Nieautoryzowany użytkownik rozłączony")
    
    @socketio.on('send_message')
    def handle_message(data):
        """Obsługuje wiadomość od użytkownika"""
        try:
            if not current_user.is_authenticated:
                emit('error', {'message': 'Musisz być zalogowany'})
                return
            
            print(f"🔔 Otrzymano wiadomość od {current_user.username}: {data}")
            
            message = data.get('message', '').strip()
            message_id = data.get('message_id')  # Pobierz message_id z frontendu
            
            print(f"💬 Message: {message}")
            print(f"🆔 Message ID: {message_id}")
            
            if not message:
                print("❌ Pusta wiadomość")
                emit('error', {'message': 'Wiadomość nie może być pusta'})
                return
            
            session_id = session.get('current_session_id')
            print(f"🔑 Current Session ID: {session_id}")
            
            if not session_id:
                print("❌ Brak current_session_id")
                emit('error', {'message': 'Brak aktywnej sesji. Utwórz nową sesję.'})
                return
            
            # Utwórz sesję czatu z poprawnym user_id
            chat_session = ChatSession(session_id, current_user.id)
            
            # Sprawdź czy to pierwsza wiadomość w sesji
            history = chat_session.load_history()
            is_first_message = len([msg for msg in history if msg['role'] == 'user' and msg.get('user_id') == current_user.id]) == 0
            
            # Zapisz wiadomość użytkownika
            chat_session.save_message(message, 'user')
            
            # Jeśli to pierwsza wiadomość, zaktualizuj tytuł sesji
            if is_first_message:
                # Skróć wiadomość do maksymalnie 50 znaków dla tytułu
                title = message[:50] + "..." if len(message) > 50 else message
                print(f"🏷️ Aktualizuję tytuł sesji na: {title}")
                
                # Aktualizuj tytuł sesji
                from app.models import UserSession
                UserSession.update_session_title(current_user.id, session_id, title)
                
                # Powiadom frontend o zmianie tytułu
                emit('session_title_updated', {
                    'session_id': session_id,
                    'new_title': title
                })
            
            # Wyślij potwierdzenie
            emit('message_received', {
                'message': message,
                'message_id': message_id,
                'timestamp': chat_session.load_history()[-1]['timestamp']
            })
            
            # Rozpocznij generowanie odpowiedzi
            emit('generating_start', {'message': 'Generuję odpowiedź...', 'message_id': message_id})
            
            # Inicjalizuj OpenAI RAG
            rag = OpenAIRAG()
            
            # Przygotuj kontekst - PEŁNA HISTORIA ROZMOWY TYLKO DLA TEJ SESJI I TEGO UŻYTKOWNIKA
            history = chat_session.load_history()
            context = []
            
            print(f"🗂️ Ładuję historię rozmowy dla sesji {session_id}: {len(history)} wiadomości")
            
            # Przekaż całą historię rozmowy do asystenta - filtruj tylko dla tego user_id
            for msg in history:
                if msg.get('user_id') == current_user.id:  # Tylko wiadomości tego użytkownika
                    context.append({
                        'role': msg['role'],
                        'content': msg['content']
                    })
            
            print(f"📚 Kontekst przygotowany dla user {current_user.id}: {len(context)} wiadomości")
            print(f"🔍 Ostatnie 3 wiadomości: {[m['role'] + ': ' + m['content'][:50] + '...' for m in context[-3:]]}")
            
            print(f"📚 Kontekst przygotowany: {len(context)} wiadomości")
            print(f"🔍 Ostatnie 3 wiadomości: {[m['role'] + ': ' + m['content'][:50] + '...' for m in context[-3:]]}")
            
            # Zapisz kontekst do pliku dla debugowania
            rag.save_conversation_context(session_id, context, message)
            
            # Generuj odpowiedź ze strumieniem - ASYSTENT OTRZYMUJE PEŁNY KONTEKST
            response_text = ""
            documents_used = 0
            
            for chunk in rag.generate_response_stream(message, context, session_id):
                response_text += chunk
                # Wyślij surowy chunk (markdown)
                emit('response_chunk', {'chunk': chunk, 'message_id': message_id})
                
                # Sprawdź czy użyto dokumentów (można to zrobić w rag.py)
                if hasattr(rag, 'last_documents_used'):
                    documents_used = rag.last_documents_used
            
            # Wyślij informacje o użytych dokumentach
            emit('documents_used', {'count': documents_used})
            
            # Zapisz pełną odpowiedź
            chat_session.save_message(response_text, 'assistant')
            
            # Wygeneruj raport PDF
            pdf_path = rag.generate_pdf_report(response_text, session_id)
            
            # Zakończ generowanie
            emit('response_complete', {
                'message': 'Odpowiedź wygenerowana',
                'message_id': message_id,
                'full_response': markdown_to_html(response_text),  # Konwertuj markdown do HTML
                'documents_used': rag.last_documents_used,
                'pdf_path': pdf_path
            })
            
        except Exception as e:
            print(f"Błąd podczas przetwarzania wiadomości: {str(e)}")
            emit('error', {'message': f'Wystąpił błąd: {str(e)}', 'message_id': message_id})
    
    @socketio.on('section_feedback')
    def handle_section_feedback(data):
        """Obsługuje feedback dla sekcji odpowiedzi z systemem uczenia się"""
        try:
            if not current_user.is_authenticated:
                emit('error', {'message': 'Musisz być zalogowany'})
                return
            
            session_id = session.get('current_session_id')
            if not session_id:
                emit('error', {'message': 'Brak aktywnej sesji'})
                return
            
            feedback_data = {
                'session_id': session_id,
                'user_id': current_user.id,
                'feedback': data.get('feedback'),
                'section_type': data.get('section_type'),
                'section_text': data.get('section_text', '')[:200],  # Limit to 200 chars
                'timestamp': datetime.now().isoformat(),
                'type': 'section'
            }
            
            # SYSTEM UCZENIA SIĘ - Aktualizuj preferencje na podstawie feedbacku
            try:
                learning_system = LearningSystem()
                learning_system.update_preferences_from_feedback(session_id, feedback_data)
                print(f"🧠 Zaktualizowano preferencje uczenia dla sesji {session_id}")
            except Exception as e:
                print(f"⚠️ Błąd aktualizacji systemu uczenia się: {e}")
            
            # Zapisz feedback do pliku
            feedback_dir = f'feedback/{session_id}'
            os.makedirs(feedback_dir, exist_ok=True)
            
            feedback_file = os.path.join(feedback_dir, 'section_feedback.json')
            
            # Wczytaj istniejący feedback lub utwórz nowy
            if os.path.exists(feedback_file):
                with open(feedback_file, 'r', encoding='utf-8') as f:
                    all_feedback = json.load(f)
            else:
                all_feedback = []
            
            all_feedback.append(feedback_data)
            
            # Zapisz feedback
            with open(feedback_file, 'w', encoding='utf-8') as f:
                json.dump(all_feedback, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Feedback sekcji zapisany: {data.get('feedback')} dla {data.get('section_type')}")
            
        except Exception as e:
            print(f"Błąd podczas zapisywania feedback sekcji: {str(e)}")
            emit('error', {'message': f'Błąd zapisywania feedback: {str(e)}'})
    
    @socketio.on('overall_feedback')
    def handle_overall_feedback(data):
        """Obsługuje feedback dla całej odpowiedzi"""
        try:
            session_id = session.get('session_id')
            if not session_id:
                emit('error', {'message': 'Błąd sesji'})
                return
            
            feedback_data = {
                'session_id': session_id,
                'feedback': data.get('feedback'),
                'full_response': data.get('full_response', '')[:1000],  # Limit to 1000 chars
                'timestamp': datetime.now().isoformat(),
                'type': 'overall'
            }
            
            # SYSTEM UCZENIA SIĘ - Aktualizuj preferencje na podstawie ogólnego feedbacku
            learning_system = LearningSystem()
            learning_system.update_preferences_from_feedback(session_id, feedback_data)
            print(f"🧠 Zaktualizowano preferencje uczenia dla sesji {session_id} (overall feedback)")
            
            # Zapisz feedback do pliku
            feedback_dir = f'feedback/{session_id}'
            os.makedirs(feedback_dir, exist_ok=True)
            
            feedback_file = os.path.join(feedback_dir, 'overall_feedback.json')
            
            # Wczytaj istniejący feedback lub utwórz nowy
            if os.path.exists(feedback_file):
                with open(feedback_file, 'r', encoding='utf-8') as f:
                    all_feedback = json.load(f)
            else:
                all_feedback = []
            
            all_feedback.append(feedback_data)
            
            # Zapisz feedback
            with open(feedback_file, 'w', encoding='utf-8') as f:
                json.dump(all_feedback, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Feedback ogólny zapisany: {data.get('feedback')}")
            
        except Exception as e:
            print(f"Błąd podczas zapisywania feedback ogólnego: {str(e)}")
            emit('error', {'message': f'Błąd zapisywania feedback: {str(e)}'})
    
    @socketio.on('detailed_feedback')
    def handle_detailed_feedback(data):
        """Obsługuje szczegółowy feedback z opisem"""
        try:
            session_id = session.get('session_id')
            if not session_id:
                emit('error', {'message': 'Błąd sesji'})
                return
            
            feedback_data = {
                'session_id': session_id,
                'section_id': data.get('section_id'),
                'section_type': data.get('section_type'),
                'feedback_type': data.get('feedback_type'),
                'content': data.get('content', '')[:500],  # Limit treści
                'description': data.get('description', '')[:1000],  # Limit opisu
                'timestamp': data.get('timestamp'),
                'type': 'detailed'
            }
            
            # SYSTEM UCZENIA SIĘ - Aktualizuj preferencje na podstawie szczegółowego feedbacku
            learning_system = LearningSystem()
            learning_system.update_preferences_from_feedback(session_id, feedback_data)
            print(f"🧠 Zaktualizowano preferencje uczenia dla sesji {session_id} (detailed feedback)")
            
            # Zapisz feedback do pliku
            feedback_dir = f'feedback/{session_id}'
            os.makedirs(feedback_dir, exist_ok=True)
            
            feedback_file = os.path.join(feedback_dir, 'detailed_feedback.json')
            
            # Wczytaj istniejący feedback lub utwórz nowy
            if os.path.exists(feedback_file):
                with open(feedback_file, 'r', encoding='utf-8') as f:
                    all_feedback = json.load(f)
            else:
                all_feedback = []
            
            all_feedback.append(feedback_data)
            
            # Zapisz feedback
            with open(feedback_file, 'w', encoding='utf-8') as f:
                json.dump(all_feedback, f, ensure_ascii=False, indent=2)
            
            # Dodaj feedback do uczenia asystenta AI
            try:
                rag = OpenAIRAG()
                rag.add_feedback_to_training(feedback_data)
            except Exception as e:
                print(f"Błąd podczas dodawania feedback do treningu: {str(e)}")
            
            print(f"✅ Szczegółowy feedback zapisany: {feedback_data['feedback_type']} dla {feedback_data['section_type']}")
            emit('feedback_saved', {'message': 'Feedback zapisany i dodany do treningu!'})
            
        except Exception as e:
            print(f"Błąd podczas zapisywania szczegółowego feedback: {str(e)}")
            emit('error', {'message': f'Błąd zapisywania feedback: {str(e)}'})
    
    @socketio.on('request_pdf')
    def handle_pdf_request(data):
        """Obsługuje żądanie wygenerowania PDF"""
        try:
            session_id = session.get('session_id')
            if not session_id:
                emit('error', {'message': 'Błąd sesji'})
                return
            
            message_id = data.get('message_id')
            content = data.get('content', '')
            
            if not content:
                emit('error', {'message': 'Brak treści do wygenerowania PDF'})
                return
            
            # Wygeneruj PDF
            rag = OpenAIRAG()
            pdf_path = rag.generate_pdf_report(content, session_id, message_id)
            
            emit('pdf_generated', {
                'message': 'PDF wygenerowany pomyślnie',
                'pdf_path': pdf_path,
                'message_id': message_id
            })
            
        except Exception as e:
            print(f"Błąd podczas generowania PDF: {str(e)}")
            emit('error', {'message': f'Błąd generowania PDF: {str(e)}'})
    
    @socketio.on('submit_feedback')
    def handle_feedback(data):
        """Obsługuje feedback od użytkownika"""
        try:
            session_id = session.get('session_id')
            if not session_id:
                emit('error', {'message': 'Błąd sesji'})
                return
            
            feedback_type = data.get('type')  # 'positive' or 'negative'
            section_id = data.get('section')  # 'overall' or section index
            timestamp = data.get('timestamp')
            
            # Zapisz feedback do pliku
            feedback_data = {
                'session_id': session_id,
                'type': feedback_type,
                'section': section_id,
                'timestamp': timestamp,
                'user_agent': request.headers.get('User-Agent', ''),
                'ip_address': request.remote_addr
            }
            
            # Utwórz katalog dla feedbacku
            feedback_dir = f'feedback/{session_id}'
            os.makedirs(feedback_dir, exist_ok=True)
            
            # Zapisz feedback do pliku JSON
            feedback_file = os.path.join(feedback_dir, f'feedback_{int(time.time())}.json')
            with open(feedback_file, 'w', encoding='utf-8') as f:
                json.dump(feedback_data, f, ensure_ascii=False, indent=2)
            
            print(f"📝 Otrzymano feedback: {feedback_type} dla sekcji {section_id} w sesji {session_id}")
            emit('feedback_received', {'message': 'Dziękuję za opinię!'})
            
        except Exception as e:
            print(f"Błąd podczas zapisywania feedbacku: {str(e)}")
            emit('error', {'message': f'Błąd zapisywania feedbacku: {str(e)}'})
    
    @socketio.on('feedback')
    def handle_feedback(data):
        """Obsługuje feedback z komentarzem użytkownika"""
        try:
            print(f"💬 Otrzymano feedback: {data}")
            
            session_id = session.get('session_id')
            if not session_id:
                emit('error', {'message': 'Błąd sesji'})
                return
            
            # Przygotuj dane feedbacku
            feedback_data = {
                'session_id': session_id,
                'message_id': data.get('message_id'),
                'section_id': data.get('section_id'),
                'feedback_type': data.get('feedback_type'),
                'section_type': data.get('section_type'),
                'content': data.get('content', '')[:500],  # Limit do 500 znaków
                'description': data.get('description', ''),  # Komentarz użytkownika
                'timestamp': data.get('timestamp', datetime.now().isoformat()),
                'type': 'section_with_comment'
            }
            
            # Zapisz feedback do pliku
            feedback_dir = f'feedback/{session_id}'
            os.makedirs(feedback_dir, exist_ok=True)
            
            feedback_file = os.path.join(feedback_dir, 'feedback.json')
            
            # Wczytaj istniejący feedback lub utwórz nowy
            if os.path.exists(feedback_file):
                with open(feedback_file, 'r', encoding='utf-8') as f:
                    all_feedback = json.load(f)
            else:
                all_feedback = []
            
            all_feedback.append(feedback_data)
            
            # Zapisz feedback
            with open(feedback_file, 'w', encoding='utf-8') as f:
                json.dump(all_feedback, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Feedback zapisany: {data.get('feedback_type')} - {data.get('description')}")
            
            # Poinformuj o zapisaniu
            emit('feedback_saved', {
                'message': 'Feedback zapisany!',
                'type': data.get('feedback_type')
            })
            
        except Exception as e:
            print(f"❌ Błąd podczas zapisywania feedback: {str(e)}")
            import traceback
            traceback.print_exc()
            emit('error', {'message': f'Błąd zapisywania feedback: {str(e)}'})

    return socketio
