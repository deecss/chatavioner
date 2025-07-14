#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Moduł Watchdog do monitorowania katalogu uploads
"""
import os
import time
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from app.models import UploadIndex

class PDFUploadHandler(FileSystemEventHandler):
    """Handler do obsługi nowych plików PDF"""
    
    def __init__(self):
        self.upload_index = UploadIndex()
    
    def on_created(self, event):
        """Obsługuje dodanie nowego pliku"""
        if event.is_directory:
            return
        
        filepath = event.src_path
        filename = os.path.basename(filepath)
        
        # Sprawdź czy to plik PDF
        if filename.lower().endswith('.pdf'):
            print(f"Nowy plik PDF wykryty: {filename}")
            
            # Poczekaj chwilę na zakończenie zapisu
            time.sleep(1)
            
            # Dodaj do indeksu
            try:
                file_size = os.path.getsize(filepath)
                self.upload_index.add_file(filename, {'size': file_size})
                print(f"Plik {filename} dodany do indeksu")
            except Exception as e:
                print(f"Błąd podczas dodawania pliku do indeksu: {str(e)}")
    
    def on_deleted(self, event):
        """Obsługuje usunięcie pliku"""
        if event.is_directory:
            return
        
        filename = os.path.basename(event.src_path)
        
        if filename.lower().endswith('.pdf'):
            print(f"Plik PDF usunięty: {filename}")
            
            # Usuń z indeksu
            try:
                if self.upload_index.remove_file(filename):
                    print(f"Plik {filename} usunięty z indeksu")
            except Exception as e:
                print(f"Błąd podczas usuwania pliku z indeksu: {str(e)}")

def start_watcher():
    """Uruchamia watchdog w osobnym wątku"""
    def run_watcher():
        upload_folder = 'uploads'
        
        # Utwórz katalog jeśli nie istnieje
        os.makedirs(upload_folder, exist_ok=True)
        
        # Inicjalizacja indeksu z istniejącymi plikami
        upload_index = UploadIndex()
        existing_files = upload_index.get_all_files()
        
        # Skanuj istniejące pliki
        for filename in os.listdir(upload_folder):
            if filename.lower().endswith('.pdf') and filename not in existing_files:
                filepath = os.path.join(upload_folder, filename)
                try:
                    file_size = os.path.getsize(filepath)
                    upload_index.add_file(filename, {'size': file_size})
                    print(f"Istniejący plik {filename} dodany do indeksu")
                except Exception as e:
                    print(f"Błąd podczas dodawania istniejącego pliku: {str(e)}")
        
        # Uruchom observer
        event_handler = PDFUploadHandler()
        observer = Observer()
        observer.schedule(event_handler, upload_folder, recursive=False)
        observer.start()
        
        print(f"Watchdog uruchomiony dla katalogu: {upload_folder}")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
            print("Watchdog zatrzymany")
        
        observer.join()
    
    # Uruchom w osobnym wątku
    watcher_thread = threading.Thread(target=run_watcher, daemon=True)
    watcher_thread.start()
    
    return watcher_thread

if __name__ == "__main__":
    # Test watchdog
    start_watcher()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Zatrzymywanie watchdog...")
