#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Panel administracyjny aplikacji Aero-Chat
"""
import os
import json
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import login_required, login_user, logout_user, current_user
from app.models import User, ChatSession, UploadIndex

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Logowanie administratora"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.authenticate(username, password)
        if user:
            login_user(user)
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Nieprawidłowe dane logowania', 'error')
    
    return render_template('admin/login.html')

@admin_bp.route('/logout')
@login_required
def logout():
    """Wylogowanie administratora"""
    logout_user()
    return redirect(url_for('admin.login'))

@admin_bp.route('/')
@login_required
def dashboard():
    """Panel główny administratora"""
    # Pobierz statystyki
    stats = get_admin_stats()
    return render_template('admin/dashboard.html', stats=stats)

@admin_bp.route('/users')
@login_required
def users():
    """Lista użytkowników i sesji"""
    sessions_data = []
    
    # Przeskanuj katalog history
    if os.path.exists('history'):
        for filename in os.listdir('history'):
            if filename.endswith('.json'):
                session_id = filename.replace('.json', '')
                chat_session = ChatSession(session_id)
                history = chat_session.load_history()
                
                if history:
                    first_message = history[0]['timestamp']
                    last_message = history[-1]['timestamp']
                    message_count = len(history)
                    
                    sessions_data.append({
                        'session_id': session_id,
                        'first_message': first_message,
                        'last_message': last_message,
                        'message_count': message_count
                    })
    
    return render_template('admin/users.html', sessions=sessions_data)

@admin_bp.route('/feedback')
@login_required
def feedback():
    """Lista feedbacków"""
    feedback_data = []
    
    # Przeskanuj katalog feedback
    if os.path.exists('feedback'):
        for filename in os.listdir('feedback'):
            if filename.endswith('.json'):
                session_id = filename.replace('.json', '')
                feedback_file = f'feedback/{filename}'
                
                try:
                    with open(feedback_file, 'r', encoding='utf-8') as f:
                        session_feedback = json.load(f)
                    
                    for fb in session_feedback:
                        feedback_data.append({
                            'session_id': session_id,
                            'timestamp': fb['timestamp'],
                            'type': fb['type'],
                            'content': fb.get('content', ''),
                            'message_id': fb.get('message_id', '')
                        })
                except:
                    continue
    
    # Sortuj po dacie
    feedback_data.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return render_template('admin/feedback.html', feedback=feedback_data)

@admin_bp.route('/documents')
@login_required
def documents():
    """Lista dokumentów"""
    upload_index = UploadIndex()
    documents = upload_index.load_index()
    
    return render_template('admin/documents.html', documents=documents)

@admin_bp.route('/reports')
@login_required
def reports():
    """Lista raportów PDF"""
    reports_data = []
    
    # Przeskanuj katalog reports
    if os.path.exists('reports'):
        for session_dir in os.listdir('reports'):
            session_path = os.path.join('reports', session_dir)
            if os.path.isdir(session_path):
                for filename in os.listdir(session_path):
                    if filename.endswith('.pdf'):
                        filepath = os.path.join(session_path, filename)
                        stat = os.stat(filepath)
                        
                        reports_data.append({
                            'session_id': session_dir,
                            'filename': filename,
                            'created_at': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                            'size': stat.st_size,
                            'path': filepath
                        })
    
    # Sortuj po dacie
    reports_data.sort(key=lambda x: x['created_at'], reverse=True)
    
    return render_template('admin/reports.html', reports=reports_data)

@admin_bp.route('/download_report/<path:filepath>')
@login_required
def download_report(filepath):
    """Pobierz raport PDF"""
    if os.path.exists(filepath) and filepath.startswith('reports/'):
        return send_file(filepath, as_attachment=True)
    else:
        flash('Plik nie został znaleziony', 'error')
        return redirect(url_for('admin.reports'))

@admin_bp.route('/api/session/<session_id>')
@login_required
def get_session_details(session_id):
    """API: Pobierz szczegóły sesji"""
    chat_session = ChatSession(session_id)
    history = chat_session.load_history()
    
    # Pobierz feedback dla sesji
    feedback_data = []
    feedback_file = f'feedback/{session_id}.json'
    if os.path.exists(feedback_file):
        try:
            with open(feedback_file, 'r', encoding='utf-8') as f:
                feedback_data = json.load(f)
        except:
            pass
    
    return jsonify({
        'session_id': session_id,
        'history': history,
        'feedback': feedback_data
    })

def get_admin_stats():
    """Pobiera statystyki dla panelu administratora"""
    stats = {
        'total_sessions': 0,
        'total_messages': 0,
        'total_documents': 0,
        'total_feedback': 0,
        'total_reports': 0
    }
    
    # Liczba sesji
    if os.path.exists('history'):
        stats['total_sessions'] = len([f for f in os.listdir('history') if f.endswith('.json')])
    
    # Liczba wiadomości
    if os.path.exists('history'):
        for filename in os.listdir('history'):
            if filename.endswith('.json'):
                try:
                    with open(f'history/{filename}', 'r', encoding='utf-8') as f:
                        history = json.load(f)
                        stats['total_messages'] += len(history)
                except:
                    pass
    
    # Liczba dokumentów
    upload_index = UploadIndex()
    documents = upload_index.load_index()
    stats['total_documents'] = len(documents)
    
    # Liczba feedbacków
    if os.path.exists('feedback'):
        for filename in os.listdir('feedback'):
            if filename.endswith('.json'):
                try:
                    with open(f'feedback/{filename}', 'r', encoding='utf-8') as f:
                        feedback = json.load(f)
                        stats['total_feedback'] += len(feedback)
                except:
                    pass
    
    # Liczba raportów
    if os.path.exists('reports'):
        for session_dir in os.listdir('reports'):
            session_path = os.path.join('reports', session_dir)
            if os.path.isdir(session_path):
                stats['total_reports'] += len([f for f in os.listdir(session_path) if f.endswith('.pdf')])
    
    return stats
