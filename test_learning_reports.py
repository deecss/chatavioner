#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script dla systemu raportów uczenia się
"""
import sys
import os
from datetime import datetime, timedelta

# Dodaj path do modułów
sys.path.append('.')

def test_learning_reports():
    """Test podstawowej funkcjonalności raportów uczenia się"""
    try:
        from utils.learning_reports import LearningReportsSystem
        
        print("🧪 Testowanie systemu raportów uczenia się...")
        
        # Inicjalizuj system
        reports_system = LearningReportsSystem()
        
        # Test 1: Generowanie raportu
        print("\n1. Test generowania raportu...")
        report = reports_system.generate_daily_report(datetime.now())
        
        if report:
            print(f"✅ Raport wygenerowany: {report['report_id']}")
            print(f"📊 Użytkownicy: {report['summary']['total_users']}")
            print(f"❓ Pytania: {report['summary']['total_questions']}")
            print(f"💬 Feedback: {report['summary']['total_feedback']}")
        else:
            print("❌ Nie udało się wygenerować raportu")
            return False
        
        # Test 2: Lista raportów
        print("\n2. Test pobierania listy raportów...")
        available_reports = reports_system.get_available_reports()
        print(f"📋 Znaleziono {len(available_reports)} raportów")
        
        # Test 3: Pobieranie konkretnego raportu
        print("\n3. Test pobierania konkretnego raportu...")
        if available_reports:
            report_id = available_reports[0]['report_id']
            detailed_report = reports_system.get_report(report_id)
            
            if detailed_report:
                print(f"✅ Szczegóły raportu pobrane: {detailed_report['date']}")
            else:
                print("❌ Nie udało się pobrać szczegółów raportu")
        
        print("\n✅ Wszystkie testy systemu raportów przeszły pomyślnie!")
        return True
        
    except Exception as e:
        print(f"❌ Błąd podczas testowania: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_aviation_filtering():
    """Test filtrowania tematyki lotniczej z kontekstem"""
    try:
        from utils.openai_rag import OpenAIRAG
        
        print("\n🧪 Testowanie filtrowania tematyki lotniczej...")
        
        # Inicjalizuj system
        rag = OpenAIRAG()
        
        # Test 1: Bezpośrednie pytanie lotnicze
        print("\n1. Test bezpośredniego pytania lotniczego...")
        query1 = "co to jest siła nośna"
        result1 = rag.is_aviation_related_with_context(query1, [])
        print(f"   Pytanie: '{query1}' -> {result1}")
        
        # Test 2: Pytanie follow-up z kontekstem lotniczym
        print("\n2. Test pytania follow-up z kontekstem lotniczym...")
        aviation_context = [
            {"role": "user", "content": "jakie są rodzaje oblodzenia"},
            {"role": "assistant", "content": "W lotnictwie wyróżniamy trzy główne rodzaje oblodzenia: rime icing, clear icing i mixed icing..."}
        ]
        query2 = "który z nich jest najniebezpieczniejszy"
        result2 = rag.is_aviation_related_with_context(query2, aviation_context)
        print(f"   Pytanie: '{query2}' -> {result2}")
        
        # Test 3: Pytanie nie-lotnicze bez kontekstu
        print("\n3. Test pytania nie-lotniczego bez kontekstu...")
        query3 = "jak ugotować makaron"
        result3 = rag.is_aviation_related_with_context(query3, [])
        print(f"   Pytanie: '{query3}' -> {result3}")
        
        # Test 4: Pytanie nie-lotnicze z kontekstem lotniczym
        print("\n4. Test pytania nie-lotniczego z kontekstem lotniczym...")
        query4 = "jak ugotować makaron"
        result4 = rag.is_aviation_related_with_context(query4, aviation_context)
        print(f"   Pytanie: '{query4}' -> {result4}")
        
        # Sprawdź wyniki
        if result1 and result2 and not result3 and not result4:
            print("\n✅ Wszystkie testy filtrowania przeszły pomyślnie!")
            return True
        else:
            print(f"\n❌ Błąd w testach filtrowania: {result1}, {result2}, {result3}, {result4}")
            return False
        
    except Exception as e:
        print(f"❌ Błąd podczas testowania filtrowania: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_scheduler():
    """Test podstawowej funkcjonalności schedulera"""
    try:
        from utils.reports_scheduler import ReportScheduler
        
        print("\n🧪 Testowanie schedulera raportów...")
        
        # Inicjalizuj scheduler
        scheduler = ReportScheduler()
        
        # Test generowania raportu na żądanie
        print("\n1. Test generowania raportu na żądanie...")
        report = scheduler.generate_report_on_demand()
        
        if report:
            print(f"✅ Raport na żądanie wygenerowany: {report['report_id']}")
            return True
        else:
            print("❌ Nie udało się wygenerować raportu na żądanie")
            return False
        
    except Exception as e:
        print(f"❌ Błąd podczas testowania schedulera: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Uruchamianie testów systemu raportów uczenia się...")
    print("=" * 60)
    
    # Uruchom wszystkie testy
    tests_passed = 0
    total_tests = 3
    
    if test_learning_reports():
        tests_passed += 1
    
    if test_aviation_filtering():
        tests_passed += 1
    
    if test_scheduler():
        tests_passed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Wyniki testów: {tests_passed}/{total_tests} przeszło pomyślnie")
    
    if tests_passed == total_tests:
        print("🎉 Wszystkie testy przeszły pomyślnie!")
        sys.exit(0)
    else:
        print("❌ Niektóre testy nie powiodły się")
        sys.exit(1)
