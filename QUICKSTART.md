# 🚀 Szybki Start - Aero-Chat

## ⚡ Uruchomienie w 5 krokach

### 1. Sklonuj lub pobierz projekt
```bash
cd /twoja/lokalizacja/
# Projekt jest już gotowy w katalogu
```

### 2. Uruchom instalator
```bash
cd aero-chat
./install.sh
```

### 3. Edytuj konfigurację
```bash
nano .env
```
**Zmień:**
```env
OPENAI_API_KEY=sk-twoj-prawdziwy-klucz-tutaj
```

### 4. Aktywuj środowisko
```bash
source venv/bin/activate
```

### 5. Uruchom aplikację
```bash
python start.py
```

## 🌐 Dostęp do aplikacji
- **Chat:** http://localhost:5000
- **Admin:** http://localhost:5000/admin
  - Login: `admin`
  - Hasło: `admin123`

## 📱 Test aplikacji

1. **Przesłanie PDF:**
   - Kliknij "📁 Dodaj PDF"
   - Wybierz dowolny plik PDF z dokumentacją lotniczą

2. **Pierwsze pytanie:**
   ```
   Wyjaśnij podstawowe zasady lotu samolotu
   ```

3. **Oceń odpowiedź:**
   - 👍 - dobra odpowiedź
   - 👎 - słaba odpowiedź  
   - ✏️ - prośba o rozwinięcie

## 🛠️ Rozwiązywanie problemów

### Błąd importu
```bash
pip install -r requirements.txt
```

### Brak klucza OpenAI
1. Zarejestruj się na https://platform.openai.com
2. Utwórz klucz API
3. Dodaj do `.env`

### Port zajęty
Zmień port w `.env`:
```env
PORT=5001
```

## 📞 Pomoc
W razie problemów sprawdź pełną dokumentację w `README.md`
