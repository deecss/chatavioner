#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zadanie cron do regularnego uruchamiania monitora uczenia się
"""
import os
import sys
import schedule
import time
from datetime import datetime

# Dodaj ścieżkę do głównego katalogu projektu
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from learning_monitor import LearningMonitor

def run_learning_analysis():
    """Uruchamia analizę systemu uczenia się"""
    try:
        print(f"\n🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Uruchamianie analizy uczenia się...")
        
        monitor = LearningMonitor()
        
        # Generuj raport
        report = monitor.generate_learning_report()
        
        # Wyświetl podsumowanie
        print(f"📊 Przeanalizowano {report['total_sessions']} sesji")
        print(f"⚡ Aktywne sesje: {report['active_sessions']}")
        print(f"💡 Sugestie ulepszenia: {len(report['improvement_suggestions'])}")
        
        # Wyczyść stare dane raz w tygodniu
        if datetime.now().weekday() == 6:  # Niedziela
            print("🧹 Cotygodniowe czyszczenie danych...")
            monitor.cleanup_old_data(days_old=30)
        
        print("✅ Analiza uczenia się zakończona pomyślnie")
        
    except Exception as e:
        print(f"❌ Błąd podczas analizy uczenia się: {e}")

def main():
    """Główna funkcja harmonogramu"""
    print("🚀 Uruchamianie harmonogramu systemu uczenia się...")
    
    # Zaplanuj regularne uruchomienia
    schedule.every().hour.do(run_learning_analysis)  # Co godzinę
    schedule.every().day.at("02:00").do(run_learning_analysis)  # Codziennie o 2:00
    schedule.every().sunday.at("03:00").do(run_learning_analysis)  # W niedziele o 3:00
    
    print("⏰ Harmonogram ustawiony:")
    print("  - Co godzinę: szybka analiza")
    print("  - Codziennie o 2:00: pełna analiza")
    print("  - W niedziele o 3:00: analiza + czyszczenie")
    
    # Uruchom pierwsze analizy
    print("\n🎯 Uruchamianie pierwszej analizy...")
    run_learning_analysis()
    
    # Główna pętla
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Sprawdzaj co minutę
    except KeyboardInterrupt:
        print("\n🛑 Zatrzymywanie harmonogramu...")
        print("✅ Harmonogram zatrzymany")

if __name__ == "__main__":
    main()
