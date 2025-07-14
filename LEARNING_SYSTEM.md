# 🧠 System Uczenia Się Asystenta - Dokumentacja

## Przegląd

System uczenia się to zaawansowana funkcjonalność, która pozwala asystentowi Aero-Chat na ciągłe doskonalenie się na podstawie historii rozmów i preferencji użytkownika.

## Kluczowe Funkcje

### 1. Analiza Historii Rozmów
- **Automatyczna analiza**: Każda sesja czatu jest analizowana pod kątem wzorców użytkownika
- **Wykrywanie preferencji**: System identyfikuje czy użytkownik preferuje:
  - Przykłady i wzory
  - Procedury krok po kroku
  - Szczegółowe wyjaśnienia teoretyczne
  - Praktyczne zastosowania

### 2. System Uczenia Się
- **Adaptacja odpowiedzi**: Asystent dostosowuje styl odpowiedzi do preferencji użytkownika
- **Zapamiętywanie kontekstu**: Jeśli użytkownik prosi o "wzory i przykłady", system będzie domyślnie je dostarczać
- **Progresywne uczenie**: Im więcej rozmów, tym lepsze dostosowanie

### 3. Analiza Wzorców
System analizuje:
- **Słowa kluczowe**: Najczęściej używane terminy
- **Typy pytań**: Definicje, wyjaśnienia, procedury, porównania
- **Długość pytań**: Krótkie, średnie, długie
- **Tematy**: Aerodynamika, nawigacja, meteorologia, itp.
- **Strukturę odpowiedzi**: Preferowane formatowanie

## Implementacja

### Główne komponenty:

1. **LearningSystem** (`utils/learning_system.py`)
   - Główna klasa systemu uczenia się
   - Analizuje historie rozmów
   - Generuje preferencje użytkownika
   - Tworzy prompty uczenia się

2. **Integracja z OpenAI RAG** (`utils/openai_rag.py`)
   - Włączenie promptów uczenia się do zapytań
   - Adaptacja instrukcji asystenta
   - Kontekst uczenia się w każdej odpowiedzi

3. **Obsługa Feedbacku** (`app/socketio_handlers.py`)
   - Aktualizacja preferencji na podstawie feedbacku
   - Zapisywanie danych uczenia się
   - Analiza pozytywnego/negatywnego feedbacku

4. **Monitor Uczenia Się** (`learning_monitor.py`)
   - Generowanie raportów
   - Analiza globalnych wzorców
   - Czyszczenie starych danych

### Pliki danych:
- `data/learning_data.json` - Dane analiz sesji
- `data/user_patterns.json` - Wzorce użytkownika
- `data/user_preferences.json` - Preferencje użytkownika
- `data/learning_report.json` - Raporty uczenia się

## Jak działa uczenie się

### Przykład scenariusza:
1. **Użytkownik pyta**: "Jak działa siła nośna?"
2. **System analizuje**: Czy to pierwsze pytanie, czy kontynuacja rozmowy
3. **Asystent odpowiada**: Standardowa odpowiedź z podstawowymi informacjami
4. **Użytkownik pisze**: "Dawaj wzory i przykłady"
5. **System uczy się**: Zapisuje preferencję dla przykładów i wzorów
6. **Następne pytanie**: "Co to jest opór aerodynamiczny?"
7. **Asystent odpowiada**: Automatycznie dodaje wzory i przykłady!

### Mechanizm uczenia się:
```python
# Przykład promptu generowanego przez system uczenia się
KONTEKST UCZENIA UŻYTKOWNIKA:
Poziom szczegółowości: high
✅ Użytkownik preferuje PRZYKŁADY i WZORY - zawsze dodawaj praktyczne przykłady!
✅ Użytkownik preferuje PROCEDURY - przedstawiaj informacje krok po kroku!
Ostatnie tematy: aerodynamika, nawigacja, systemy
⚠️ OBOWIĄZKOWE: Zawsze dodawaj konkretne przykłady i wzory!
```

## API Endpoints

### `/api/learning_status`
Pobiera status systemu uczenia się dla aktualnej sesji:
```json
{
  "session_id": "abc123",
  "preferences": {
    "detail_level": "high",
    "prefers_examples": true,
    "prefers_procedures": true,
    "prefers_theory": true,
    "prefers_practical": true
  },
  "learning_data_count": 5,
  "has_learning_data": true,
  "system_active": true
}
```

### `/api/learning_report`
Generuje raport uczenia się:
```json
{
  "total_sessions": 25,
  "active_sessions": 3,
  "learning_patterns": {...},
  "improvement_suggestions": [
    {
      "type": "examples",
      "message": "Użytkownicy często proszą o przykłady",
      "priority": "high"
    }
  ]
}
```

## Uruchamianie

### Automatyczne uruchamianie
System uczenia się uruchamia się automatycznie przy starcie aplikacji:
```bash
python start.py
```

### Ręczne uruchamianie monitora
```bash
python learning_monitor.py
```

### Harmonogram (background)
```bash
python learning_scheduler.py
```

## Monitorowanie

### Sprawdzanie statusu
```bash
python -c "from learning_monitor import LearningMonitor; LearningMonitor().print_learning_status()"
```

### Generowanie raportów
```bash
python -c "from learning_monitor import LearningMonitor; LearningMonitor().generate_learning_report()"
```

## Konfiguracja

### Parametry uczenia się
- `max_docs=5` - Maksymalna liczba dokumentów do analizy
- `max_retries=3` - Maksymalna liczba prób przy generowaniu odpowiedzi
- `days_old=30` - Okres przechowywania danych uczenia się

### Dostosowywanie
System można dostosować modyfikując:
1. **Wzorce analizy** w `LearningSystem._categorize_request_types()`
2. **Priorytety uczenia** w `LearningSystem._determine_structure_preference()`
3. **Prompt templates** w `LearningSystem.generate_learning_prompt()`

## Bezpieczeństwo

- Dane uczenia się są przechowywane lokalnie
- Automatyczne czyszczenie starych danych
- Limit długości zapisywanych tekstów
- Brak przechowywania wrażliwych danych

## Monitoring i Maintenance

### Regularne zadania:
- **Co godzinę**: Analiza nowych sesji
- **Codziennie**: Generowanie raportów
- **Co tydzień**: Czyszczenie starych danych

### Logi:
- `🧠` - Operacje systemu uczenia się
- `📚` - Analiza danych
- `🎯` - Aktualizacje preferencji
- `📊` - Generowanie raportów

## Troubleshooting

### Problemy z uczeniem się:
1. **Brak danych uczenia się**: Sprawdź czy katalog `data/` istnieje
2. **Błędy analizy**: Sprawdź format plików JSON w `history/`
3. **Brak aktualizacji preferencji**: Sprawdź feedback handlers

### Resetowanie systemu:
```bash
rm -rf data/learning_data.json data/user_preferences.json data/user_patterns.json
```

## Przyszłe rozszerzenia

- **Uczenie się międzysesyjne**: Globalne wzorce dla wszystkich użytkowników
- **Analiza sentymentu**: Ocena zadowolenia użytkowników
- **Personalizacja UI**: Dostosowywanie interfejsu do preferencji
- **Eksport danych**: Możliwość eksportu danych uczenia się
- **Dashboard**: Interfejs webowy do monitorowania uczenia się

---

**Uwaga**: System uczenia się jest w pełni zgodny z RODO i nie przechowuje danych osobowych. Wszystkie dane są anonimizowane i używane wyłącznie do poprawy jakości odpowiedzi asystenta.
