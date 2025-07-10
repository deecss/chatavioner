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
    
    def create_assistant(self):
        """Tworzy nowego asystenta AI"""
        try:
            print("🔄 Tworzenie nowego asystenta OpenAI...")
            assistant = self.client.beta.assistants.create(
                name="Aero-Chat Assistant",
                instructions="""Jesteś ekspertem w dziedzinie lotnictwa i awioniki. 
                Twoje zadanie to odpowiadanie na pytania związane z:
                - Zasadami lotu i aerodynamiką
                - Konstrukcją i systemami statków powietrznych
                - Przepisami lotniczymi (ICAO, EASA, FAA)
                - Nawigacją lotniczą
                - Meteorologią lotniczą
                - Bezpieczeństwem lotów
                - Systemami awionicznymi
                
                BARDZO WAŻNE - FORMATOWANIE ODPOWIEDZI:
                Odpowiadaj zawsze w języku polskim w formacie Markdown:
                
                # Główny tytuł (jeśli potrzebny)
                ## Podtytuł dla głównych sekcji
                ### Podtytuł dla podsekcji
                
                **Pogrubiony tekst** dla ważnych pojęć.
                
                Używaj list punktowanych:
                - Punkt pierwszy
                - Punkt drugi
                - Punkt trzeci
                
                Lub list numerowanych:
                1. Pierwszy element
                2. Drugi element
                3. Trzeci element
                
                Dziel odpowiedź na logiczne sekcje z nagłówkami. Każdy akapit powinien być zwięzły ale wyczerpujący.
                
                Strukturyzuj odpowiedzi aby były czytelne i profesjonalne:
                - Zaczynaj od krótkiego wprowadzenia
                - Podziel treść na logiczne sekcje
                - Zakończ podsumowaniem lub praktycznymi wskazówkami
                
                Jeśli nie jesteś pewien odpowiedzi, powiedz o tym otwarcie.
                
                Kiedy otrzymasz listę dostępnych dokumentów PDF, wybierz maksymalnie 10 najważniejszych 
                dla danego pytania i zwróć ich nazwy.""",
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
    
    def select_relevant_documents(self, query, max_docs=10):
        """Wybiera najistotniejsze dokumenty dla zapytania"""
        print(f"🔍 Wybieranie dokumentów dla zapytania: {query[:50]}...")
        
        upload_index = UploadIndex()
        all_files = upload_index.get_all_files()
        
        print(f"🔍 Znaleziono {len(all_files)} plików w indeksie")
        
        if not all_files:
            print("⚠️  Brak plików w indeksie!")
            return []
        
        # Prosta heurystyka - możesz to ulepszyć
        # Na razie zwracamy pierwszych max_docs plików
        selected = all_files[:max_docs]
        print(f"🔍 Wybrano {len(selected)} plików: {selected[:3]}...")
        return selected
    
    def create_vector_store_with_files(self, file_paths):
        """Tworzy vector store z wybranymi plikami"""
        try:
            # Utwórz vector store
            vector_store = self.client.beta.vector_stores.create(
                name=f"temp_store_{int(time.time())}"
            )
            
            # Przesłij pliki
            file_ids = []
            for file_path in file_paths:
                full_path = os.path.join('uploads', file_path)
                if os.path.exists(full_path):
                    with open(full_path, 'rb') as f:
                        file_obj = self.client.files.create(
                            file=f,
                            purpose="assistants"
                        )
                        file_ids.append(file_obj.id)
            
            # Dodaj pliki do vector store
            if file_ids:
                self.client.beta.vector_stores.file_batches.create(
                    vector_store_id=vector_store.id,
                    file_ids=file_ids
                )
            
            return vector_store.id, file_ids
            
        except Exception as e:
            print(f"Błąd podczas tworzenia vector store: {str(e)}")
            return None, []
    
    def generate_response_stream(self, query, context, session_id):
        """Generuje odpowiedź w trybie strumieniowym"""
        try:
            print(f"🔍 Rozpoczynam generowanie odpowiedzi dla: {query[:50]}...")
            
            # Wybierz istotne dokumenty
            relevant_docs = self.select_relevant_documents(query)
            print(f"🔍 Wybrano {len(relevant_docs)} dokumentów: {relevant_docs[:3]}...")
            
            # Utwórz vector store z dokumentami
            vector_store_id, file_ids = self.create_vector_store_with_files(relevant_docs)
            print(f"🔍 Vector store ID: {vector_store_id}, Pliki: {len(file_ids)}")
            
            # Przygotuj kontekst rozmowy
            messages = []
            for msg in context:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            
            # Dodaj aktualne pytanie
            messages.append({
                "role": "user",
                "content": query
            })
            
            print(f"🔍 Przygotowano {len(messages)} wiadomości w kontekście")
            
            # Utwórz wątek
            print(f"🔍 Tworzę wątek z asystentem {self.assistant_id}")
            thread = self.client.beta.threads.create(
                messages=messages,
                tool_resources={
                    "file_search": {
                        "vector_store_ids": [vector_store_id] if vector_store_id else []
                    }
                }
            )
            
            print(f"🔍 Wątek utworzony: {thread.id}")
            
            # Uruchom asystenta
            print(f"🔍 Uruchamiam asystenta w trybie strumieniowym...")
            run = self.client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=self.assistant_id,
                stream=True
            )
            
            # Przetwórz strumień odpowiedzi
            response_text = ""
            chunk_count = 0
            for event in run:
                if event.event == 'thread.message.delta':
                    for content in event.data.delta.content:
                        if content.type == 'text':
                            chunk = content.text.value
                            response_text += chunk
                            chunk_count += 1
                            if chunk_count <= 3:  # Loguj tylko pierwsze 3 chunki
                                print(f"🔍 Otrzymano chunk #{chunk_count}: {chunk[:30]}...")
                            yield chunk
            
            print(f"🔍 Otrzymano łącznie {chunk_count} chunków, długość odpowiedzi: {len(response_text)}")
            
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
