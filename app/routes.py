#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Główne routes aplikacji Aero-Chat
"""
import os
import uuid
import json
from datetime import datetime
from flask import Blueprint, render_template, request, session, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user, login_user, logout_user
from app.models import ChatSession, UploadIndex, User, UserSession

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Strona główna - przekierowanie do logowania lub czatu"""
    if current_user.is_authenticated:
        return redirect(url_for('main.chat'))
    return redirect(url_for('main.login'))

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Strona logowania użytkowników"""
    if current_user.is_authenticated:
        return redirect(url_for('main.chat'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.authenticate(username, password)
        if user:
            login_user(user)
            return redirect(url_for('main.chat'))
        else:
            flash('Nieprawidłowe dane logowania', 'error')
    
    return render_template('login.html')

@main_bp.route('/logout')
@login_required
def logout():
    """Wylogowanie użytkownika"""
    logout_user()
    session.clear()
    return redirect(url_for('main.login'))

@main_bp.route('/chat')
@login_required
def chat():
    """Główny interfejs czatu"""
    user_sessions = UserSession.get_user_sessions(current_user.id)
    return render_template('chat.html', 
                         user_id=current_user.id,
                         username=current_user.username,
                         sessions=user_sessions)

@main_bp.route('/api/sessions', methods=['GET'])
@login_required
def get_user_sessions():
    """Pobiera sesje użytkownika"""
    try:
        sessions = UserSession.get_user_sessions(current_user.id)
        return jsonify(sessions)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main_bp.route('/api/sessions', methods=['POST'])
@login_required
def create_session():
    """Tworzy nową sesję czatu"""
    try:
        data = request.get_json()
        title = data.get('title', f"Nowa sesja {datetime.now().strftime('%d.%m %H:%M')}")
        
        user_session = UserSession(current_user.id, title=title)
        user_session.save()
        
        return jsonify({
            'session_id': user_session.session_id,
            'title': user_session.title,
            'created_at': user_session.created_at,
            'updated_at': user_session.updated_at
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main_bp.route('/api/sessions/<session_id>', methods=['DELETE'])
@login_required
def delete_session(session_id):
    """Usuwa sesję użytkownika"""
    try:
        success = UserSession.delete_session(current_user.id, session_id)
        if success:
            return jsonify({'message': 'Sesja usunięta pomyślnie'})
        else:
            return jsonify({'error': 'Nie udało się usunąć sesji'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main_bp.route('/api/sessions/<session_id>/title', methods=['PUT'])
@login_required
def update_session_title(session_id):
    """Aktualizuje tytuł sesji"""
    try:
        data = request.get_json()
        title = data.get('title')
        
        if not title:
            return jsonify({'error': 'Brak tytułu'}), 400
        
        success = UserSession.update_session_title(current_user.id, session_id, title)
        if success:
            return jsonify({'message': 'Tytuł sesji zaktualizowany pomyślnie'})
        else:
            return jsonify({'error': 'Nie udało się zaktualizować tytułu sesji'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main_bp.route('/api/sessions/<session_id>/history')
@login_required
def get_session_history(session_id):
    """Pobiera historię konkretnej sesji"""
    try:
        chat_session = ChatSession(session_id, current_user.id)
        history = chat_session.load_history()
        
        # Sprawdź czy sesja należy do użytkownika
        user_sessions = UserSession.get_user_sessions(current_user.id)
        session_ids = [s['session_id'] for s in user_sessions]
        
        if session_id not in session_ids and history:
            # Sprawdź czy w historii są wiadomości tego użytkownika
            user_messages = [msg for msg in history if msg.get('user_id') == current_user.id]
            if not user_messages:
                return jsonify({'error': 'Brak dostępu do tej sesji'}), 403
        
        return jsonify(history)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main_bp.route('/api/current_session')
@login_required
def get_current_session():
    """Pobiera aktualną sesję z session storage"""
    session_id = session.get('current_session_id')
    if session_id:
        return jsonify({'session_id': session_id})
    return jsonify({'session_id': None})

@main_bp.route('/api/current_session', methods=['POST'])
@login_required
def set_current_session():
    """Ustawia aktualną sesję w session storage"""
    data = request.get_json()
    session_id = data.get('session_id')
    
    if session_id:
        session['current_session_id'] = session_id
        return jsonify({'message': 'Sesja ustawiona pomyślnie'})
    
    return jsonify({'error': 'Brak session_id'}), 400

@main_bp.route('/avioner')
@login_required
def avioner_chat():
    """Nowy widok czatu Avioner AI Bot"""
    user_sessions = UserSession.get_user_sessions(current_user.id)
    return render_template('avioner_chat.html', 
                         user_id=current_user.id,
                         username=current_user.username,
                         sessions=user_sessions)

@main_bp.route('/api/upload', methods=['POST'])
@login_required
def upload_file():
    """Endpoint do przesyłania plików PDF"""
    if 'file' not in request.files:
        return jsonify({'error': 'Brak pliku'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Nie wybrano pliku'}), 400
    
    if file and file.filename.lower().endswith('.pdf'):
        # Zapisz plik
        upload_folder = 'uploads'
        os.makedirs(upload_folder, exist_ok=True)
        
        # Generuj unikalną nazwę pliku
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        filename = f"{timestamp}_{file.filename}"
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)
        
        # Dodaj do indeksu
        upload_index = UploadIndex()
        upload_index.add_file(filename, {'size': os.path.getsize(filepath)})
        
        return jsonify({
            'message': 'Plik przesłany pomyślnie',
            'filename': filename
        })
    
    return jsonify({'error': 'Niepoprawny format pliku. Akceptowane są tylko pliki PDF.'}), 400

@main_bp.route('/api/feedback', methods=['POST'])
@login_required
def submit_feedback():
    """Endpoint do przesyłania feedbacku"""
    data = request.get_json()
    
    if not data or 'type' not in data:
        return jsonify({'error': 'Brakuje danych feedbacku'}), 400
    
    session_id = session.get('current_session_id')
    if not session_id:
        return jsonify({'error': 'Brak aktywnej sesji'}), 400
    
    chat_session = ChatSession(session_id, current_user.id)
    chat_session.save_feedback(data)
    
    return jsonify({'message': 'Feedback zapisany pomyślnie'})

@main_bp.route('/api/history')
def get_history():
    """Endpoint do pobierania historii czatu"""
    session_id = session.get('session_id')
    if not session_id:
        return jsonify([])
    
    chat_session = ChatSession(session_id)
    history = chat_session.load_history()
    
    return jsonify(history)

@main_bp.route('/api/clear_history', methods=['POST'])
@login_required
def clear_history():
    """Endpoint do czyszczenia historii aktualnej sesji"""
    session_id = session.get('current_session_id')
    if not session_id:
        return jsonify({'error': 'Brak aktywnej sesji'}), 400
    
    history_file = f'history/{session_id}.json'
    if os.path.exists(history_file):
        os.remove(history_file)
    
    return jsonify({'message': 'Historia wyczyszczona pomyślnie'})

@main_bp.route('/api/files')
@login_required
def get_files():
    """Endpoint do pobierania listy załadowanych plików"""
    try:
        upload_index = UploadIndex()
        files = upload_index.get_files_by_status()
        
        # Przekształć dane do formatu wymaganego przez frontend
        file_list = []
        for filename, metadata in files.items():
            # Usuń timestamp z nazwy pliku dla wyświetlenia
            display_name = filename
            if '_' in filename:
                parts = filename.split('_', 1)
                if len(parts) > 1 and parts[0].isdigit():
                    display_name = parts[1]
            
            file_list.append({
                'name': display_name,
                'filename': filename,
                'size': metadata.get('size', 0),
                'upload_date': metadata.get('upload_date', '')
            })
        
        # Sortuj po dacie dodania (najnowsze pierwsze)
        file_list.sort(key=lambda x: x.get('upload_date', ''), reverse=True)
        
        return jsonify(file_list)
    
    except Exception as e:
        return jsonify({'error': f'Błąd pobierania listy plików: {str(e)}'}), 500

@main_bp.route('/api/documents')
@login_required
def get_documents():
    """Endpoint do pobierania listy dokumentów dla nowego widoku"""
    try:
        upload_index = UploadIndex()
        files = upload_index.get_files_by_status()
        
        # Formatuj do prostszego widoku
        documents = []
        for filename, metadata in files.items():
            # Usuń timestamp z nazwy
            display_name = filename
            if '_' in filename:
                parts = filename.split('_', 1)
                if len(parts) > 1 and parts[0].isdigit():
                    display_name = parts[1]
            
            # Formatuj rozmiar pliku
            size = metadata.get('size', 0)
            if size > 1024 * 1024:
                size_str = f"{size / (1024 * 1024):.1f} MB"
            elif size > 1024:
                size_str = f"{size / 1024:.1f} KB"
            else:
                size_str = f"{size} B"
            
            documents.append({
                'name': display_name,
                'size': size_str,
                'filename': filename
            })
        
        return jsonify(documents)
    
    except Exception as e:
        return jsonify({'error': f'Błąd pobierania dokumentów: {str(e)}'}), 500

@main_bp.route('/api/learning_status')
@login_required
def get_learning_status():
    """Endpoint do pobierania statusu systemu uczenia się"""
    try:
        from utils.learning_system import LearningSystem
        
        learning_system = LearningSystem()
        session_id = session.get('current_session_id')
        
        if not session_id:
            return jsonify({'error': 'Brak aktywnej sesji'}), 400
        
        # Pobierz preferencje użytkownika
        preferences = learning_system.get_user_preferences(session_id)
        
        # Pobierz historię uczenia się
        learning_data = []
        if os.path.exists(learning_system.learning_data_file):
            try:
                with open(learning_system.learning_data_file, 'r', encoding='utf-8') as f:
                    all_data = json.load(f)
                    # Znajdź dane dla aktualnej sesji
                    learning_data = [data for data in all_data if data.get('session_id') == session_id]
            except Exception as e:
                print(f"Błąd wczytywania danych uczenia: {e}")
        
        status = {
            'session_id': session_id,
            'preferences': preferences,
            'learning_data_count': len(learning_data),
            'has_learning_data': len(learning_data) > 0,
            'last_analysis': learning_data[-1].get('timestamp') if learning_data else None,
            'system_active': True
        }
        
        return jsonify(status)
        
    except Exception as e:
        return jsonify({'error': f'Błąd pobierania statusu uczenia się: {str(e)}'}), 500

@main_bp.route('/api/learning_report')
@login_required
def get_learning_report():
    """Endpoint do pobierania raportu uczenia się"""
    try:
        from learning_monitor import LearningMonitor
        
        monitor = LearningMonitor()
        report = monitor.generate_learning_report()
        
        return jsonify(report)
        
    except Exception as e:
        return jsonify({'error': f'Błąd generowania raportu: {str(e)}'}), 500
