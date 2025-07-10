#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modele danych dla aplikacji Aero-Chat
"""
import json
import os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

class User(UserMixin):
    """Model użytkownika do autoryzacji administratora"""
    
    def __init__(self, user_id, username, password_hash=None):
        self.id = user_id
        self.username = username
        self.password_hash = password_hash
    
    @staticmethod
    def get(user_id):
        """Pobiera użytkownika z pliku JSON"""
        users_file = 'data/users.json'
        if not os.path.exists(users_file):
            return None
        
        try:
            with open(users_file, 'r', encoding='utf-8') as f:
                users = json.load(f)
                
            for user_data in users:
                if user_data['id'] == user_id:
                    return User(user_data['id'], user_data['username'], user_data['password_hash'])
        except:
            return None
        
        return None
    
    @staticmethod
    def authenticate(username, password):
        """Uwierzytelnia użytkownika"""
        users_file = 'data/users.json'
        if not os.path.exists(users_file):
            return None
        
        try:
            with open(users_file, 'r', encoding='utf-8') as f:
                users = json.load(f)
                
            for user_data in users:
                if user_data['username'] == username:
                    if check_password_hash(user_data['password_hash'], password):
                        return User(user_data['id'], user_data['username'], user_data['password_hash'])
        except:
            return None
        
        return None
    
    @staticmethod
    def create_default_admin():
        """Tworzy domyślnego administratora"""
        users_file = 'data/users.json'
        os.makedirs(os.path.dirname(users_file), exist_ok=True)
        
        if not os.path.exists(users_file):
            admin_user = {
                'id': 'admin',
                'username': 'admin',
                'password_hash': generate_password_hash('admin123')
            }
            
            with open(users_file, 'w', encoding='utf-8') as f:
                json.dump([admin_user], f, ensure_ascii=False, indent=2)

class ChatSession:
    """Model sesji czatu"""
    
    def __init__(self, session_id):
        self.session_id = session_id
        self.history_file = f'history/{session_id}.json'
        self.feedback_file = f'feedback/{session_id}.json'
        
    def load_history(self):
        """Ładuje historię czatu"""
        if not os.path.exists(self.history_file):
            return []
        
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    
    def save_message(self, message, role='user'):
        """Zapisuje wiadomość do historii"""
        history = self.load_history()
        
        new_message = {
            'role': role,
            'content': message,
            'timestamp': datetime.now().isoformat()
        }
        
        history.append(new_message)
        
        os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    
    def save_feedback(self, feedback_data):
        """Zapisuje feedback do pliku"""
        feedback = []
        
        if os.path.exists(self.feedback_file):
            try:
                with open(self.feedback_file, 'r', encoding='utf-8') as f:
                    feedback = json.load(f)
            except:
                feedback = []
        
        feedback_entry = {
            'timestamp': datetime.now().isoformat(),
            'type': feedback_data.get('type'),
            'content': feedback_data.get('content'),
            'message_id': feedback_data.get('message_id')
        }
        
        feedback.append(feedback_entry)
        
        os.makedirs(os.path.dirname(self.feedback_file), exist_ok=True)
        with open(self.feedback_file, 'w', encoding='utf-8') as f:
            json.dump(feedback, f, ensure_ascii=False, indent=2)

class UploadIndex:
    """Model indeksu przesłanych plików"""
    
    def __init__(self):
        self.index_file = 'data/upload_index.json'
    
    def load_index(self):
        """Ładuje indeks plików"""
        if not os.path.exists(self.index_file):
            return {}
        
        try:
            with open(self.index_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    
    def save_index(self, index_data):
        """Zapisuje indeks plików"""
        os.makedirs(os.path.dirname(self.index_file), exist_ok=True)
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)
    
    def add_file(self, filename, metadata):
        """Dodaje plik do indeksu"""
        index = self.load_index()
        index[filename] = {
            'added_at': datetime.now().isoformat(),
            'size': metadata.get('size', 0),
            'processed': False
        }
        self.save_index(index)
    
    def get_all_files(self):
        """Pobiera wszystkie pliki z indeksu"""
        index = self.load_index()
        return list(index.keys())
    
    def get_files(self):
        """Pobiera listę wszystkich plików z indeksu"""
        return self.load_index()
