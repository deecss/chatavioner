#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skrypt uruchamiający Aero-Chat z automatyczną inicjalizacją
"""
import os
import sys
from dotenv import load_dotenv

# Załaduj zmienne środowiskowe na początku
load_dotenv()

def check_requirements():
    """Sprawdza czy wszystkie wymagania są spełnione"""
    required_env_vars = ['OPENAI_API_KEY']
    missing_vars = []
    
    for var in required_env_vars:
        value = os.getenv(var)
        if not value or value.strip() == '' or 'twoj-klucz' in value:
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Brakuje zmiennych środowiskowych:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\n📝 Edytuj plik .env i dodaj brakujące klucze API")
        return False
    
    return True

def setup_directories():
    """Tworzy wymagane katalogi"""
    directories = [
        'uploads', 'history', 'feedback', 'reports', 
        'data', 'data/user_sessions', 'training_data'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    
    print("📁 Katalogi utworzone pomyślnie")

def setup_openai_assistant():
    """Tworzy asystenta OpenAI jeśli nie istnieje"""
    try:
        assistant_id = os.getenv('ASSISTANT_ID')
        
        if not assistant_id or assistant_id.strip() == '' or 'twoj-assistant' in assistant_id:
            print("🤖 Tworzenie nowego asystenta OpenAI...")
            
            # Import w bloku try żeby obsłużyć brak instalacji
            from utils.openai_rag import OpenAIRAG
            rag = OpenAIRAG()
            
            if rag.assistant_id:
                print(f"✅ Asystent utworzony: {rag.assistant_id}")
                
                # Aktualizuj plik .env
                with open('.env', 'r') as f:
                    lines = f.readlines()
                
                # Znajdź i zaktualizuj linię ASSISTANT_ID
                for i, line in enumerate(lines):
                    if line.startswith('ASSISTANT_ID='):
                        lines[i] = f'ASSISTANT_ID={rag.assistant_id}\n'
                        break
                
                with open('.env', 'w') as f:
                    f.writelines(lines)
                
                print("📝 Plik .env zaktualizowany z ID asystenta")
            else:
                print("❌ Nie udało się utworzyć asystenta")
        else:
            print(f"🤖 Używam istniejącego asystenta: {assistant_id[:20]}...")
            
    except Exception as e:
        print(f"❌ Błąd podczas tworzenia asystenta: {e}")
        print("💡 Sprawdź czy klucz OpenAI API jest poprawny")

def setup_admin_user():
    """Tworzy domyślnego administratora jeśli nie istnieje"""
    try:
        from app.models import User
        
        users_file = 'data/users.json'
        if not os.path.exists(users_file):
            User.create_default_admin()
            print("👤 Domyślny administrator utworzony:")
            print("   Login: admin")
            print("   Hasło: admin123")
        else:
            print("👤 Administrator już istnieje")
            
    except Exception as e:
        print(f"❌ Błąd podczas tworzenia administratora: {e}")

def setup_learning_system():
    """Inicjalizuje system uczenia się i raporty"""
    try:
        print("🧠 Inicjalizacja systemu uczenia się...")
        from utils.learning_system import LearningSystem
        from utils.learning_reports import LearningReportsSystem
        from utils.reports_scheduler import start_report_scheduler
        
        learning_system = LearningSystem()
        learning_reports = LearningReportsSystem()
        
        # Sprawdź czy istnieją dane do analizy
        history_dir = 'history'
        if os.path.exists(history_dir):
            sessions = [f.replace('.json', '') for f in os.listdir(history_dir) if f.endswith('.json')]
            if sessions:
                # Analizuj wszystkich użytkowników - nowy system!
                print("👥 Analizuję preferencje wszystkich użytkowników...")
                learning_system.analyze_and_cache_all_users()
                
                # Analizuj ostatnie sesje (dla kompatybilności)
                print(f"📚 Analizuję ostatnie {min(10, len(sessions))} sesji...")
                analyzed_count = 0
                
                for session_id in sessions[-10:]:  # Ostatnie 10 sesji
                    try:
                        analysis = learning_system.analyze_conversation_history(session_id)
                        if analysis:
                            learning_system.save_learning_data(analysis)
                            analyzed_count += 1
                    except Exception as e:
                        print(f"⚠️  Błąd analizy sesji {session_id}: {e}")
                
                print(f"✅ Przeanalizowano {analyzed_count} sesji dla systemu uczenia się")
                
                # Generuj globalne wzorce
                global_patterns = learning_system.analyze_all_sessions()
                print(f"🌐 Wygenerowano globalne wzorce dla {global_patterns.get('total_sessions', 0)} sesji")
                
                # Wygeneruj przykładowy raport jeśli nie ma żadnych
                available_reports = learning_reports.get_available_reports()
                if len(available_reports) == 0:
                    print("📊 Generuję przykładowy raport uczenia się...")
                    try:
                        from datetime import datetime
                        report = learning_reports.generate_daily_report(datetime.now())
                        print(f"✅ Wygenerowano przykładowy raport: {report['report_id']}")
                    except Exception as e:
                        print(f"⚠️  Błąd generowania przykładowego raportu: {e}")
                else:
                    print(f"📋 Znaleziono {len(available_reports)} istniejących raportów")
                
            else:
                print("📝 Brak sesji do analizy - system uczenia się gotowy na nowe dane")
        else:
            print("📁 Tworzę katalog historii dla systemu uczenia się")
        
        # Uruchom scheduler raportów
        print("⏰ Uruchamianie schedulera raportów...")
        try:
            start_report_scheduler()
            print("✅ Scheduler raportów uruchomiony pomyślnie")
        except Exception as e:
            print(f"⚠️  Błąd uruchamiania schedulera: {e}")
        
        print("🎯 System uczenia się uruchomiony pomyślnie!")
        print("📊 System teraz analizuje WSZYSTKIE sesje każdego użytkownika!")
        
    except Exception as e:
        print(f"❌ Błąd inicjalizacji systemu uczenia się: {e}")
        print("⚠️  Aplikacja będzie działać bez systemu uczenia się")

def main():
    """Główna funkcja uruchamiająca"""
    print("🛩️  Aero-Chat - Uruchamianie aplikacji")
    print("=" * 50)
    
    # Sprawdź zmienne środowiskowe
    if not check_requirements():
        sys.exit(1)
    
    # Utwórz katalogi
    setup_directories()
    
    # Utwórz/sprawdź asystenta OpenAI
    setup_openai_assistant()
    
    # Utwórz administratora
    setup_admin_user()
    
    # Inicjalizuj system uczenia się
    setup_learning_system()
    
    # Importuj i uruchom aplikację
    try:
        from app import create_app
        from flask_socketio import SocketIO
        from watcher import start_watcher
        
        print("\n🚀 Uruchamianie serwera...")
        
        app = create_app()
        
        # Konfiguracja SocketIO z większymi timeout dla długich odpowiedzi
        socketio = SocketIO(
            app, 
            cors_allowed_origins="*", 
            async_mode="threading",
            ping_timeout=300,        # 5 minut na ping timeout
            ping_interval=25,        # Ping co 25 sekund
            max_http_buffer_size=1000000  # 1MB buffer
        )
        
        # Pobierz port z zmiennych środowiskowych
        port = int(os.environ.get("PORT", 5000))
        
        # Uruchom watcher
        start_watcher()
        print("👁️  Watcher uruchomiony")
        
        # Rejestruj handlery WebSocket
        from app.socketio_handlers import register_socketio_handlers
        register_socketio_handlers(socketio)
        
        print("\n✅ Aplikacja gotowa!")
        print(f"🌐 Adres: http://localhost:{port}")
        print(f"⚙️  Panel admin: http://localhost:{port}/admin")
        print("\n💡 Aby zatrzymać serwer naciśnij Ctrl+C")
        print("=" * 50)
        
        # Uruchom serwer
        socketio.run(app, host="0.0.0.0", port=port, debug=True)
        
    except ImportError as e:
        print(f"❌ Błąd importu: {e}")
        print("💡 Czy zainstalowałeś wszystkie zależności? Uruchom:")
        print("   pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Błąd uruchamiania: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
