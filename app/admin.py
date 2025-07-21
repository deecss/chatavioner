#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Panel administracyjny aplikacji Aero-Chat
"""
import os
import json
import logging
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file, make_response

from flask_login import login_required, login_user, logout_user, current_user
from app.models import User, ChatSession, UploadIndex, UserSession
from app.session_analytics import SessionAnalytics
from utils.learning_reports import LearningReportsSystem
from utils.reports_scheduler import get_report_scheduler

class UserData:
    """Klasa wrapper dla danych użytkownika"""
    def __init__(self, data):
        for key, value in data.items():
            setattr(self, key, value)

# Inicjalizuj instancję analytics
analytics = SessionAnalytics()

# Inicjalizuj system raportów uczenia się
learning_reports_system = LearningReportsSystem()

# Dodaj logger
logger = logging.getLogger(__name__)

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
        'active_users_today': global_stats.get('active_users_today', 0),
        'avg_questions_per_session': global_stats['total_messages'] / global_stats['total_sessions'] if global_stats.get('total_sessions', 0) > 0 else 0,
        'top_performers': global_stats.get('top_performers', []),
        'system_health': 'OK',
        'sessions_today': global_stats.get('sessions_today', 0),
        'avg_session_duration': global_stats.get('avg_session_duration', 0)
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
    
    # Przygotowanie danych użytkowników z dodatkowymi statystykami
    enhanced_users = []
    
    for user in users_list:
        user_stats = analytics.get_user_statistics(user.id)
        
        # Tworzenie obiektu z rozszerzonymi danymi
        enhanced_user = {
            'id': user.id,
            'username': user.username,
            'role': getattr(user, 'role', 'user'),
            'created_at': getattr(user, 'created_at', None),
            'email': getattr(user, 'email', None),
            
            # Dane z analytics
            'sessions_count': user_stats.get('total_sessions', 0),
            'total_sessions': user_stats.get('total_sessions', 0),
            'total_messages': user_stats.get('total_messages', 0),
            'total_time': user_stats.get('total_time', 0),
            'avg_session_duration': user_stats.get('avg_session_duration', 0),
            'avg_engagement': user_stats.get('avg_engagement', 0),
            'favorite_topics': user_stats.get('favorite_topics', [])[:3],
            'productivity_score': user_stats.get('productivity_score', 0),
            'quality_score': user_stats.get('quality_score', 0),
            'feedback_count': user_stats.get('feedback_count', 0),
            
            # Dodatkowe atrybuty wymagane przez template
            'is_active': user_stats.get('is_active', False),
            'is_new': user_stats.get('is_new', False),
            'messages_per_session': user_stats.get('messages_per_session', 0),
            'engagement_score': user_stats.get('avg_engagement', 0),
            'overall_rating': user_stats.get('overall_rating', 0),
            'last_activity': None
        }
        
        # Bezpieczne sprawdzenie recent_sessions
        if user_stats.get('recent_sessions'):
            enhanced_user['last_activity'] = user_stats['recent_sessions'][0].get('end_time')
        
        enhanced_users.append(UserData(enhanced_user))
    
    # Przygotowanie statystyk dla szablonu
    stats = {
        'total_users': len(enhanced_users),
        'new_users_today': len([u for u in enhanced_users if getattr(u, 'is_new', False)]),
        'active_users': len([u for u in enhanced_users if getattr(u, 'is_active', False)]),
        'activity_rate': (len([u for u in enhanced_users if getattr(u, 'is_active', False)]) / len(enhanced_users) * 100) if enhanced_users else 0,
        'avg_engagement': sum([getattr(u, 'avg_engagement', 0) for u in enhanced_users]) / len(enhanced_users) if enhanced_users else 0,
        'engagement_trend': 5.2,  # Przykładowa wartość trendu
        'avg_productivity': sum([getattr(u, 'productivity_score', 0) for u in enhanced_users]) / len(enhanced_users) if enhanced_users else 0
    }
    
    # Paginacja
    page = 1
    total_pages = 1
    
    return render_template('admin/users.html', 
                         users=enhanced_users, 
                         stats=stats, 
                         page=page, 
                         total_pages=total_pages)

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

@admin_bp.route('/analytics')
@login_required
def analytics_dashboard():
    """Dashboard analityczny - szczegółowe statystyki"""
    analytics = SessionAnalytics()
    
    # Pobierz kompletne statystyki dla szablonu
    stats = {
        'active_users': analytics.get_active_users_count(),
        'user_growth': analytics.get_user_growth_percentage(),
        'daily_sessions': analytics.get_daily_sessions_count(),
        'avg_session_duration': analytics.get_average_session_duration(),
        'avg_engagement': analytics.get_average_engagement(),
        'engagement_trend': analytics.get_engagement_trend(),
        'response_quality': analytics.get_response_quality_percentage(),
        'positive_feedback': analytics.get_positive_feedback_percentage(),
        'top_topics': analytics.get_top_topics_with_stats(),
        'top_users': analytics.get_top_users_detailed(),
        'avg_response_time': analytics.get_average_response_time(),
        'system_uptime': analytics.get_system_uptime(),
        'system_errors': analytics.get_system_errors_count(),
        'resource_usage': analytics.get_resource_usage(),
        'activity_growth': analytics.get_activity_growth_percentage(),
        'predicted_users': analytics.get_predicted_users(),
        'positive_feedback_count': analytics.get_positive_feedback_count(),
        'negative_feedback_count': analytics.get_negative_feedback_count(),
        'positive_feedback_percentage': analytics.get_positive_feedback_percentage(),
        'negative_feedback_percentage': analytics.get_negative_feedback_percentage(),
        'feedback_response_rate': analytics.get_feedback_response_rate(),
        'recent_sessions': analytics.get_recent_sessions(20),
        'activity_labels': analytics.get_activity_labels(),
        'activity_data': analytics.get_activity_data()
    }
    
    return render_template('admin/analytics.html', stats=stats)

# Nowe endpointy dla rozszerzonej funkcjonalności

@admin_bp.route('/user/<user_id>')
@login_required
def user_details(user_id):
    """Szczegółowe informacje o użytkowniku"""
    if not current_user.is_admin():
        flash('Brak uprawnień administratora', 'error')
        return redirect(url_for('admin.dashboard'))
    
    user = User.get(user_id)
    if not user:
        flash('Użytkownik nie został znaleziony', 'error')
        return redirect(url_for('admin.users'))
    
    # Odśwież dane analityczne
    analytics.load_all_data()
    
    # Pobierz szczegółowe statystyki użytkownika
    user_stats = analytics.get_user_statistics(user_id)
    
    # Przygotuj dane użytkownika z dodatkowym kontekstem
    enhanced_user = {
        'id': user.id,
        'username': user.username,
        'role': getattr(user, 'role', 'user'),
        'created_at': getattr(user, 'created_at', None),
        'email': getattr(user, 'email', None),
        **user_stats
    }
    
    return render_template('admin/user_details.html', user=UserData(enhanced_user))

@admin_bp.route('/user/<user_id>/sessions')
@login_required
def user_sessions(user_id):
    """Lista sesji użytkownika"""
    if not current_user.is_admin():
        flash('Brak uprawnień administratora', 'error')
        return redirect(url_for('admin.dashboard'))
    
    user = User.get(user_id)
    if not user:
        flash('Użytkownik nie został znaleziony', 'error')
        return redirect(url_for('admin.users'))
    
    # Odśwież dane analityczne
    analytics.load_all_data()
    
    # Pobierz sesje użytkownika
    sessions = analytics.get_user_all_sessions(user_id)
    
    # Przekształć sesje na format wymagany przez szablon
    formatted_sessions = []
    for session in sessions:
        session_data = {
            'session_id': session.get('session_id'),
            'first_message': session.get('start_time', ''),
            'last_message': session.get('end_time', ''),
            'message_count': session.get('message_count', 0),
            'duration': session.get('duration', 0),
            'topics': session.get('topics', []),
            'engagement_score': session.get('engagement_score', 0)
        }
        formatted_sessions.append(session_data)
    
    return render_template('admin/user_sessions.html', 
                         user=user, 
                         sessions=formatted_sessions)

@admin_bp.route('/export-session-data/<session_id>')
@login_required
def export_session_data(session_id):
    """Eksportuj dane sesji jako JSON"""
    analytics = SessionAnalytics()
    session_data = analytics.get_session_complete_data(session_id)
    
    if not session_data:
        flash('Sesja nie została znaleziona', 'error')
        return redirect(url_for('admin.dashboard'))
    
    # Przygotuj dane do eksportu
    export_data = {
        'session_id': session_id,
        'export_timestamp': datetime.now().isoformat(),
        'data': session_data
    }
    
    response = make_response(json.dumps(export_data, indent=2, ensure_ascii=False))
    response.headers['Content-Type'] = 'application/json'
    response.headers['Content-Disposition'] = f'attachment; filename=session_{session_id[:8]}.json'
    
    return response

@admin_bp.route('/export-user-report/<user_id>')
@login_required
def export_user_report(user_id):
    """Eksportuj pełny raport użytkownika"""
    if not current_user.is_admin():
        flash('Brak uprawnień administratora', 'error')
        return redirect(url_for('admin.dashboard'))
    
    user = User.get(user_id)
    if not user:
        flash('Użytkownik nie został znaleziony', 'error')
        return redirect(url_for('admin.users'))
    
    # Odśwież dane analityczne
    analytics.load_all_data()
    
    # Pobierz pełne dane użytkownika
    user_stats = analytics.get_user_statistics(user_id)
    sessions = analytics.get_user_all_sessions(user_id)
    
    # Tworzenie raportu
    report = {
        'user_info': {
            'id': user.id,
            'username': user.username,
            'role': getattr(user, 'role', 'user'),
            'created_at': getattr(user, 'created_at', None)
        },
        'statistics': user_stats,
        'sessions': sessions,
        'generated_at': datetime.now().isoformat()
    }
    
    # Zapisz raport do pliku
    filename = f"user_report_{user.username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = os.path.join('reports', filename)
    
    os.makedirs('reports', exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    return send_file(filepath, as_attachment=True, download_name=filename)

@admin_bp.route('/export-users')
@login_required
def export_users():
    """Eksportuj dane użytkowników z filtrami"""
    period = request.args.get('period', 'month')
    status = request.args.get('status', 'all')
    engagement = request.args.get('engagement', 'all')
    
    analytics = SessionAnalytics()
    users_data = analytics.get_users_filtered_data(period, status, engagement)
    
    export_data = {
        'export_timestamp': datetime.now().isoformat(),
        'filters': {
            'period': period,
            'status': status,
            'engagement': engagement
        },
        'users': users_data
    }
    
    response = make_response(json.dumps(export_data, indent=2, ensure_ascii=False))
    response.headers['Content-Type'] = 'application/json'
    response.headers['Content-Disposition'] = f'attachment; filename=users_export_{period}.json'
    
    return response

@admin_bp.route('/export-analytics')
@login_required
def export_analytics():
    """Eksportuj dane analityczne"""
    range_param = request.args.get('range', 'month')
    
    analytics = SessionAnalytics()
    analytics_data = analytics.get_complete_analytics_data(range_param)
    
    export_data = {
        'export_timestamp': datetime.now().isoformat(),
        'range': range_param,
        'analytics': analytics_data
    }
    
    response = make_response(json.dumps(export_data, indent=2, ensure_ascii=False))
    response.headers['Content-Type'] = 'application/json'
    response.headers['Content-Disposition'] = f'attachment; filename=analytics_{range_param}.json'
    
    return response

# API endpointy dla aktualizacji w czasie rzeczywistym

@admin_bp.route('/api/quick-stats')
@login_required
def api_quick_stats():
    """API dla szybkich statystyk"""
    try:
        analytics = SessionAnalytics()
        
        # Podstawowe statystyki
        global_stats = analytics.get_global_statistics()
        
        # Przygotuj bezpieczne dane
        stats = {
            'active_sessions': global_stats.get('active_sessions', 0),
            'today_sessions': global_stats.get('sessions_today', 0),
            'system_status': 'OK'
        }
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Błąd w api_quick_stats: {e}")
        return jsonify({
            'active_sessions': 0,
            'today_sessions': 0,
            'system_status': 'Error'
        })

# =============================================
# LEARNING REPORTS ROUTES
# =============================================

@admin_bp.route('/learning-reports')
@login_required
def learning_reports():
    """Panel raportów uczenia się"""
    if not current_user.is_admin():
        flash('Brak uprawnień administratora', 'error')
        return redirect(url_for('admin.dashboard'))
    
    try:
        # Pobierz listę dostępnych raportów
        available_reports = learning_reports_system.get_available_reports()
        
        # Pobierz scheduler info
        scheduler = get_report_scheduler()
        scheduler_status = {
            'is_running': scheduler.running if scheduler else False,
            'next_report_time': '02:00 (jutro)' if scheduler and scheduler.running else 'Nie zaplanowano'
        }
        
        return render_template('admin/learning_reports.html', 
                             reports=available_reports,
                             scheduler_status=scheduler_status)
    
    except Exception as e:
        logger.error(f"Błąd w learning_reports: {e}")
        flash(f'Błąd ładowania raportów: {str(e)}', 'error')
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/learning-reports/generate', methods=['POST'])
@login_required
def generate_learning_report():
    """Generuje raport uczenia się na żądanie"""
    if not current_user.is_admin():
        return jsonify({'error': 'Brak uprawnień'}), 403
    
    try:
        # Pobierz datę z formularza
        date_str = request.form.get('date')
        
        if date_str:
            date = datetime.strptime(date_str, '%Y-%m-%d')
        else:
            date = datetime.now()
        
        # Generuj raport
        report = learning_reports_system.generate_daily_report(date)
        
        return jsonify({
            'success': True,
            'report_id': report['report_id'],
            'message': f'Raport za {date.strftime("%Y-%m-%d")} został wygenerowany'
        })
    
    except Exception as e:
        logger.error(f"Błąd generowania raportu: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/learning-reports/<report_id>')
@login_required
def view_learning_report(report_id):
    """Wyświetla szczegóły raportu uczenia się"""
    if not current_user.is_admin():
        flash('Brak uprawnień administratora', 'error')
        return redirect(url_for('admin.dashboard'))
    
    try:
        report = learning_reports_system.get_report(report_id)
        
        if not report:
            flash('Nie znaleziono raportu', 'error')
            return redirect(url_for('admin.learning_reports'))
        
        return render_template('admin/learning_report_detail.html', report=report)
    
    except Exception as e:
        logger.error(f"Błąd wyświetlania raportu {report_id}: {e}")
        flash(f'Błąd ładowania raportu: {str(e)}', 'error')
        return redirect(url_for('admin.learning_reports'))

@admin_bp.route('/learning-reports/<report_id>/download')
@login_required
def download_learning_report(report_id):
    """Pobiera raport uczenia się jako plik JSON"""
    if not current_user.is_admin():
        return jsonify({'error': 'Brak uprawnień'}), 403
    
    try:
        report = learning_reports_system.get_report(report_id)
        
        if not report:
            return jsonify({'error': 'Nie znaleziono raportu'}), 404
        
        # Utwórz response z plikiem JSON
        response = make_response(json.dumps(report, indent=2, ensure_ascii=False))
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        response.headers['Content-Disposition'] = f'attachment; filename=learning_report_{report_id}.json'
        
        return response
    
    except Exception as e:
        logger.error(f"Błąd pobierania raportu {report_id}: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/learning-reports/api/summary')
@login_required
def api_learning_summary():
    """API dla podsumowania raportów uczenia się"""
    if not current_user.is_admin():
        return jsonify({'error': 'Brak uprawnień'}), 403
    
    try:
        # Pobierz ostatnie raporty
        recent_reports = learning_reports_system.get_available_reports()[:7]  # Ostatnie 7 dni
        
        if not recent_reports:
            return jsonify({
                'summary': {
                    'total_reports': 0,
                    'avg_users_per_day': 0,
                    'avg_questions_per_day': 0,
                    'avg_feedback_per_day': 0,
                    'trend': 'brak danych'
                }
            })
        
        # Oblicz statystyki
        total_users = sum(r['summary'].get('total_users', 0) for r in recent_reports)
        total_questions = sum(r['summary'].get('total_questions', 0) for r in recent_reports)
        total_feedback = sum(r['summary'].get('total_feedback', 0) for r in recent_reports)
        
        days_count = len(recent_reports)
        
        summary = {
            'total_reports': days_count,
            'avg_users_per_day': total_users / days_count,
            'avg_questions_per_day': total_questions / days_count,
            'avg_feedback_per_day': total_feedback / days_count,
            'trend': 'rosnąco' if days_count > 1 and recent_reports[0]['summary'].get('total_users', 0) > recent_reports[-1]['summary'].get('total_users', 0) else 'stabilnie'
        }
        
        return jsonify({'summary': summary})
    
    except Exception as e:
        logger.error(f"Błąd w api_learning_summary: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/learning-reports/scheduler/start', methods=['POST'])
@login_required
def start_scheduler():
    """Uruchamia scheduler raportów"""
    if not current_user.is_admin():
        return jsonify({'error': 'Brak uprawnień'}), 403
    
    try:
        from utils.reports_scheduler import start_report_scheduler
        start_report_scheduler()
        
        return jsonify({
            'success': True,
            'message': 'Scheduler raportów został uruchomiony'
        })
    
    except Exception as e:
        logger.error(f"Błąd uruchamiania schedulera: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/learning-reports/scheduler/stop', methods=['POST'])
@login_required
def stop_scheduler():
    """Zatrzymuje scheduler raportów"""
    if not current_user.is_admin():
        return jsonify({'error': 'Brak uprawnień'}), 403
    
    try:
        from utils.reports_scheduler import stop_report_scheduler
        stop_report_scheduler()
        
        return jsonify({
            'success': True,
            'message': 'Scheduler raportów został zatrzymany'
        })
    
    except Exception as e:
        logger.error(f"Błąd zatrzymywania schedulera: {e}")
        return jsonify({'error': str(e)}), 500

# API endpoints dla raportów uczenia się

@admin_bp.route('/api/learning-reports')
@login_required
def api_learning_reports():
    """API endpoint dla listy raportów uczenia się"""
    if not current_user.is_admin():
        return jsonify({'error': 'Brak uprawnień'}), 403
    
    try:
        reports = learning_reports_system.get_available_reports()
        return jsonify({
            'success': True,
            'reports': reports
        })
    except Exception as e:
        logger.error(f"Błąd API learning-reports: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/learning-report/<report_id>')
@login_required
def api_learning_report_detail(report_id):
    """API endpoint dla szczegółów raportu"""
    if not current_user.is_admin():
        return jsonify({'error': 'Brak uprawnień'}), 403
    
    try:
        report = learning_reports_system.get_report(report_id)
        if not report:
            return jsonify({'error': 'Raport nie znaleziony'}), 404
        
        return jsonify({
            'success': True,
            'report': report
        })
    except Exception as e:
        logger.error(f"Błąd API learning-report detail: {e}")
        return jsonify({'error': str(e)}), 500

# Dodatkowe API endpointy dla raportów uczenia się
@admin_bp.route('/api/learning-reports/<report_id>')
@login_required
def api_learning_report_details(report_id):
    """API endpoint dla szczegółów konkretnego raportu"""
    if not current_user.is_admin():
        return jsonify({'error': 'Brak uprawnień'}), 403
    
    try:
        from utils.reports_scheduler import get_scheduler
        
        scheduler = get_scheduler()
        report = scheduler.get_report_details(report_id)
        
        if not report:
            return jsonify({'success': False, 'message': 'Raport nie znaleziony'}), 404
        
        return jsonify({
            'success': True,
            'report': report
        })
    except Exception as e:
        logger.error(f"Błąd API learning-report details: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/api/learning-reports/<report_id>', methods=['DELETE'])
@login_required
def api_delete_learning_report(report_id):
    """API endpoint do usuwania raportu"""
    if not current_user.is_admin():
        return jsonify({'error': 'Brak uprawnień'}), 403
    
    try:
        from utils.reports_scheduler import get_scheduler
        
        scheduler = get_scheduler()
        result = scheduler.delete_report(report_id)
        
        if result:
            return jsonify({
                'success': True,
                'message': 'Raport usunięty pomyślnie'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Nie udało się usunąć raportu'
            }), 404
    except Exception as e:
        logger.error(f"Błąd usuwania raportu: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/api/learning-reports/<report_id>/download')
@login_required
def api_download_learning_report(report_id):
    """API endpoint do pobierania raportu"""
    if not current_user.is_admin():
        return jsonify({'error': 'Brak uprawnień'}), 403
    
    try:
        from utils.reports_scheduler import get_scheduler
        
        scheduler = get_scheduler()
        report_data = scheduler.get_report_details(report_id)
        
        if not report_data:
            return jsonify({'error': 'Raport nie znaleziony'}), 404
        
        # Generuj raport jako JSON do pobrania
        response = make_response(json.dumps(report_data, indent=2, ensure_ascii=False))
        response.headers["Content-Disposition"] = f"attachment; filename=learning_report_{report_id}.json"
        response.headers["Content-Type"] = "application/json"
        
        return response
    except Exception as e:
        logger.error(f"Błąd pobierania raportu: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/learning-reports/<report_id>/send-email', methods=['POST'])
@login_required
def api_send_specific_report_email(report_id):
    """API endpoint do wysyłania konkretnego raportu emailem"""
    if not current_user.is_admin():
        return jsonify({'error': 'Brak uprawnień'}), 403
    
    try:
        from utils.reports_scheduler import get_scheduler
        
        scheduler = get_scheduler()
        result = scheduler.send_specific_report_email(report_id)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Błąd wysyłania raportu emailem: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/api/learning-reports/generate', methods=['POST'])
@login_required
def api_generate_learning_report():
    """API endpoint do generowania nowego raportu"""
    if not current_user.is_admin():
        return jsonify({'error': 'Brak uprawnień'}), 403
    
    try:
        from utils.reports_scheduler import get_scheduler
        
        data = request.json
        report_date = data.get('date')
        report_type = data.get('type', 'daily')
        
        scheduler = get_scheduler()
        result = scheduler.generate_report_on_demand(report_date, report_type)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Błąd generowania raportu: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/api/learning-reports/scheduler/status')
@login_required
def api_scheduler_status():
    """API endpoint dla statusu schedulera"""
    if not current_user.is_admin():
        return jsonify({'error': 'Brak uprawnień'}), 403
    
    try:
        from utils.reports_scheduler import get_scheduler
        
        scheduler = get_scheduler()
        status = scheduler.get_scheduler_status()
        
        return jsonify({
            'success': True,
            'status': status
        })
    except Exception as e:
        logger.error(f"Błąd statusu schedulera: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/api/learning-reports/scheduler/start', methods=['POST'])
@login_required
def api_start_scheduler():
    """API endpoint do uruchamiania schedulera"""
    if not current_user.is_admin():
        return jsonify({'error': 'Brak uprawnień'}), 403
    
    try:
        from utils.reports_scheduler import get_scheduler
        
        scheduler = get_scheduler()
        result = scheduler.start_scheduler()
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Błąd uruchamiania schedulera: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/api/learning-reports/scheduler/stop', methods=['POST'])
@login_required
def api_stop_scheduler():
    """API endpoint do zatrzymywania schedulera"""
    if not current_user.is_admin():
        return jsonify({'error': 'Brak uprawnień'}), 403
    
    try:
        from utils.reports_scheduler import get_scheduler
        
        scheduler = get_scheduler()
        result = scheduler.stop_scheduler()
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Błąd zatrzymywania schedulera: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/api/users')
@login_required
def api_users():
    """API endpoint dla listy użytkowników"""
    if not current_user.is_admin():
        return jsonify({'error': 'Brak uprawnień'}), 403
    
    try:
        import os
        import json
        
        users_data = {}
        users_file = os.path.join('data', 'users.json')
        
        if os.path.exists(users_file):
            with open(users_file, 'r', encoding='utf-8') as f:
                users_list = json.load(f)
                
                # Konwertuj listę na słownik z ID jako kluczem
                for user in users_list:
                    if isinstance(user, dict) and 'id' in user:
                        users_data[user['id']] = user
        
        users_list = []
        for user_id, user_data in users_data.items():
            users_list.append({
                'id': user_id,
                'username': user_data.get('username', user_id),
                'created_at': user_data.get('created_at', ''),
                'last_login': user_data.get('last_login', '')
            })
        
        return jsonify({
            'success': True,
            'users': users_list
        })
    except Exception as e:
        logger.error(f"Błąd ładowania użytkowników: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/api/users/<user_id>/activity')
@login_required
def api_user_activity(user_id):
    """API endpoint dla aktywności użytkownika"""
    if not current_user.is_admin():
        return jsonify({'error': 'Brak uprawnień'}), 403
    
    try:
        import os
        import json
        from utils.learning_reports import LearningReportsSystem
        from datetime import datetime, timedelta
        import glob
        
        # Użyj systemu raportów do analizy aktywności użytkownika
        reports_system = LearningReportsSystem()
        
        # Analizuj ostatnie 30 dni
        end_time = datetime.now()
        start_time = end_time - timedelta(days=30)
        
        # Pobierz podstawowe dane użytkownika
        user_info = reports_system._get_user_info(user_id)
        
        # Analizuj aktywność użytkownika z plików historii
        questions = []
        sessions_count = 0
        total_questions = 0
        last_activity = None
        
        if os.path.exists('history'):
            for filename in os.listdir('history'):
                if filename.endswith('.json'):
                    filepath = os.path.join('history', filename)
                    
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            history = json.load(f)
                        
                        # Sprawdź czy użytkownik był aktywny w tej sesji
                        user_active_in_session = False
                        session_questions = []
                        
                        for message in history:
                            if not isinstance(message, dict):
                                continue
                            
                            if message.get('user_id') == user_id:
                                user_active_in_session = True
                                
                                msg_time = reports_system._parse_timestamp(message.get('timestamp'))
                                if msg_time:
                                    if not last_activity or msg_time > last_activity:
                                        last_activity = msg_time
                                
                                if message.get('role') == 'user':
                                    total_questions += 1
                                    content = message.get('content', '')
                                    
                                    # Dodaj pytanie do listy
                                    question_data = {
                                        'content': content[:200] + "..." if len(content) > 200 else content,
                                        'timestamp': msg_time.isoformat() if msg_time else message.get('timestamp', ''),
                                        'session_id': filename.replace('.json', ''),
                                        'topic': reports_system._detect_topic(content)
                                    }
                                    session_questions.append(question_data)
                        
                        if user_active_in_session:
                            sessions_count += 1
                            questions.extend(session_questions)
                    
                    except Exception as e:
                        print(f"⚠️  Błąd analizy pliku historii {filename}: {e}")
        
        # Sortuj pytania chronologicznie (najnowsze pierwsze)
        questions.sort(key=lambda x: x['timestamp'], reverse=True)
        
        activity = {
            'username': user_info.get('username', user_id),
            'total_sessions': sessions_count,
            'total_questions': total_questions,
            'last_activity': last_activity.isoformat() if last_activity else None,
            'recent_questions': questions[:20]  # Ostatnie 20 pytań
        }
        
        return jsonify(activity)
        
    except Exception as e:
        print(f"⚠️  Błąd pobierania aktywności użytkownika {user_id}: {e}")
        return jsonify({
            'error': 'Błąd pobierania danych',
            'username': user_id,
            'total_sessions': 0,
            'total_questions': 0,
            'last_activity': None,
            'recent_questions': []
        })

@admin_bp.route('/api/learning-reports/email-config')
@login_required
def api_email_config():
    """API endpoint do pobierania konfiguracji email"""
    if not current_user.is_admin():
        return jsonify({'error': 'Brak uprawnień'}), 403
    
    try:
        from utils.reports_scheduler import get_scheduler
        
        scheduler = get_scheduler()
        config = scheduler.get_email_config()
        
        return jsonify({
            'success': True,
            'config': config
        })
    except Exception as e:
        logger.error(f"Błąd pobierania konfiguracji email: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/api/learning-reports/email-config', methods=['POST'])
@login_required
def api_update_email_config():
    """API endpoint do aktualizowania konfiguracji email"""
    if not current_user.is_admin():
        return jsonify({'error': 'Brak uprawnień'}), 403
    
    try:
        from utils.reports_scheduler import get_scheduler
        
        data = request.get_json()
        scheduler = get_scheduler()
        scheduler.set_email_config(data)
        
        return jsonify({
            'success': True,
            'message': 'Konfiguracja email zaktualizowana'
        })
    except Exception as e:
        logger.error(f"Błąd aktualizowania konfiguracji email: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


# === NOWA FUNKCJONALNOŚĆ: PODRĘCZNIK ATPL ===

@admin_bp.route('/handbook')
@login_required
def handbook():
    """Panel podręcznika ATPL"""
    if not current_user.is_admin():
        flash('Brak uprawnień do panelu administratora', 'error')
        return redirect(url_for('main.index'))
    
    try:
        from utils.atpl_handbook_generator import get_handbook_generator
        
        generator = get_handbook_generator()
        
        # Sprawdź czy struktura istnieje
        try:
            structure = generator.get_handbook_structure()
            progress = generator.get_progress_overview()
        except Exception:
            structure = None
            progress = None
        
        return render_template('admin/handbook.html', 
                             structure=structure,
                             progress=progress)
    except Exception as e:
        logger.error(f"Błąd ładowania podręcznika: {e}")
        flash(f'Błąd ładowania podręcznika: {e}', 'error')
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/api/handbook/analyze-program', methods=['POST'])
@login_required
def api_analyze_program():
    """API endpoint do analizy programu ATPL"""
    if not current_user.is_admin():
        return jsonify({'error': 'Brak uprawnień'}), 403
    
    try:
        from utils.atpl_handbook_generator import get_handbook_generator
        
        generator = get_handbook_generator()
        structure = generator.analyze_program_structure()
        
        return jsonify({
            'success': True,
            'structure': structure,
            'message': f'Program przeanalizowany: {len(structure.get("modules", []))} modułów'
        })
    except Exception as e:
        logger.error(f"Błąd analizy programu: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/api/handbook/structure')
@login_required
def api_handbook_structure():
    """API endpoint do pobierania struktury podręcznika"""
    if not current_user.is_admin():
        return jsonify({'error': 'Brak uprawnień'}), 403
    
    try:
        from utils.atpl_handbook_generator import get_handbook_generator
        
        generator = get_handbook_generator()
        structure = generator.get_handbook_structure()
        progress = generator.get_progress_overview()
        
        return jsonify({
            'success': True,
            'structure': structure,
            'progress': progress
        })
    except Exception as e:
        logger.error(f"Błąd pobierania struktury: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/api/handbook/generate-content', methods=['POST'])
@login_required
def api_generate_content():
    """API endpoint do generowania treści rozdziału/tematu"""
    if not current_user.is_admin():
        return jsonify({'error': 'Brak uprawnień'}), 403
    
    try:
        data = request.get_json()
        module_id = data.get('module_id')
        chapter_id = data.get('chapter_id')
        topic_id = data.get('topic_id')
        ai_type = data.get('ai_type', 'comprehensive')  # Domyślnie kompletny
        
        if not module_id or not chapter_id:
            return jsonify({'success': False, 'message': 'Brak wymaganych parametrów'}), 400
        
        from utils.atpl_handbook_generator import get_handbook_generator
        
        generator = get_handbook_generator()
        content = generator.generate_chapter_content(module_id, chapter_id, topic_id, ai_type)
        
        return jsonify({
            'success': True,
            'content': content,
            'message': 'Treść wygenerowana pomyślnie'
        })
    except Exception as e:
        logger.error(f"Błąd generowania treści: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/api/handbook/content')
@login_required
def api_get_content():
    """API endpoint do pobierania treści"""
    if not current_user.is_admin():
        return jsonify({'error': 'Brak uprawnień'}), 403
    
    try:
        module_id = request.args.get('module_id')
        chapter_id = request.args.get('chapter_id')
        topic_id = request.args.get('topic_id')
        
        if not module_id or not chapter_id:
            return jsonify({'success': False, 'message': 'Brak wymaganych parametrów'}), 400
        
        from utils.atpl_handbook_generator import get_handbook_generator
        
        generator = get_handbook_generator()
        content = generator.get_content(module_id, chapter_id, topic_id)
        
        return jsonify({
            'success': True,
            'content': content
        })
    except Exception as e:
        logger.error(f"Błąd pobierania treści: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/api/handbook/edit-content', methods=['POST'])
@login_required
def api_edit_content():
    """API endpoint do edycji treści"""
    if not current_user.is_admin():
        return jsonify({'error': 'Brak uprawnień'}), 403
    
    try:
        data = request.get_json()
        module_id = data.get('module_id')
        chapter_id = data.get('chapter_id')
        topic_id = data.get('topic_id')
        content = data.get('content')
        
        if not module_id or not chapter_id or not content:
            return jsonify({'success': False, 'message': 'Brak wymaganych parametrów'}), 400
        
        from utils.atpl_handbook_generator import get_handbook_generator
        
        generator = get_handbook_generator()
        generator.edit_content(module_id, chapter_id, topic_id, content)
        
        return jsonify({
            'success': True,
            'message': 'Treść zaktualizowana pomyślnie'
        })
    except Exception as e:
        logger.error(f"Błąd edycji treści: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/api/handbook/export', methods=['POST'])
@login_required
def api_export_handbook():
    """API endpoint do eksportu podręcznika"""
    if not current_user.is_admin():
        return jsonify({'error': 'Brak uprawnień'}), 403
    
    try:
        data = request.get_json() or {}
        format_type = data.get('format', 'markdown')
        
        from utils.atpl_handbook_generator import get_handbook_generator
        
        generator = get_handbook_generator()
        export_result = generator.export_handbook(format_type)
        
        if isinstance(export_result, dict):
            return jsonify({
                'success': True,
                'download_url': export_result.get('download_url'),
                'filename': export_result.get('filename'),
                'message': 'Podręcznik wyeksportowany pomyślnie'
            })
        else:
            # Fallback for old format
            return jsonify({
                'success': True,
                'download_url': f'/handbook/exports/{export_result}',
                'filename': export_result,
                'message': 'Podręcznik wyeksportowany pomyślnie'
            })
    except Exception as e:
        logger.error(f"Błąd eksportu podręcznika: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/api/handbook/upload-image', methods=['POST'])
@login_required
def api_upload_handbook_image():
    """API endpoint do przesyłania obrazów do podręcznika"""
    if not current_user.is_admin():
        return jsonify({'error': 'Brak uprawnień'}), 403
    
    try:
        if 'image' not in request.files:
            return jsonify({'success': False, 'message': 'Brak pliku'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'success': False, 'message': 'Nie wybrano pliku'}), 400
        
        # Sprawdź typ pliku
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        
        if file_ext not in allowed_extensions:
            return jsonify({'success': False, 'message': 'Nieprawidłowy typ pliku'}), 400
        
        # Utwórz katalog na obrazy
        images_dir = os.path.join('handbook', 'images')
        os.makedirs(images_dir, exist_ok=True)
        
        # Wygeneruj unikalną nazwę pliku
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{file.filename}"
        filepath = os.path.join(images_dir, filename)
        
        # Zapisz plik
        file.save(filepath)
        
        # Zwróć URL do pliku
        file_url = f"/handbook/images/{filename}"
        
        return jsonify({
            'success': True,
            'message': 'Obraz przesłany pomyślnie',
            'url': file_url,
            'filename': filename
        })
        
    except Exception as e:
        logger.error(f"Błąd przesyłania obrazu: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/api/handbook/save-content', methods=['POST'])
@login_required
def api_save_handbook_content():
    """API endpoint do zapisywania treści podręcznika"""
    if not current_user.is_admin():
        return jsonify({'error': 'Brak uprawnień'}), 403
    
    try:
        data = request.get_json()
        module_id = data.get('module_id')
        chapter_id = data.get('chapter_id')
        topic_id = data.get('topic_id')
        content = data.get('content')
        
        if not module_id or not chapter_id or content is None:
            return jsonify({'success': False, 'message': 'Brakuje wymaganych danych'}), 400
        
        from utils.atpl_handbook_generator import get_handbook_generator
        
        generator = get_handbook_generator()
        generator.edit_content(module_id, chapter_id, topic_id, content)
        
        return jsonify({
            'success': True,
            'message': 'Treść została zapisana'
        })
        
    except Exception as e:
        logger.error(f"Błąd zapisywania treści: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/api/handbook/progress')
@login_required
def api_handbook_progress():
    """API endpoint do pobierania postępu podręcznika"""
    if not current_user.is_admin():
        return jsonify({'error': 'Brak uprawnień'}), 403
    
    try:
        from utils.atpl_handbook_generator import get_handbook_generator
        
        generator = get_handbook_generator()
        progress = generator.get_progress_overview()
        
        return jsonify({
            'success': True,
            'progress': progress
        })
        
    except Exception as e:
        logger.error(f"Błąd pobierania postępu: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/handbook/images/<filename>')
def serve_handbook_image(filename):
    """Serwowanie obrazów z podręcznika"""
    try:
        images_dir = os.path.join('handbook', 'images')
        return send_file(os.path.join(images_dir, filename))
    except Exception as e:
        logger.error(f"Błąd serwowania obrazu: {e}")
        return "Obraz nie znaleziony", 404

@admin_bp.route('/api/handbook/reset', methods=['POST'])
@login_required
def api_reset_handbook():
    """API endpoint do resetowania podręcznika"""
    if not current_user.is_admin():
        return jsonify({'error': 'Brak uprawnień'}), 403
    
    try:
        from utils.atpl_handbook_generator import get_handbook_generator
        
        generator = get_handbook_generator()
        generator.reset_handbook()
        
        return jsonify({
            'success': True,
            'message': 'Podręcznik został zresetowany'
        })
    except Exception as e:
        logger.error(f"Błąd resetowania podręcznika: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
