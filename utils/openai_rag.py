#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Moduł OpenAI RAG dla aplikacji Aero-Chat
"""
import os
import json
import time
from datetime import datetime
import httpx
from openai import OpenAI
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from app.models import UploadIndex
from utils.learning_system import LearningSystem

class OpenAIRAG:
    """Klasa do obsługi RAG z OpenAI Assistants API"""
    
    def __init__(self):
        """Inicjalizuje klienta OpenAI"""
        try:
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key or 'twoj-klucz' in api_key:
                raise ValueError("Nieprawidłowy klucz OpenAI API")
            
            # Konfiguracja proxy jeśli jest ustawiona
            proxy_url = os.getenv("HTTPS_PROXY") or os.getenv("HTTP_PROXY")
            if proxy_url:
                transport = httpx.HTTPTransport(proxy=proxy_url)
                http_client = httpx.Client(transport=transport, timeout=30.0)
            else:
                http_client = httpx.Client(timeout=30.0)
            
            # Inicjalizuj klienta OpenAI z poprawną konfiguracją
            self.client = OpenAI(
                api_key=api_key,
                http_client=http_client
            )
            
            self.assistant_id = os.getenv('ASSISTANT_ID')
            self.model = "gpt-4o"
            
            # Sprawdź czy assistant_id jest pusty lub zawiera placeholder
            if not self.assistant_id or self.assistant_id.strip() == '' or 'twoj-assistant' in self.assistant_id:
                print("🔄 Brak ID asystenta, tworzę nowego...")
                self.assistant_id = self.create_assistant()
            else:
                # Sprawdź czy asystent nadal istnieje
                try:
                    self.client.beta.assistants.retrieve(self.assistant_id)
                    print(f"✅ Asystent znaleziony: {self.assistant_id}")
                except Exception as e:
                    print(f"⚠️  Asystent {self.assistant_id} nie istnieje, tworzę nowego...")
                    self.assistant_id = self.create_assistant()
                
        except Exception as e:
            print(f"❌ Błąd inicjalizacji OpenAI: {e}")
            raise
    
        # Inicjalizuj system uczenia się
        self.learning_system = LearningSystem()
        
        # Inicjalizuj zmienne śledzące
        self.last_documents_used = 0
        
    def create_assistant(self):
        """Tworzy nowego asystenta AI"""
        try:
            print("🔄 Tworzenie nowego asystenta OpenAI...")
            assistant = self.client.beta.assistants.create(
                name="Aero-Chat Assistant",
                instructions="""Jesteś ekspertem w dziedzinie lotnictwa i awioniki z zaawansowanym systemem uczenia się. 
                
                🚨 SUROWE OGRANICZENIE TEMATYCZNE:
                ODPOWIADASZ WYŁĄCZNIE NA PYTANIA Z DZIEDZINY LOTNICTWA!
                
                Tematy dozwolone:
                - Zasady lotu i aerodynamika
                - Konstrukcja i systemy statków powietrznych
                - Przepisy lotnicze (ICAO, EASA, FAA, polskie)
                - Nawigacja lotnicza
                - Meteorologia lotnicza
                - Bezpieczeństwo lotów
                - Systemy awioniczne
                - Historia lotnictwa
                - Licencje pilota
                - Procedury lotnicze
                - Komunikacja lotnicza
                - Planowanie lotów
                - Operacje lotniskowe
                - Szkolenia lotnicze
                - Certyfikacja lotnicza
                - Maintenance i obsługa techniczna
                - Współczesne technologie lotnicze
                
                ❌ KATEGORYCZNIE ODRZUCAJ pytania o:
                - Tematykę niezwiązaną z lotnictwem
                - Inne rodzaje transportu (samochody, pociągi, statki)
                - Politykę, ekonomię (chyba że bezpośrednio związane z lotnictwem)
                - Medycynę (chyba że medycyna lotnicza)
                - Inne dziedziny nauki i techniki
                - Rozrywkę, filmy, gry
                - Życie osobiste, porady życiowe
                - Inne tematy spoza lotnictwa
                
                🛑 REAKCJA NA PYTANIA SPOZA LOTNICTWA:
                Jeśli pytanie nie dotyczy lotnictwa, odpowiedz DOKŁADNIE:
                
                "<p><strong>Przepraszam, ale jestem wyspecjalizowanym asystentem lotniczym.</strong></p>
                <p>Mogę odpowiadać wyłącznie na pytania związane z lotnictwem, awionik, przepisami lotniczymi, nawigacją, meteorologią lotniczą, bezpieczeństwem lotów i związanymi tematami.</p>
                <p>Proszę zadaj pytanie dotyczące lotnictwa, a chętnie pomogę!</p>"
                
                ⚠️ BARDZO WAŻNE - PAMIĘĆ ROZMOWY:
                - ZAWSZE czytaj i analizuj całą historię rozmowy
                - Jeśli użytkownik zadaje to samo pytanie ponownie, odwołaj się do wcześniejszej odpowiedzi
                - Jeśli użytkownik prosi o więcej szczegółów, rozbuduj poprzednią odpowiedź
                - Jeśli użytkownik zadaje pytanie kontynuujące temat, podejmij wątek z wcześniejszej rozmowy
                - Pamiętaj preferencje użytkownika z poprzednich odpowiedzi
                
                SYSTEM UCZENIA SIĘ:
                Musisz się stale uczyć i dostosowywać do preferencji użytkownika:
                - Zapamiętuj jakie odpowiedzi użytkownik preferuje
                - Jeśli użytkownik prosi o "wzory i przykłady", zawsze je dostarczaj w przyszłych odpowiedziach
                - Jeśli użytkownik lubi szczegółowe wyjaśnienia, dostarczaj je konsekwentnie
                - Jeśli użytkownik preferuje praktyczne podejście, skupiaj się na zastosowaniach
                - Analizuj wzorce w pytaniach i dostosowuj styl odpowiedzi
                
                BARDZO WAŻNE - FORMATOWANIE ODPOWIEDZI:
                Odpowiadaj zawsze w języku polskim w formacie HTML:
                
                <h2>Główny tytuł sekcji</h2>
                <h3>Podtytuł dla podsekcji</h3>
                
                <p><strong>Pogrubiony tekst</strong> dla ważnych pojęć.</p>
                
                <p>Każdy akapit w osobnych tagach &lt;p&gt;.</p>
                
                Używaj list punktowanych:
                <ul>
                <li>Punkt pierwszy</li>
                <li>Punkt drugi</li>
                <li>Punkt trzeci</li>
                </ul>
                
                Lub list numerowanych:
                <ol>
                <li>Pierwszy element</li>
                <li>Drugi element</li>
                <li>Trzeci element</li>
                </ol>
                
                STRUKTURYZUJ ODPOWIEDZI:
                - Każdy nagłówek w osobnym tagu &lt;h2&gt; lub &lt;h3&gt;
                - Każdy akapit w osobnym tagu &lt;p&gt;
                - Listy zawsze w &lt;ul&gt; lub &lt;ol&gt;
                - Używaj &lt;strong&gt; dla ważnych terminów
                
                OBOWIĄZKOWO BAZUJ NA PRZESŁANYCH PLIKACH PDF:
                - Zawsze odwołuj się do konkretnych dokumentów
                - Cytuj fragmenty z dokumentów
                - Wskazuj strony lub sekcje dokumentów
                - Jeśli nie ma informacji w dokumentach, jasno to zaznacz
                
                Jeśli nie jesteś pewien odpowiedzi, powiedz o tym otwarcie.
                
                Strukturyzuj odpowiedzi aby były czytelne i profesjonalne:
                - Zaczynaj od krótkiego wprowadzenia w &lt;p&gt;
                - Podziel treść na logiczne sekcje z &lt;h2&gt; lub &lt;h3&gt;
                - Zakończ podsumowaniem w &lt;p&gt; lub praktycznymi wskazówkami
                
                PAMIĘTAJ: Używaj TYLKO HTML, nie Markdown!""",
                model=self.model,
                tools=[{"type": "file_search"}]
            )
            
            # Zapisz ID asystenta do .env
            self.save_assistant_id_to_env(assistant.id)
            
            print(f"✅ Nowy asystent utworzony: {assistant.id}")
            return assistant.id
            
        except Exception as e:
            print(f"❌ Błąd podczas tworzenia asystenta: {str(e)}")
            print(f"💡 Sprawdź czy klucz OpenAI API jest poprawny")
            return None
    
    def save_assistant_id_to_env(self, assistant_id):
        """Zapisuje ID asystenta do pliku .env"""
        try:
            env_file = '.env'
            if os.path.exists(env_file):
                with open(env_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                # Znajdź i zaktualizuj linię ASSISTANT_ID
                updated = False
                for i, line in enumerate(lines):
                    if line.startswith('ASSISTANT_ID='):
                        lines[i] = f'ASSISTANT_ID={assistant_id}\n'
                        updated = True
                        break
                
                # Jeśli nie znaleziono, dodaj na końcu
                if not updated:
                    lines.append(f'ASSISTANT_ID={assistant_id}\n')
                
                # Zapisz z powrotem
                with open(env_file, 'w', encoding='utf-8') as f:
                    f.writelines(lines)
                    
                print(f"💾 ID asystenta zapisany do .env: {assistant_id}")
                
        except Exception as e:
            print(f"⚠️  Nie udało się zapisać ID asystenta do .env: {e}")
    
    def clean_assistant_memory(self):
        """Czyści pamięć asystenta - usuwa stare pliki i vector stores"""
        try:
            print("🧹 Czyszczenie pamięci asystenta...")
            
            # Pobierz wszystkie pliki z OpenAI
            files_response = self.client.files.list()
            files_to_delete = []
            
            for file in files_response.data:
                # Usuń pliki starsze niż 1 godzina (3600 sekund)
                file_age = time.time() - file.created_at
                if file_age > 3600:  # 1 godzina
                    files_to_delete.append(file.id)
                    
            # Usuń stare pliki
            for file_id in files_to_delete:
                try:
                    self.client.files.delete(file_id)
                    print(f"🗑️  Usunięto stary plik: {file_id}")
                except Exception as e:
                    print(f"⚠️  Nie udało się usunąć pliku {file_id}: {e}")
            
            # Pobierz wszystkie vector stores
            vector_stores_response = self.client.beta.vector_stores.list()
            stores_to_delete = []
            
            for store in vector_stores_response.data:
                # Usuń vector stores starsze niż 1 godzina
                store_age = time.time() - store.created_at
                if store_age > 3600:  # 1 godzina
                    stores_to_delete.append(store.id)
                    
            # Usuń stare vector stores
            for store_id in stores_to_delete:
                try:
                    self.client.beta.vector_stores.delete(store_id)
                    print(f"🗑️  Usunięto stary vector store: {store_id}")
                except Exception as e:
                    print(f"⚠️  Nie udało się usunąć vector store {store_id}: {e}")
                    
            print(f"✅ Wyczyszczono {len(files_to_delete)} plików i {len(stores_to_delete)} vector stores")
            
        except Exception as e:
            print(f"❌ Błąd podczas czyszczenia pamięci: {str(e)}")

    def cancel_active_runs(self, thread_id):
        """Anuluje wszystkie aktywne runy w wątku"""
        try:
            print(f"🔍 Sprawdzam aktywne runy w wątku {thread_id}")
            
            # Pobierz wszystkie runy w wątku
            runs = self.client.beta.threads.runs.list(thread_id=thread_id)
            
            active_runs = []
            for run in runs.data:
                if run.status in ['queued', 'in_progress', 'requires_action']:
                    active_runs.append(run.id)
                    
            # Anuluj aktywne runy
            for run_id in active_runs:
                try:
                    self.client.beta.threads.runs.cancel(thread_id=thread_id, run_id=run_id)
                    print(f"⚠️  Anulowano aktywny run: {run_id}")
                except Exception as e:
                    print(f"❌ Nie udało się anulować run {run_id}: {e}")
                    
            if active_runs:
                print(f"✅ Anulowano {len(active_runs)} aktywnych runów")
                time.sleep(1)  # Krótkie opóźnienie aby anulowanie się dokończyło
            else:
                print("✅ Brak aktywnych runów do anulowania")
                
        except Exception as e:
            print(f"❌ Błąd podczas anulowania aktywnych runów: {str(e)}")

    def select_relevant_documents(self, query, max_docs=5):  # Zmniejszono z 10 do 5
        """Wybiera najistotniejsze dokumenty dla zapytania"""
        print(f"🔍 Wybieranie dokumentów dla zapytania: {query[:50]}...")
        
        upload_index = UploadIndex()
        all_files = upload_index.get_all_files()
        
        print(f"🔍 Znaleziono {len(all_files)} plików w indeksie")
        
        if not all_files:
            print("⚠️  Brak plików w indeksie!")
            self.last_documents_used = 0
            return []

        # Filtruj tylko pliki PDF mniejsze niż 20MB
        selected_files = []
        for file_path in all_files[:max_docs]:
            full_path = os.path.join('uploads', file_path)
            if os.path.exists(full_path):
                file_size = os.path.getsize(full_path)
                if file_size < 20 * 1024 * 1024:  # 20MB limit
                    selected_files.append(file_path)
                else:
                    print(f"⚠️  Plik {file_path} jest za duży ({file_size/1024/1024:.1f}MB), pomijam")
                    
        self.last_documents_used = len(selected_files)
        print(f"🔍 Wybrano {len(selected_files)} plików: {selected_files[:3]}...")
        return selected_files

    def create_vector_store_with_files(self, file_paths):
        """Tworzy vector store z wybranymi plikami"""
        try:
            if not file_paths:
                print("⚠️  Brak plików do przesłania")
                return None, []
                
            # Utwórz vector store
            vector_store = self.client.beta.vector_stores.create(
                name=f"temp_store_{int(time.time())}"
            )
            
            # Przesłaj pliki (maksymalnie 5 na raz)
            file_ids = []
            for file_path in file_paths[:5]:  # Limit do 5 plików
                full_path = os.path.join('uploads', file_path)
                if os.path.exists(full_path):
                    try:
                        with open(full_path, 'rb') as f:
                            file_obj = self.client.files.create(
                                file=f,
                                purpose='assistants'
                            )
                            file_ids.append(file_obj.id)
                            print(f"📄 Przesłano plik: {file_path} -> {file_obj.id}")
                    except Exception as e:
                        print(f"❌ Błąd przesyłania pliku {file_path}: {e}")
                        
            if not file_ids:
                print("⚠️  Nie udało się przesłać żadnych plików")
                self.client.beta.vector_stores.delete(vector_store.id)
                return None, []
                
            # Dodaj pliki do vector store
            try:
                self.client.beta.vector_stores.file_batches.create(
                    vector_store_id=vector_store.id,
                    file_ids=file_ids
                )
                print(f"✅ Dodano {len(file_ids)} plików do vector store")
                
                # Poczekaj na przetworzenie
                time.sleep(2)
                
                return vector_store.id, file_ids
                
            except Exception as e:
                print(f"❌ Błąd dodawania plików do vector store: {e}")
                # Usuń utworzone zasoby
                self.cleanup_resources(vector_store.id, file_ids, None)
                return None, []
                
        except Exception as e:
            print(f"❌ Błąd tworzenia vector store: {e}")
            return None, []

    def generate_response_stream(self, query, context, session_id):
        """Generuje odpowiedź w trybie strumieniowym z systemem uczenia się"""
        try:
            print(f"🔍 Rozpoczynam generowanie odpowiedzi dla: {query[:50]}...")
            
            # Sprawdź czy pytanie dotyczy lotnictwa (sprawdzenie na poziomie aplikacji)
            if not self.is_aviation_related(query):
                print(f"⚠️  Pytanie nie dotyczy lotnictwa: {query[:100]}...")
                rejection_message = ("Przepraszam, ale jestem asystentem specjalizującym się wyłącznie w tematyce lotniczej. "
                                   "Mogę pomóc w następujących obszarach:\n"
                                   "- Pilotaż i procedury lotnicze\n"
                                   "- Aerodynamika i mechanika lotu\n"
                                   "- Nawigacja i komunikacja\n"
                                   "- Meteorologia lotnicza\n"
                                   "- Przepisy i certyfikacja\n"
                                   "- Bezpieczeństwo lotów\n"
                                   "- Awionika i systemy pokładowe\n"
                                   "- Maintenance i serwis\n\n"
                                   "Proszę zadać pytanie związane z lotnictwem.")
                
                # Zwróć odpowiedź jako generator dla zachowania zgodności
                def rejection_generator():
                    print(f"🚫 Zwracam wiadomość odmowy: {rejection_message[:100]}...")
                    yield rejection_message
                
                return rejection_generator()
            
            # Wyciągnij user_id z kontekstu (jeśli dostępny)
            user_id = None
            if context:
                # Znajdź pierwszą wiadomość z user_id
                for msg in context:
                    if isinstance(msg, dict) and 'user_id' in msg:
                        user_id = msg['user_id']
                        break
            
            print(f"🆔 User ID z kontekstu: {user_id}")
            
            # ANALIZUJ PREFERENCJE UŻYTKOWNIKA I UCZEŚSIA
            print("🧠 Analizuję preferencje użytkownika...")
            learning_prompt = self.learning_system.generate_learning_prompt(session_id, query, user_id)
            print(f"📚 Prompt uczenia: {learning_prompt}")
            
            # Zapisz analizę sesji dla przyszłego uczenia
            session_analysis = self.learning_system.analyze_conversation_history(session_id, user_id)
            if session_analysis:
                self.learning_system.save_learning_data(session_analysis)
                print("💾 Zapisano dane uczenia")
            
            # WYCZYŚĆ PAMIĘĆ ASYSTENTA PRZED ROZPOCZĘCIEM
            self.clean_assistant_memory()
            
            # Wybierz istotne dokumenty (maksymalnie 5)
            relevant_docs = self.select_relevant_documents(query, max_docs=5)
            print(f"🔍 Wybrano {len(relevant_docs)} dokumentów: {relevant_docs[:3]}...")
            
            # Ustaw liczbę użytych dokumentów
            self.last_documents_used = len(relevant_docs)
            
            # Utwórz vector store z dokumentami
            vector_store_id, file_ids = self.create_vector_store_with_files(relevant_docs)
            
            if not vector_store_id:
                print("⚠️  Nie udało się utworzyć vector store, kontynuuję bez plików")
                
            print(f"🔍 Vector store ID: {vector_store_id}, Pliki: {len(file_ids)}")
            
            # Przygotuj kontekst rozmowy (pełna historia, zwiększ do 30 wiadomości)
            messages = []
            # Zwiększ kontekst do 30 ostatnich wiadomości (15 par pytanie-odpowiedź)
            recent_context = context[-30:] if len(context) > 30 else context
            
            print(f"🔍 Przygotowuję kontekst z {len(recent_context)} wiadomości (z {len(context)} całkowitych)")
            print(f"📚 Pierwsze pytanie w sesji: {context[0]['content'][:100] if context else 'Brak kontekstu'}...")
            print(f"📚 Ostatnie pytanie w sesji: {context[-1]['content'][:100] if context else 'Brak kontekstu'}...")
            
            # Wyświetl streszczenie całej historii
            if len(context) > 0:
                user_questions = [msg['content'][:50] + "..." for msg in context if msg['role'] == 'user']
                print(f"📋 Wszystkie pytania użytkownika w sesji ({len(user_questions)}):")
                for i, q in enumerate(user_questions, 1):
                    print(f"   {i}. {q}")
            
            for msg in recent_context:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
                
            # Dodaj szczegółowe instrukcje dotyczące kontekstu sesji
            context_instruction = ""
            if len(context) > 1:  # Jeśli jest historia rozmowy
                first_question = context[0]['content'] if context[0]['role'] == 'user' else "Brak pierwszego pytania"
                context_instruction = f"""
                
                🚨 PRZYPOMNIENIE: ODPOWIADASZ WYŁĄCZNIE NA PYTANIA LOTNICZE!
                
                WAŻNE INSTRUKCJE DOTYCZĄCE KONTEKSTU SESJI:
                - Pamiętaj, że to kontynuacja rozmowy - przeanalizuj całą historię powyżej
                - Pierwsze pytanie użytkownika w tej sesji to: "{first_question}"
                - Jeśli użytkownik pyta o coś, co było wcześniej omawiane, odwołaj się do tego
                - Jeśli użytkownik pyta o pierwsze pytanie, odpowiedz konkretnie
                - Zachowaj spójność ze stylem odpowiedzi preferowanym przez użytkownika
                - Nawiązuj do wcześniejszych tematów gdy to właściwe
                
                🛑 SPRAWDŹ CZY PYTANIE DOTYCZY LOTNICTWA:
                Jeśli pytanie poniżej NIE dotyczy lotnictwa, awioniki, przepisów lotniczych, nawigacji lotniczej, meteorologii lotniczej, bezpieczeństwa lotów lub związanych tematów, odpowiedz DOKŁADNIE standardową formułą odmowy.
                
                AKTUALNE PYTANIE: {query}
                """
            else:
                context_instruction = f"""
                
                🚨 PRZYPOMNIENIE: ODPOWIADASZ WYŁĄCZNIE NA PYTANIA LOTNICZE!
                
                🛑 SPRAWDŹ CZY PYTANIE DOTYCZY LOTNICTWA:
                Jeśli pytanie poniżej NIE dotyczy lotnictwa, awioniki, przepisów lotniczych, nawigacji lotniczej, meteorologii lotniczej, bezpieczeństwa lotów lub związanych tematów, odpowiedz DOKŁADNIE standardową formułą odmowy.
                
                PYTANIE: {query}
                """
            
            # Kombinuj prompt uczenia z instrukcjami kontekstu
            final_query = context_instruction
            if learning_prompt:
                final_query = f"{learning_prompt}\n\n{context_instruction}"
            
            # Dodaj aktualne pytanie z promptem uczenia
            messages.append({
                "role": "user",
                "content": final_query
            })
            
            print(f"🔍 Przygotowano {len(messages)} wiadomości w kontekście (z promptem uczenia)")
            
            # Utwórz wątek
            print(f"🔍 Tworzę wątek z asystentem {self.assistant_id}")
            
            thread_data = {
                "messages": messages
            }
            
            # Dodaj vector store tylko jeśli istnieje
            if vector_store_id:
                thread_data["tool_resources"] = {
                    "file_search": {
                        "vector_store_ids": [vector_store_id]
                    }
                }
            
            thread = self.client.beta.threads.create(**thread_data)
            
            print(f"🔍 Wątek utworzony: {thread.id}")
            
            # Uruchom asystenta z dodatkowym zabezpieczeniem i retry
            print(f"🔍 Uruchamiam asystenta w trybie strumieniowym...")
            
            max_retries = 3
            retry_count = 0
            
            while retry_count < max_retries:
                try:
                    # Sprawdź czy wątek ma aktywne runy i je anuluj
                    self.cancel_active_runs(thread.id)
                    
                    # Przygotuj parametry dla run
                    run_params = {
                        'thread_id': thread.id,
                        'assistant_id': self.assistant_id,
                        'stream': True,
                        'max_completion_tokens': 4000  # Ograniczenie długości odpowiedzi
                    }
                    
                    # Dodaj temperature tylko jeśli model go obsługuje
                    # Niektóre modele (np. o1-preview, o3-mini) nie obsługują temperature
                    try:
                        run_params['temperature'] = 0.7
                        run = self.client.beta.threads.runs.create(**run_params)
                    except Exception as temp_error:
                        print(f"⚠️  Model nie obsługuje temperature, używam bez tego parametru: {temp_error}")
                        # Usuń temperature i spróbuj ponownie
                        run_params.pop('temperature', None)
                        run = self.client.beta.threads.runs.create(**run_params)
                    
                    # Przetwórz strumień odpowiedzi
                    response_text = ""
                    chunk_count = 0
                    stream_failed = False
                
                    for event in run:
                        if event.event == 'thread.message.delta':
                            if hasattr(event.data, 'delta') and hasattr(event.data.delta, 'content'):
                                for content in event.data.delta.content:
                                    if content.type == 'text' and hasattr(content.text, 'value'):
                                        chunk = content.text.value
                                        response_text += chunk
                                        chunk_count += 1
                                        if chunk_count <= 3:  # Loguj tylko pierwsze 3 chunki
                                            print(f"🔍 Otrzymano chunk #{chunk_count}: {chunk[:30]}...")
                                        yield chunk
                        elif event.event == 'thread.run.completed':
                            print("✅ Ukończono generowanie odpowiedzi")
                            break
                        elif event.event == 'thread.run.failed':
                            error_details = getattr(event.data, 'last_error', None)
                            if error_details:
                                error_msg = f"OpenAI API Error: {error_details.code} - {error_details.message}"
                                print(f"❌ {error_msg}")
                                stream_failed = True
                                if retry_count < max_retries - 1:
                                    print(f"🔄 Próbuję ponownie ({retry_count + 1}/{max_retries})...")
                                    break
                                else:
                                    yield f"Przepraszam, wystąpił błąd po stronie OpenAI: {error_details.message}. Spróbuj ponownie za chwilę."
                            else:
                                print(f"❌ Błąd podczas generowania: {event.data}")
                                stream_failed = True
                                if retry_count < max_retries - 1:
                                    print(f"🔄 Próbuję ponownie ({retry_count + 1}/{max_retries})...")
                                    break
                                else:
                                    yield "Przepraszam, wystąpił nieoczekiwany błąd. Spróbuj ponownie."
                            break
                        elif event.event == 'thread.run.cancelled':
                            print("⚠️ Generowanie zostało anulowane")
                            yield "Generowanie odpowiedzi zostało anulowane."
                            return
                    
                    # Jeśli nie było błędu, zakończ retry loop
                    if not stream_failed:
                        print(f"🔍 Otrzymano łącznie {chunk_count} chunków, długość odpowiedzi: {len(response_text)}")
                        break
                        
                except Exception as stream_error:
                    print(f"❌ Błąd podczas streamowania: {stream_error}")
                    if retry_count < max_retries - 1:
                        print(f"🔄 Próbuję ponownie ({retry_count + 1}/{max_retries})...")
                        retry_count += 1
                        time.sleep(2 ** retry_count)  # Exponential backoff
                        continue
                    else:
                        yield f"Przepraszam, wystąpił błąd podczas generowania odpowiedzi: {str(stream_error)}"
                        break
                
                retry_count += 1
                if stream_failed and retry_count < max_retries:
                    time.sleep(2 ** retry_count)  # Exponential backoff
            
            # Poczekaj na zakończenie
            time.sleep(1)
            
            # Usuń tymczasowe zasoby
            self.cleanup_resources(vector_store_id, file_ids, thread.id)
            print(f"🔍 Zakończono generowanie odpowiedzi")
            
        except Exception as e:
            print(f"❌ Błąd podczas generowania odpowiedzi: {str(e)}")
            import traceback
            traceback.print_exc()
            yield f"Przepraszam, wystąpił błąd: {str(e)}"
    
    def cleanup_resources(self, vector_store_id, file_ids, thread_id):
        """Usuwa tymczasowe zasoby"""
        try:
            # Usuń pliki
            for file_id in file_ids:
                try:
                    self.client.files.delete(file_id)
                except:
                    pass
            
            # Usuń vector store
            if vector_store_id:
                try:
                    self.client.beta.vector_stores.delete(vector_store_id)
                except:
                    pass
            
            # Usuń wątek
            if thread_id:
                try:
                    self.client.beta.threads.delete(thread_id)
                except:
                    pass
                    
        except Exception as e:
            print(f"Błąd podczas usuwania zasobów: {str(e)}")
    
    def generate_pdf_report(self, content, session_id, message_id=None):
        """Generuje raport PDF z odpowiedzi"""
        try:
            # Utwórz katalog dla sesji
            reports_dir = f'reports/{session_id}'
            os.makedirs(reports_dir, exist_ok=True)
            
            # Nazwa pliku PDF
            if message_id:
                filename = f'answer_{message_id}.pdf'
            else:
                filename = f'answer_{int(time.time())}.pdf'
            
            filepath = os.path.join(reports_dir, filename)
            
            # Utwórz dokument PDF
            doc = SimpleDocTemplate(filepath, pagesize=A4)
            
            # Style
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                alignment=TA_CENTER,
                spaceAfter=30
            )
            
            normal_style = ParagraphStyle(
                'CustomNormal',
                parent=styles['Normal'],
                fontSize=12,
                alignment=TA_JUSTIFY,
                spaceAfter=12
            )
            
            # Treść dokumentu
            story = []
            
            # Tytuł
            story.append(Paragraph("Aero-Chat - Raport Odpowiedzi", title_style))
            story.append(Spacer(1, 12))
            
            # Data
            story.append(Paragraph(f"Data: {datetime.now().strftime('%d.%m.%Y %H:%M')}", normal_style))
            story.append(Paragraph(f"Sesja: {session_id}", normal_style))
            story.append(Spacer(1, 20))
            
            # Odpowiedź
            story.append(Paragraph("Odpowiedź:", styles['Heading2']))
            
            # Podziel treść na akapity
            paragraphs = content.split('\n\n')
            for para in paragraphs:
                if para.strip():
                    story.append(Paragraph(para.strip(), normal_style))
            
            # Zbuduj PDF
            doc.build(story)
            
            return filepath
            
        except Exception as e:
            print(f"Błąd podczas generowania PDF: {str(e)}")
            return None
    
    def add_feedback_to_training(self, feedback_data):
        """Dodaje feedback do bazy wiedzy asystenta"""
        try:
            # Zapisz feedback w specjalnym katalogu treningowym
            training_dir = 'training_data'
            os.makedirs(training_dir, exist_ok=True)
            
            # Stwórz nazwę pliku bazując na typie sekcji i timestampie
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'feedback_{feedback_data["section_type"]}_{timestamp}.json'
            filepath = os.path.join(training_dir, filename)
            
            # Przygotuj dane treningowe
            training_data = {
                'feedback_type': feedback_data['feedback_type'],
                'section_type': feedback_data['section_type'],
                'content': feedback_data['content'],
                'user_description': feedback_data['description'],
                'timestamp': feedback_data['timestamp'],
                'session_id': feedback_data['session_id'],
                'improvement_notes': self.generate_improvement_notes(feedback_data)
            }
            
            # Zapisz do pliku JSON
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(training_data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Feedback dodany do bazy treningowej: {filename}")
            
            # Jeśli feedback jest negatywny, spróbuj poprawić odpowiedź
            if feedback_data['feedback_type'] == 'negative':
                self.process_negative_feedback(feedback_data)
                
        except Exception as e:
            print(f"❌ Błąd podczas dodawania feedback do treningu: {str(e)}")
    
    def generate_improvement_notes(self, feedback_data):
        """Generuje notatki o poprawach na podstawie feedbacku"""
        notes = []
        
        if feedback_data['feedback_type'] == 'negative':
            notes.append("Treść wymaga poprawy według użytkownika")
            if feedback_data['description']:
                notes.append(f"Uwagi użytkownika: {feedback_data['description']}")
                
            # Dodaj sugestie poprawy na podstawie typu sekcji
            if feedback_data['section_type'] == 'header':
                notes.append("Rozważ zmianę struktury nagłówka lub jego treści")
            elif feedback_data['section_type'] == 'paragraph':
                notes.append("Rozważ przepisanie akapitu dla lepszej jasności")
            elif feedback_data['section_type'] == 'list':
                notes.append("Rozważ zmianę struktury listy lub jej elementów")
        else:
            notes.append("Treść uznana za przydatną przez użytkownika")
            if feedback_data['description']:
                notes.append(f"Pozytywne uwagi: {feedback_data['description']}")
        
        return notes
    
    def process_negative_feedback(self, feedback_data):
        """Przetwarza negatywny feedback i próbuje poprawić przyszłe odpowiedzi"""
        try:
            # Zapisz do pliku z negatywnymi feedbackami
            negative_feedback_file = 'training_data/negative_feedback_summary.json'
            
            # Wczytaj istniejące negatywne feedbacki
            if os.path.exists(negative_feedback_file):
                with open(negative_feedback_file, 'r', encoding='utf-8') as f:
                    all_negative = json.load(f)
            else:
                all_negative = []
            
            # Dodaj nowy feedback
            all_negative.append({
                'content': feedback_data['content'],
                'description': feedback_data['description'],
                'section_type': feedback_data['section_type'],
                'timestamp': feedback_data['timestamp']
            })
            
            # Zapisz z powrotem
            with open(negative_feedback_file, 'w', encoding='utf-8') as f:
                json.dump(all_negative, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Negatywny feedback dodany do analizy: {feedback_data['section_type']}")
            
        except Exception as e:
            print(f"❌ Błąd podczas przetwarzania negatywnego feedbacku: {str(e)}")

    def get_training_insights(self):
        """Pobiera insights z feedbacku treningowego"""
        try:
            training_dir = 'training_data'
            if not os.path.exists(training_dir):
                return {}
            
            insights = {
                'total_feedback': 0,
                'positive_feedback': 0,
                'negative_feedback': 0,
                'section_types': {},
                'common_issues': []
            }
            
            # Przeanalizuj wszystkie pliki feedbacku
            for filename in os.listdir(training_dir):
                if filename.startswith('feedback_') and filename.endswith('.json'):
                    filepath = os.path.join(training_dir, filename)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        
                        insights['total_feedback'] += 1
                        
                        if data['feedback_type'] == 'positive':
                            insights['positive_feedback'] += 1
                        else:
                            insights['negative_feedback'] += 1
                        
                        # Statystyki typów sekcji
                        section_type = data['section_type']
                        if section_type not in insights['section_types']:
                            insights['section_types'][section_type] = {'positive': 0, 'negative': 0}
                        insights['section_types'][section_type][data['feedback_type']] += 1
            
            return insights
            
        except Exception as e:
            print(f"❌ Błąd podczas pobierania insights: {str(e)}")
            return {}
    
    def save_conversation_context(self, session_id, context, current_message):
        """Zapisuje kontekst rozmowy do pliku dla debugowania i uczenia się"""
        try:
            os.makedirs('history', exist_ok=True)
            context_file = f'history/{session_id}_full_context.json'
            
            # Przygotuj strukturę do zapisu
            conversation_data = {
                'timestamp': datetime.now().isoformat(),
                'session_id': session_id,
                'total_messages': len(context),
                'current_message': current_message,
                'full_conversation': context,
                'summary': {
                    'user_messages': len([m for m in context if m['role'] == 'user']),
                    'assistant_messages': len([m for m in context if m['role'] == 'assistant']),
                    'last_3_messages': context[-3:] if len(context) >= 3 else context
                }
            }
            
            with open(context_file, 'w', encoding='utf-8') as f:
                json.dump(conversation_data, f, ensure_ascii=False, indent=2)
            
            print(f"💾 Kontekst rozmowy zapisany do {context_file}")
            print(f"📊 Statystyki: {conversation_data['summary']}")
            
        except Exception as e:
            print(f"⚠️  Błąd zapisu kontekstu rozmowy: {e}")

    def load_conversation_context(self, session_id):
        """Ładuje kontekst rozmowy z pliku"""
        try:
            context_file = f'history/{session_id}_full_context.json'
            if os.path.exists(context_file):
                with open(context_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return data.get('full_conversation', [])
            return []
        except Exception as e:
            print(f"⚠️  Błąd ładowania kontekstu rozmowy: {e}")
            return []
    
    def is_aviation_related(self, query: str) -> bool:
        """Sprawdza czy pytanie dotyczy lotnictwa"""
        aviation_keywords = [
            # Polskie terminy lotnicze
            'lotnictwo', 'pilot', 'samolot', 'śmigłowiec', 'helikopter', 'szybowiec',
            'silnik', 'skrzydło', 'kadłub', 'usterzenie', 'podwozie', 'aerodynamika',
            'siła nośna', 'opór', 'ciąg', 'lot', 'lądowanie', 'start', 'wzlot',
            'nawigacja', 'GPS', 'radar', 'radio', 'komunikacja', 'wieża', 'kontrola',
            'meteorologia', 'pogoda', 'turbulencje', 'wiatr', 'chmury', 'widoczność',
            'ICAO', 'EASA', 'FAA', 'ULC', 'przepisy', 'certyfikacja', 'licencja',
            'VFR', 'IFR', 'ATPL', 'PPL', 'CPL', 'IR', 'MEP', 'SEP',
            'lotnisko', 'pas', 'tower', 'hangar', 'terminal', 'ramp',
            'awionika', 'autopilot', 'transponder', 'altimetr', 'prędkościomierz',
            'bezpieczeństwo', 'wypadek', 'incydent', 'śledztwo', 'raport',
            'szkolenie', 'instruktor', 'egzamin', 'kurs', 'symulator',
            'maintenance', 'przegląd', 'naprawa', 'serwis', 'części',
            'paliwo', 'tankowanie', 'masa', 'balans', 'środek ciężkości',
            'przestrzeń', 'powietrzna', 'trasa', 'plan', 'lotu',
            
            # Angielskie terminy lotnicze
            'aviation', 'aircraft', 'airplane', 'helicopter', 'glider', 'pilot',
            'engine', 'wing', 'fuselage', 'landing', 'takeoff', 'flight',
            'navigation', 'weather', 'airport', 'runway', 'control', 'tower',
            'avionics', 'autopilot', 'altimeter', 'airspeed', 'attitude',
            'VOR', 'NDB', 'ILS', 'DME', 'ADF', 'HSI', 'CDI',
            'turbulence', 'ceiling', 'visibility', 'crosswind', 'headwind',
            'approach', 'departure', 'cruise', 'descent', 'climb',
            'checklist', 'procedure', 'emergency', 'malfunction', 'failure',
            'certification', 'training', 'instructor', 'student', 'solo',
            'ground', 'school', 'simulator', 'logbook', 'hours',
            'maintenance', 'inspection', 'repair', 'overhaul', 'AD',
            'airworthiness', 'registration', 'insurance', 'hangar',
            'fuel', 'weight', 'balance', 'loading', 'performance',
            'aerodynamics', 'lift', 'drag', 'thrust', 'stall'
        ]
        
        # Sprawdź czy pytanie zawiera słowa kluczowe lotnicze
        query_lower = query.lower()
        for keyword in aviation_keywords:
            if keyword in query_lower:
                return True
        
        # Sprawdź czy pytanie zawiera typowe frazesy lotnicze
        aviation_phrases = [
            'jak działa', 'co to jest', 'zasada', 'procedura', 'jak wykonać',
            'jakie są', 'kiedy', 'gdzie', 'dlaczego', 'w lotnictwie',
            'w samolocie', 'podczas lotu', 'na lotnisku', 'w powietrzu',
            'pilot', 'kontroler', 'mechanik', 'instruktor', 'egzaminator'
        ]
        
        for phrase in aviation_phrases:
            if phrase in query_lower:
                # Jeśli zawiera frazę lotniczą, sprawdź kontekst
                for keyword in aviation_keywords:
                    if keyword in query_lower:
                        return True
        
        return False
