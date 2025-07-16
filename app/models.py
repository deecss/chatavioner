#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Modele danych dla aplikacji Aero-Chat
"""
import json
import os
import uuid
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

# Przechowywanie aktualnej sesji dla każdego użytkownika
# user_id -> session_id
USER_CURRENT_SESSIONS = {}

class User(UserMixin):
    """Model użytkownika do autoryzacji administratora"""
    
    def __init__(self, user_id, username, password_hash=None, role='user', created_at=None):
        self.id = user_id
        self.username = username
        self.password_hash = password_hash
        self.role = role
        self.created_at = created_at or datetime.now().isoformat()
    
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
                    return User(
                        user_data['id'], 
                        user_data['username'], 
                        user_data['password_hash'],
                        user_data.get('role', 'user'),
                        user_data.get('created_at')
                    )
        except:
            return None
        
        return None
    
    @staticmethod
    def get_by_username(username):
        """Pobiera użytkownika po nazwie użytkownika"""
        users_file = 'data/users.json'
        if not os.path.exists(users_file):
            return None
        
        try:
            with open(users_file, 'r', encoding='utf-8') as f:
                users = json.load(f)
                
            for user_data in users:
                if user_data['username'] == username:
                    return User(
                        user_data['id'], 
                        user_data['username'], 
                        user_data['password_hash'],
                        user_data.get('role', 'user'),
                        user_data.get('created_at')
                    )
        except:
            return None
        
        return None
    
    @staticmethod
    def get_all_users():
        """Pobiera wszystkich użytkowników"""
        users_file = 'data/users.json'
        if not os.path.exists(users_file):
            return []
        
        try:
            with open(users_file, 'r', encoding='utf-8') as f:
                users_data = json.load(f)
                
            return [User(
                user['id'], 
                user['username'], 
                user['password_hash'],
                user.get('role', 'user'),
                user.get('created_at')
            ) for user in users_data]
        except:
            return []
    
    @staticmethod
    def authenticate(username, password):
        """Uwierzytelnia użytkownika"""
        user = User.get_by_username(username)
        if user and check_password_hash(user.password_hash, password):
            return user
        return None
    
    @staticmethod
    def create_user(username, password, role='user'):
        """Tworzy nowego użytkownika"""
        users_file = 'data/users.json'
        os.makedirs(os.path.dirname(users_file), exist_ok=True)
        
        # Sprawdź czy użytkownik już istnieje
        if User.get_by_username(username):
            return None, "Użytkownik już istnieje"
        
        # Wczytaj istniejących użytkowników
        users = []
        if os.path.exists(users_file):
            try:
                with open(users_file, 'r', encoding='utf-8') as f:
                    users = json.load(f)
            except:
                users = []
        
        # Dodaj nowego użytkownika
        new_user_data = {
            'id': str(uuid.uuid4()),
            'username': username,
            'password_hash': generate_password_hash(password),
            'role': role,
            'created_at': datetime.now().isoformat()
        }
        
        users.append(new_user_data)
        
        # Zapisz do pliku
        with open(users_file, 'w', encoding='utf-8') as f:
            json.dump(users, f, ensure_ascii=False, indent=2)
        
        return User(
            new_user_data['id'],
            new_user_data['username'],
            new_user_data['password_hash'],
            new_user_data['role'],
            new_user_data['created_at']
        ), None
    
    @staticmethod
    def delete_user(user_id):
        """Usuwa użytkownika"""
        users_file = 'data/users.json'
        if not os.path.exists(users_file):
            return False
        
        try:
            with open(users_file, 'r', encoding='utf-8') as f:
                users = json.load(f)
            
            # Znajdź i usuń użytkownika
            users = [user for user in users if user['id'] != user_id]
            
            with open(users_file, 'w', encoding='utf-8') as f:
                json.dump(users, f, ensure_ascii=False, indent=2)
            
            return True
        except:
            return False
    
    def update_password(self, new_password):
        """Aktualizuje hasło użytkownika"""
        users_file = 'data/users.json'
        if not os.path.exists(users_file):
            return False
        
        try:
            with open(users_file, 'r', encoding='utf-8') as f:
                users = json.load(f)
            
            # Znajdź i zaktualizuj użytkownika
            for user in users:
                if user['id'] == self.id:
                    user['password_hash'] = generate_password_hash(new_password)
                    break
            
            with open(users_file, 'w', encoding='utf-8') as f:
                json.dump(users, f, ensure_ascii=False, indent=2)
            
            self.password_hash = generate_password_hash(new_password)
            return True
        except:
            return False
    
    def is_admin(self):
        """Sprawdza czy użytkownik ma uprawnienia administratora"""
        return self.role == 'admin'
    
    def is_authenticated(self):
        """Wymagane przez Flask-Login"""
        return True
    
    def is_active(self):
        """Wymagane przez Flask-Login"""
        return True
    
    def is_anonymous(self):
        """Wymagane przez Flask-Login"""
        return False
    
    def get_id(self):
        """Wymagane przez Flask-Login"""
        return str(self.id)
    
    @staticmethod
    def create_default_admin():
        """Tworzy domyślnego administratora"""
        users_file = 'data/users.json'
        os.makedirs(os.path.dirname(users_file), exist_ok=True)
        
        if not os.path.exists(users_file):
            admin_user = {
                'id': 'admin',
                'username': 'admin',
                'password_hash': generate_password_hash('admin123'),
                'role': 'admin',
                'created_at': datetime.now().isoformat()
            }
            
            with open(users_file, 'w', encoding='utf-8') as f:
                json.dump([admin_user], f, ensure_ascii=False, indent=2)

class UserSession:
    """Model sesji użytkownika"""
    
    def __init__(self, user_id, session_id=None, title=None):
        self.user_id = user_id
        self.session_id = session_id or str(uuid.uuid4())
        self.title = title or f"Sesja {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()
    
    def save(self):
        """Zapisuje sesję do bazy danych"""
        sessions_file = f'data/user_sessions/{self.user_id}.json'
        os.makedirs(os.path.dirname(sessions_file), exist_ok=True)
        
        # Wczytaj istniejące sesje
        sessions = []
        if os.path.exists(sessions_file):
            try:
                with open(sessions_file, 'r', encoding='utf-8') as f:
                    sessions = json.load(f)
            except:
                sessions = []
        
        # Sprawdź czy sesja już istnieje
        session_exists = False
        for i, session in enumerate(sessions):
            if session['session_id'] == self.session_id:
                sessions[i] = {
                    'session_id': self.session_id,
                    'title': self.title,
                    'created_at': self.created_at,
                    'updated_at': datetime.now().isoformat()
                }
                session_exists = True
                break
        
        # Jeśli sesja nie istnieje, dodaj ją
        if not session_exists:
            sessions.append({
                'session_id': self.session_id,
                'title': self.title,
                'created_at': self.created_at,
                'updated_at': self.updated_at
            })
        
        # Zapisz sesje
        with open(sessions_file, 'w', encoding='utf-8') as f:
            json.dump(sessions, f, ensure_ascii=False, indent=2)
    
    @staticmethod
    def get_user_sessions(user_id):
        """Pobiera wszystkie sesje użytkownika"""
        sessions_file = f'data/user_sessions/{user_id}.json'
        if not os.path.exists(sessions_file):
            return []
        
        try:
            with open(sessions_file, 'r', encoding='utf-8') as f:
                sessions_data = json.load(f)
            
            return sorted(sessions_data, key=lambda x: x['updated_at'], reverse=True)
        except:
            return []
    
    @staticmethod
    def delete_session(user_id, session_id):
        """Usuwa sesję użytkownika"""
        sessions_file = f'data/user_sessions/{user_id}.json'
        if not os.path.exists(sessions_file):
            return False
        
        try:
            with open(sessions_file, 'r', encoding='utf-8') as f:
                sessions = json.load(f)
            
            # Usuń sesję
            sessions = [s for s in sessions if s['session_id'] != session_id]
            
            with open(sessions_file, 'w', encoding='utf-8') as f:
                json.dump(sessions, f, ensure_ascii=False, indent=2)
            
            # Usuń pliki historii sesji
            history_file = f'history/{session_id}.json'
            if os.path.exists(history_file):
                os.remove(history_file)
            
            return True
        except:
            return False
    
    @staticmethod
    def update_session_title(user_id, session_id, new_title):
        """Aktualizuje tytuł sesji użytkownika"""
        sessions_file = f'data/user_sessions/{user_id}.json'
        if not os.path.exists(sessions_file):
            return False
        
        try:
            with open(sessions_file, 'r', encoding='utf-8') as f:
                sessions = json.load(f)
            
            # Znajdź i zaktualizuj sesję
            for session in sessions:
                if session['session_id'] == session_id:
                    session['title'] = new_title
                    session['updated_at'] = datetime.now().isoformat()
                    break
            else:
                return False  # Sesja nie została znaleziona
            
            with open(sessions_file, 'w', encoding='utf-8') as f:
                json.dump(sessions, f, ensure_ascii=False, indent=2)
            
            return True
        except:
            return False
    
    @staticmethod
    def get_current_session(user_id):
        """Pobiera aktualną sesję użytkownika"""
        return USER_CURRENT_SESSIONS.get(user_id)
    
    @staticmethod
    def set_current_session(user_id, session_id):
        """Ustawia aktualną sesję użytkownika"""
        USER_CURRENT_SESSIONS[user_id] = session_id
        print(f"🔄 Ustawiono aktualną sesję dla użytkownika {user_id}: {session_id}")
    
    @staticmethod
    def clear_current_session(user_id):
        """Usuwa aktualną sesję użytkownika"""
        if user_id in USER_CURRENT_SESSIONS:
            del USER_CURRENT_SESSIONS[user_id]
            print(f"🗑️ Wyczyszczono aktualną sesję dla użytkownika {user_id}")

class ChatSession:
    """Model sesji czatu"""
    
    def __init__(self, session_id, user_id=None):
        self.session_id = session_id
        self.user_id = user_id
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
            'timestamp': datetime.now().isoformat(),
            'user_id': self.user_id
        }
        
        history.append(new_message)
        
        os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        
        # Aktualizuj sesję użytkownika
        if self.user_id:
            user_session = UserSession(self.user_id, self.session_id)
            user_session.save()
    
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
            'message_id': feedback_data.get('message_id'),
            'user_id': self.user_id
        }
        
        feedback.append(feedback_entry)
        
        os.makedirs(os.path.dirname(self.feedback_file), exist_ok=True)
        with open(self.feedback_file, 'w', encoding='utf-8') as f:
            json.dump(feedback, f, ensure_ascii=False, indent=2)

class UploadIndex:
    """Klasa do zarządzania indeksem przesłanych plików"""
    
    def __init__(self):
        self.index_file = 'data/upload_index.json'
        self.ensure_index_exists()
    
    def ensure_index_exists(self):
        """Zapewnia istnienie pliku indeksu"""
        os.makedirs(os.path.dirname(self.index_file), exist_ok=True)
        if not os.path.exists(self.index_file):
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump({}, f, ensure_ascii=False, indent=2)
    
    def add_file(self, filename, metadata=None):
        """Dodaje plik do indeksu"""
        try:
            with open(self.index_file, 'r', encoding='utf-8') as f:
                index = json.load(f)
        except:
            index = {}
        
        if metadata is None:
            metadata = {}
        
        index[filename] = {
            'added_at': datetime.now().isoformat(),
            'size': metadata.get('size', 0),
            'processed': metadata.get('processed', False),
            **metadata
        }
        
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(index, f, ensure_ascii=False, indent=2)
    
    def remove_file(self, filename):
        """Usuwa plik z indeksu"""
        try:
            with open(self.index_file, 'r', encoding='utf-8') as f:
                index = json.load(f)
            
            if filename in index:
                del index[filename]
                
                with open(self.index_file, 'w', encoding='utf-8') as f:
                    json.dump(index, f, ensure_ascii=False, indent=2)
                return True
        except:
            pass
        return False
    
    def get_all_files(self):
        """Pobiera wszystkie pliki z indeksu"""
        try:
            with open(self.index_file, 'r', encoding='utf-8') as f:
                index = json.load(f)
            return list(index.keys())
        except:
            return []
    
    def get_file_info(self, filename):
        """Pobiera informacje o pliku"""
        try:
            with open(self.index_file, 'r', encoding='utf-8') as f:
                index = json.load(f)
            return index.get(filename)
        except:
            return None
    
    def update_file_metadata(self, filename, metadata):
        """Aktualizuje metadane pliku"""
        try:
            with open(self.index_file, 'r', encoding='utf-8') as f:
                index = json.load(f)
            
            if filename in index:
                index[filename].update(metadata)
                
                with open(self.index_file, 'w', encoding='utf-8') as f:
                    json.dump(index, f, ensure_ascii=False, indent=2)
                return True
        except:
            pass
        return False
    
    def get_files_by_status(self, processed=None):
        """Pobiera pliki według statusu przetwarzania"""
        try:
            with open(self.index_file, 'r', encoding='utf-8') as f:
                index = json.load(f)
            
            if processed is None:
                return index
            
            return {k: v for k, v in index.items() if v.get('processed', False) == processed}
        except:
            return {}
