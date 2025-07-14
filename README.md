# 🛩️ Aero-Chat - Asystent AI dla Branży Lotniczej

## 📋 Opis

Aero-Chat to zaawansowana aplikacja webowa służąca jako asystent AI dla branży lotniczej. Wykorzystuje OpenAI GPT-4o i Assistants API z technologią RAG (Retrieval-Augmented Generation) do udzielania precyzyjnych odpowiedzi na pytania związane z lotnictwem, aerodynamiką, przepisami lotniczymi, nawigacją i meteorologią.

## ✨ Funkcjonalności

### 🎯 Główne funkcje
- **Chat z AI w czasie rzeczywistym** - streaming odpowiedzi przez WebSocket
- **RAG z dokumentami PDF** - automatyczne wykorzystanie przesłanych podręczników lotniczych
- **🧠 System uczenia się** - asystent ciągle się uczy i dostosowuje do preferencji użytkownika
- **System feedbacku** - ocenianie odpowiedzi (👍/👎/✏️) w czasie rzeczywistym
- **Generowanie raportów PDF** - eksport odpowiedzi do dokumentów PDF
- **Panel administratora** - zarządzanie sesjami, feedbackiem i dokumentami
- **Automatyczne uczenie** - konwersja feedbacku na dane treningowe

### 🧠 System Uczenia się (NOWY!)
- **Adaptacja do preferencji** - asystent zapamiętuje jak użytkownik lubi otrzymywać odpowiedzi
- **Wzory i przykłady** - jeśli użytkownik prosi o "wzory i przykłady", asystent będzie je domyślnie dodawać
- **Kontekst uczenia się** - cała historia rozmów jest analizowana i uwzględniana
- **Progresywne dostosowywanie** - im więcej rozmów, tym lepsze dostosowanie
- **Analiza wzorców** - system wykrywa preferencje dotyczące szczegółowości, formatowania i stylu

### 🔧 Funkcje techniczne
- **Monitorowanie plików** - automatyczne wykrywanie nowych PDF-ów
- **Sesje użytkowników** - persistentna historia rozmów
- **Vector Store** - tymczasowe przechowywanie wektorów dla każdego zapytania
- **Cleanup zasobów** - automatyczne usuwanie tymczasowych plików

## 🏗️ Architektura

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   OpenAI API    │
│   (HTML/JS)     │◄──►│   (Flask)       │◄──►│  (GPT-4o + RAG) │
│                 │    │                 │    │                 │
│ • Chat UI       │    │ • WebSocket     │    │ • Assistants    │
│ • Real-time     │    │ • RAG Logic     │    │ • Vector Store  │
│ • Feedback      │    │ • PDF Upload    │    │ • File Search   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Static Files   │    │   Data Storage  │    │  External APIs  │
│                 │    │                 │    │                 │
│ • CSS/JS        │    │ • JSON Files    │    │ • ReportLab     │
│ • Images        │    │ • Upload Index  │    │ • Watchdog      │
│ • Templates     │    │ • Session Data  │    │ • Flask-SocketIO│
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Instalacja i Uruchomienie

### Wymagania
- Python 3.12+
- Klucz OpenAI API
- System operacyjny: Windows/Linux/macOS

### 1. Klonowanie repozytorium
```bash
git clone https://github.com/your-repo/aero-chat.git
cd aero-chat
```

### 2. Utworzenie środowiska wirtualnego
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate
```

### 3. Instalacja zależności
```bash
pip install -r requirements.txt
```

### 4. Konfiguracja zmiennych środowiskowych
Skopiuj plik `.env` i uzupełnij:

```bash
cp .env.example .env
```

Edytuj `.env`:
```env
# OpenAI API - WSTAW SWOJE KLUCZE!
OPENAI_API_KEY=sk-twoj-klucz-openai-tutaj
ASSISTANT_ID=asst-twoj-assistant-id-tutaj  # Zostanie utworzony automatycznie

