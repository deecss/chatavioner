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
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime, timedelta
from utils.learning_reports import LearningReportsSystem

class ReportScheduler:
    """Scheduler dla automatycznego generowania raportów"""
    
    def __init__(self):
        self.reports_system = LearningReportsSystem()
        self.running = False
        self.thread = None
        
        # Konfiguracja email
        self.email_config = {
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'email_from': 'damian.szykut00@gmail.com',
            'email_to': 'biuro@avioner.pl',
            'app_password': 'fcib cmkr fnqd qsnx',  # Hasło aplikacji Gmail
            'email_enabled': True
        }
    
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
        
        # Konfiguracja harmonogramu
        # Codziennie o 2:00 - generowanie raportów
        schedule.every().day.at("02:00").do(self.generate_daily_report)
        
        # Codziennie o 20:00 - wysyłanie emaili
        schedule.every().day.at("20:00").do(self.send_daily_email_report)
        
        # Czyszczenie starych raportów co tydzień
        schedule.every().sunday.at("01:00").do(self.cleanup_old_reports)
        
        self.running = True
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
        
        print("✅ Scheduler raportów uruchomiony")
        print("📅 Harmonogram:")
        print("   - Generowanie raportów: codziennie o 2:00")
        print("   - Wysyłanie emaili: codziennie o 20:00")
        print("   - Czyszczenie starych raportów: w niedziele o 1:00")
    
    def stop(self):
        """Zatrzymuje scheduler"""
        if not self.running:
            print("📊 Scheduler raportów nie jest uruchomiony")
            return
        
        print("🛑 Zatrzymywanie schedulera raportów...")
        self.running = False
        schedule.clear()
        
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)
        
        print("✅ Scheduler raportów zatrzymany")
    
    def _run_scheduler(self):
        """Uruchamia pętlę schedulera"""
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Sprawdzaj co minutę
            except Exception as e:
                print(f"❌ Błąd schedulera: {e}")
                time.sleep(60)
    
    def generate_daily_report(self):
        """Generuje dzienny raport"""
        try:
            print("📊 Generowanie dziennego raportu...")
            
            # Generuj raport za wczorajszy dzień
            yesterday = datetime.now() - timedelta(days=1)
            report = self.reports_system.generate_daily_report(yesterday)
            
            print(f"✅ Raport wygenerowany: {report['report_id']}")
            print(f"📈 Aktywnych użytkowników: {report['summary']['total_users']}")
            print(f"❓ Zadano pytań: {report['summary']['total_questions']}")
            
        except Exception as e:
            print(f"❌ Błąd generowania raportu: {e}")
    
    def cleanup_old_reports(self):
        """Usuwa stare raporty (starsze niż 30 dni)"""
        try:
            print("🧹 Czyszczenie starych raportów...")
            
            reports_dir = 'reports'
            if not os.path.exists(reports_dir):
                print("📁 Brak katalogu raportów")
                return
            
            cutoff_date = datetime.now() - timedelta(days=30)
            deleted_count = 0
            
            for user_dir in os.listdir(reports_dir):
                user_path = os.path.join(reports_dir, user_dir)
                if os.path.isdir(user_path):
                    for report_file in os.listdir(user_path):
                        if report_file.endswith('.json'):
                            report_path = os.path.join(user_path, report_file)
                            try:
                                # Sprawdź datę modyfikacji pliku
                                mtime = datetime.fromtimestamp(os.path.getmtime(report_path))
                                if mtime < cutoff_date:
                                    os.remove(report_path)
                                    deleted_count += 1
                            except Exception as e:
                                print(f"❌ Błąd usuwania {report_path}: {e}")
            
            print(f"🗑️  Usunięto {deleted_count} starych raportów")
            
        except Exception as e:
            print(f"❌ Błąd czyszczenia raportów: {e}")
    
    def get_status(self):
        """Zwraca status schedulera"""
        return {
            'is_running': self.running,
            'scheduled_jobs': len(schedule.jobs),
            'email_enabled': self.email_config['email_enabled'],
            'next_report_time': self._get_next_job_time("generate_daily_report"),
            'next_email_time': self._get_next_job_time("send_daily_email_report"),
            'next_cleanup_time': self._get_next_job_time("cleanup_old_reports")
        }
    
    def _get_next_job_time(self, job_name):
        """Pobiera czas następnego uruchomienia zadania"""
        try:
            for job in schedule.jobs:
                if job.job_func.__name__ == job_name:
                    return job.next_run.strftime('%Y-%m-%d %H:%M:%S')
            return None
        except:
            return None
    
    def send_daily_email_report(self):
        """Wysyła dzienny raport emailem"""
        try:
            if not self.email_config['email_enabled']:
                print("📧 Wysyłanie emaili wyłączone")
                return
            
            print("📧 Wysyłanie dziennego raportu emailem...")
            
            # Wygeneruj raport za wczorajszy dzień
            yesterday = datetime.now() - timedelta(days=1)
            report = self.reports_system.generate_daily_report(yesterday)
            
            # Wyślij email z raportem
            self._send_email_report(report)
            
            print(f"✅ Raport wysłany emailem: {report['report_id']}")
            
        except Exception as e:
            print(f"❌ Błąd wysyłania emaila: {e}")
    
    def send_email_on_demand(self, report_date=None):
        """Wysyła raport emailem na żądanie"""
        try:
            if not self.email_config['email_enabled']:
                return {'success': False, 'error': 'Wysyłanie emaili wyłączone'}
            
            if report_date:
                date = datetime.strptime(report_date, '%Y-%m-%d')
            else:
                date = datetime.now() - timedelta(days=1)
            
            print(f"📧 Wysyłanie raportu emailem na żądanie za {date.strftime('%Y-%m-%d')}...")
            
            # Wygeneruj raport
            report = self.reports_system.generate_daily_report(date)
            
            # Wyślij email
            self._send_email_report(report)
            
            print(f"✅ Raport wysłany emailem: {report['report_id']}")
            return {'success': True, 'report_id': report['report_id']}
            
        except Exception as e:
            print(f"❌ Błąd wysyłania emaila na żądanie: {e}")
            return {'success': False, 'error': str(e)}
    
    def _send_email_report(self, report):
        """Wysyła email z raportem"""
        try:
            # Przygotuj dane raportu
            summary = report.get('summary', {})
            date = report.get('date', datetime.now().strftime('%Y-%m-%d'))
            
            # Utwórz wiadomość
            msg = MIMEMultipart()
            msg['From'] = self.email_config['email_from']
            msg['To'] = self.email_config['email_to']
            msg['Subject'] = f"📊 Dzienny raport Avioner AI - {date}"
            
            # Treść HTML
            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;">
                        📊 Dzienny raport Avioner AI Chat
                    </h2>
                    
                    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <h3 style="color: #2c3e50; margin-top: 0;">📅 Data: {date}</h3>
                        <p style="color: #7f8c8d; margin: 5px 0;">Raport wygenerowany: {report.get('generated_at', 'N/A')}</p>
                    </div>
                    
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 20px 0;">
                        <div style="background-color: #e8f5e8; padding: 15px; border-radius: 5px; text-align: center;">
                            <h4 style="color: #27ae60; margin: 0;">👥 Aktywni użytkownicy</h4>
                            <p style="font-size: 24px; font-weight: bold; margin: 10px 0; color: #2c3e50;">
                                {summary.get('total_users', 0)}
                            </p>
                        </div>
                        
                        <div style="background-color: #e8f4f8; padding: 15px; border-radius: 5px; text-align: center;">
                            <h4 style="color: #3498db; margin: 0;">❓ Zadano pytań</h4>
                            <p style="font-size: 24px; font-weight: bold; margin: 10px 0; color: #2c3e50;">
                                {summary.get('total_questions', 0)}
                            </p>
                        </div>
                        
                        <div style="background-color: #fff3e0; padding: 15px; border-radius: 5px; text-align: center;">
                            <h4 style="color: #f39c12; margin: 0;">📝 Otrzymano opinii</h4>
                            <p style="font-size: 24px; font-weight: bold; margin: 10px 0; color: #2c3e50;">
                                {summary.get('total_feedback', 0)}
                            </p>
                        </div>
                        
                        <div style="background-color: #f8e8f8; padding: 15px; border-radius: 5px; text-align: center;">
                            <h4 style="color: #9b59b6; margin: 0;">📈 Średnia pytań/użytkownik</h4>
                            <p style="font-size: 24px; font-weight: bold; margin: 10px 0; color: #2c3e50;">
                                {summary.get('avg_questions_per_user', 0):.1f}
                            </p>
                        </div>
                    </div>
                    
                    <div style="background-color: #f0f8ff; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <h4 style="color: #2c3e50; margin-top: 0;">👍 Wskaźnik pozytywnych opinii</h4>
                        <div style="background-color: #3498db; height: 20px; border-radius: 10px; position: relative;">
                            <div style="background-color: #27ae60; height: 100%; width: {summary.get('feedback_ratio', 0) * 100}%; border-radius: 10px; display: flex; align-items: center; justify-content: center;">
                                <span style="color: white; font-weight: bold; font-size: 12px;">
                                    {summary.get('feedback_ratio', 0):.1%}
                                </span>
                            </div>
                        </div>
                    </div>
                    
                    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <h4 style="color: #2c3e50; margin-top: 0;">🏆 Najaktywniejsze tematy</h4>
                        <ul style="list-style: none; padding: 0;">
            """
            
            # Dodaj najpopularniejsze tematy
            topic_distribution = report.get('topic_distribution', {})
            popular_topics = topic_distribution.get('most_popular_topics', [])[:5]
            
            print(f"🔍 Debug - popular_topics: {popular_topics}")
            
            if popular_topics:
                for topic, count in popular_topics:
                    html_body += f"""
                                <li style="background-color: white; margin: 5px 0; padding: 10px; border-radius: 3px; display: flex; justify-content: space-between;">
                                    <span style="color: #2c3e50;">{topic.title()}</span>
                                    <span style="background-color: #3498db; color: white; padding: 2px 8px; border-radius: 10px; font-size: 12px;">{count}</span>
                                </li>
                    """
            else:
                html_body += """
                            <li style="background-color: white; margin: 5px 0; padding: 10px; border-radius: 3px; color: #7f8c8d; font-style: italic;">
                                Brak danych o tematach w tym okresie
                            </li>
                """
            
            html_body += """
                        </ul>
                    </div>
                    
                    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <h4 style="color: #2c3e50; margin-top: 0;">❓ Przykładowe pytania według tematów</h4>
            """
            
            # Dodaj przykładowe pytania według tematów
            questions_by_topic = report.get('questions_analysis', {}).get('questions_by_topic', {})
            for topic, questions in list(questions_by_topic.items())[:3]:  # Top 3 tematy
                html_body += f"""
                        <div style="background-color: white; margin: 10px 0; padding: 10px; border-radius: 3px; border-left: 4px solid #3498db;">
                            <h5 style="color: #2c3e50; margin: 0 0 10px 0;">🎯 {topic.title()}</h5>
                            <ul style="list-style: none; padding: 0; margin: 0;">
                """
                
                for question in questions[:3]:  # Maksymalnie 3 pytania na temat
                    html_body += f"""
                                <li style="color: #555; margin: 5px 0; padding: 5px; background-color: #f9f9f9; border-radius: 3px;">
                                    • {question.get('content', '')[:150]}{'...' if len(question.get('content', '')) > 150 else ''}
                                </li>
                    """
                
                html_body += """
                            </ul>
                        </div>
                """
            
            html_body += """
                    </div>
                    
                    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <h4 style="color: #2c3e50; margin-top: 0;">🧑‍🎓 Szczegóły aktywności użytkowników</h4>
            """
            
            # Dodaj szczegóły użytkowników
            user_activity = report.get('user_activity', [])
            for user in user_activity[:5]:  # Top 5 użytkowników
                html_body += f"""
                        <div style="background-color: white; margin: 10px 0; padding: 10px; border-radius: 3px; border-left: 4px solid #27ae60;">
                            <h5 style="color: #2c3e50; margin: 0 0 10px 0;">👤 {user.get('username', 'Nieznany użytkownik')}</h5>
                            <div style="display: flex; gap: 15px; flex-wrap: wrap;">
                                <span style="background-color: #3498db; color: white; padding: 3px 8px; border-radius: 10px; font-size: 12px;">
                                    Pytania: {user.get('questions_count', 0)}
                                </span>
                                <span style="background-color: #e74c3c; color: white; padding: 3px 8px; border-radius: 10px; font-size: 12px;">
                                    Sesje: {user.get('sessions_count', 0)}
                                </span>
                                <span style="background-color: #f39c12; color: white; padding: 3px 8px; border-radius: 10px; font-size: 12px;">
                                    Feedback: {user.get('feedback_given', 0)}
                                </span>
                            </div>
                """
                
                # Dodaj przykładowe pytania użytkownika
                if user.get('detailed_activity'):
                    questions = [act for act in user.get('detailed_activity', []) if act.get('type') == 'question']
                    if questions:
                        html_body += f"""
                            <div style="margin-top: 10px;">
                                <h6 style="color: #666; margin: 5px 0;">Przykładowe pytania:</h6>
                                <ul style="list-style: none; padding: 0; margin: 0;">
                        """
                        for q in questions[:2]:  # Maksymalnie 2 pytania
                            html_body += f"""
                                    <li style="color: #777; margin: 3px 0; padding: 3px; background-color: #f9f9f9; border-radius: 3px; font-size: 11px;">
                                        {q.get('content_preview', '')[:100]}{'...' if len(q.get('content_preview', '')) > 100 else ''}
                                    </li>
                            """
                        html_body += """
                                </ul>
                            </div>
                        """
                
                html_body += """
                        </div>
                """
            
            html_body += """
                    </div>
                    
                    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <h4 style="color: #2c3e50; margin-top: 0;">🔄 Najnowsze pytania</h4>
                        <ul style="list-style: none; padding: 0;">
            """
            
            # Dodaj najnowsze pytania
            recent_questions = report.get('questions_analysis', {}).get('recent_questions', [])
            for question in recent_questions[-5:]:  # Ostatnie 5 pytań
                html_body += f"""
                            <li style="background-color: white; margin: 5px 0; padding: 10px; border-radius: 3px; border-left: 3px solid #9b59b6;">
                                <div style="color: #2c3e50; margin-bottom: 5px;">
                                    {question.get('content', '')[:200]}{'...' if len(question.get('content', '')) > 200 else ''}
                                </div>
                                <div style="font-size: 11px; color: #7f8c8d;">
                                    Użytkownik: {question.get('user_id', 'N/A')} | 
                                    Złożoność: {question.get('complexity', 'N/A')} | 
                                    Temat: {question.get('topic', 'N/A')}
                                </div>
                            </li>
                """
            
            html_body += """
                        </ul>
                    </div>
                    
                    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <h4 style="color: #2c3e50; margin-top: 0;">🎯 Ostatnie opinie</h4>
                        <ul style="list-style: none; padding: 0;">
            """
            
            # Dodaj ostatnie opinie
            recent_feedback = report.get('feedback_analysis', {}).get('recent_feedback', [])
            for feedback in recent_feedback[-3:]:  # Ostatnie 3 opinie
                feedback_color = '#27ae60' if feedback.get('type') == 'positive' else '#e74c3c'
                html_body += f"""
                            <li style="background-color: white; margin: 5px 0; padding: 10px; border-radius: 3px; border-left: 3px solid {feedback_color};">
                                <div style="color: #2c3e50; margin-bottom: 5px;">
                                    {feedback.get('type', 'N/A').upper()}: {feedback.get('comment', 'Brak komentarza')}
                                </div>
                                <div style="font-size: 11px; color: #7f8c8d;">
                                    Użytkownik: {feedback.get('user_id', 'N/A')} | 
                                    Ocena: {feedback.get('rating', 'N/A')}
                                </div>
                            </li>
                """
            
            html_body += """
                        </ul>
                    </div>
                    
                    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <h4 style="color: #2c3e50; margin-top: 0;">🎯 Ostatnie opinie</h4>
                        <ul style="list-style: none; padding: 0;">
            """
            
            # Dodaj ostatnie opinie
            recent_feedback = report.get('feedback_analysis', {}).get('recent_feedback', [])
            for feedback in recent_feedback[-3:]:  # Ostatnie 3 opinie
                feedback_color = '#27ae60' if feedback.get('type') == 'positive' else '#e74c3c'
                html_body += f"""
                            <li style="background-color: white; margin: 5px 0; padding: 10px; border-radius: 3px; border-left: 3px solid {feedback_color};">
                                <div style="color: #2c3e50; margin-bottom: 5px;">
                                    {feedback.get('type', 'N/A').upper()}: {feedback.get('comment', 'Brak komentarza')}
                                </div>
                                <div style="font-size: 11px; color: #7f8c8d;">
                                    Użytkownik: {feedback.get('user_id', 'N/A')} | 
                                    Ocena: {feedback.get('rating', 'N/A')}
                                </div>
                            </li>
                """
            
            html_body += """
                        </div>
                    </div>
                    
                    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <h4 style="color: #2c3e50; margin-top: 0;">🔥 Przykładowe pytania użytkowników</h4>
                        <div style="background-color: white; padding: 10px; border-radius: 3px;">
            """
            
            # Dodaj przykładowe pytania
            example_questions = report.get('example_questions', [])
            for i, question in enumerate(example_questions[:5]):  # Pokaż 5 przykładowych pytań
                question_text = question.get('question', 'Brak pytania')
                user_name = question.get('user', 'Anonimowy')
                timestamp = question.get('timestamp', 'N/A')
                
                html_body += f"""
                            <div style="border-left: 3px solid #3498db; padding-left: 15px; margin: 10px 0;">
                                <p style="margin: 0; color: #2c3e50; font-style: italic;">"{question_text}"</p>
                                <small style="color: #7f8c8d;">— {user_name} ({timestamp})</small>
                            </div>
                """
            
            html_body += """
                        </div>
                    </div>
                    
                    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                        <p style="color: #7f8c8d; font-size: 12px; margin: 0;">
                            Ten raport został wygenerowany automatycznie przez system Avioner AI Chat.<br>
                            Aby uzyskać więcej informacji, zaloguj się do panelu administracyjnego.
                        </p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Dodaj treść HTML
            msg.attach(MIMEText(html_body, 'html', 'utf-8'))
            
            # Dodaj raport jako załącznik JSON
            report_json = str(report).encode('utf-8')
            attachment = MIMEBase('application', 'octet-stream')
            attachment.set_payload(report_json)
            encoders.encode_base64(attachment)
            attachment.add_header(
                'Content-Disposition',
                f'attachment; filename="raport_{date}.json"'
            )
            msg.attach(attachment)
            
            # Wyślij email
            server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'])
            server.starttls()
            server.login(self.email_config['email_from'], self.email_config['app_password'])
            
            text = msg.as_string()
            server.sendmail(self.email_config['email_from'], self.email_config['email_to'], text)
            server.quit()
            
            print(f"✅ Email wysłany pomyślnie do {self.email_config['email_to']}")
            
        except Exception as e:
            print(f"❌ Błąd wysyłania emaila: {e}")
            raise e
    
    def set_email_config(self, config):
        """Ustawia konfigurację email"""
        self.email_config.update(config)
        print(f"✅ Konfiguracja email zaktualizowana")
    
    def get_email_config(self):
        """Pobiera konfigurację email (bez hasła)"""
        config = self.email_config.copy()
        config['app_password'] = '***'  # Ukryj hasło
        return config
    
    def test_email_sending(self):
        """Test wysyłania emaila"""
        try:
            print("🧪 Test wysyłania emaila...")
            
            # Wygeneruj testowy raport
            today = datetime.now()
            report = self.reports_system.generate_daily_report(today)
            
            # Wyślij email
            self._send_email_report(report)
            
            print("✅ Test emaila zakończony pomyślnie")
            return True
            
        except Exception as e:
            print(f"❌ Błąd testu emaila: {e}")
            return False
    
    def get_report_details(self, report_id: str):
        """Pobiera szczegóły konkretnego raportu"""
        try:
            reports = self.reports_system.get_available_reports()
            
            for report in reports:
                if report.get('report_id') == report_id:
                    return report
            
            return None
        except Exception as e:
            print(f"❌ Błąd pobierania szczegółów raportu: {e}")
            return None
    
    def delete_report(self, report_id: str):
        """Usuwa raport"""
        try:
            return self.reports_system.delete_report(report_id)
        except Exception as e:
            print(f"❌ Błąd usuwania raportu: {e}")
            return False
    
    def send_specific_report_email(self, report_id: str):
        """Wysyła konkretny raport emailem"""
        try:
            report = self.get_report_details(report_id)
            if not report:
                return {
                    'success': False,
                    'message': 'Raport nie znaleziony'
                }
            
            # Wyślij email
            self._send_email_report(report)
            
            return {
                'success': True,
                'message': f'Raport {report_id} wysłany emailem'
            }
        except Exception as e:
            print(f"❌ Błąd wysyłania raportu emailem: {e}")
            return {
                'success': False,
                'message': str(e)
            }
    
    def generate_report_on_demand(self, date_str: str = None, report_type: str = 'daily'):
        """Generuje raport na żądanie"""
        try:
            if date_str:
                date = datetime.strptime(date_str, '%Y-%m-%d')
            else:
                date = datetime.now()
            
            print(f"📊 Generowanie raportu na żądanie za {date.strftime('%Y-%m-%d')}...")
            
            if report_type == 'daily':
                report = self.reports_system.generate_daily_report(date)
            elif report_type == 'weekly':
                report = self.reports_system.generate_weekly_report(date)
            elif report_type == 'monthly':
                report = self.reports_system.generate_monthly_report(date)
            else:
                report = self.reports_system.generate_daily_report(date)
            
            print(f"✅ Raport wygenerowany: {report['report_id']}")
            return {
                'success': True,
                'report_id': report['report_id'],
                'message': 'Raport wygenerowany pomyślnie'
            }
            
        except Exception as e:
            print(f"❌ Błąd generowania raportu na żądanie: {e}")
            return {
                'success': False,
                'message': str(e)
            }
    
    def get_scheduler_status(self):
        """Pobiera status schedulera"""
        try:
            return {
                'running': self.running,
                'email_enabled': self.email_config.get('email_enabled', False),
                'scheduled_jobs': len(schedule.jobs),
                'last_report_time': None,
                'next_report_time': self._get_next_job_time('generate_daily_report'),
                'next_email_time': self._get_next_job_time('send_daily_email_report')
            }
        except Exception as e:
            print(f"❌ Błąd pobierania statusu schedulera: {e}")
            return {
                'running': False,
                'email_enabled': False,
                'scheduled_jobs': 0,
                'last_report_time': None,
                'next_report_time': None,
                'next_email_time': None
            }


# Globalne zmienne dla instancji schedulera
_scheduler = None

def get_report_scheduler():
    """Zwraca globalną instancję schedulera"""
    global _scheduler
    if _scheduler is None:
        _scheduler = ReportScheduler()
    return _scheduler

def start_report_scheduler():
    """Uruchamia scheduler raportów"""
    global _scheduler
    if _scheduler is None:
        _scheduler = ReportScheduler()
    _scheduler.start()
    return _scheduler

def stop_report_scheduler():
    """Zatrzymuje scheduler raportów"""
    global _scheduler
    if _scheduler is not None:
        _scheduler.stop()
        _scheduler = None

def get_scheduler():
    """Alias dla get_report_scheduler"""
    return get_report_scheduler()

def restart_scheduler():
    """Restartuje scheduler"""
    stop_report_scheduler()
    return start_report_scheduler()

def is_scheduler_running():
    """Sprawdza czy scheduler jest uruchomiony"""
    global _scheduler
    return _scheduler is not None and _scheduler.running