#!/bin/bash
# Skrypt instalacyjny dla Aero-Chat

echo "🛩️  Aero-Chat - Instalator"
echo "=========================="

# Sprawdź czy Python3 jest zainstalowany
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 nie jest zainstalowany!"
    echo "   Zainstaluj Python 3.12+ i spróbuj ponownie"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✅ Python wykryty: $PYTHON_VERSION"

# Sprawdź czy pip jest zainstalowany
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 nie jest zainstalowany!"
    echo "   Zainstaluj pip3 i spróbuj ponownie"
    exit 1
fi

echo "✅ pip3 wykryty"

# Utwórz środowisko wirtualne
echo "📦 Tworzenie środowiska wirtualnego..."
python3 -m venv venv

# Aktywuj środowisko wirtualne
echo "🔄 Aktywacja środowiska wirtualnego..."
source venv/bin/activate

# Upgraduj pip
echo "⬆️  Aktualizacja pip..."
pip install --upgrade pip

# Zainstaluj zależności
echo "📚 Instalacja zależności..."
pip install -r requirements.txt

# Utwórz katalogi
echo "📁 Tworzenie katalogów..."
mkdir -p uploads history feedback reports data training_data

# Skopiuj przykładowy .env jeśli nie istnieje
if [ ! -f .env ]; then
    echo "📝 Tworzenie pliku .env..."
    cp .env .env.backup 2>/dev/null || true
    echo "⚠️  WAŻNE: Edytuj plik .env i dodaj swój klucz OpenAI API!"
fi

echo ""
echo "✅ Instalacja zakończona pomyślnie!"
echo ""
echo "📋 Następne kroki:"
echo "1. Edytuj plik .env i dodaj swój klucz OpenAI API"
echo "2. Aktywuj środowisko wirtualne: source venv/bin/activate"
echo "3. Uruchom aplikację: python start.py"
echo ""
echo "🌐 Aplikacja będzie dostępna pod: http://localhost:5000"
echo "⚙️  Panel admin: http://localhost:5000/admin (admin/admin123)"