# Pozostałe ustawienia są już skonfigurowane
FLASK_ENV=development
FLASK_APP=backend.app
SECRET_KEY=your-super-secret-key-change-this-in-production-12345
```

### 5. Utworzenie domyślnego administratora
```bash
python -c "from app.models import User; User.create_default_admin()"
```

### 6. Uruchomienie aplikacji

#### Standardowy start
```bash
python start.py
```

#### Uruchomienie z systemem uczenia się (ZALECANE)
```bash
./learning_menu.sh
```

#### Lub klasyczny sposób
```bash
python run.py
```

Aplikacja będzie dostępna pod adresem: `http://localhost:5000`

### 7. System uczenia się
Aby w pełni wykorzystać system uczenia się:

```bash
# Testuj system uczenia się
python test_learning_system.py

# Monitoruj uczenie się
python learning_monitor.py

# Uruchom harmonogram uczenia się w tle
python learning_scheduler.py
```

## 📁 Struktura Projektu

```
aero-chat/
├── 📄 run.py                      # Punkt startowy aplikacji
├── 📄 start.py                    # Zaawansowany start z systemem uczenia się
├── 📄 watcher.py                  # Watchdog dla monitorowania plików
├── 📄 trainer.py                  # Skrypt uczenia na feedbacku
├── 📄 learning_monitor.py         # Monitor systemu uczenia się
├── 📄 learning_scheduler.py       # Harmonogram uczenia się
├── 📄 test_learning_system.py     # Testy systemu uczenia się
├── 📄 learning_menu.sh            # Menu uruchamiania z systemem uczenia się
├── 📄 requirements.txt            # Zależności Python
├── 📄 .env                        # Zmienne środowiskowe
├── 📄 README.md                   # Dokumentacja
│
├── 📁 app/                        # Główny moduł aplikacji
│   ├── 📄 __init__.py            # Inicjalizacja Flask
│   ├── 📄 models.py              # Modele danych (JSON)
│   ├── 📄 routes.py              # Główne routes
│   ├── 📄 admin.py               # Panel administratora
│   └── 📄 socketio_handlers.py   # Obsługa WebSocket
│
├── 📁 utils/                      # Narzędzia pomocnicze
│   ├── 📄 __init__.py
│   ├── 📄 openai_rag.py          # Logika RAG z OpenAI
│   └── 📄 learning_system.py     # 🧠 System uczenia się (NOWY!)
│
├── 📁 templates/                  # Szablony HTML (Jinja2)
│   ├── 📄 base.html              # Szablon bazowy
│   ├── 📄 chat.html              # Interfejs czatu
│   └── 📁 admin/                 # Szablony panelu admin
│       ├── 📄 login.html
│       ├── 📄 dashboard.html
│       ├── 📄 users.html
│       ├── 📄 feedback.html
│       ├── 📄 documents.html
│       └── 📄 reports.html
│
├── 📁 static/                     # Pliki statyczne
│   ├── 📁 js/
│   │   └── 📄 chat.js            # Logika frontendowa
│   └── 📁 css/                   # (style w Tailwind CDN)
│
├── 📁 uploads/                    # Przesłane pliki PDF
├── 📁 history/                    # Historia czatów (JSON)
├── 📁 feedback/                   # Feedback użytkowników (JSON)
├── 📁 reports/                    # Wygenerowane raporty PDF
├── 📁 data/                       # Dane systemowe
└── 📁 training_data/              # Dane do fine-tuningu
```

## 🔧 Konfiguracja

### Zmienne środowiskowe
```env
# Flask
FLASK_ENV=development
FLASK_APP=backend.app
SECRET_KEY=your-secret-key

# OpenAI
OPENAI_API_KEY=sk-your-api-key
ASSISTANT_ID=asst-your-assistant-id

# Upload
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=16777216  # 16MB

# RAG
MAX_SELECTED_DOCUMENTS=10
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
```

### Domyślne dane logowania Admin
```
Login: admin
Hasło: admin123
```

## 🎮 Użytkowanie

### 1. Przesyłanie dokumentów
1. Kliknij przycisk "📁 Dodaj PDF" w interfejsie
2. Wybierz plik PDF z dokumentacją lotniczą
3. Plik zostanie automatycznie zindeksowany

### 2. Zadawanie pytań
1. Wpisz pytanie w polu czatu
2. System automatycznie wybierze najistotniejsze dokumenty
3. Odpowiedź będzie generowana w czasie rzeczywistym

