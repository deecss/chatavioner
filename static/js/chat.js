class ChatApp {
    constructor() {
        this.socket = null;
        this.sessionId = null;
        this.isConnected = false;
        this.messageIdCounter = 0;
        this.currentTypingMessageId = null;
        this.messageCount = 0;
        this.init();
    }

    init() {
        this.initSocket();
        this.initElements();
        this.bindEvents();
        this.startSession();
    }

    initSocket() {
        this.socket = io();
        
        this.socket.on('connect', () => {
            this.isConnected = true;
            this.updateConnectionStatus(true);
            console.log('✅ Połączono z serwerem');
        });

        this.socket.on('disconnect', () => {
            this.isConnected = false;
            this.updateConnectionStatus(false);
            console.log('❌ Rozłączono z serwerem');
        });

        this.socket.on('response_chunk', (data) => {
            this.handleResponseChunk(data);
        });

        this.socket.on('response_complete', (data) => {
            this.handleResponseComplete(data);
        });

        this.socket.on('error', (data) => {
            this.handleError(data);
        });

        this.socket.on('feedback_saved', (data) => {
            this.handleFeedbackSaved(data);
        });
    }

    initElements() {
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.chatMessages = document.getElementById('chatMessages');
        this.connectionStatus = document.getElementById('connectionStatus');
        this.messageCounter = document.getElementById('messageCounter');
        this.uploadBtn = document.getElementById('uploadBtn');
        this.uploadModal = document.getElementById('uploadModal');
        this.uploadForm = document.getElementById('uploadForm');
    }

    bindEvents() {
        console.log('🔧 Wiążę eventy...');
        
        // Sprawdź czy elementy istnieją
        console.log('SendButton:', this.sendButton);
        console.log('MessageInput:', this.messageInput);
        
        // Wysyłanie wiadomości
        this.sendButton?.addEventListener('click', (e) => {
            console.log('🖱️ Kliknięto przycisk wyślij');
            e.preventDefault();
            this.sendMessage();
        });
        
        this.messageInput?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                console.log('⌨️ Naciśnięto Enter');
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Upload modal
        this.uploadBtn?.addEventListener('click', () => this.showUploadModal());
        this.uploadForm?.addEventListener('submit', (e) => this.handleUpload(e));

        // Szybkie akcje
        document.querySelectorAll('.quick-action-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const question = e.target.dataset.question;
                if (question) {
                    this.messageInput.value = question;
                    this.sendMessage();
                }
            });
        });

        // Zamknięcie modalu
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal-overlay')) {
                this.hideUploadModal();
            }
        });
    }

    startSession() {
        this.sessionId = this.generateSessionId();
        console.log(`🔄 Rozpoczęto sesję: ${this.sessionId}`);
    }

    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    sendMessage() {
        console.log('📨 sendMessage() wywołane');
        const message = this.messageInput?.value.trim();
        console.log('💬 Wiadomość:', message);
        console.log('🔗 Połączony:', this.isConnected);
        
        if (!message || !this.isConnected) {
            console.log('❌ Brak wiadomości lub brak połączenia');
            return;
        }

        // Dodaj wiadomość użytkownika
        this.addMessage(message, 'user');
        
        // Wyczyść input
        this.messageInput.value = '';

        // Przygotuj wiadomość do asystenta
        const messageId = this.generateMessageId();
        this.currentTypingMessageId = messageId;
        
        // Dodaj wskaźnik pisania
        this.addTypingIndicator(messageId);

        // Wyślij do serwera
        this.socket.emit('send_message', {
            message: message,
            session_id: this.sessionId,
            message_id: messageId,
            context: this.getContext()
        });
    }

    generateMessageId() {
        return 'msg_' + Date.now() + '_' + (++this.messageIdCounter);
    }

    addMessage(content, role, messageId = null) {
        if (!this.chatMessages) return;

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}-message message-enter`;
        if (messageId) {
            messageDiv.id = messageId;
        }

        if (role === 'user') {
            messageDiv.innerHTML = `
                <div class="p-4">
                    <div class="font-semibold mb-2">Ty</div>
                    <div class="prose">${this.escapeHtml(content)}</div>
                </div>
            `;
        } else {
            messageDiv.innerHTML = `
                <div class="p-4">
                    <div class="font-semibold mb-2 flex items-center">
                        <span class="mr-2">🤖</span>
                        Asystent AI
                    </div>
                    <div class="prose" id="content-${messageId}">${content}</div>
                </div>
            `;
        }

        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
        this.updateMessageCounter();
    }

    addTypingIndicator(messageId) {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'message assistant-message message-enter';
        typingDiv.id = messageId;
        typingDiv.innerHTML = `
            <div class="p-4">
                <div class="font-semibold mb-2 flex items-center">
                    <span class="mr-2">🤖</span>
                    Asystent AI
                </div>
                <div class="flex items-center space-x-1">
                    <div class="typing-dots">
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                        <div class="typing-dot"></div>
                    </div>
                    <span class="text-sm text-gray-500 ml-2">Analizuję dokumenty...</span>
                </div>
            </div>
        `;

        this.chatMessages.appendChild(typingDiv);
        this.scrollToBottom();
    }

    handleResponseChunk(data) {
        console.log('📨 Otrzymano chunk:', data);
        
        if (!data.message_id) return;

        const messageElement = document.getElementById(data.message_id);
        if (!messageElement) {
            console.warn('⚠️ Nie znaleziono elementu wiadomości:', data.message_id);
            return;
        }

        // Sprawdź czy to jest jeszcze wskaźnik pisania
        const isTypingIndicator = messageElement.querySelector('.typing-dots');
        if (isTypingIndicator) {
            // Zamień wskaźnik pisania na rzeczywistą odpowiedź
            messageElement.innerHTML = `
                <div class="p-4">
                    <div class="font-semibold mb-2 flex items-center">
                        <i class="fas fa-robot mr-2"></i>
                        Asystent AI
                    </div>
                    <div class="prose whitespace-pre-wrap" id="content-${data.message_id}"></div>
                </div>
            `;
        }

        let contentElement = messageElement.querySelector(`#content-${data.message_id}`);
        if (!contentElement) {
            console.warn('⚠️ Nie znaleziono elementu zawartości:', data.message_id);
            return;
        }

        // Dodaj chunk do zawartości (surowy tekst, wyświetlany w czasie rzeczywistym)
        // WAŻNE: używamy textContent a nie innerHTML, żeby widzieć surowy tekst podczas streamowania
        // Formatowanie HTML zostanie dodane w handleResponseComplete
        contentElement.textContent = (contentElement.textContent || '') + data.chunk;
        
        console.log('📝 Zaktualizowano zawartość, długość:', contentElement.textContent.length);
        this.scrollToBottom();
    }

    handleResponseComplete(data) {
        console.log('✅ Odpowiedź kompletna:', data);
        
        if (!data.message_id) return;

        const messageElement = document.getElementById(data.message_id);
        if (!messageElement) return;

        const contentElement = messageElement.querySelector(`#content-${data.message_id}`);
        if (!contentElement) return;

        // Przekonwertuj markdown na HTML i dodaj sekcje z feedbackiem
        const htmlContent = this.convertMarkdownToHtml(data.full_response);
        const sectionsHtml = this.createSectionsWithFeedback(htmlContent, data.message_id);
        
        contentElement.innerHTML = sectionsHtml;

        // Dodaj ogólny feedback dla całej odpowiedzi
        this.addOverallFeedback(messageElement, data.message_id);

        this.scrollToBottom();
        this.updateMessageCounter();
    }

    convertMarkdownToHtml(markdown) {
        // Prosta konwersja markdown na HTML
        let html = markdown;
        
        // Nagłówki
        html = html.replace(/^### (.*$)/gm, '<h3>$1</h3>');
        html = html.replace(/^## (.*$)/gm, '<h2>$1</h2>');
        html = html.replace(/^# (.*$)/gm, '<h1>$1</h1>');
        
        // Pogrubienie
        html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        
        // Kursywa
        html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
        
        // Listy punktowane
        html = html.replace(/^- (.*$)/gm, '<li>$1</li>');
        html = html.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
        
        // Listy numerowane
        html = html.replace(/^\d+\. (.*$)/gm, '<li>$1</li>');
        html = html.replace(/(<li>.*<\/li>)/s, '<ol>$1</ol>');
        
        // Akapity
        html = html.replace(/\n\n/g, '</p><p>');
        html = '<p>' + html + '</p>';
        
        // Usuwanie pustych akapitów
        html = html.replace(/<p><\/p>/g, '');
        
        return html;
    }

    createSectionsWithFeedback(html, messageId) {
        // Podziel na sekcje (nagłówki, akapity, listy)
        const sections = this.parseHtmlIntoSections(html);
        
        let result = '';
        sections.forEach((section, index) => {
            const sectionId = `${messageId}_section_${index}`;
            result += `
                <div class="content-section relative mb-4" data-section-id="${sectionId}">
                    ${section}
                    <div class="feedback-container">
                        <button class="feedback-btn feedback-btn-positive" 
                                onclick="chatApp.sendSectionFeedback('${sectionId}', 'positive')"
                                title="Przydatne">
                            <i class="fas fa-thumbs-up"></i>
                        </button>
                        <button class="feedback-btn feedback-btn-negative" 
                                onclick="chatApp.sendSectionFeedback('${sectionId}', 'negative')"
                                title="Nieprzydatne">
                            <i class="fas fa-thumbs-down"></i>
                        </button>
                    </div>
                </div>
            `;
        });
        
        return result;
    }

    parseHtmlIntoSections(html) {
        // Prosta parser - dzieli na sekcje po nagłówkach i akapitach
        const sections = [];
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = html;
        
        let currentSection = '';
        
        Array.from(tempDiv.childNodes).forEach(node => {
            if (node.nodeType === Node.ELEMENT_NODE) {
                const tagName = node.tagName.toLowerCase();
                
                if (['h1', 'h2', 'h3'].includes(tagName)) {
                    // Nowy nagłówek - zapisz poprzednią sekcję
                    if (currentSection.trim()) {
                        sections.push(currentSection.trim());
                    }
                    currentSection = node.outerHTML;
                } else if (['p', 'ul', 'ol'].includes(tagName)) {
                    // Dodaj do bieżącej sekcji
                    currentSection += node.outerHTML;
                } else {
                    currentSection += node.outerHTML;
                }
            }
        });
        
        // Dodaj ostatnią sekcję
        if (currentSection.trim()) {
            sections.push(currentSection.trim());
        }
        
        return sections.length > 0 ? sections : [html];
    }

    addOverallFeedback(messageElement, messageId) {
        const feedbackDiv = document.createElement('div');
        feedbackDiv.className = 'mt-4 pt-4 border-t border-gray-200 flex items-center justify-between';
        feedbackDiv.innerHTML = `
            <div class="text-sm text-gray-600">
                Czy ta odpowiedź była pomocna?
            </div>
            <div class="flex space-x-2">
                <button class="feedback-btn feedback-btn-positive" 
                        onclick="chatApp.sendOverallFeedback('${messageId}', 'positive')"
                        title="Odpowiedź była pomocna">
                    <i class="fas fa-thumbs-up"></i>
                </button>
                <button class="feedback-btn feedback-btn-negative" 
                        onclick="chatApp.sendOverallFeedback('${messageId}', 'negative')"
                        title="Odpowiedź nie była pomocna">
                    <i class="fas fa-thumbs-down"></i>
                </button>
                <button class="ml-4 btn btn-secondary"
                        onclick="chatApp.exportToPdf('${messageId}')">
                    <i class="fas fa-file-pdf mr-2"></i>
                    Eksportuj PDF
                </button>
            </div>
        `;
        
        messageElement.querySelector('.p-4').appendChild(feedbackDiv);
    }

    sendSectionFeedback(sectionId, feedbackType) {
        const button = document.querySelector(`[data-section-id="${sectionId}"] .feedback-btn-${feedbackType}`);
        if (!button) return;

        // Wizualna informacja zwrotna
        this.animateFeedbackButton(button, feedbackType);

        // Wyślij do serwera
        this.socket.emit('section_feedback', {
            session_id: this.sessionId,
            section_id: sectionId,
            feedback_type: feedbackType,
            content: document.querySelector(`[data-section-id="${sectionId}"]`).textContent.trim()
        });
    }

    sendOverallFeedback(messageId, feedbackType) {
        const button = document.querySelector(`#${messageId} .feedback-btn-${feedbackType}`);
        if (!button) return;

        // Wizualna informacja zwrotna
        this.animateFeedbackButton(button, feedbackType);

        // Wyślij do serwera
        this.socket.emit('overall_feedback', {
            session_id: this.sessionId,
            message_id: messageId,
            feedback_type: feedbackType,
            content: document.querySelector(`#content-${messageId}`).textContent.trim()
        });
    }

    animateFeedbackButton(button, feedbackType) {
        // Usuń poprzednią aktywność
        const container = button.closest('.feedback-container') || button.parentElement;
        container.querySelectorAll('.feedback-btn').forEach(btn => {
            btn.classList.remove('active');
        });

        // Dodaj aktywność do klikniętego przycisku
        button.classList.add('active');

        // Animacja
        button.style.transform = 'scale(1.3)';
        setTimeout(() => {
            button.style.transform = '';
        }, 200);

        // Pokaż powiadomienie
        this.showFeedbackNotification(feedbackType);
    }

    showFeedbackNotification(feedbackType) {
        const message = feedbackType === 'positive' ? 
            'Dziękujemy za pozytywną opinię!' : 
            'Dziękujemy za opinię. Będziemy się starać lepiej!';

        const notification = document.createElement('div');
        notification.className = 'notification notification-success';
        notification.innerHTML = `
            <i class="fas fa-check-circle mr-2"></i>
            <span>${message}</span>
        `;

        document.body.appendChild(notification);

        // Animacja pojawiania się
        setTimeout(() => {
            notification.classList.add('show');
        }, 100);

        // Automatyczne usuwanie
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                if (document.body.contains(notification)) {
                    document.body.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }

    handleFeedbackSaved(data) {
        console.log('✅ Feedback zapisany:', data);
    }

    exportToPdf(messageId) {
        const content = document.querySelector(`#content-${messageId}`).textContent;
        
        this.socket.emit('export_pdf', {
            session_id: this.sessionId,
            message_id: messageId,
            content: content
        });

        // Pokaż powiadomienie
        this.showFeedbackNotification('positive');
    }

    handleError(data) {
        console.error('❌ Błąd:', data);
        
        // Usuń wskaźnik pisania
        if (this.currentTypingMessageId) {
            const typingElement = document.getElementById(this.currentTypingMessageId);
            if (typingElement) {
                typingElement.remove();
            }
        }

        // Pokaż błąd
        this.addMessage(`Wystąpił błąd: ${data.error}`, 'assistant');
    }

    getContext() {
        const messages = [];
        const messageElements = this.chatMessages.querySelectorAll('.message');
        
        messageElements.forEach((msg) => {
            const role = msg.classList.contains('user-message') ? 'user' : 'assistant';
            const content = msg.querySelector('.prose')?.textContent || '';
            if (content.trim()) {
                messages.push({ role, content: content.trim() });
            }
        });
        
        return messages.slice(-10); // Ostatnie 10 wiadomości
    }

    updateConnectionStatus(connected) {
        if (!this.connectionStatus) return;

        if (connected) {
            this.connectionStatus.className = 'w-3 h-3 rounded-full status-connected';
            this.connectionStatus.title = 'Połączono';
        } else {
            this.connectionStatus.className = 'w-3 h-3 rounded-full status-disconnected';
            this.connectionStatus.title = 'Rozłączono';
        }
    }

    updateMessageCounter() {
        this.messageCount++;
        if (this.messageCounter) {
            this.messageCounter.textContent = this.messageCount;
        }
    }

    scrollToBottom() {
        if (this.chatMessages) {
            this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        }
    }

    showUploadModal() {
        if (this.uploadModal) {
            this.uploadModal.classList.remove('hidden');
        }
    }

    hideUploadModal() {
        if (this.uploadModal) {
            this.uploadModal.classList.add('hidden');
        }
    }

    handleUpload(e) {
        e.preventDefault();
        // Implementacja uploadu
        console.log('Upload w toku...');
        this.hideUploadModal();
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Inicjalizuj aplikację
let chatApp;
document.addEventListener('DOMContentLoaded', () => {
    chatApp = new ChatApp();
});
