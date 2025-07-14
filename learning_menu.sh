#!/bin/bash
# -*- coding: utf-8 -*-
"""
Skrypt uruchamiający Aero-Chat z systemem uczenia się
"""

echo "🛩️  AERO-CHAT - SYSTEM UCZENIA SIĘ"
echo "=" * 50

echo "📋 Menu:"
echo "1. Uruchom aplikację (z systemem uczenia się)"
echo "2. Przetestuj system uczenia się"
echo "3. Pokaż status systemu uczenia się"
echo "4. Uruchom monitor uczenia się"
echo "5. Uruchom harmonogram uczenia się (background)"
echo "6. Wyczyść dane uczenia się"
echo "7. Zainstaluj/zaktualizuj zależności"
echo "0. Wyjście"
echo ""

read -p "Wybierz opcję (0-7): " choice

case $choice in
    1)
        echo "🚀 Uruchamianie aplikacji z systemem uczenia się..."
        python3 start.py
        ;;
    2)
        echo "🧪 Testowanie systemu uczenia się..."
        python3 test_learning_system.py
        ;;
    3)
        echo "📊 Sprawdzanie statusu systemu uczenia się..."
        python3 -c "from learning_monitor import LearningMonitor; LearningMonitor().print_learning_status()"
        ;;
    4)
        echo "🔍 Uruchamianie monitora uczenia się..."
        python3 learning_monitor.py
        ;;
    5)
        echo "⏰ Uruchamianie harmonogramu uczenia się w tle..."
        nohup python3 learning_scheduler.py > learning_scheduler.log 2>&1 &
        echo "✅ Harmonogram uruchomiony w tle (PID: $!)"
        echo "📋 Logi: tail -f learning_scheduler.log"
        ;;
    6)
        echo "🧹 Czyszczenie danych uczenia się..."
        read -p "Czy na pewno chcesz usunąć wszystkie dane uczenia się? (y/N): " confirm
        if [[ $confirm == [yY] ]]; then
            rm -f data/learning_data.json
            rm -f data/user_preferences.json
            rm -f data/user_patterns.json
            rm -f data/learning_report.json
            echo "✅ Dane uczenia się wyczyszczone"
        else
            echo "❌ Anulowano"
        fi
        ;;
    7)
        echo "📦 Instalowanie/aktualizowanie zależności..."
        pip3 install -r requirements.txt
        echo "✅ Zależności zainstalowane"
        ;;
    0)
        echo "👋 Do widzenia!"
        exit 0
        ;;
    *)
        echo "❌ Nieprawidłowa opcja"
        exit 1
        ;;
esac