### 3. Ocenianie odpowiedzi
- **👍** - Odpowiedź przydatna
- **👎** - Odpowiedź nieprzydatna  
- **✏️** - Prośba o rozwinięcie (z możliwością dodania komentarza)
- **📄** - Generowanie PDF z odpowiedzi

### 4. Panel administratora
Dostępny pod `/admin`:
- **Dashboard** - statystyki i wykresy
- **Użytkownicy** - sesje i aktywność
- **Feedback** - zebrany feedback z możliwością filtrowania
- **Dokumenty** - zarządzanie przesłanymi PDF-ami
- **Raporty** - pobieranie wygenerowanych PDF-ów

## 🔬 Uczenie na Feedbacku

### Generowanie danych treningowych
```bash
python trainer.py
```

Opcje:
1. **Generuj dane treningowe (JSONL)** - dla fine-tuningu
2. **Generuj raport feedbacku** - analiza zebranego feedbacku
3. **Oba** - pełne przetwarzanie

### Format danych wyjściowych
- `training_data/training_data_YYYYMMDD_HHMMSS.jsonl` - dane do fine-tuningu
- `training_data/feedback_report_YYYYMMDD_HHMMSS.json` - raport analityczny

## 🛠️ Rozwój i Dostosowanie

### Dodawanie nowych funkcji
1. **Nowe routes** - dodaj w `app/routes.py`
2. **Nowe szablony** - utwórz w `templates/`
3. **Nowe handlery WebSocket** - dodaj w `app/socketio_handlers.py`

### Dostosowanie asystenta AI
Edytuj instrukcje w `utils/openai_rag.py`:
```python
instructions = """Twoje instrukcje dla asystenta..."""
```

### Dodawanie nowych typów plików
Rozszerz `watcher.py` o obsługę innych formatów.

## 🐛 Troubleshooting

### Częste problemy

**1. Błąd "Import flask could not be resolved"**
```bash
# Sprawdź aktywację środowiska wirtualnego
pip install -r requirements.txt
```

**2. Błąd połączenia z OpenAI**
```bash
# Sprawdź klucz API w .env
export OPENAI_API_KEY=your-key
```

**3. Błędy WebSocket**
```bash
# Sprawdź czy port 5000 jest wolny
netstat -an | grep 5000
```

**4. Problemy z przesyłaniem plików**
```bash
# Sprawdź uprawnienia do katalogu uploads/
chmod 755 uploads/
```

### Logi debugowania
```bash
# Uruchom z debugiem
FLASK_ENV=development python run.py
```

## 📊 Monitorowanie

### Metryki systemowe
- Liczba aktywnych sesji
- Średni czas odpowiedzi
- Wykorzystanie dokumentów
- Rozkład feedbacku

### Pliki logów
- Historia czatów: `history/*.json`
- Feedback: `feedback/*.json`
- Indeks plików: `data/upload_index.json`

## 🔒 Bezpieczeństwo

### Najlepsze praktyki
1. **Zmień domyślne hasła** w produkcji
2. **Używaj HTTPS** w środowisku produkcyjnym
3. **Ogranicz rozmiar plików** (domyślnie 16MB)
4. **Regularne backupy** danych JSON

### Konfiguracja produkcyjna
```env
FLASK_ENV=production
SECRET_KEY=super-secure-random-key
JWT_SECRET_KEY=another-secure-key
```

## 🤝 Wsparcie

### Kontakt
- **GitHub Issues** - dla błędów i propozycji funkcji
- **Email** - support@aero-chat.com
- **Dokumentacja** - wiki w repozytorium

### Współpraca
1. Fork repozytorium
2. Utwórz branch funkcji
3. Dodaj testy
4. Wyślij Pull Request

## 📜 Licencja

MIT License - szczegóły w pliku `LICENSE`

## 🙏 Podziękowania

- **OpenAI** - za API Assistants i GPT-4o
- **Flask** - za framework webowy
- **Tailwind CSS** - za system stylów
- **ReportLab** - za generowanie PDF-ów

---

**Aero-Chat** - *Twój AI copilot w świecie lotnictwa* ✈️
