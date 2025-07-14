// Avioner AI Bot - Chat Application JavaScript
// Wersja: 2.0 - Kompletna przebudowa

class AvioneChat {
    constructor() {
        this.socket = null;
        this.sessionId = null;
        this.isConnected = false;
        this.currentFeedback = null;
        this.stats = {
            questions: 0,
            documents: 0,
            startTime: Date.now(),
            responses: [],
            totalMessages: 0
        };
        
        console.log('🚀 Avioner AI Bot - Inicjalizacja klasy AvioneChat');
    }

    // Inicjalizacja aplikacji
    async init() {
        try {
            console.log('🔧 Inicjalizacja aplikacji...');
            
            // Pobierz session_id z serwera
            this.sessionId = window.SERVER_SESSION_ID || this.generateSessionId();
            console.log('📋 Session ID:', this.sessionId);
            
            // Inicjalizuj elementy DOM najpierw
            this.initDOM();
            
            // Inicjalizuj Socket.IO
            await this.initSocket();
            await this.initSocket();
            
            // Załaduj dokumenty
            await this.loadDocuments();
            
            // Uruchom licznik czasu
            this.startSessionTimer();
            
            console.log('✅ Aplikacja zainicjalizowana pomyślnie');
            
        } catch (error) {
            console.error('❌ Błąd podczas inicjalizacji:', error);
            this.showError('Błąd inicjalizacji aplikacji');
        }
    }

    // Inicjalizacja Socket.IO
    async initSocket() {
        return new Promise((resolve, reject) => {
            try {
                console.log('🔌 Łączenie z Socket.IO...');
                
                this.socket = io({
                    transports: ['websocket', 'polling'],
                    timeout: 20000,
                    reconnection: true,
                    reconnectionAttempts: 5,
                    reconnectionDelay: 1000
                });

                this.socket.on('connect', () => {
                    console.log('✅ Socket.IO połączony:', this.socket.id);
                    this.isConnected = true;
                    this.updateConnectionStatus(true);
                    resolve();
                });

                this.socket.on('disconnect', () => {
                    console.log('❌ Socket.IO rozłączony');
                    this.isConnected = false;
                    this.updateConnectionStatus(false);
                });

                this.socket.on('response', (data) => {
                    console.log('📨 Otrzymano odpowiedź:', data);
                    this.handleResponse(data);
                });

                this.socket.on('error', (error) => {
                    console.error('❌ Socket.IO błąd:', error);
                    this.showError('Błąd połączenia z serwerem');
                    reject(error);
                });

                this.socket.on('connect_error', (error) => {
                    console.error('❌ Socket.IO błąd połączenia:', error);
                    this.updateConnectionStatus(false);
                    reject(error);
                });

            } catch (error) {
                console.error('❌ Błąd inicjalizacji Socket.IO:', error);
                reject(error);
            }
        });
    }

    // Inicjalizacja elementów DOM
    initDOM() {
        console.log('🎨 Inicjalizacja elementów DOM...');
        
        // Cache elementów DOM
        this.elements = {
            chatContainer: document.getElementById('chatContainer'),
            messageInput: document.getElementById('messageInput'),
            sendBtn: document.getElementById('sendBtn'),
            messageCount: document.getElementById('messageCount'),
            questionsCount: document.getElementById('questionsCount'),
            documentsCount: document.getElementById('documentsCount'),
            sessionTime: document.getElementById('sessionTime'),
            documentsList: document.getElementById('documentsList'),
            charCount: document.getElementById('charCount'),
            connectionDot: document.getElementById('connectionDot'),
            connectionText: document.getElementById('connectionText'),
            welcomeMessage: document.getElementById('welcomeMessage'),
            
            // Feedback modal
            feedbackModal: document.getElementById('feedbackModal'),
            feedbackPositive: document.getElementById('feedbackPositive'),
            feedbackNegative: document.getElementById('feedbackNegative'),
            feedbackDescription: document.getElementById('feedbackDescription'),
            feedbackCancel: document.getElementById('feedbackCancel'),
            feedbackSubmit: document.getElementById('feedbackSubmit')
        };

        // Sprawdź czy elementy istnieją
        const missingElements = [];
        for (const [key, element] of Object.entries(this.elements)) {
            if (!element) {
                missingElements.push(key);
            }
        }

        if (missingElements.length > 0) {
            console.warn('⚠️ Brakujące elementy DOM:', missingElements);
        }

        // Event listenery
        this.setupEventListeners();
    }

