#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Skrypt do uczenia na podstawie feedbacku
"""
import os
import json
from datetime import datetime
from app.models import ChatSession, UploadIndex

class FeedbackTrainer:
    """Klasa do przetwarzania feedbacku na dane treningowe"""
    
    def __init__(self):
        self.feedback_dir = 'feedback'
        self.history_dir = 'history'
        self.output_dir = 'training_data'
        os.makedirs(self.output_dir, exist_ok=True)
    
    def collect_feedback(self):
        """Zbiera wszystkie feedbacki z sesji"""
        all_feedback = []
        
        if not os.path.exists(self.feedback_dir):
            return all_feedback
        
        for filename in os.listdir(self.feedback_dir):
            if filename.endswith('.json'):
                session_id = filename.replace('.json', '')
                
                try:
                    with open(f'{self.feedback_dir}/{filename}', 'r', encoding='utf-8') as f:
                        feedback_data = json.load(f)
                    
                    # Pobierz historię sesji
                    chat_session = ChatSession(session_id)
                    history = chat_session.load_history()
                    
                    # Połącz feedback z historią
                    for fb in feedback_data:
                        fb['session_id'] = session_id
                        fb['history'] = history
                        all_feedback.append(fb)
                        
                except Exception as e:
                    print(f"Błąd podczas przetwarzania feedbacku {filename}: {str(e)}")
        
        return all_feedback
    
    def process_positive_feedback(self, feedback_data):
        """Przetwarza pozytywny feedback (👍)"""
        positive_examples = []
        
        for fb in feedback_data:
            if fb.get('type') == 'positive':
                # Znajdź odpowiedź asystenta w historii
                history = fb.get('history', [])
                for i, msg in enumerate(history):
                    if msg['role'] == 'assistant':
                        # Znajdź poprzednie pytanie użytkownika
                        if i > 0 and history[i-1]['role'] == 'user':
                            positive_examples.append({
                                'question': history[i-1]['content'],
                                'answer': msg['content'],
                                'session_id': fb['session_id'],
                                'timestamp': fb['timestamp']
                            })
        
        return positive_examples
    
    def process_negative_feedback(self, feedback_data):
        """Przetwarza negatywny feedback (👎)"""
        negative_examples = []
        
        for fb in feedback_data:
            if fb.get('type') == 'negative':
                # Znajdź odpowiedź asystenta w historii
                history = fb.get('history', [])
                for i, msg in enumerate(history):
                    if msg['role'] == 'assistant':
                        # Znajdź poprzednie pytanie użytkownika
                        if i > 0 and history[i-1]['role'] == 'user':
                            negative_examples.append({
                                'question': history[i-1]['content'],
                                'poor_answer': msg['content'],
                                'session_id': fb['session_id'],
                                'timestamp': fb['timestamp'],
                                'improvement_needed': True
                            })
        
        return negative_examples
    
    def process_improvement_feedback(self, feedback_data):
        """Przetwarza feedback z prośbami o rozwinięcie (✏️)"""
        improvement_examples = []
        
        for fb in feedback_data:
            if fb.get('type') == 'improve':
                # Znajdź odpowiedź asystenta w historii
                history = fb.get('history', [])
                for i, msg in enumerate(history):
                    if msg['role'] == 'assistant':
                        # Znajdź poprzednie pytanie użytkownika
                        if i > 0 and history[i-1]['role'] == 'user':
                            improvement_examples.append({
                                'question': history[i-1]['content'],
                                'original_answer': msg['content'],
                                'improvement_request': fb.get('content', ''),
                                'session_id': fb['session_id'],
                                'timestamp': fb['timestamp']
                            })
        
        return improvement_examples
    
    def generate_training_jsonl(self):
        """Generuje plik JSONL do fine-tuningu"""
        feedback_data = self.collect_feedback()
        
        if not feedback_data:
            print("Brak danych feedbacku do przetworzenia")
            return
        
        # Przetwórz różne typy feedbacku
        positive_examples = self.process_positive_feedback(feedback_data)
        negative_examples = self.process_negative_feedback(feedback_data)
        improvement_examples = self.process_improvement_feedback(feedback_data)
        
        # Generuj dane treningowe
        training_data = []
        
        # Przykłady pozytywne - wzmacniają dobre odpowiedzi
        for example in positive_examples:
            training_data.append({
                "messages": [
                    {"role": "user", "content": example['question']},
                    {"role": "assistant", "content": example['answer']}
                ],
                "metadata": {
                    "feedback_type": "positive",
                    "session_id": example['session_id'],
                    "timestamp": example['timestamp']
                }
            })
        
        # Przykłady negatywne - pokazują co poprawić
        for example in negative_examples:
            training_data.append({
                "messages": [
                    {"role": "system", "content": "Poprzednia odpowiedź otrzymała negatywny feedback. Zaproponuj lepszą odpowiedź."},
                    {"role": "user", "content": example['question']},
                    {"role": "assistant", "content": f"Rozumiem, że poprzednia odpowiedź nie była satysfakcjonująca. Pozwól mi udzielić lepszej odpowiedzi:\n\n{example['poor_answer']}\n\nCzy mogę rozwinąć jakiś konkretny aspekt?"}
                ],
                "metadata": {
                    "feedback_type": "negative",
                    "session_id": example['session_id'],
                    "timestamp": example['timestamp']
                }
            })
        
        # Przykłady z prośbami o rozwinięcie
        for example in improvement_examples:
            training_data.append({
                "messages": [
                    {"role": "user", "content": f"{example['question']}\n\nDodatkowe wyjaśnienie: {example['improvement_request']}"},
                    {"role": "assistant", "content": f"{example['original_answer']}\n\nRozwiniecie:\n{example['improvement_request']}"}
                ],
                "metadata": {
                    "feedback_type": "improve",
                    "session_id": example['session_id'],
                    "timestamp": example['timestamp']
                }
            })
        
        # Zapisz do pliku JSONL
        output_file = f"{self.output_dir}/training_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for item in training_data:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        
        print(f"Dane treningowe zapisane do: {output_file}")
        print(f"Liczba przykładów: {len(training_data)}")
        print(f"- Pozytywnych: {len(positive_examples)}")
        print(f"- Negatywnych: {len(negative_examples)}")
        print(f"- Do rozwinięcia: {len(improvement_examples)}")
        
        return output_file
    
    def generate_report(self):
        """Generuje raport z feedbacku"""
        feedback_data = self.collect_feedback()
        
        if not feedback_data:
            print("Brak danych feedbacku do analizy")
            return
        
        # Statystyki
        stats = {
            'total_feedback': len(feedback_data),
            'positive': len([f for f in feedback_data if f.get('type') == 'positive']),
            'negative': len([f for f in feedback_data if f.get('type') == 'negative']),
            'improve': len([f for f in feedback_data if f.get('type') == 'improve']),
            'sessions': len(set([f['session_id'] for f in feedback_data]))
        }
        
        # Raport
        report = {
            'generated_at': datetime.now().isoformat(),
            'statistics': stats,
            'feedback_data': feedback_data
        }
        
        # Zapisz raport
        report_file = f"{self.output_dir}/feedback_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"Raport feedbacku zapisany do: {report_file}")
        print(f"Statystyki:")
        print(f"- Łączna liczba feedbacków: {stats['total_feedback']}")
        print(f"- Pozytywnych: {stats['positive']}")
        print(f"- Negatywnych: {stats['negative']}")
        print(f"- Do rozwinięcia: {stats['improve']}")
        print(f"- Sesji: {stats['sessions']}")
        
        return report_file

def main():
    """Główna funkcja skryptu"""
    trainer = FeedbackTrainer()
    
    print("=== Aero-Chat Feedback Trainer ===")
    print("1. Generuj dane treningowe (JSONL)")
    print("2. Generuj raport feedbacku")
    print("3. Oba")
    
    choice = input("Wybierz opcję (1/2/3): ").strip()
    
    if choice == '1':
        trainer.generate_training_jsonl()
    elif choice == '2':
        trainer.generate_report()
    elif choice == '3':
        trainer.generate_report()
        trainer.generate_training_jsonl()
    else:
        print("Nieprawidłowy wybór")

if __name__ == "__main__":
    main()
