/**
 * Aero-Chat - Klient WebSocket i obsługa UI
 */
class ChatApp {
    constructor(sessionId) {
        this.sessionId = sessionId;
        this.socket = null;
        this.isGenerating = false;
        this.currentMessageId = 0;
        
        this.initializeSocket();
        this.initializeUI();
        this.loadHistory();
    }
    
    initializeSocket() {
        this.socket = io();
        
        this.socket.on('connect', () => {
            console.log('Connected to server');
            this.updateConnectionStatus(true);
        });
        
        this.socket.on('disconnect', () => {
            console.log('Disconnected from server');
            this.updateConnectionStatus(false);
        });
        
        this.socket.on('connected', (data) => {
            console.log('Server confirmation:', data.message);
        });
        
        this.socket.on('message_received', (data) => {
            console.log('Message received confirmation');
            this.addMessage(data.message, 'user', data.timestamp);
        });
        
        this.socket.on('generating_start', (data) => {
            console.log('Generation started');
            this.showTypingIndicator();
            this.isGenerating = true;
            this.updateSendButton();
        });
        
        this.socket.on('response_chunk', (data) => {
            this.appendToCurrentResponse(data.chunk);
        });
        
        this.socket.on('generating_end', (data) => {
            console.log('Generation ended');
            this.hideTypingIndicator();
            this.isGenerating = false;
            this.updateSendButton();
            this.finalizeCurrentResponse(data.pdf_path);
        });
        
        this.socket.on('error', (data) => {
            console.error('Socket error:', data.message);
            this.showError(data.message);
            this.hideTypingIndicator();
            this.isGenerating = false;
            this.updateSendButton();
        });
        
        this.socket.on('pdf_generated', (data) => {
            console.log('PDF generated:', data.pdf_path);
            this.showNotification('PDF wygenerowany pomyślnie');
        });
    }
    
    initializeUI() {
        const messageInput = document.getElementById('messageInput');
        const sendBtn = document.getElementById('sendBtn');
        
        // Send button handler
        sendBtn.addEventListener('click', () => {
            this.sendMessage();
        });
        
        // Enter key handler
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Auto-resize textarea
        messageInput.addEventListener('input', (e) => {
            e.target.style.height = 'auto';
            e.target.style.height = e.target.scrollHeight + 'px';
        });
    }
    
    sendMessage() {
        const messageInput = document.getElementById('messageInput');
        const message = messageInput.value.trim();
        
        if (!message || this.isGenerating) {
            return;
        }
        
        // Clear input
        messageInput.value = '';
        messageInput.style.height = 'auto';
        
        // Send message via WebSocket
        this.socket.emit('send_message', {
            message: message,
            session_id: this.sessionId
        });
    }
    
