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

@admin_bp.route('/api/generate-learning-report', methods=['POST'])
@login_required
def api_generate_learning_report():
    """API endpoint do generowania raportu uczenia się"""
    if not current_user.is_admin():
        return jsonify({'error': 'Brak uprawnień'}), 403
    
    try:
        data = request.get_json()
        date_str = data.get('date')
        report_type = data.get('type', 'daily')
        
        if not date_str:
            return jsonify({'error': 'Data jest wymagana'}), 400
        
        # Konwertuj string na datetime
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            return jsonify({'error': 'Nieprawidłowy format daty'}), 400
        
        # Generuj raport
        report = learning_reports_system.generate_daily_report(date)
        
        return jsonify({
            'success': True,
            'report_id': report['report_id'],
            'message': 'Raport został wygenerowany pomyślnie'
        })
    except Exception as e:
        logger.error(f"Błąd generowania raportu: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/toggle-scheduler', methods=['POST'])
@login_required
def api_toggle_scheduler():
    """API endpoint do przełączania schedulera"""
    if not current_user.is_admin():
        return jsonify({'error': 'Brak uprawnień'}), 403
    
    try:
        from utils.reports_scheduler import get_report_scheduler
        scheduler = get_report_scheduler()
        
        if scheduler.is_running:
            scheduler.stop()
            status = False
            message = 'Scheduler został zatrzymany'
        else:
            scheduler.start()
            status = True
            message = 'Scheduler został uruchomiony'
        
        return jsonify({
            'success': True,
            'status': status,
            'message': message
        })
    except Exception as e:
        logger.error(f"Błąd przełączania schedulera: {e}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/api/live-stats')
@login_required
def api_live_stats():
    """API endpoint dla statystyk na żywo"""
    if not current_user.is_admin():
        return jsonify({'error': 'Brak uprawnień'}), 403
    
    try:
        # Pobierz statystyki z różnych źródeł
        stats = {
            'active_sessions': len(analytics.get_active_sessions()),
            'today_questions': analytics.get_today_questions_count(),
            'last_report': analytics.get_last_report_date(),
            'system_status': 'OK'
        }
        
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        logger.error(f"Błąd API live-stats: {e}")
        return jsonify({'error': str(e)}), 500
