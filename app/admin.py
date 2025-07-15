#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Panel administracyjny aplikacji Aero-Chat
"""
import os
import json
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import login_required, login_user, logout_user, current_user
from app.models import User, ChatSession, UploadIndex, UserSession
from app.session_analytics import SessionAnalytics

admin_bp = Blueprint('admin', __name__)

# Inicjalizuj analitykę sesji
analytics = SessionAnalytics()

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
    """Panel główny administratora z rozszerzonymi statystykami"""
    # Odśwież dane analityczne
    analytics.load_all_data()
    
    # Pobierz rozszerzone statystyki
    global_stats = analytics.get_global_statistics()
    
    # Dodaj dodatkowe statystyki
    stats = {
        **global_stats,
        'total_users': len(User.get_all_users()),
        'active_users_today': get_active_users_today(),
        'avg_questions_per_session': global_stats['total_messages'] / global_stats['total_sessions'] if global_stats.get('total_sessions', 0) > 0 else 0,
        'top_performers': get_top_performing_users(),
        'system_health': calculate_system_health()
    }
    
    return render_template('admin/dashboard.html', stats=stats)

@admin_bp.route('/users')
@login_required
def users():
    """Lista użytkowników z rozszerzonymi statystykami"""
    if not current_user.is_admin():
        flash('Brak uprawnień administratora', 'error')
        return redirect(url_for('admin.dashboard'))
    
    # Odśwież dane analityczne
    analytics.load_all_data()
    
    users_list = User.get_all_users()
    
    # Dodaj szczegółowe statystyki dla każdego użytkownika
    for user in users_list:
        user_stats = analytics.get_user_statistics(user.id)
        user.sessions_count = user_stats['total_sessions']
        user.total_messages = user_stats['total_messages']
        user.total_time = user_stats['total_time']
        user.avg_engagement = user_stats['avg_engagement']
        user.favorite_topics = user_stats['favorite_topics'][:3]  # Top 3 tematy
        user.productivity_score = user_stats['productivity_score']
        user.last_activity = None
        
        if user_stats['recent_sessions']:
            user.last_activity = user_stats['recent_sessions'][0]['end_time']
    
    return render_template('admin/users.html', users=users_list)

@admin_bp.route('/users/add', methods=['GET', 'POST'])
@login_required 
def add_user():
    """Dodawanie nowego użytkownika"""
    if not current_user.is_admin():
        flash('Brak uprawnień administratora', 'error')
        return redirect(url_for('admin.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role', 'user')
        
        if not username or not password:
            flash('Login i hasło są wymagane', 'error')
        else:
            user, error = User.create_user(username, password, role)
            if user:
                flash(f'Użytkownik {username} został utworzony pomyślnie', 'success')
                return redirect(url_for('admin.users'))
            else:
                flash(f'Błąd tworzenia użytkownika: {error}', 'error')
    
    return render_template('admin/add_user.html')

@admin_bp.route('/users/<user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    """Usuwanie użytkownika"""
    if not current_user.is_admin():
        return jsonify({'error': 'Brak uprawnień'}), 403
    
    if user_id == current_user.id:
        return jsonify({'error': 'Nie można usunąć siebie'}), 400
    
    if User.delete_user(user_id):
        flash('Użytkownik został usunięty', 'success')
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'Błąd usuwania użytkownika'}), 500

@admin_bp.route('/users/<user_id>/sessions')
@login_required
def user_sessions(user_id):
    """Szczegółowe sesje konkretnego użytkownika"""
    if not current_user.is_admin():
        flash('Brak uprawnień administratora', 'error')
        return redirect(url_for('admin.dashboard'))
    
    user = User.get(user_id)
    if not user:
        flash('Użytkownik nie znaleziony', 'error')
        return redirect(url_for('admin.users'))
    
    # Odśwież dane analityczne
    analytics.load_all_data()
    
    # Pobierz statystyki użytkownika
    user_stats = analytics.get_user_statistics(user_id)
    
    # Pobierz szczegółowe dane sesji
    sessions_data = []
    for session in user_stats['recent_sessions']:
        session_details = analytics.get_session_details(session['session_id'])
        if session_details:
            sessions_data.append(session_details)
    
    return render_template('admin/user_sessions.html', 
                         user=user, 
                         sessions=sessions_data, 
                         user_stats=user_stats)

@admin_bp.route('/feedback')
@login_required
def feedback():
    """Lista feedbacków"""
    feedback_data = []
    
    # Przeskanuj katalog feedback - nowy format z podkatalogami sesji
    if os.path.exists('feedback'):
        for item in os.listdir('feedback'):
            item_path = os.path.join('feedback', item)
            
            # Sprawdź czy to katalog sesji
            if os.path.isdir(item_path):
                session_id = item
                # Przeskanuj pliki w katalogu sesji
                for feedback_file in os.listdir(item_path):
                    if feedback_file.endswith('.json'):
                        file_path = os.path.join(item_path, feedback_file)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                fb_data = json.load(f)
                                
                            feedback_data.append({
                                'session_id': session_id,
                                'timestamp': fb_data.get('timestamp'),
                                'feedback_type': fb_data.get('feedback_type'),
                                'section_type': fb_data.get('section_type', 'message'),
                                'content': fb_data.get('content', '')[:100],  # Limit display
                                'message_id': fb_data.get('message_id', ''),
                                'section_id': fb_data.get('section_id', ''),
                                'description': fb_data.get('description', ''),
                                'file_name': feedback_file
                            })
                        except Exception as e:
                            print(f"Błąd wczytywania feedback: {e}")
                            continue
            
            # Stary format - pliki bezpośrednio w katalogu feedback
            elif item.endswith('.json'):
                session_id = item.replace('.json', '')
                feedback_file = os.path.join('feedback', item)
                
                try:
                    with open(feedback_file, 'r', encoding='utf-8') as f:
                        session_feedback = json.load(f)
                    
                    if isinstance(session_feedback, list):
                        for fb in session_feedback:
                            feedback_data.append({
                                'session_id': session_id,
                                'timestamp': fb.get('timestamp'),
                                'feedback_type': fb.get('type', fb.get('feedback_type')),
                                'section_type': fb.get('section_type', 'message'),
                                'content': fb.get('content', ''),
                                'message_id': fb.get('message_id', ''),
                                'section_id': '',
                                'description': '',
                                'file_name': item
                            })
                except Exception as e:
                    print(f"Błąd wczytywania starego feedback: {e}")
                    continue
    
    # Sortuj po dacie
    feedback_data.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    
    return render_template('admin/feedback.html', feedback=feedback_data)

@admin_bp.route('/documents')
@login_required
def documents():
    """Lista dokumentów"""
    upload_index = UploadIndex()
    documents = upload_index.get_files_by_status()
    
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

@admin_bp.route('/sessions/<session_id>')
@login_required
def session_details(session_id):
    """Szczegółowy podgląd sesji"""
    if not current_user.is_admin():
        flash('Brak uprawnień administratora', 'error')
        return redirect(url_for('admin.dashboard'))
    
    # Odśwież dane analityczne
    analytics.load_all_data()
    
    session_data = analytics.get_session_details(session_id)
    if not session_data:
        flash('Sesja nie znaleziona', 'error')
        return redirect(url_for('admin.dashboard'))
    
    # Pobierz informacje o użytkowniku
    user = None
    if session_data['user_id']:
        user = User.get(session_data['user_id'])
    
    return render_template('admin/session_details.html', 
                         session=session_data, 
                         user=user)

@admin_bp.route('/api/sessions/<session_id>/export')
@login_required
def export_session_data(session_id):
    """Eksportuj dane sesji do JSON"""
    if not current_user.is_admin():
        return jsonify({'error': 'Brak uprawnień'}), 403
    
    analytics.load_all_data()
    session_data = analytics.get_session_details(session_id)
    
    if not session_data:
        return jsonify({'error': 'Sesja nie znaleziona'}), 404
    
    return jsonify(session_data)

@admin_bp.route('/analytics')
@login_required
def analytics_dashboard():
    """Panel analityczny z wykresami i statystykami"""
    if not current_user.is_admin():
        flash('Brak uprawnień administratora', 'error')
        return redirect(url_for('admin.dashboard'))
    
    # Odśwież dane analityczne
    analytics.load_all_data()
    
    # Pobierz dane dla wykresów
    global_stats = analytics.get_global_statistics()
    
    # Statystyki czasowe (ostatnie 30 dni)
    daily_stats = get_daily_statistics()
    
    # Top użytkownicy
    top_users = get_top_users_detailed()
    
    # Analiza tematów
    topic_analysis = analyze_topics_distribution()
    
    return render_template('admin/analytics.html', 
                         global_stats=global_stats,
                         daily_stats=daily_stats,
                         top_users=top_users,
                         topic_analysis=topic_analysis)

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
    documents = upload_index.get_all_files()
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
