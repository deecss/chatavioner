# 📁 Struktura Projektu Aero-Chat

## 🗂️ Kompletna Struktura Katalogów

```
aero-chat/
├── 📄 README.md                    # Główna dokumentacja
├── 📄 QUICKSTART.md               # Szybki start
├── 📄 LICENSE                     # Licencja MIT
├── 📄 .gitignore                  # Pliki ignorowane przez Git
├── 📄 .env                        # Zmienne środowiskowe
├── 📄 requirements.txt            # Zależności Python
├── 📄 install.sh                  # Skrypt instalacyjny (Linux/macOS)
├── 📄 run.py                      # Punkt startowy (prosty)
├── 📄 start.py                    # Punkt startowy (z inicjalizacją)
├── 📄 watcher.py                  # Watchdog do monitorowania plików
├── 📄 trainer.py                  # Skrypt uczenia na feedbacku
├── 📄 create_sample_pdf.py        # Generator przykładowego PDF
│
├── 📁 app/                        # Główny moduł aplikacji
│   ├── 📄 __init__.py            # Factory aplikacji Flask
│   ├── 📄 models.py              # Modele danych (JSON-based)
│   ├── 📄 routes.py              # Główne endpoints HTTP
│   ├── 📄 admin.py               # Panel administratora
│   └── 📄 socketio_handlers.py   # Obsługa WebSocket
│
├── 📁 utils/                      # Narzędzia pomocnicze
│   ├── 📄 __init__.py
│   └── 📄 openai_rag.py          # Logika RAG z OpenAI API
│
├── 📁 templates/                  # Szablony HTML (Jinja2)
│   ├── 📄 base.html              # Szablon bazowy
│   ├── 📄 chat.html              # Główny interfejs czatu
│   └── 📁 admin/                 # Szablony panelu administratora
│       ├── 📄 login.html         # Logowanie administratora
│       ├── 📄 dashboard.html     # Dashboard ze statystykami
│       ├── 📄 users.html         # Lista sesji użytkowników
│       ├── 📄 feedback.html      # Przegląd feedbacku
│       ├── 📄 documents.html     # Zarządzanie dokumentami PDF
│       └── 📄 reports.html       # Raporty i eksport
│
├── 📁 static/                     # Pliki statyczne
│   ├── 📁 js/
│   │   └── 📄 chat.js            # Logika frontendowa + WebSocket
│   └── 📁 css/                   # (Style przez Tailwind CDN)
│
├── 📁 uploads/                    # Przesłane pliki PDF (utworzone automatycznie)
├── 📁 history/                    # Historia czatów w JSON (utworzone automatycznie)
├── 📁 feedback/                   # Feedback użytkowników (utworzone automatycznie)
├── 📁 reports/                    # Wygenerowane raporty PDF (utworzone automatycznie)
├── 📁 data/                       # Dane systemowe (utworzone automatycznie)
│   ├── 📄 users.json             # Użytkownicy administratora
│   └── 📄 upload_index.json      # Indeks przesłanych plików
└── 📁 training_data/              # Dane do fine-tuningu (utworzone automatycznie)
    ├── 📄 training_data_*.jsonl   # Dane treningowe
    └── 📄 feedback_report_*.json  # Raporty feedbacku
```

## 🎯 Kluczowe Pliki

### 🚀 Uruchomienie
- **`start.py`** - Główny punkt startowy z inicjalizacją
- **`run.py`** - Prosty punkt startowy (bez dodatkowych kontroli)
- **`install.sh`** - Automatyczna instalacja (Linux/macOS)

### ⚙️ Konfiguracja
- **`.env`** - Wszystkie zmienne środowiskowe
- **`requirements.txt`** - Zależności Python
- **`.gitignore`** - Pliki ignorowane przez Git

### 🧠 Logika Biznesowa
- **`app/models.py`** - User, ChatSession, UploadIndex, etc.
- **`utils/openai_rag.py`** - Główna logika RAG + OpenAI
- **`app/socketio_handlers.py`** - Real-time komunikacja
- **`watcher.py`** - Monitorowanie nowych PDF-ów

### 🎨 Interfejs Użytkownika
- **`templates/chat.html`** - Główny interface czatu
- **`static/js/chat.js`** - Logika frontendowa
- **`templates/admin/`** - Kompletny panel administratora

### 🔧 Narzędzia
- **`trainer.py`** - Konwersja feedbacku → dane treningowe
- **`create_sample_pdf.py`** - Generator przykładowych plików

## 📊 Przepływ Danych

```
[PDF Upload] → [Watcher] → [Upload Index] → [Vector Store]
                              ↓
[User Query] → [WebSocket] → [RAG Logic] → [OpenAI API]
                              ↓
[Response Stream] → [Frontend] → [User Feedback] → [Training Data]
                              ↓
[PDF Report] → [Reports Folder] → [Admin Panel]
```

## 🔑 Zmienne Środowiskowe

| Zmienna | Opis | Wymagana |
|---------|------|----------|
| `OPENAI_API_KEY` | Klucz API OpenAI | ✅ |
| `ASSISTANT_ID` | ID asystenta OpenAI | ⚙️ (auto) |
| `SECRET_KEY` | Klucz Flask | ✅ |
| `PORT` | Port serwera | ❌ (5000) |
| `FLASK_ENV` | Środowisko Flask | ❌ (dev) |

## 🎛️ Dostępne Endpointy

### 🌐 Frontend
- `GET /` - Główny interfejs czatu
- `GET /admin` - Panel administratora
- `POST /admin/login` - Logowanie administratora

### 🔌 WebSocket Events
- `connect` - Połączenie
- `send_message` - Wysłanie wiadomości
- `response_chunk` - Chunk odpowiedzi
- `request_pdf` - Żądanie PDF

### 📡 API REST
- `POST /api/upload` - Upload pliku PDF
- `POST /api/feedback` - Przesłanie feedbacku
- `GET /api/history` - Historia czatu
- `POST /api/clear_history` - Wyczyszczenie historii

## 🎯 Następne Kroki

1. **Edytuj `.env`** - dodaj swój klucz OpenAI API
2. **Uruchom `./install.sh`** - automatyczna instalacja
3. **Uruchom `python start.py`** - start aplikacji
4. **Odwiedź `http://localhost:5000`** - testuj aplikację
5. **Panel admin: `http://localhost:5000/admin`** - (admin/admin123)

---

**Projekt gotowy do uruchomienia!** 🎉
