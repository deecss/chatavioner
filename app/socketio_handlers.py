#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Obsługa WebSocket dla aplikacji Aero-Chat
"""
import os
import json
import time
import asyncio
from datetime import datetime
from flask import session, request
from flask_socketio import emit, disconnect
from app.models import ChatSession
from utils.openai_rag import OpenAIRAG

def register_socketio_handlers(socketio):
    """Rejestruje handlery WebSocket"""
    
    @socketio.on('connect')
    def handle_connect():
        """Obsługuje połączenie WebSocket"""
        print(f"Użytkownik połączony: {session.get('session_id', 'nieznany')}")
        emit('connected', {'message': 'Połączono z serwerem'})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Obsługuje rozłączenie WebSocket"""
        print(f"Użytkownik rozłączony: {session.get('session_id', 'nieznany')}")
    
    @socketio.on('send_message')
    def handle_message(data):
        """Obsługuje wiadomość od użytkownika"""
        try:
            message = data.get('message', '').strip()
            message_id = data.get('message_id')  # Pobierz message_id z frontendu
            
            if not message:
                emit('error', {'message': 'Wiadomość nie może być pusta'})
                return
            
            session_id = session.get('session_id')
            if not session_id:
                emit('error', {'message': 'Błąd sesji'})
                return
            
            # Zapisz wiadomość użytkownika
            chat_session = ChatSession(session_id)
            chat_session.save_message(message, 'user')
            
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
            
            # Przygotuj kontekst
            history = chat_session.load_history()
            context = []
            for msg in history[-10:]:  # Ostatnie 10 wiadomości
                context.append({
                    'role': msg['role'],
                    'content': msg['content']
                })
            
            # Generuj odpowiedź ze strumieniem
            response_text = ""
            for chunk in rag.generate_response_stream(message, context, session_id):
                response_text += chunk
                emit('response_chunk', {'chunk': chunk, 'message_id': message_id})
            
            # Zapisz pełną odpowiedź
            chat_session.save_message(response_text, 'assistant')
            
            # Wygeneruj raport PDF
            pdf_path = rag.generate_pdf_report(response_text, session_id)
            
            # Zakończ generowanie
            emit('response_complete', {
                'message': 'Odpowiedź wygenerowana',
                'message_id': message_id,
                'full_response': response_text,
                'pdf_path': pdf_path
            })
            
        except Exception as e:
            print(f"Błąd podczas przetwarzania wiadomości: {str(e)}")
            emit('error', {'message': f'Wystąpił błąd: {str(e)}', 'message_id': message_id})
    
    @socketio.on('section_feedback')
    def handle_section_feedback(data):
        """Obsługuje feedback dla sekcji odpowiedzi"""
        try:
            session_id = session.get('session_id')
            if not session_id:
                emit('error', {'message': 'Błąd sesji'})
                return
            
            feedback_data = {
                'session_id': session_id,
                'feedback': data.get('feedback'),
                'section_type': data.get('section_type'),
                'section_text': data.get('section_text', '')[:200],  # Limit to 200 chars
                'timestamp': datetime.now().isoformat(),
                'type': 'section'
            }
            
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
    
    return socketio
