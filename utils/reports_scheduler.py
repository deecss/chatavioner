#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Harmonogram generowania raportów uczenia się
Automatyczne generowanie dziennych raportów i czyszczenie starych plików
"""
import os
import sys
import time
import schedule
import threading
from datetime import datetime, timedelta
from utils.learning_reports import LearningReportsSystem

class ReportScheduler:
    """Scheduler dla automatycznego generowania raportów"""
    
    def __init__(self):
        self.reports_system = LearningReportsSystem()
        self.running = False
        self.thread = None
    
    @property
    def is_running(self):
        """Zwraca status schedulera"""
        return self.running
    
    def start(self):
        """Uruchamia scheduler"""
        if self.running:
            print("📊 Scheduler raportów już działa")
            return
        
        print("🚀 Uruchamianie schedulera raportów...")
        
        # Zaplanuj zadania
        schedule.every().day.at("02:00").do(self.generate_daily_report)
        schedule.every().week.at("03:00").do(self.cleanup_old_reports)
        
        # Dodaj zadanie testowe (uruchomi się za 1 minutę)
        schedule.every(1).minutes.do(self.test_report_generation)
        
        self.running = True
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
        
        print("✅ Scheduler raportów uruchomiony")
        print("📅 Dzienny raport: codziennie o 02:00")
        print("🧹 Czyszczenie: co tydzień o 03:00")
        print("🧪 Test: za 1 minutę")
    
    def stop(self):
        """Zatrzymuje scheduler"""
        if not self.running:
            return
        
        print("⏹️  Zatrzymywanie schedulera raportów...")
        self.running = False
        
        if self.thread:
            self.thread.join(timeout=5)
        
        schedule.clear()
        print("✅ Scheduler raportów zatrzymany")
    
    def _run_scheduler(self):
        """Główna pętla schedulera"""
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Sprawdzaj co minutę
            except Exception as e:
                print(f"❌ Błąd w schedulerze raportów: {e}")
                time.sleep(60)
    
    def generate_daily_report(self):
        """Generuje dzienny raport"""
        try:
            print("📊 Generowanie dziennego raportu...")
            
            # Generuj raport za wczorajszy dzień
            yesterday = datetime.now() - timedelta(days=1)
            report = self.reports_system.generate_daily_report(yesterday)
            
            # Wyślij powiadomienie (opcjonalnie)
            self._send_notification(report)
            
            print(f"✅ Dzienny raport wygenerowany: {report['report_id']}")
            
        except Exception as e:
            print(f"❌ Błąd generowania dziennego raportu: {e}")
    
    def cleanup_old_reports(self):
        """Czyści stare raporty"""
        try:
            print("🧹 Czyszczenie starych raportów...")
            self.reports_system.cleanup_old_reports(days_to_keep=30)
            print("✅ Stare raporty wyczyszczone")
            
        except Exception as e:
            print(f"❌ Błąd czyszczenia raportów: {e}")
    
    def test_report_generation(self):
        """Test generowania raportu (uruchomi się raz)"""
        try:
            print("🧪 Test generowania raportu...")
            
            # Generuj raport za dziś
            today = datetime.now()
            report = self.reports_system.generate_daily_report(today)
            
            print(f"✅ Test zakończony pomyślnie: {report['report_id']}")
            
            # Usuń to zadanie po pierwszym uruchomieniu
            schedule.clear('test_report_generation')
            
        except Exception as e:
            print(f"❌ Błąd testu raportu: {e}")
    
    def _send_notification(self, report):
        """Wysyła powiadomienie o wygenerowanym raporcie"""
        try:
            # Tutaj można dodać integrację z emailem, Slack, itp.
            summary = report.get('summary', {})
            
            notification = f"""
📊 Dzienny raport uczenia się - {report['date']}

👥 Aktywnych użytkowników: {summary.get('total_users', 0)}
❓ Zadano pytań: {summary.get('total_questions', 0)}
📝 Otrzymano opinii: {summary.get('total_feedback', 0)}
📈 Średnia pytań na użytkownika: {summary.get('avg_questions_per_user', 0):.1f}
👍 Wskaźnik pozytywnych opinii: {summary.get('feedback_ratio', 0):.1%}
            """
            
            print(notification)
            
            # Opcjonalnie zapisz do pliku powiadomień
            notifications_file = "data/notifications.log"
            with open(notifications_file, 'a', encoding='utf-8') as f:
                f.write(f"{datetime.now().isoformat()}: {notification}\n")
            
        except Exception as e:
            print(f"⚠️  Błąd wysyłania powiadomienia: {e}")
    
    def generate_report_on_demand(self, date_str: str = None):
        """Generuje raport na żądanie"""
        try:
            if date_str:
                date = datetime.strptime(date_str, '%Y-%m-%d')
            else:
                date = datetime.now()
            
            print(f"📊 Generowanie raportu na żądanie za {date.strftime('%Y-%m-%d')}...")
            
            report = self.reports_system.generate_daily_report(date)
            
            print(f"✅ Raport wygenerowany: {report['report_id']}")
            return report
            
        except Exception as e:
            print(f"❌ Błąd generowania raportu na żądanie: {e}")
            return None

# Globalny scheduler
report_scheduler = None

def start_report_scheduler():
    """Uruchamia globalny scheduler raportów"""
    global report_scheduler
    
    if report_scheduler is None:
        report_scheduler = ReportScheduler()
    
    report_scheduler.start()

def stop_report_scheduler():
    """Zatrzymuje globalny scheduler raportów"""
    global report_scheduler
    
    if report_scheduler:
        report_scheduler.stop()

def get_report_scheduler():
    """Pobiera instancję schedulera"""
    global report_scheduler
    return report_scheduler

# Uruchom scheduler jeśli ten plik jest wykonywany bezpośrednio
if __name__ == "__main__":
    try:
        scheduler = ReportScheduler()
        scheduler.start()
        
        print("🔄 Scheduler działa... Naciśnij Ctrl+C aby zatrzymać")
        
        while True:
            time.sleep(1)
    
    except KeyboardInterrupt:
        print("\n⏹️  Zatrzymywanie schedulera...")
        scheduler.stop()
        sys.exit(0)
    except Exception as e:
        print(f"❌ Błąd: {e}")
        sys.exit(1)
