#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generator podręcznika ATPL
Automatyczne tworzenie podręcznika na podstawie dostępnych dokumentów i AI
"""

import os
import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
import PyPDF2
from .openai_rag import OpenAIRAG
import re


class ATPLHandbookGenerator:
    """Generator podręcznika ATPL na podstawie dostępnych dokumentów"""
    
    def __init__(self):
        try:
            # Użyj istniejącej konfiguracji OpenAI RAG
            self.openai_rag = OpenAIRAG()
            self.client = self.openai_rag.client
        except Exception as e:
            print(f"⚠️  Błąd inicjalizacji OpenAI: {e}")
            self.client = None
        
        self.handbook_dir = 'handbook'
        self.program_file = None
        self.handbook_structure = {}
        self.progress_file = os.path.join(self.handbook_dir, 'progress.json')
        
        # Utwórz katalog na podręcznik
        os.makedirs(self.handbook_dir, exist_ok=True)
        
        # Załaduj postęp jeśli istnieje
        self.load_progress()
    
    def find_program_file(self) -> Optional[str]:
        """Znajdź plik z programem ATPL"""
        uploads_dir = 'uploads'
        if not os.path.exists(uploads_dir):
            return None
        
        for filename in os.listdir(uploads_dir):
            if 'Program_ATPL-ang_serwis' in filename and filename.endswith('.pdf'):
                self.program_file = os.path.join(uploads_dir, filename)
                return self.program_file
        
        return None
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Wyciągnij tekst z PDF używając PyPDF2"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                
                for page in pdf_reader.pages:
                    text += page.extract_text()
                
                return text
        except Exception as e:
            print(f"❌ Błąd wyciągania tekstu z PDF: {e}")
            return ""
    
    def analyze_program_structure(self) -> Dict[str, Any]:
        """Analizuj strukturę programu ATPL używając AI"""
        if not self.program_file:
            if not self.find_program_file():
                raise Exception("Nie znaleziono pliku z programem ATPL")
        
        print(f"📄 Analizuję strukturę programu: {self.program_file}")
        
        # Sprawdź dostępność klienta OpenAI
        if not self.client:
            raise Exception("Klient OpenAI nie jest dostępny. Sprawdź konfigurację OPENAI_API_KEY.")
        
        # Wyciągnij tekst z PDF
        program_text = self.extract_text_from_pdf(self.program_file)
        
        if not program_text.strip():
            raise Exception("Nie udało się wyciągnąć tekstu z pliku programu")
        
        # Użyj AI do analizy struktury
        try:
            if not self.client:
                raise Exception("Klient OpenAI nie jest dostępny")
            
            # Podziel tekst na mniejsze części jeśli jest za długi
            max_chunk_size = 12000  # Bezpieczniejszy limit
            text_chunks = []
            
            if len(program_text) > max_chunk_size:
                print(f"📋 Dokument jest duży ({len(program_text)} znaków), dzielę na części...")
                for i in range(0, len(program_text), max_chunk_size):
                    chunk = program_text[i:i + max_chunk_size]
                    text_chunks.append(chunk)
            else:
                text_chunks = [program_text]
            
            print(f"🔄 Analizuję {len(text_chunks)} części dokumentu...")
            
            # Analizuj pierwszą część dla głównej struktury
            response = self.client.chat.completions.create(
                model="gpt-4o",  # Użyj nowszego modelu
                messages=[
                    {
                        "role": "system",
                        "content": """Jesteś ekspertem od lotnictwa i analizy dokumentów szkoleniowych ATPL.
                        Przeanalizuj podany tekst programu szkolenia ATPL i wyciągnij strukturę kursu.
                        
                        Zwróć odpowiedź w formacie JSON z następującą strukturą:
                        {
                            "title": "Tytuł programu",
                            "description": "Opis programu",
                            "total_hours": "Łączna liczba godzin",
                            "modules": [
                                {
                                    "id": "module_1",
                                    "title": "Tytuł modułu",
                                    "description": "Opis modułu",
                                    "hours": "Liczba godzin",
                                    "chapters": [
                                        {
                                            "id": "chapter_1_1",
                                            "title": "Tytuł rozdziału",
                                            "description": "Opis rozdziału",
                                            "topics": [
                                                {
                                                    "id": "topic_1_1_1",
                                                    "title": "Tytuł tematu",
                                                    "description": "Opis tematu",
                                                    "subtopics": ["podtemat 1", "podtemat 2"]
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ]
                        }
                        
                        Zachowaj wszystkie szczegóły i hierarchię jak w oryginalnym dokumencie.
                        Używaj polskich nazw dla części po polsku i angielskich dla części w języku angielskim.
                        Skoncentruj się na głównej strukturze - moduły, rozdziały i tematy."""
                    },
                    {
                        "role": "user",
                        "content": f"Przeanalizuj następujący tekst programu szkolenia ATPL (część 1/{len(text_chunks)}):\n\n{text_chunks[0]}"
                    }
                ],
                temperature=0.3,
                timeout=60  # 60 sekund timeout
            )
            
            structure_text = response.choices[0].message.content
            print(f"📝 Otrzymano odpowiedź AI ({len(structure_text)} znaków)")
            
            # Wyciągnij JSON z odpowiedzi
            json_match = re.search(r'\{.*\}', structure_text, re.DOTALL)
            if json_match:
                structure = json.loads(json_match.group())
            else:
                # Spróbuj sparsować całą odpowiedź jako JSON
                try:
                    structure = json.loads(structure_text)
                except json.JSONDecodeError:
                    # Jeśli nie można sparsować, utwórz podstawową strukturę
                    print("⚠️  Nie można sparsować odpowiedzi AI, tworzę podstawową strukturę...")
                    structure = {
                        "title": "Program Szkolenia ATPL",
                        "description": "Automatycznie wygenerowana struktura z analizy OCR",
                        "total_hours": "Nie określono",
                        "modules": [
                            {
                                "id": "module_1",
                                "title": "Moduł 1 - Podstawy",
                                "description": "Podstawowy moduł szkoleniowy",
                                "hours": "Nie określono",
                                "chapters": [
                                    {
                                        "id": "chapter_1_1",
                                        "title": "Rozdział 1.1",
                                        "description": "Wprowadzenie do tematu",
                                        "topics": [
                                            {
                                                "id": "topic_1_1_1",
                                                "title": "Temat 1.1.1",
                                                "description": "Podstawowy temat",
                                                "subtopics": ["Wprowadzenie", "Podstawy"]
                                            }
                                        ]
                                    }
                                ]
                            }
                        ]
                    }
            
            # Sprawdź czy struktura ma wymagane pola
            if not isinstance(structure, dict) or 'modules' not in structure:
                raise Exception("AI zwróciło nieprawidłową strukturę")
            
            # Dodaj ID jeśli brakuje
            for i, module in enumerate(structure.get('modules', [])):
                if 'id' not in module:
                    module['id'] = f"module_{i+1}"
                for j, chapter in enumerate(module.get('chapters', [])):
                    if 'id' not in chapter:
                        chapter['id'] = f"chapter_{i+1}_{j+1}"
                    for k, topic in enumerate(chapter.get('topics', [])):
                        if 'id' not in topic:
                            topic['id'] = f"topic_{i+1}_{j+1}_{k+1}"
            
            # Zapisz strukturę
            self.handbook_structure = structure
            self.save_progress()
            
            print(f"✅ Struktura programu przeanalizowana: {len(structure.get('modules', []))} modułów")
            return structure
            
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Błąd analizy struktury: {error_msg}")
            
            # Obsługa specyficznych błędów
            if "timed out" in error_msg.lower() or "timeout" in error_msg.lower():
                print("⏱️  Timeout API - spróbuję utworzyć podstawową strukturę z OCR...")
                
                # Utwórz podstawową strukturę na podstawie pierwszych linii tekstu
                lines = program_text.split('\n')[:50]  # Pierwszych 50 linii
                
                # Znajdź potencjalne tytuły (linie z dużymi literami lub numerami)
                potential_titles = []
                for line in lines:
                    line = line.strip()
                    if line and (line.isupper() or re.match(r'^\d+\.', line) or re.match(r'^[IVX]+\.', line)):
                        potential_titles.append(line)
                
                structure = {
                    "title": "Program Szkolenia ATPL (OCR)",
                    "description": "Struktura utworzona automatycznie z analizy OCR po timeout API",
                    "total_hours": "Nie określono",
                    "modules": []
                }
                
                # Utwórz moduły z znalezionych tytułów
                for i, title in enumerate(potential_titles[:10]):  # Maksymalnie 10 modułów
                    module = {
                        "id": f"module_{i+1}",
                        "title": title[:100],  # Ograniczenie długości
                        "description": f"Moduł automatycznie wyodrębniony z OCR",
                        "hours": "Nie określono",
                        "chapters": [
                            {
                                "id": f"chapter_{i+1}_1",
                                "title": f"Rozdział 1 - {title[:50]}",
                                "description": "Automatycznie utworzony rozdział",
                                "topics": [
                                    {
                                        "id": f"topic_{i+1}_1_1",
                                        "title": f"Wprowadzenie do {title[:30]}",
                                        "description": "Temat wprowadzający",
                                        "subtopics": ["Podstawy", "Teoria", "Praktyka"]
                                    }
                                ]
                            }
                        ]
                    }
                    structure["modules"].append(module)
                
                if not structure["modules"]:
                    # Jeśli nie znaleziono żadnych tytułów, utwórz podstawową strukturę
                    structure["modules"] = [
                        {
                            "id": "module_1",
                            "title": "Moduł 1 - Podstawy ATPL",
                            "description": "Podstawowy moduł szkoleniowy",
                            "hours": "Nie określono",
                            "chapters": [
                                {
                                    "id": "chapter_1_1",
                                    "title": "Wprowadzenie",
                                    "description": "Podstawowe informacje",
                                    "topics": [
                                        {
                                            "id": "topic_1_1_1",
                                            "title": "Podstawy lotnictwa",
                                            "description": "Fundamentalne zagadnienia",
                                            "subtopics": ["Historia", "Regulacje", "Bezpieczeństwo"]
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                
                print(f"📋 Utworzono strukturę fallback z {len(structure['modules'])} modułów")
            else:
                raise e
    
    def get_handbook_structure(self) -> Dict[str, Any]:
        """Pobierz strukturę podręcznika"""
        if not self.handbook_structure:
            return self.analyze_program_structure()
        return self.handbook_structure
    
    def generate_chapter_content(self, module_id: str, chapter_id: str = None, topic_id: str = None, ai_type: str = 'comprehensive') -> str:
        """Generuj treść rozdziału/tematu używając AI i dostępnych dokumentów"""
        structure = self.get_handbook_structure()
        
        # Znajdź odpowiedni element struktury
        target_item = None
        context = ""
        
        for module in structure.get('modules', []):
            if module['id'] == module_id:
                if not chapter_id:
                    # Generowanie dla modułu
                    target_item = module
                    context = f"Moduł: {module.get('title', module_id)}"
                    break
                
                for chapter in module.get('chapters', []):
                    if chapter['id'] == chapter_id:
                        if topic_id:
                            for topic in chapter.get('topics', []):
                                if topic['id'] == topic_id:
                                    target_item = topic
                                    context = f"Moduł: {module['title']}\nRozdział: {chapter['title']}\nTemat: {topic['title']}"
                                    break
                        else:
                            target_item = chapter
                            context = f"Moduł: {module['title']}\nRozdział: {chapter['title']}"
                        break
        
        if not target_item:
            if topic_id and chapter_id:
                raise Exception(f"Nie znaleziono tematu: {module_id}/{chapter_id}/{topic_id}")
            elif chapter_id:
                raise Exception(f"Nie znaleziono rozdziału: {module_id}/{chapter_id}")
            else:
                raise Exception(f"Nie znaleziono modułu: {module_id}")
        
        # Znajdź powiązane dokumenty
        related_docs = self._find_related_documents(target_item['title'], target_item.get('description', ''))
        
        # Generuj treść używając AI z odpowiednim promptem
        try:
            system_prompt = self._get_ai_system_prompt(ai_type)
            
            user_prompt = f"""Kontekst: {context}
            
            Tytuł: {target_item['title']}
            Opis: {target_item.get('description', '')}
            
            Powiązane dokumenty dostępne w systemie:
            {chr(10).join(related_docs[:5])}  # Maksymalnie 5 dokumentów
            
            Wygeneruj treść szkoleniową zgodnie z wybranym typem."""
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.4
            )
            
            content = response.choices[0].message.content
            
            # Zapisz wygenerowaną treść
            self._save_generated_content(module_id, chapter_id, topic_id, content)
            
            # Zaktualizuj postęp
            self._update_progress(module_id, chapter_id, topic_id, 'generated')
            
            return content
            
        except Exception as e:
            print(f"❌ Błąd generowania treści: {e}")
            raise e
    
    def _get_ai_system_prompt(self, ai_type: str) -> str:
        """Pobierz odpowiedni system prompt dla typu AI"""
        prompts = {
            'comprehensive': """Jesteś ekspertem lotniczym i instruktorem ATPL. Tworzysz kompletny, profesjonalny podręcznik szkoleniowy.
            
            Wygeneruj bardzo szczegółową treść w formacie markdown z następującymi sekcjami:
            
            # Tytuł tematu
            
            ## 📖 Wprowadzenie
            Szczegółowe wprowadzenie do tematu z kontekstem historycznym i znaczeniem w lotnictwie
            
            ## 🎯 Cele szkoleniowe
            - Konkretne cele uczenia się
            - Kompetencje do osiągnięcia
            - Standardy oceny
            
            ## 📚 Teoria i podstawy
            Szczegółowe wyjaśnienie teorii z:
            - Definicjami i pojęciami
            - Wzorami matematycznymi (jeśli dotyczy)
            - Diagramami ASCII
            - Przykładami praktycznymi
            
            ## ⚙️ Procedury
            Dokładne procedury krok po kroku z:
            - Listami kontrolnymi
            - Punktami decyzyjnymi
            - Akcjami awaryjnymi
            
            ## 🛩️ Zastosowanie w praktyce
            Rzeczywiste scenariusze lotnicze z:
            - Studiami przypadków
            - Analizą błędów
            - Najlepszymi praktykami
            
            ## ⚖️ Regulacje i przepisy
            Szczegółowe przepisy z:
            - Przepisami ICAO
            - Regulacjami EASA
            - Przepisami krajowymi
            - Interpretacjami prawymi
            
            ## 🔧 Aspekty techniczne
            Techniczne szczegóły systemów i urządzeń
            
            ## ❓ Pytania kontrolne
            10-15 pytań różnego typu:
            - Pytania jednokrotnego wyboru
            - Pytania wielokrotnego wyboru
            - Pytania otwarte
            - Zadania praktyczne
            
            ## 📋 Listy kontrolne
            Praktyczne listy kontrolne do użycia
            
            ## 📚 Bibliografia i źródła
            Kompletna lista źródeł i dodatkowej literatury
            
            ## 💡 Wskazówki dla instruktorów
            Porady metodyczne i dydaktyczne
            
            Używaj profesjonalnego języka lotniczego, dodawaj tabele, diagramy ASCII, przykłady obliczeń.""",
            
            'summary': """Jesteś ekspertem lotniczym tworzącym zwięzłe streszczenia. 
            
            Wygeneruj kondensowaną treść w formacie markdown:
            
            # Tytuł tematu
            
            ## 🔍 Kluczowe pojęcia
            Najważniejsze definicje i pojęcia (3-5 punktów)
            
            ## ⚡ Główne zasady
            Fundamentalne zasady i reguły (3-5 punktów)
            
            ## 📊 Fakty i liczby
            Ważne parametry, limity, wartości
            
            ## ⚠️ Kluczowe zagrożenia
            Główne ryzyka i sposoby ich unikania
            
            ## 📝 Pamiętaj
            Lista najważniejszych rzeczy do zapamiętania
            
            ## 🎯 Szybki test
            3-5 krótkich pytań sprawdzających
            
            Maksymalnie 2 strony tekstu, konkretnie i na temat.""",
            
            'practical': """Jesteś instruktorem praktycznego szkolenia lotniczego.
            
            Wygeneruj treść skupioną na praktycznych aspektach:
            
            # Tytuł tematu
            
            ## 🛠️ Praktyczne zastosowanie
            Jak to wygląda w rzeczywistości
            
            ## 📋 Procedury krok po kroku
            Szczegółowe instrukcje wykonania
            
            ## 🎯 Typowe scenariusze
            Prawdziwe sytuacje z kabiny pilota
            
            ## ⚠️ Częste błędy
            Co może pójść nie tak i jak tego unikać
            
            ## 💡 Wskazówki praktyczne
            Triki i rady od doświadczonych pilotów
            
            ## 🎮 Ćwiczenia symulatorowe
            Scenariusze do treningu na symulatorze
            
            ## ✅ Lista kontrolna
            Punkt po punkcie co sprawdzać
            
            ## 🚨 Procedury awaryjne
            Co robić w sytuacjach nietypowych
            
            Fokus na praktykę, mniej teorii, więcej działania.""",
            
            'regulatory': """Jesteś specjalistą od przepisów lotniczych.
            
            Wygeneruj treść skupioną na aspektach prawnych:
            
            # Tytuł tematu
            
            ## ⚖️ Podstawa prawna
            Główne akty prawne i przepisy
            
            ## 🌍 Przepisy ICAO
            Międzynarodowe standardy i zalecane praktyki
            
            ## 🇪🇺 Regulacje EASA
            Europejskie przepisy wykonawcze
            
            ## 🇵🇱 Przepisy krajowe
            Polskie regulacje i interpretacje
            
            ## 📋 Wymagania szczegółowe
            Konkretne wymagania i standardy
            
            ## 📊 Limity i ograniczenia
            Wszystkie parametry i ograniczenia prawne
            
            ## 📝 Obowiązki i odpowiedzialność
            Kto za co odpowiada zgodnie z prawem
            
            ## ⚠️ Konsekwencje naruszenia
            Kary i sankcje za nieprzestrzeganie
            
            ## 📚 Źródła prawne
            Dokładne odniesienia do przepisów
            
            ## 🔄 Aktualizacje przepisów
            Najnowsze zmiany i nowelizacje
            
            Precyzyjnie, z numerami paragrafów i odniesień prawnych."""
        }
        
        return prompts.get(ai_type, prompts['comprehensive'])
    
    def _find_related_documents(self, title: str, description: str) -> List[str]:
        """Znajdź dokumenty powiązane z tematem"""
        uploads_dir = 'uploads'
        if not os.path.exists(uploads_dir):
            return []
        
        related_docs = []
        search_terms = [title.lower()]
        
        # Wyciągnij kluczowe słowa z opisu
        if description:
            words = re.findall(r'\b\w{4,}\b', description.lower())
            search_terms.extend(words[:10])  # Maksymalnie 10 słów kluczowych
        
        for filename in os.listdir(uploads_dir):
            if filename.endswith('.pdf'):
                filename_lower = filename.lower()
                
                # Sprawdź czy nazwa pliku zawiera któreś ze słów kluczowych
                for term in search_terms:
                    if term in filename_lower:
                        related_docs.append(filename)
                        break
        
        return list(set(related_docs))  # Usuń duplikaty
    
    def _save_generated_content(self, module_id: str, chapter_id: str = None, topic_id: str = None, content: str = ''):
        """Zapisz wygenerowaną treść do pliku"""
        content_dir = os.path.join(self.handbook_dir, 'content')
        os.makedirs(content_dir, exist_ok=True)
        
        # Ustal nazwę pliku na podstawie dostępnych parametrów
        if topic_id and chapter_id:
            filename = f"{module_id}_{chapter_id}_{topic_id}.md"
        elif chapter_id:
            filename = f"{module_id}_{chapter_id}.md"
        else:
            filename = f"{module_id}.md"
        
        filepath = os.path.join(content_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"💾 Zapisano treść: {filepath}")
    
    def _update_progress(self, module_id: str, chapter_id: str = None, topic_id: str = None, status: str = 'unknown'):
        """Zaktualizuj postęp generowania"""
        if 'progress' not in self.handbook_structure:
            self.handbook_structure['progress'] = {}
        
        # Ustal klucz na podstawie dostępnych parametrów
        if topic_id and chapter_id:
            key = f"{module_id}_{chapter_id}_{topic_id}"
        elif chapter_id:
            key = f"{module_id}_{chapter_id}"
        else:
            key = f"{module_id}"
        
        self.handbook_structure['progress'][key] = {
            'status': status,
            'updated_at': datetime.now().isoformat(),
            'module_id': module_id,
            'chapter_id': chapter_id,
            'topic_id': topic_id
        }
        
        self.save_progress()
    
    def get_progress_overview(self) -> Dict[str, Any]:
        """Pobierz przegląd postępu"""
        structure = self.get_handbook_structure()
        progress = structure.get('progress', {})
        
        total_items = 0
        completed_items = 0
        
        for module in structure.get('modules', []):
            for chapter in module.get('chapters', []):
                total_items += 1
                chapter_key = f"{module['id']}_{chapter['id']}"
                if chapter_key in progress and progress[chapter_key]['status'] == 'generated':
                    completed_items += 1
                
                for topic in chapter.get('topics', []):
                    total_items += 1
                    topic_key = f"{module['id']}_{chapter['id']}_{topic['id']}"
                    if topic_key in progress and progress[topic_key]['status'] == 'generated':
                        completed_items += 1
        
        completion_percentage = (completed_items / total_items * 100) if total_items > 0 else 0
        
        return {
            'total_items': total_items,
            'completed_items': completed_items,
            'completion_percentage': round(completion_percentage, 1),
            'modules_count': len(structure.get('modules', [])),
            'last_updated': structure.get('last_updated'),
            'progress_details': progress
        }
    
    def get_content(self, module_id: str, chapter_id: str = None, topic_id: str = None) -> Optional[str]:
        """Pobierz wygenerowaną treść"""
        content_dir = os.path.join(self.handbook_dir, 'content')
        
        if topic_id and chapter_id:
            filename = f"{module_id}_{chapter_id}_{topic_id}.md"
        elif chapter_id:
            filename = f"{module_id}_{chapter_id}.md"
        else:
            filename = f"{module_id}.md"
        
        filepath = os.path.join(content_dir, filename)
        
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        
        return None
    
    def edit_content(self, module_id: str, chapter_id: str = None, topic_id: str = None, new_content: str = ''):
        """Edytuj treść rozdziału/tematu"""
        self._save_generated_content(module_id, chapter_id, topic_id, new_content)
        self._update_progress(module_id, chapter_id, topic_id, 'edited')
        
        if topic_id and chapter_id:
            print(f"✅ Zaktualizowano treść tematu: {module_id}/{chapter_id}/{topic_id}")
        elif chapter_id:
            print(f"✅ Zaktualizowano treść rozdziału: {module_id}/{chapter_id}")
        else:
            print(f"✅ Zaktualizowano treść modułu: {module_id}")
    
    def export_handbook(self, format_type: str = 'markdown') -> str:
        """Eksportuj cały podręcznik do jednego pliku"""
        structure = self.get_handbook_structure()
        
        if format_type == 'markdown':
            return self._export_to_markdown(structure)
        elif format_type == 'html':
            return self._export_to_html(structure)
        else:
            raise Exception(f"Nieobsługiwany format: {format_type}")
    
    def _export_to_markdown(self, structure: Dict[str, Any]) -> str:
        """Eksportuj do Markdown"""
        content = f"# {structure.get('title', 'Podręcznik ATPL')}\n\n"
        content += f"{structure.get('description', '')}\n\n"
        content += f"**Łączna liczba godzin:** {structure.get('total_hours', 'N/A')}\n\n"
        content += "---\n\n"
        
        for module in structure.get('modules', []):
            content += f"# {module['title']}\n\n"
            content += f"{module.get('description', '')}\n\n"
            content += f"**Godziny:** {module.get('hours', 'N/A')}\n\n"
            
            for chapter in module.get('chapters', []):
                content += f"## {chapter['title']}\n\n"
                
                # Dodaj treść rozdziału jeśli istnieje
                chapter_content = self.get_content(module['id'], chapter['id'])
                if chapter_content:
                    content += chapter_content + "\n\n"
                else:
                    content += f"{chapter.get('description', '')}\n\n"
                    content += "*Treść jeszcze nie została wygenerowana*\n\n"
                
                for topic in chapter.get('topics', []):
                    content += f"### {topic['title']}\n\n"
                    
                    # Dodaj treść tematu jeśli istnieje
                    topic_content = self.get_content(module['id'], chapter['id'], topic['id'])
                    if topic_content:
                        content += topic_content + "\n\n"
                    else:
                        content += f"{topic.get('description', '')}\n\n"
                        content += "*Treść jeszcze nie została wygenerowana*\n\n"
        
        # Zapisz eksport
        export_dir = os.path.join(self.handbook_dir, 'exports')
        os.makedirs(export_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        export_path = os.path.join(export_dir, f'atpl_handbook_{timestamp}.md')
        
        with open(export_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"📄 Podręcznik wyeksportowany: {export_path}")
        return export_path
    
    def save_progress(self):
        """Zapisz postęp do pliku"""
        self.handbook_structure['last_updated'] = datetime.now().isoformat()
        
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(self.handbook_structure, f, ensure_ascii=False, indent=2)
    
    def load_progress(self):
        """Załaduj postęp z pliku"""
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    self.handbook_structure = json.load(f)
                print(f"📖 Załadowano postęp podręcznika")
            except Exception as e:
                print(f"⚠️  Błąd ładowania postępu: {e}")
                self.handbook_structure = {}
        else:
            self.handbook_structure = {}
    
    def reset_handbook(self):
        """Resetuj cały podręcznik"""
        import shutil
        
        if os.path.exists(self.handbook_dir):
            shutil.rmtree(self.handbook_dir)
        
        os.makedirs(self.handbook_dir, exist_ok=True)
        self.handbook_structure = {}
        
        print("🔄 Podręcznik został zresetowany")


# Globalna instancja generatora
_handbook_generator = None

def get_handbook_generator():
    """Pobierz globalną instancję generatora podręcznika"""
    global _handbook_generator
    if _handbook_generator is None:
        _handbook_generator = ATPLHandbookGenerator()
    return _handbook_generator
