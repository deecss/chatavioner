#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skrypt do monitorowania i analizy systemu uczenia się
"""
import os
import json
import time
from datetime import datetime, timedelta
from utils.learning_system import LearningSystem

class LearningMonitor:
    """Klasa do monitorowania systemu uczenia się"""
    
    def __init__(self):
        self.learning_system = LearningSystem()
        self.report_file = 'data/learning_report.json'
    
    def generate_learning_report(self):
        """Generuje raport o stanie uczenia się"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_sessions': 0,
            'active_sessions': 0,
            'learning_patterns': {},
            'user_preferences': {},
            'improvement_suggestions': []
        }
        
        # Analizuj wszystkie sesje
        history_dir = 'history'
        if os.path.exists(history_dir):
            sessions = [f.replace('.json', '') for f in os.listdir(history_dir) if f.endswith('.json')]
            report['total_sessions'] = len(sessions)
            
            # Sprawdź aktywne sesje (ostatnie 24h)
            active_sessions = []
            for session_id in sessions:
                session_file = os.path.join(history_dir, f'{session_id}.json')
                if os.path.exists(session_file):
                    modified_time = datetime.fromtimestamp(os.path.getmtime(session_file))
                    if datetime.now() - modified_time < timedelta(days=1):
                        active_sessions.append(session_id)
            
            report['active_sessions'] = len(active_sessions)
            
            # Analizuj wzorce uczenia się
            all_patterns = {}
            for session_id in sessions[:20]:  # Ostatnie 20 sesji
                try:
                    analysis = self.learning_system.analyze_conversation_history(session_id)
                    if analysis:
                        patterns = analysis.get('user_patterns', {})
                        for pattern_type, pattern_data in patterns.items():
                            if pattern_type not in all_patterns:
                                all_patterns[pattern_type] = []
                            all_patterns[pattern_type].append(pattern_data)
                except Exception as e:
                    print(f"Błąd analizy sesji {session_id}: {e}")
            
            report['learning_patterns'] = all_patterns
            
            # Generuj sugestie ulepszenia
            suggestions = self._generate_improvement_suggestions(all_patterns)
            report['improvement_suggestions'] = suggestions
        
        # Zapisz raport
        try:
            with open(self.report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            print(f"✅ Raport uczenia się zapisany: {self.report_file}")
        except Exception as e:
            print(f"❌ Błąd zapisywania raportu: {e}")
        
        return report
    
    def _generate_improvement_suggestions(self, patterns):
        """Generuje sugestie ulepszenia na podstawie wzorców"""
        suggestions = []
        
        # Analiza częstotliwości pytań o przykłady
        example_requests = []
        for pattern_data in patterns.get('request_types', []):
            if isinstance(pattern_data, dict):
                example_requests.append(pattern_data.get('examples', 0))
        
        if example_requests and sum(example_requests) > len(example_requests) * 2:
            suggestions.append({
                'type': 'examples',
                'message': 'Użytkownicy często proszą o przykłady - rozważenie domyślne dodawanie przykładów',
                'priority': 'high'
            })
        
        # Analiza preferencji szczegółowości
        detail_preferences = []
        for pattern_data in patterns.get('preferred_detail_level', []):
            if isinstance(pattern_data, str):
                detail_preferences.append(pattern_data)
        
        if detail_preferences:
            most_common = max(set(detail_preferences), key=detail_preferences.count)
            suggestions.append({
                'type': 'detail_level',
                'message': f'Najczęstsza preferencja szczegółowości: {most_common}',
                'priority': 'medium'
            })
        
        # Analiza długości pytań
        question_lengths = []
        for pattern_data in patterns.get('question_length', []):
            if isinstance(pattern_data, dict):
                question_lengths.append(pattern_data.get('avg_length', 0))
        
        if question_lengths:
            avg_length = sum(question_lengths) / len(question_lengths)
            if avg_length < 5:
                suggestions.append({
                    'type': 'question_length',
                    'message': 'Użytkownicy zadają krótkie pytania - możliwe uproszczenie interfejsu',
                    'priority': 'low'
                })
            elif avg_length > 20:
                suggestions.append({
                    'type': 'question_length',
                    'message': 'Użytkownicy zadają długie pytania - możliwe dodanie funkcji analizy kontekstu',
                    'priority': 'medium'
                })
        
        return suggestions
    
    def print_learning_status(self):
        """Wyświetla status systemu uczenia się"""
        print("\n" + "="*60)
        print("📊 STATUS SYSTEMU UCZENIA SIĘ")
        print("="*60)
        
        # Sprawdź dane uczenia się
        if os.path.exists(self.learning_system.learning_data_file):
            try:
                with open(self.learning_system.learning_data_file, 'r', encoding='utf-8') as f:
                    learning_data = json.load(f)
                print(f"📚 Dane uczenia się: {len(learning_data)} sesji przeanalizowanych")
                
                if learning_data:
                    latest = learning_data[-1]
                    print(f"📅 Ostatnia analiza: {latest.get('timestamp', 'N/A')}")
                    print(f"💬 Ostatnia sesja: {latest.get('session_id', 'N/A')}")
                    print(f"📝 Liczba wiadomości: {latest.get('total_messages', 0)}")
            except Exception as e:
                print(f"❌ Błąd wczytywania danych uczenia: {e}")
        else:
            print("⚠️  Brak danych uczenia się")
        
        # Sprawdź preferencje
        if os.path.exists(self.learning_system.preferences_file):
            try:
                with open(self.learning_system.preferences_file, 'r', encoding='utf-8') as f:
                    preferences = json.load(f)
                print(f"🎯 Preferencje użytkowników: {len(preferences)} sesji")
                
                # Podsumowanie preferencji
                total_examples = sum(1 for p in preferences.values() if p.get('prefers_examples', False))
                total_procedures = sum(1 for p in preferences.values() if p.get('prefers_procedures', False))
                total_theory = sum(1 for p in preferences.values() if p.get('prefers_theory', False))
                
                print(f"  📊 Preferują przykłady: {total_examples}/{len(preferences)}")
                print(f"  📋 Preferują procedury: {total_procedures}/{len(preferences)}")
                print(f"  🧠 Preferują teorię: {total_theory}/{len(preferences)}")
                
            except Exception as e:
                print(f"❌ Błąd wczytywania preferencji: {e}")
        else:
            print("⚠️  Brak zapisanych preferencji")
        
        # Sprawdź aktywne sesje
        history_dir = 'history'
        if os.path.exists(history_dir):
            sessions = [f for f in os.listdir(history_dir) if f.endswith('.json')]
            print(f"📁 Sesje w historii: {len(sessions)}")
            
            # Sprawdź ostatnie aktywne sesje
            active_sessions = []
            for session_file in sessions:
                session_path = os.path.join(history_dir, session_file)
                modified_time = datetime.fromtimestamp(os.path.getmtime(session_path))
                if datetime.now() - modified_time < timedelta(hours=24):
                    active_sessions.append(session_file)
            
            print(f"⚡ Aktywne sesje (24h): {len(active_sessions)}")
        
        print("="*60)
        print("✅ System uczenia się działa poprawnie")
        print("="*60 + "\n")
    
    def cleanup_old_data(self, days_old=30):
        """Usuwa stare dane uczenia się"""
        print(f"🧹 Czyszczenie danych starszych niż {days_old} dni...")
        
        cleanup_count = 0
        
        # Wyczyść stare dane uczenia się
        if os.path.exists(self.learning_system.learning_data_file):
            try:
                with open(self.learning_system.learning_data_file, 'r', encoding='utf-8') as f:
                    learning_data = json.load(f)
                
                cutoff_date = datetime.now() - timedelta(days=days_old)
                new_data = []
                
                for data in learning_data:
                    try:
                        data_date = datetime.fromisoformat(data.get('timestamp', ''))
                        if data_date > cutoff_date:
                            new_data.append(data)
                        else:
                            cleanup_count += 1
                    except:
                        # Zachowaj dane z nieprawidłową datą
                        new_data.append(data)
                
                if cleanup_count > 0:
                    with open(self.learning_system.learning_data_file, 'w', encoding='utf-8') as f:
                        json.dump(new_data, f, ensure_ascii=False, indent=2)
                    print(f"🗑️  Usunięto {cleanup_count} starych zapisów uczenia się")
                
            except Exception as e:
                print(f"❌ Błąd podczas czyszczenia danych uczenia: {e}")
        
        print("✅ Czyszczenie zakończone")

def main():
    """Główna funkcja skryptu"""
    monitor = LearningMonitor()
    
    print("🚀 Uruchamianie monitora systemu uczenia się...")
    
    # Wyświetl aktualny status
    monitor.print_learning_status()
    
    # Generuj raport
    print("📊 Generowanie raportu uczenia się...")
    report = monitor.generate_learning_report()
    
    # Wyświetl podsumowanie raportu
    print("\n📋 PODSUMOWANIE RAPORTU:")
    print(f"📊 Całkowita liczba sesji: {report['total_sessions']}")
    print(f"⚡ Aktywne sesje: {report['active_sessions']}")
    print(f"💡 Sugestie ulepszenia: {len(report['improvement_suggestions'])}")
    
    if report['improvement_suggestions']:
        print("\n🎯 SUGESTIE ULEPSZENIA:")
        for suggestion in report['improvement_suggestions']:
            priority_icon = "🔴" if suggestion['priority'] == 'high' else "🟡" if suggestion['priority'] == 'medium' else "🟢"
            print(f"  {priority_icon} {suggestion['message']}")
    
    # Opcjonalne czyszczenie starych danych
    print("\n🧹 Czy chcesz wyczyścić stare dane? (y/n): ", end="")
    choice = input().lower()
    if choice == 'y':
        monitor.cleanup_old_data()
    
    print("\n✅ Monitor zakończony pomyślnie!")

if __name__ == "__main__":
    main()
