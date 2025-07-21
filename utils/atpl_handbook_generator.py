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
import fitz  # PyMuPDF dla lepszego OCR
from openai import OpenAI
import re


class ATPLHandbookGenerator:
    """Generator podręcznika ATPL na podstawie dostępnych dokumentów"""
    
    def __init__(self):
        self.client = OpenAI()
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
        """Wyciągnij tekst z PDF używając PyMuPDF (lepsze OCR)"""
        try:
            doc = fitz.open(pdf_path)
            text = ""
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text += page.get_text()
            
            doc.close()
            return text
        except Exception as e:
            print(f"❌ Błąd wyciągania tekstu z PDF: {e}")
            # Fallback do PyPDF2
            return self._extract_text_pypdf2(pdf_path)
    
    def _extract_text_pypdf2(self, pdf_path: str) -> str:
        """Fallback - wyciągnij tekst używając PyPDF2"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                
                for page in pdf_reader.pages:
                    text += page.extract_text()
                
                return text
        except Exception as e:
            print(f"❌ Błąd PyPDF2: {e}")
            return ""
    
    def analyze_program_structure(self) -> Dict[str, Any]:
        """Analizuj strukturę programu ATPL używając AI"""
        if not self.program_file:
            if not self.find_program_file():
                raise Exception("Nie znaleziono pliku z programem ATPL")
        
        print(f"📄 Analizuję strukturę programu: {self.program_file}")
        
        # Wyciągnij tekst z PDF
        program_text = self.extract_text_from_pdf(self.program_file)
        
        if not program_text.strip():
            raise Exception("Nie udało się wyciągnąć tekstu z pliku programu")
        
        # Użyj AI do analizy struktury
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
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
                        Używaj polskich nazw dla części po polsku i angielskich dla części w języku angielskim."""
                    },
                    {
                        "role": "user",
                        "content": f"Przeanalizuj następujący tekst programu szkolenia ATPL:\n\n{program_text[:15000]}"  # Ograniczenie dla API
                    }
                ],
                temperature=0.3
            )
            
            structure_text = response.choices[0].message.content
            
            # Wyciągnij JSON z odpowiedzi
            json_match = re.search(r'\{.*\}', structure_text, re.DOTALL)
            if json_match:
                structure = json.loads(json_match.group())
            else:
                # Spróbuj sparsować całą odpowiedź jako JSON
                structure = json.loads(structure_text)
            
            # Zapisz strukturę
            self.handbook_structure = structure
            self.save_progress()
            
            print(f"✅ Struktura programu przeanalizowana: {len(structure.get('modules', []))} modułów")
            return structure
            
        except Exception as e:
            print(f"❌ Błąd analizy struktury: {e}")
            raise e
    
    def get_handbook_structure(self) -> Dict[str, Any]:
        """Pobierz strukturę podręcznika"""
        if not self.handbook_structure:
            return self.analyze_program_structure()
        return self.handbook_structure
    
    def generate_chapter_content(self, module_id: str, chapter_id: str, topic_id: str = None) -> str:
        """Generuj treść rozdziału/tematu używając AI i dostępnych dokumentów"""
        structure = self.get_handbook_structure()
        
        # Znajdź odpowiedni element struktury
        target_item = None
        context = ""
        
        for module in structure.get('modules', []):
            if module['id'] == module_id:
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
            raise Exception(f"Nie znaleziono elementu: {module_id}/{chapter_id}/{topic_id}")
        
        # Znajdź powiązane dokumenty
        related_docs = self._find_related_documents(target_item['title'], target_item.get('description', ''))
        
        # Generuj treść używając AI
        try:
            system_prompt = """Jesteś ekspertem lotniczym i instruktorem ATPL. Tworzysz profesjonalny podręcznik szkoleniowy.
            
            Wygeneruj kompletną treść dla podanego tematu w formacie markdown z następującymi sekcjami:
            
            # Tytuł tematu
            
            ## Wprowadzenie
            Krótkie wprowadzenie do tematu
            
            ## Cele szkoleniowe
            - Cel 1
            - Cel 2
            
            ## Teoria
            Szczegółowe wyjaśnienie teorii z przykładami
            
            ## Procedury (jeśli dotyczy)
            Krok po kroku procedury
            
            ## Przykłady praktyczne
            Rzeczywiste przykłady z lotnictwa
            
            ## Regulacje i przepisy
            Odnośne przepisy ICAO, EASA itp.
            
            ## Pytania kontrolne
            5-10 pytań sprawdzających zrozumienie
            
            ## Dodatkowe źródła
            Bibliografia i dodatkowe materiały
            
            Użyj profesjonalnego języka, dodaj diagramy w formie tekstu ASCII gdzie to możliwe.
            Opieraj się na faktach i aktualnych przepisach lotniczych."""
            
            user_prompt = f"""Kontekst: {context}
            
            Tytuł: {target_item['title']}
            Opis: {target_item.get('description', '')}
            
            Powiązane dokumenty dostępne w systemie:
            {chr(10).join(related_docs[:5])}  # Maksymalnie 5 dokumentów
            
            Wygeneruj kompletną treść szkoleniową dla tego tematu."""
            
            response = self.client.chat.completions.create(
                model="gpt-4",
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
    
    def _save_generated_content(self, module_id: str, chapter_id: str, topic_id: str, content: str):
        """Zapisz wygenerowaną treść do pliku"""
        content_dir = os.path.join(self.handbook_dir, 'content')
        os.makedirs(content_dir, exist_ok=True)
        
        if topic_id:
            filename = f"{module_id}_{chapter_id}_{topic_id}.md"
        else:
            filename = f"{module_id}_{chapter_id}.md"
        
        filepath = os.path.join(content_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"💾 Zapisano treść: {filepath}")
    
    def _update_progress(self, module_id: str, chapter_id: str, topic_id: str, status: str):
        """Zaktualizuj postęp generowania"""
        if 'progress' not in self.handbook_structure:
            self.handbook_structure['progress'] = {}
        
        key = f"{module_id}_{chapter_id}"
        if topic_id:
            key += f"_{topic_id}"
        
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
    
    def get_content(self, module_id: str, chapter_id: str, topic_id: str = None) -> Optional[str]:
        """Pobierz wygenerowaną treść"""
        content_dir = os.path.join(self.handbook_dir, 'content')
        
        if topic_id:
            filename = f"{module_id}_{chapter_id}_{topic_id}.md"
        else:
            filename = f"{module_id}_{chapter_id}.md"
        
        filepath = os.path.join(content_dir, filename)
        
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        
        return None
    
    def edit_content(self, module_id: str, chapter_id: str, topic_id: str, new_content: str):
        """Edytuj treść rozdziału/tematu"""
        self._save_generated_content(module_id, chapter_id, topic_id, new_content)
        self._update_progress(module_id, chapter_id, topic_id, 'edited')
        print(f"✅ Zaktualizowano treść: {module_id}/{chapter_id}/{topic_id}")
    
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