    // Konfiguracja event listenerów
    setupEventListeners() {
        console.log('🎯 Konfiguracja event listenerów...');
        
        // Wysyłanie wiadomości
        if (this.elements.sendBtn) {
            this.elements.sendBtn.addEventListener('click', () => this.sendMessage());
        }

        // Enter w textarea
        if (this.elements.messageInput) {
            this.elements.messageInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.sendMessage();
                }
            });

            // Licznik znaków
            this.elements.messageInput.addEventListener('input', () => {
                const length = this.elements.messageInput.value.length;
                if (this.elements.charCount) {
                    this.elements.charCount.textContent = `${length}/1000`;
                }
            });
        }

        // Quick questions
        document.querySelectorAll('.quick-question-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const question = btn.getAttribute('data-question');
                if (question) {
                    this.sendQuickQuestion(question);
                }
            });
        });

        // Feedback modal
        if (this.elements.feedbackPositive) {
            this.elements.feedbackPositive.addEventListener('click', () => {
                this.setFeedbackType('positive');
            });
        }

        if (this.elements.feedbackNegative) {
            this.elements.feedbackNegative.addEventListener('click', () => {
                this.setFeedbackType('negative');
            });
        }

        if (this.elements.feedbackCancel) {
            this.elements.feedbackCancel.addEventListener('click', () => {
                this.closeFeedbackModal();
            });
        }

        if (this.elements.feedbackSubmit) {
            this.elements.feedbackSubmit.addEventListener('click', () => {
                this.submitFeedback();
            });
        }

        // Zamknięcie modala po kliknięciu tła
        if (this.elements.feedbackModal) {
            this.elements.feedbackModal.addEventListener('click', (e) => {
                if (e.target === this.elements.feedbackModal) {
                    this.closeFeedbackModal();
                }
            });
        }
    }

    // Wysłanie wiadomości
    async sendMessage() {
        if (!this.elements.messageInput) return;
        
        const message = this.elements.messageInput.value.trim();
        if (!message) {
            console.warn('⚠️ Pusta wiadomość');
            return;
        }

        if (!this.isConnected) {
            this.showError('Brak połączenia z serwerem');
            return;
        }

        try {
            console.log('📤 Wysyłanie wiadomości:', message);
            
            // Dodaj wiadomość użytkownika do chatu
            this.addUserMessage(message);
            
            // Wyczyść input
            this.elements.messageInput.value = '';
            if (this.elements.charCount) {
                this.elements.charCount.textContent = '0/1000';
            }
            
            // Ukryj welcome message
            this.hideWelcomeMessage();
            
            // Pokaż typing indicator
            this.showTypingIndicator();
            
            // Wyślij przez Socket.IO
            this.socket.emit('send_message', {
                message: message,
                session_id: this.sessionId,
                timestamp: new Date().toISOString()
            });
            
            // Aktualizuj statystyki
            this.stats.questions++;
            this.stats.totalMessages++;
            this.updateStats();
            
        } catch (error) {
            console.error('❌ Błąd wysyłania wiadomości:', error);
            this.showError('Błąd wysyłania wiadomości');
            this.hideTypingIndicator();
        }
    }

    // Wysłanie szybkiego pytania
    sendQuickQuestion(question) {
        if (this.elements.messageInput) {
            this.elements.messageInput.value = question;
            this.sendMessage();
        }
    }

    // Obsługa odpowiedzi z serwera
    handleResponse(data) {
        console.log('📥 Przetwarzanie odpowiedzi:', data);
        
        try {
            this.hideTypingIndicator();
            
            if (data.error) {
                this.showError(data.error);
                return;
            }

            // Dodaj odpowiedź asystenta
            this.addAssistantMessage(data.response || data.message);
            
            // Aktualizuj statystyki
            if (data.documents_used) {
                this.stats.documents = Math.max(this.stats.documents, data.documents_used);
            }
            
            // Zapisz czas odpowiedzi
            this.stats.responses.push({
                timestamp: Date.now(),
                response_time: data.response_time || 0
            });
            
            this.updateStats();
            
        } catch (error) {
            console.error('❌ Błąd przetwarzania odpowiedzi:', error);
            this.showError('Błąd przetwarzania odpowiedzi');
        }
    }

    // Dodanie wiadomości użytkownika
    addUserMessage(message) {
        const messageElement = this.createMessageElement({
            type: 'user',
            content: message,
            timestamp: new Date()
        });
        
        this.appendMessage(messageElement);
    }

    // Dodanie wiadomości asystenta
    addAssistantMessage(message) {
        const messageElement = this.createMessageElement({
            type: 'assistant',
            content: message,
            timestamp: new Date()
        });
        
        this.appendMessage(messageElement);
    }

    // Tworzenie elementu wiadomości
    createMessageElement(data) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${data.type}-message mb-6`;
        
        const isUser = data.type === 'user';
        const timestamp = this.formatTime(data.timestamp);
        
        messageDiv.innerHTML = `
            <div class="flex ${isUser ? 'justify-end' : 'justify-start'}">
                <div class="max-w-3xl ${isUser ? 'bg-blue-600 text-white' : 'bg-white border'} rounded-lg p-4 shadow-sm">
                    <div class="flex items-center mb-2">
                        <div class="w-8 h-8 rounded-full ${isUser ? 'bg-blue-500' : 'bg-gray-200'} flex items-center justify-center mr-3">
                            <i class="fas ${isUser ? 'fa-user' : 'fa-robot'} text-sm ${isUser ? 'text-white' : 'text-gray-600'}"></i>
                        </div>
                        <div>
                            <div class="font-semibold text-sm">${isUser ? 'Ty' : 'Avioner AI Bot'}</div>
                            <div class="text-xs opacity-75">${timestamp}</div>
                        </div>
                    </div>
                    <div class="message-content">
                        ${this.formatMessageContent(data.content, !isUser)}
                    </div>
                </div>
            </div>
        `;
        
        return messageDiv;
    }

    // Formatowanie treści wiadomości
    formatMessageContent(content, isAssistant = false) {
        if (!content) return '';
        
        // Jeśli to odpowiedź asystenta, dodaj możliwość feedbacku
        if (isAssistant && typeof content === 'string') {
            // Podziel na sekcje (paragrafy, nagłówki, listy)
            const sections = this.splitIntoSections(content);
            
            return sections.map((section, index) => {
                const sectionId = `section-${Date.now()}-${index}`;
                return `
                    <div class="message-section" data-section-id="${sectionId}">
                        <div class="section-content">${section}</div>
                        <div class="section-feedback">
                            <button class="feedback-btn" onclick="avioneChat.openFeedbackModal('${sectionId}', this)" title="Oceń przydatność tej sekcji">
                                <i class="fas fa-thumbs-up"></i>
                            </button>
                        </div>
                    </div>
                `;
            }).join('');
        }
        
        return content;
    }

    // Podział odpowiedzi na sekcje do feedbacku
    splitIntoSections(content) {
        // Uproszczona logika - można rozbudować
        const sections = [];
        
        // Podział na podstawie HTML tagów lub pustych linii
        const parts = content.split(/\n\s*\n/);
        
        parts.forEach(part => {
            if (part.trim()) {
                sections.push(part.trim());
            }
        });
        
        return sections.length > 0 ? sections : [content];
    }

    // Dodanie wiadomości do chatu
    appendMessage(messageElement) {
        if (!this.elements.chatContainer) return;
        
        this.elements.chatContainer.appendChild(messageElement);
        this.scrollToBottom();
    }

    // Przewijanie do dołu
    scrollToBottom() {
        if (this.elements.chatContainer) {
            this.elements.chatContainer.scrollTop = this.elements.chatContainer.scrollHeight;
        }
    }

    // Ukrycie welcome message
    hideWelcomeMessage() {
        if (this.elements.welcomeMessage) {
            this.elements.welcomeMessage.style.display = 'none';
        }
    }

    // Pokazanie typing indicator
    showTypingIndicator() {
        if (this.typingIndicator) {
            this.typingIndicator.remove();
        }
        
        this.typingIndicator = document.createElement('div');
        this.typingIndicator.className = 'typing-indicator mb-6';
        this.typingIndicator.innerHTML = `
            <div class="flex justify-start">
                <div class="bg-gray-200 rounded-lg p-4 shadow-sm">
                    <div class="flex items-center">
                        <div class="w-8 h-8 rounded-full bg-gray-300 flex items-center justify-center mr-3">
                            <i class="fas fa-robot text-sm text-gray-600"></i>
                        </div>
                        <div class="flex space-x-1">
                            <div class="w-2 h-2 bg-gray-400 rounded-full animate-pulse"></div>
                            <div class="w-2 h-2 bg-gray-400 rounded-full animate-pulse delay-100"></div>
                            <div class="w-2 h-2 bg-gray-400 rounded-full animate-pulse delay-200"></div>
                        </div>
                        <span class="ml-2 text-sm text-gray-600">Avioner AI Bot pisze...</span>
                    </div>
                </div>
            </div>
        `;
        
        if (this.elements.chatContainer) {
            this.elements.chatContainer.appendChild(this.typingIndicator);
            this.scrollToBottom();
        }
    }

    // Ukrycie typing indicator
    hideTypingIndicator() {
        if (this.typingIndicator) {
            this.typingIndicator.remove();
            this.typingIndicator = null;
        }
    }

    // Aktualizacja statusu połączenia
    updateConnectionStatus(connected) {
        if (this.elements.connectionDot && this.elements.connectionText) {
            if (connected) {
                this.elements.connectionDot.className = 'w-3 h-3 bg-green-400 rounded-full animate-pulse';
                this.elements.connectionText.textContent = 'Połączono';
            } else {
                this.elements.connectionDot.className = 'w-3 h-3 bg-red-400 rounded-full';
                this.elements.connectionText.textContent = 'Rozłączono';
            }
        }
    }

    // Aktualizacja statystyk
    updateStats() {
        if (this.elements.questionsCount) {
            this.elements.questionsCount.textContent = this.stats.questions.toString();
        }
        
        if (this.elements.documentsCount) {
            this.elements.documentsCount.textContent = this.stats.documents.toString();
        }
        
        if (this.elements.messageCount) {
            this.elements.messageCount.textContent = this.stats.totalMessages.toString();
        }
    }

    // Licznik czasu sesji
    startSessionTimer() {
        setInterval(() => {
            const elapsed = Date.now() - this.stats.startTime;
            const minutes = Math.floor(elapsed / 60000);
            const seconds = Math.floor((elapsed % 60000) / 1000);
            
            if (this.elements.sessionTime) {
                this.elements.sessionTime.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
            }
        }, 1000);
    }

    // Ładowanie listy dokumentów
    async loadDocuments() {
        try {
            console.log('📄 Ładowanie listy dokumentów...');
            
            const response = await fetch('/api/documents');
            const documents = await response.json();
            
            if (this.elements.documentsList) {
                if (documents.length > 0) {
                    this.elements.documentsList.innerHTML = documents.map(doc => `
                        <div class="flex items-center justify-between p-2 bg-gray-50 rounded">
                            <div class="flex items-center">
                                <i class="fas fa-file-pdf text-red-500 mr-2"></i>
                                <span class="text-xs truncate">${doc.name}</span>
                            </div>
                            <span class="text-xs text-gray-500">${doc.size}</span>
                        </div>
                    `).join('');
                } else {
                    this.elements.documentsList.innerHTML = `
                        <div class="text-center py-4 text-gray-500">
                            <i class="fas fa-inbox mb-2"></i>
                            <p class="text-sm">Brak dokumentów</p>
                        </div>
                    `;
                }
            }
            
        } catch (error) {
            console.error('❌ Błąd ładowania dokumentów:', error);
            if (this.elements.documentsList) {
                this.elements.documentsList.innerHTML = `
                    <div class="text-center py-4 text-red-500">
                        <i class="fas fa-exclamation-triangle mb-2"></i>
                        <p class="text-sm">Błąd ładowania</p>
                    </div>
                `;
            }
        }
    }

    // Otwieranie modala feedbacku
    openFeedbackModal(sectionId, buttonElement) {
        const section = document.querySelector(`[data-section-id="${sectionId}"]`);
        if (!section) return;
        
        const content = section.querySelector('.section-content').innerHTML;
        
        this.currentFeedback = {
            sectionId: sectionId,
            content: content,
            type: null
        };
        
        // Pokaż modal
        if (this.elements.feedbackModal) {
            this.elements.feedbackModal.classList.remove('hidden');
        }
        
        // Reset formularza
        this.resetFeedbackForm();
    }

    // Ustawienie typu feedbacku
    setFeedbackType(type) {
        if (this.currentFeedback) {
            this.currentFeedback.type = type;
        }
        
        // Aktualizuj style przycisków
        if (this.elements.feedbackPositive && this.elements.feedbackNegative) {
            this.elements.feedbackPositive.classList.toggle('bg-green-500', type === 'positive');
            this.elements.feedbackPositive.classList.toggle('text-white', type === 'positive');
            this.elements.feedbackNegative.classList.toggle('bg-red-500', type === 'negative');
            this.elements.feedbackNegative.classList.toggle('text-white', type === 'negative');
        }
    }

    // Zamknięcie modala feedbacku
    closeFeedbackModal() {
        if (this.elements.feedbackModal) {
            this.elements.feedbackModal.classList.add('hidden');
        }
        
        this.currentFeedback = null;
        this.resetFeedbackForm();
    }

    // Reset formularza feedbacku
    resetFeedbackForm() {
        if (this.elements.feedbackDescription) {
            this.elements.feedbackDescription.value = '';
        }
        
        if (this.elements.feedbackPositive && this.elements.feedbackNegative) {
            this.elements.feedbackPositive.classList.remove('bg-green-500', 'text-white');
            this.elements.feedbackNegative.classList.remove('bg-red-500', 'text-white');
        }
    }

    // Wysłanie feedbacku
    async submitFeedback() {
        if (!this.currentFeedback || !this.currentFeedback.type) {
            this.showError('Wybierz ocenę');
            return;
        }
        
        try {
            const feedbackData = {
                session_id: this.sessionId,
                section_id: this.currentFeedback.sectionId,
                content: this.currentFeedback.content,
                type: this.currentFeedback.type,
                description: this.elements.feedbackDescription?.value || '',
                timestamp: new Date().toISOString()
            };
            
            console.log('📤 Wysyłanie feedbacku:', feedbackData);
            
            const response = await fetch('/api/feedback', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(feedbackData)
            });
            
            if (response.ok) {
                this.showSuccess('Feedback zapisany');
                this.closeFeedbackModal();
                
                // Oznacz sekcję jako ocenioną
                const section = document.querySelector(`[data-section-id="${this.currentFeedback.sectionId}"]`);
                if (section) {
                    const feedbackBtn = section.querySelector('.feedback-btn');
                    if (feedbackBtn) {
                        feedbackBtn.innerHTML = `<i class="fas fa-check text-green-500"></i>`;
                        feedbackBtn.disabled = true;
                    }
                }
                
            } else {
                this.showError('Błąd zapisywania feedbacku');
            }
            
        } catch (error) {
            console.error('❌ Błąd wysyłania feedbacku:', error);
            this.showError('Błąd wysyłania feedbacku');
        }
    }

    // Pokazanie błędu
    showError(message) {
        console.error('❌ Błąd:', message);
        // Można dodać toast notification
        alert('Błąd: ' + message);
    }

    // Pokazanie sukcesu
    showSuccess(message) {
        console.log('✅ Sukces:', message);
        // Można dodać toast notification
        alert('Sukces: ' + message);
    }

    // Formatowanie czasu
    formatTime(date) {
        return new Date(date).toLocaleTimeString('pl-PL', {
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    // Generowanie session ID
    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
}

// Globalna instancja
let avioneChat = null;

// Inicjalizacja po załadowaniu strony
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Avioner AI Bot - Inicjalizacja...');
    
    avioneChat = new AvioneChat();
    avioneChat.init().catch(error => {
        console.error('❌ Błąd inicjalizacji:', error);
    });
});

// Funkcje globalne (dla kompatybilności)
function initializeChat() {
    console.log('🔧 initializeChat() wywoływana (kompatybilność)');
    if (avioneChat) {
        avioneChat.init();
    }
}

function sendQuickAction(question) {
    console.log('⚡ sendQuickAction():', question);
    if (avioneChat) {
        avioneChat.sendQuickQuestion(question);
    }
}

function clearChat() {
    console.log('🧹 clearChat()');
    if (avioneChat && avioneChat.elements.chatContainer) {
        avioneChat.elements.chatContainer.innerHTML = '';
        avioneChat.stats.questions = 0;
        avioneChat.stats.totalMessages = 0;
        avioneChat.updateStats();
    }
}

function exportChat() {
    console.log('💾 exportChat()');
    // Implementacja eksportu
    alert('Funkcja eksportu będzie wkrótce dostępna');
}

// Export dla innych skryptów
window.avioneChat = avioneChat;
window.AvioneChat = AvioneChat;
