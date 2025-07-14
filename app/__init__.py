#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Moduł główny aplikacji Aero-Chat
"""
import os
from flask import Flask
from flask_login import LoginManager
from flask_socketio import SocketIO
from dotenv import load_dotenv

# Załaduj zmienne środowiskowe
load_dotenv()

def create_app():
    """Tworzy i konfiguruje aplikację Flask"""
    # Ustaw jawną ścieżkę do templates i static
    template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
    static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static'))
    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
    
    # Konfiguracja
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
    app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 16*1024*1024))
    
    # Inicjalizacja Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'
    login_manager.login_message = 'Zaloguj się aby uzyskać dostęp do czatu'
    login_manager.login_message_category = 'info'
    
    from app.models import User
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.get(user_id)
    
    # Rejestracja blueprintów
    from app.routes import main_bp
    from app.admin import admin_bp
    from app.socketio_handlers import register_socketio_handlers
    
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    # Inicjalizacja SocketIO
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")
    register_socketio_handlers(socketio)
    
    return app