    addMessage(content, role, timestamp = null) {
        const chatMessages = document.getElementById('chatMessages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message fade-in ${role}`;
        messageDiv.dataset.messageId = this.currentMessageId++;
        
        const isUser = role === 'user';
        const time = timestamp ? new Date(timestamp).toLocaleTimeString() : new Date().toLocaleTimeString();
        
        messageDiv.innerHTML = `
            <div class="flex ${isUser ? 'justify-end' : 'justify-start'} mb-4">
                <div class="flex ${isUser ? 'flex-row-reverse' : 'flex-row'} items-start max-w-3xl">
                    <div class="flex-shrink-0 ${isUser ? 'ml-3' : 'mr-3'}">
                        <div class="w-8 h-8 rounded-full ${isUser ? 'bg-blue-500' : 'bg-gray-500'} flex items-center justify-center">
                            <span class="text-white text-sm font-bold">${isUser ? 'U' : 'AI'}</span>
                        </div>
                    </div>
                    <div class="flex-1">
                        <div class="flex items-center ${isUser ? 'justify-end' : 'justify-start'} mb-1">
                            <span class="text-sm font-medium ${isUser ? 'text-blue-600' : 'text-gray-600'}">
                                ${isUser ? 'Ty' : 'Asystent AI'}
                            </span>
                            <span class="text-xs text-gray-500 ml-2">${time}</span>
                        </div>
                        <div class="p-3 rounded-lg ${isUser ? 'bg-blue-500 text-white' : 'bg-white border shadow-sm'} message-content">
                            ${this.formatMessage(content)}
                        </div>
                        ${!isUser ? this.createFeedbackButtons(messageDiv.dataset.messageId) : ''}
                    </div>
                </div>
            </div>
        `;
        
        chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
        this.updateMessageCount();
        
        return messageDiv;
    }
    
    showTypingIndicator() {
        const typingIndicator = document.getElementById('typingIndicator');
        typingIndicator.classList.remove('hidden');
        
        // Add empty response message
        this.currentResponseDiv = this.addMessage('', 'assistant');
        const messageContent = this.currentResponseDiv.querySelector('.message-content');
        messageContent.innerHTML = '<span class="typing-cursor">|</span>';
        
        this.scrollToBottom();
    }
    
    hideTypingIndicator() {
        const typingIndicator = document.getElementById('typingIndicator');
        typingIndicator.classList.add('hidden');
    }
    
    appendToCurrentResponse(chunk) {
        if (!this.currentResponseDiv) return;
        
        const messageContent = this.currentResponseDiv.querySelector('.message-content');
        if (!this.currentResponseText) {
            this.currentResponseText = '';
        }
        
        this.currentResponseText += chunk;
        messageContent.innerHTML = this.formatMessage(this.currentResponseText) + '<span class="typing-cursor">|</span>';
        
        this.scrollToBottom();
    }
    
    finalizeCurrentResponse(pdfPath) {
        if (!this.currentResponseDiv) return;
        
        const messageContent = this.currentResponseDiv.querySelector('.message-content');
        messageContent.innerHTML = this.formatMessage(this.currentResponseText);
        
        // Add feedback buttons
        const feedbackDiv = this.currentResponseDiv.querySelector('.message-content').parentNode;
        feedbackDiv.innerHTML += this.createFeedbackButtons(this.currentResponseDiv.dataset.messageId);
        
        // Add PDF download button if available
        if (pdfPath) {
            const pdfButton = document.createElement('div');
            pdfButton.className = 'mt-2';
            pdfButton.innerHTML = `
                <a href="${pdfPath}" target="_blank" 
                   class="inline-flex items-center px-3 py-1 bg-green-100 text-green-700 rounded-lg hover:bg-green-200 text-sm">
                    📄 Pobierz PDF
                </a>
            `;
            feedbackDiv.appendChild(pdfButton);
        }
        
        this.currentResponseDiv = null;
        this.currentResponseText = '';
        this.scrollToBottom();
    }
    
    createFeedbackButtons(messageId) {
        return `
            <div class="flex items-center space-x-2 mt-2 feedback-buttons">
                <button class="feedback-btn" data-type="positive" data-message-id="${messageId}" 
                        title="Przydatna odpowiedź">
                    👍
                </button>
                <button class="feedback-btn" data-type="negative" data-message-id="${messageId}" 
                        title="Nieprzydatna odpowiedź">
                    👎
                </button>
                <button class="feedback-btn" data-type="improve" data-message-id="${messageId}" 
                        title="Rozwiń odpowiedź">
                    ✏️
                </button>
                <button class="feedback-btn pdf-btn" data-message-id="${messageId}" 
                        title="Generuj PDF">
                    📄
                </button>
            </div>
        `;
    }
    
    formatMessage(content) {
        // Simple formatting - convert newlines to <br> and handle basic markdown
        return content
            .replace(/\n\n/g, '</p><p>')
            .replace(/\n/g, '<br>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/`(.*?)`/g, '<code>$1</code>')
            .replace(/^(.*)$/, '<p>$1</p>')
            .replace(/<p><\/p>/g, '');
    }
    
    updateConnectionStatus(connected) {
        const statusDot = document.getElementById('connectionStatus');
        const statusText = statusDot.nextElementSibling;
        
        if (connected) {
            statusDot.className = 'w-3 h-3 bg-green-400 rounded-full';
            statusText.textContent = 'Połączono';
        } else {
            statusDot.className = 'w-3 h-3 bg-red-400 rounded-full';
            statusText.textContent = 'Rozłączono';
        }
    }
    
    updateSendButton() {
        const sendBtn = document.getElementById('sendBtn');
        if (this.isGenerating) {
            sendBtn.textContent = 'Generuję...';
            sendBtn.disabled = true;
            sendBtn.classList.add('opacity-50', 'cursor-not-allowed');
        } else {
            sendBtn.textContent = 'Wyślij';
            sendBtn.disabled = false;
            sendBtn.classList.remove('opacity-50', 'cursor-not-allowed');
        }
    }
    
    updateMessageCount() {
        const messageCount = document.getElementById('messageCount');
        const messages = document.querySelectorAll('.message');
        messageCount.textContent = messages.length;
    }
    
    scrollToBottom() {
        const chatMessages = document.getElementById('chatMessages');
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4';
        errorDiv.innerHTML = `
            <strong>Błąd:</strong> ${message}
        `;
        
        const chatMessages = document.getElementById('chatMessages');
        chatMessages.appendChild(errorDiv);
        this.scrollToBottom();
        
        // Remove error after 5 seconds
        setTimeout(() => {
            errorDiv.remove();
        }, 5000);
    }
    
    showNotification(message) {
        const notification = document.getElementById('notification');
        const notificationText = document.getElementById('notificationText');
        
        notificationText.textContent = message;
        notification.classList.remove('translate-x-full');
        
        setTimeout(() => {
            notification.classList.add('translate-x-full');
        }, 3000);
    }
    
    loadHistory() {
        fetch('/api/history')
            .then(response => response.json())
            .then(history => {
                const chatMessages = document.getElementById('chatMessages');
                // Clear welcome message
                chatMessages.innerHTML = '';
                
                history.forEach(msg => {
                    this.addMessage(msg.content, msg.role, msg.timestamp);
                });
                
                if (history.length === 0) {
                    // Show welcome message if no history
                    chatMessages.innerHTML = `
                        <div class="text-center text-gray-500 text-sm py-8">
                            <div class="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                                <span class="text-blue-600 text-2xl">✈</span>
                            </div>
                            <p>Witaj w Aero-Chat! Jestem Twoim asystentem AI do spraw lotnictwa.</p>
                            <p class="mt-2">Możesz zadać mi pytanie o aerodynamikę, przepisy lotnicze, nawigację, meteorologię i wiele więcej.</p>
                        </div>
                    `;
                }
            })
            .catch(error => {
                console.error('Error loading history:', error);
            });
    }
    
    clearHistory() {
        fetch('/api/clear_history', { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                if (data.message) {
                    const chatMessages = document.getElementById('chatMessages');
                    chatMessages.innerHTML = `
                        <div class="text-center text-gray-500 text-sm py-8">
                            <div class="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                                <span class="text-blue-600 text-2xl">✈</span>
                            </div>
                            <p>Historia została wyczyszczona.</p>
                            <p class="mt-2">Możesz rozpocząć nową rozmowę.</p>
                        </div>
                    `;
                    this.currentMessageId = 0;
                    this.updateMessageCount();
                    this.showNotification('Historia wyczyszczona');
                }
            })
            .catch(error => {
                console.error('Error clearing history:', error);
                this.showError('Błąd podczas czyszczenia historii');
            });
    }
    
    submitFeedback(type, messageId, content = '') {
        const feedbackData = {
            type: type,
            message_id: messageId,
            content: content
        };
        
        fetch('/api/feedback', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(feedbackData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.message) {
                this.showNotification('Dziękujemy za feedback!');
                
                // Mark button as active
                const button = document.querySelector(`[data-message-id="${messageId}"][data-type="${type}"]`);
                if (button) {
                    button.classList.add('active');
                }
            }
        })
        .catch(error => {
            console.error('Error submitting feedback:', error);
            this.showError('Błąd podczas przesyłania feedbacku');
        });
    }
}

// Initialize feedback button handlers
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('feedback-btn')) {
        const type = e.target.dataset.type;
        const messageId = e.target.dataset.messageId;
        
        if (type === 'improve') {
            // Show input for improvement request
            const content = prompt('Jak możemy poprawić tę odpowiedź?');
            if (content) {
                window.chatApp.submitFeedback(type, messageId, content);
            }
        } else if (e.target.classList.contains('pdf-btn')) {
            // Generate PDF for this message
            const messageDiv = document.querySelector(`[data-message-id="${messageId}"]`);
            const messageContent = messageDiv.querySelector('.message-content').textContent;
            
            window.chatApp.socket.emit('request_pdf', {
                message_id: messageId,
                content: messageContent
            });
        } else {
            // Simple feedback
            window.chatApp.submitFeedback(type, messageId);
        }
    }
});

// Export for global access
window.ChatApp = ChatApp;
