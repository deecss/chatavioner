#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skrypt testowy demonstrujący działanie systemu uczenia się
"""
import os
import json
import time
from datetime import datetime
from utils.learning_system import LearningSystem
from app.models import ChatSession

def create_test_session():
    """Tworzy przykładową sesję testową"""
    session_id = "test_learning_session"
    
    # Symuluj historię rozmowy
    test_messages = [
        {"role": "user", "content": "Jak działa siła nośna?", "timestamp": datetime.now().isoformat()},
        {"role": "assistant", "content": "<h2>Siła nośna</h2><p>Siła nośna to jedna z podstawowych sił...</p>", "timestamp": datetime.now().isoformat()},
        {"role": "user", "content": "Dawaj wzory i przykłady", "timestamp": datetime.now().isoformat()},
        {"role": "assistant", "content": "<h2>Wzory i przykłady siły nośnej</h2><p>Wzór: L = CL × ρ × V² × S</p><p>Przykład: Dla samolotu Cessna 172...</p>", "timestamp": datetime.now().isoformat()},
        {"role": "user", "content": "Co to jest opór aerodynamiczny?", "timestamp": datetime.now().isoformat()},
        {"role": "assistant", "content": "<h2>Opór aerodynamiczny</h2><p>Wzór: D = CD × ρ × V² × S</p><p>Przykład praktyczny: Podczas lotu...</p>", "timestamp": datetime.now().isoformat()},
        {"role": "user", "content": "Jakie są procedury startowe?", "timestamp": datetime.now().isoformat()},
        {"role": "assistant", "content": "<h2>Procedury startowe</h2><ol><li>Sprawdzenie przed startem</li><li>Ustawienie klap</li><li>Sprawdzenie silnika</li></ol>", "timestamp": datetime.now().isoformat()},
        {"role": "user", "content": "Pokażesz mi jeszcze więcej przykładów?", "timestamp": datetime.now().isoformat()},
        {"role": "assistant", "content": "<h2>Dodatkowe przykłady</h2><p>Przykład 1: Boeing 747...</p><p>Przykład 2: Airbus A320...</p>", "timestamp": datetime.now().isoformat()},
    ]
    
    # Zapisz testową sesję
    chat_session = ChatSession(session_id)
    
    # Usuń istniejący plik testowy
    if os.path.exists(chat_session.history_file):
        os.remove(chat_session.history_file)
    
    # Dodaj wiadomości po kolei
    for msg in test_messages:
        chat_session.save_message(msg["content"], msg["role"])
        time.sleep(0.1)  # Małe opóźnienie
    
    print(f"✅ Utworzono testową sesję: {session_id}")
    return session_id

def test_learning_analysis():
    """Testuje analizę systemu uczenia się"""
    print("\n🧪 TESTOWANIE ANALIZY SYSTEMU UCZENIA SIĘ")
    print("=" * 50)
    
    # Utwórz system uczenia się
    learning_system = LearningSystem()
    
    # Utwórz testową sesję
    session_id = create_test_session()
    
    # Przeanalizuj sesję
    print(f"🔍 Analizuję sesję: {session_id}")
    analysis = learning_system.analyze_conversation_history(session_id)
    
    if analysis:
        print("📊 WYNIKI ANALIZY:")
        print(f"   Całkowita liczba wiadomości: {analysis['total_messages']}")
        print(f"   Wykryte wzorce użytkownika: {len(analysis['user_patterns'])}")
        print(f"   Progresja tematów: {analysis['topic_progression']}")
        
        # Pokaż słowa kluczowe
        keywords = analysis['user_patterns'].get('common_keywords', [])
        print(f"   Najczęstsze słowa kluczowe: {keywords[:5]}")
        
        # Pokaż typy pytań
        question_types = analysis['question_types']
        print(f"   Typy pytań: {question_types}")
        
        # Pokaż preferencje
        preferences = learning_system.get_user_preferences(session_id)
        print(f"   Preferuje przykłady: {preferences['prefers_examples']}")
        print(f"   Preferuje procedury: {preferences['prefers_procedures']}")
        print(f"   Preferuje teorię: {preferences['prefers_theory']}")
        print(f"   Poziom szczegółowości: {preferences['detail_level']}")
        
        # Zapisz dane uczenia się
        learning_system.save_learning_data(analysis)
        print("💾 Dane uczenia się zapisane")
        
    else:
        print("❌ Nie udało się przeanalizować sesji")
    
    return session_id

def test_learning_prompt():
    """Testuje generowanie promptu uczenia się"""
    print("\n🎯 TESTOWANIE GENEROWANIA PROMPTU UCZENIA SIĘ")
    print("=" * 50)
    
    learning_system = LearningSystem()
    session_id = "test_learning_session"
    
    # Wygeneruj prompt uczenia się
    prompt = learning_system.generate_learning_prompt(session_id, "Jak działa silnik turbinowy?")
    
    print("🧠 WYGENEROWANY PROMPT:")
    print("-" * 30)
    print(prompt)
    print("-" * 30)
    
    # Sprawdź czy prompt zawiera odpowiednie informacje
    if "PRZYKŁADY" in prompt:
        print("✅ Prompt zawiera informacje o preferencji przykładów")
    if "PROCEDURY" in prompt:
        print("✅ Prompt zawiera informacje o preferencji procedur")
    if "OBOWIĄZKOWE" in prompt:
        print("✅ Prompt zawiera obowiązkowe instrukcje")
    
    return prompt

def test_feedback_learning():
    """Testuje uczenie się na podstawie feedbacku"""
    print("\n👍 TESTOWANIE UCZENIA SIĘ Z FEEDBACKU")
    print("=" * 50)
    
    learning_system = LearningSystem()
    session_id = "test_learning_session"
    
    # Symuluj pozytywny feedback na przykłady
    feedback_data = {
        'feedback': 'positive',
        'section_type': 'example',
        'content': 'świetny przykład z wzorami',
        'timestamp': datetime.now().isoformat()
    }
    
    print("📝 Symulacja pozytywnego feedbacku na przykłady...")
    learning_system.update_preferences_from_feedback(session_id, feedback_data)
    
    # Pobierz zaktualizowane preferencje
    preferences = learning_system.get_user_preferences(session_id)
    print(f"🎯 Zaktualizowane preferencje:")
    print(f"   Preferuje przykłady: {preferences['prefers_examples']}")
    print(f"   Preferuje procedury: {preferences['prefers_procedures']}")
    print(f"   Preferuje teorię: {preferences['prefers_theory']}")
    
    # Sprawdź czy preferencje zostały zaktualizowane
    if preferences['prefers_examples']:
        print("✅ System nauczył się, że użytkownik preferuje przykłady!")
    else:
        print("❌ System nie zaktualizował preferencji")

def test_global_patterns():
    """Testuje analizę globalnych wzorców"""
    print("\n🌐 TESTOWANIE GLOBALNYCH WZORCÓW")
    print("=" * 50)
    
    learning_system = LearningSystem()
    
    # Wygeneruj globalne wzorce
    global_patterns = learning_system.analyze_all_sessions()
    
    print("📊 GLOBALNE WZORCE:")
    print(f"   Całkowita liczba sesji: {global_patterns.get('total_sessions', 0)}")
    print(f"   Popularne tematy: {dict(global_patterns.get('popular_topics', {}))}")
    print(f"   Preferowane struktury: {dict(global_patterns.get('preferred_structures', {}))}")
    
    # Pokaż najczęstsze słowa kluczowe
    common_keywords = global_patterns.get('common_keywords', {})
    if common_keywords:
        top_keywords = dict(list(common_keywords.items())[:10])
        print(f"   Najczęstsze słowa kluczowe: {top_keywords}")

def cleanup_test_data():
    """Czyści dane testowe"""
    print("\n🧹 CZYSZCZENIE DANYCH TESTOWYCH")
    print("=" * 50)
    
    # Usuń testową sesję
    test_session_file = "history/test_learning_session.json"
    if os.path.exists(test_session_file):
        os.remove(test_session_file)
        print("🗑️  Usunięto testową sesję")
    
    # Opcjonalnie wyczyść inne dane testowe
    print("✅ Czyszczenie zakończone")

def main():
    """Główna funkcja testowa"""
    print("🚀 URUCHAMIANIE TESTÓW SYSTEMU UCZENIA SIĘ")
    print("=" * 60)
    
    try:
        # Test 1: Analiza sesji
        session_id = test_learning_analysis()
        
        # Test 2: Generowanie promptu
        prompt = test_learning_prompt()
        
        # Test 3: Uczenie się z feedbacku
        test_feedback_learning()
        
        # Test 4: Globalne wzorce
        test_global_patterns()
        
        print("\n🎉 WSZYSTKIE TESTY ZAKOŃCZONE POMYŚLNIE!")
        print("=" * 60)
        
        # Opcjonalne czyszczenie
        print("\n🧹 Czy chcesz wyczyścić dane testowe? (y/n): ", end="")
        choice = input().lower()
        if choice == 'y':
            cleanup_test_data()
        
    except Exception as e:
        print(f"\n❌ BŁĄD PODCZAS TESTÓW: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
