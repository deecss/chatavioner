#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Główne routes aplikacji Aero-Chat
"""
import os
import uuid
from flask import Blueprint, render_template, request, session, jsonify
from app.models import ChatSession, UploadIndex

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Strona główna z interfejsem czatu"""
    # Generuj ID sesji jeśli nie istnieje
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    
    return render_template('chat.html', session_id=session['session_id'])

@main_bp.route('/api/upload', methods=['POST'])
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
        filename = f"{uuid.uuid4()}_{file.filename}"
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
def submit_feedback():
    """Endpoint do przesyłania feedbacku"""
    data = request.get_json()
    
    if not data or 'type' not in data:
        return jsonify({'error': 'Brakuje danych feedbacku'}), 400
    
    session_id = session.get('session_id')
    if not session_id:
        return jsonify({'error': 'Brak sesji'}), 400
    
    chat_session = ChatSession(session_id)
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
def clear_history():
    """Endpoint do czyszczenia historii czatu"""
    session_id = session.get('session_id')
    if not session_id:
        return jsonify({'error': 'Brak sesji'}), 400
    
    history_file = f'history/{session_id}.json'
    if os.path.exists(history_file):
        os.remove(history_file)
    
    return jsonify({'message': 'Historia wyczyszczona pomyślnie'})

@main_bp.route('/api/files')
def get_files():
    """Endpoint do pobierania listy załadowanych plików"""
    try:
        upload_index = UploadIndex()
        files = upload_index.get_files()
        
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
