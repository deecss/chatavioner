/**
 * Aero-Chat - Aplikacja czatu z AI
 * Obsługuje formatowanie HTML, feedback dla sekcji, i nowoczesny interfejs
 */

class ChatApp {
    constructor(sessionId) {
        this.sessionId = sessionId;
        this.socket = null;
        this.currentResponse = '';
        this.messageCount = 0;
        this.isGenerating = false;
        
        this.init();
    }
    
    init() {
        this.initializeSocket();
        this.setupEventListeners();
        this.loadHistory();
    }
    
    initializeSocket() {
        this.socket = io();
        
        this.socket.on('connect', () => {
            console.log('Połączono z serwerem');
            this.updateConnectionStatus(true);
        });
        
        this.socket.on('disconnect', () => {
            console.log('Rozłączono z serwerem');
            this.updateConnectionStatus(false);
        });
        
        this.socket.on('message_received', (data) => {
            this.addMessage(data.message, 'user', data.timestamp);
        });
        
        this.socket.on('generating_start', () => {
            this.showTypingIndicator();
            this.isGenerating = true;
            this.currentResponse = '';
        });
        
        this.socket.on('response_chunk', (data) => {
            this.currentResponse += data.chunk;
            this.updateCurrentResponse();
        });
        
        this.socket.on('generating_end', (data) => {
            this.hideTypingIndicator();
            this.isGenerating = false;
            this.finalizeResponse();
        });
        
        this.socket.on('error', (data) => {
            this.hideTypingIndicator();
            this.showError(data.message);
            this.isGenerating = false;
        });
    }
    
    setupEventListeners() {
        const messageInput = document.getElementById('messageInput');
        const sendBtn = document.getElementById('sendBtn');
        
        // Send button
        sendBtn.addEventListener('click', () => this.sendMessage());
        
        // Enter key
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Disable send button while generating
        messageInput.addEventListener('input', () => {
            sendBtn.disabled = this.isGenerating || !messageInput.value.trim();
        });
    }
    
    sendMessage() {
        const messageInput = document.getElementById('messageInput');
        const message = messageInput.value.trim();
        
        if (!message || this.isGenerating) return;
        
        this.socket.emit('send_message', { message });
        messageInput.value = '';
        document.getElementById('charCount').textContent = '0 / 2000';
        document.getElementById('sendBtn').disabled = true;
    }
    
    addMessage(content, role, timestamp) {
        const chatMessages = document.getElementById('chatMessages');
        const messageElement = document.createElement('div');
        
        if (role === 'user') {
            messageElement.className = 'flex justify-end';
            messageElement.innerHTML = `
                <div class="max-w-3xl">
                    <div class="bg-blue-600 text-white px-4 py-3 rounded-lg shadow-sm">
                        <p class="whitespace-pre-wrap">${this.escapeHtml(content)}</p>
                    </div>
                    <div class="text-xs text-gray-500 mt-1 text-right">
                        ${this.formatTime(timestamp)}
                    </div>
                </div>
            `;
        } else {
            messageElement.className = 'flex justify-start';
            messageElement.innerHTML = `
                <div class="max-w-4xl">
                    <div class="bg-white border border-gray-200 rounded-lg shadow-sm">
                        <div class="p-4">
                            <div class="prose prose-sm max-w-none" id="response-content">
                                ${this.formatResponse(content)}
                            </div>
                        </div>
                    </div>
                    <div class="text-xs text-gray-500 mt-1">
                        ${this.formatTime(timestamp)}
                    </div>
                </div>
            `;
        }
        
        chatMessages.appendChild(messageElement);
        this.scrollToBottom();
        
        if (role === 'user') {
            this.messageCount++;
            document.getElementById('messageCount').textContent = this.messageCount;
        }
        
        // Add feedback buttons for assistant responses
        if (role === 'assistant') {
            this.addFeedbackButtons(messageElement);
        }
    }
    
    formatResponse(content) {
        // Parse markdown-like formatting to HTML
        let html = content;
        
        // Headers
        html = html.replace(/^### (.*$)/gm, '<h3 class="text-lg font-semibold text-gray-800 mt-4 mb-2 section-header" data-section="header">$1</h3>');
        html = html.replace(/^## (.*$)/gm, '<h2 class="text-xl font-semibold text-gray-800 mt-4 mb-2 section-header" data-section="header">$1</h2>');
        html = html.replace(/^# (.*$)/gm, '<h1 class="text-2xl font-bold text-gray-800 mt-4 mb-2 section-header" data-section="header">$1</h1>');
        
        // Bold text
        html = html.replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-gray-800">$1</strong>');
        
        // Lists
        html = html.replace(/^- (.*$)/gm, '<li class="ml-4 mb-1 section-item" data-section="list">• $1</li>');
        html = html.replace(/^\d+\. (.*$)/gm, '<li class="ml-4 mb-1 section-item" data-section="list">$1</li>');
        
        // Paragraphs
        const paragraphs = html.split('\n\n');
        html = paragraphs.map(p => {
            p = p.trim();
            if (p && !p.startsWith('<')) {
                return `<p class="mb-3 text-gray-700 leading-relaxed section-paragraph" data-section="paragraph">${p}</p>`;
            }
            return p;
        }).join('\n');
        
        return html;
    }
    
    addFeedbackButtons(messageElement) {
        const responseContent = messageElement.querySelector('#response-content');
        
        // Add feedback buttons to each section
        const sections = responseContent.querySelectorAll('[data-section]');
        sections.forEach((section, index) => {
            const feedbackContainer = document.createElement('div');
            feedbackContainer.className = 'inline-flex items-center space-x-1 ml-2 opacity-0 hover:opacity-100 transition-opacity';
            feedbackContainer.innerHTML = `
                <button class="feedback-btn text-green-600 hover:text-green-700 text-xs p-1 rounded" 
                        data-feedback="positive" data-section-id="${index}" title="Przydatne">
                    👍
                </button>
                <button class="feedback-btn text-red-600 hover:text-red-700 text-xs p-1 rounded" 
                        data-feedback="negative" data-section-id="${index}" title="Nieprzydatne">
                    👎
                </button>
            `;
            
            section.appendChild(feedbackContainer);
        });
        
        // Add overall feedback at the end
        const overallFeedback = document.createElement('div');
        overallFeedback.className = 'mt-4 pt-3 border-t border-gray-200 flex items-center justify-between';
        overallFeedback.innerHTML = `
            <div class="flex items-center space-x-2">
                <span class="text-sm text-gray-600">Oceń odpowiedź:</span>
                <button class="feedback-btn bg-green-100 text-green-700 hover:bg-green-200 px-3 py-1 rounded-full text-sm transition-colors" 
                        data-feedback="positive" data-section-id="overall">
                    👍 Przydatne
                </button>
                <button class="feedback-btn bg-red-100 text-red-700 hover:bg-red-200 px-3 py-1 rounded-full text-sm transition-colors" 
                        data-feedback="negative" data-section-id="overall">
                    👎 Nieprzydatne
                </button>
            </div>
            <div class="flex items-center space-x-2">
                <button class="text-blue-600 hover:text-blue-700 text-sm" onclick="this.parentElement.parentElement.parentElement.classList.toggle('expanded')">
                    📄 Eksportuj PDF
                </button>
                <button class="text-gray-600 hover:text-gray-700 text-sm">
                    🔗 Udostępnij
                </button>
            </div>
        `;
        
        responseContent.appendChild(overallFeedback);
        
        // Add event listeners for feedback buttons
        const feedbackBtns = responseContent.querySelectorAll('.feedback-btn');
        feedbackBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.submitFeedback(e.target.dataset.feedback, e.target.dataset.sectionId);
            });
        });
    }
    
    submitFeedback(type, sectionId) {
        console.log(`Feedback: ${type} for section: ${sectionId}`);
        
        // Send feedback to server
        this.socket.emit('submit_feedback', {
            type: type,
            section: sectionId,
            session_id: this.sessionId,
            timestamp: new Date().toISOString()
        });
        
        // Visual feedback
        const feedbackBtn = event.target;
        feedbackBtn.classList.add('opacity-50');
        feedbackBtn.disabled = true;
        
        // Show confirmation
        const confirmation = document.createElement('span');
        confirmation.className = 'text-xs text-green-600 ml-2';
        confirmation.textContent = 'Dziękuję za opinię!';
        feedbackBtn.parentElement.appendChild(confirmation);
        
        setTimeout(() => {
            if (confirmation.parentElement) {
                confirmation.remove();
            }
        }, 3000);
    }
    
    updateCurrentResponse() {
        const responseElements = document.querySelectorAll('#response-content');
        const currentElement = responseElements[responseElements.length - 1];
        
        if (currentElement) {
            currentElement.innerHTML = this.formatResponse(this.currentResponse);
            this.scrollToBottom();
        }
    }
    
    finalizeResponse() {
        const timestamp = new Date().toISOString();
        const responseElements = document.querySelectorAll('#response-content');
        const currentElement = responseElements[responseElements.length - 1];
        
        if (currentElement) {
            const messageElement = currentElement.closest('.max-w-4xl').parentElement;
            this.addFeedbackButtons(messageElement);
        }
        
        document.getElementById('sendBtn').disabled = false;
    }
    
    showTypingIndicator() {
        document.getElementById('typingIndicator').classList.remove('hidden');
        
        // Add assistant message container
        const chatMessages = document.getElementById('chatMessages');
        const messageElement = document.createElement('div');
        messageElement.className = 'flex justify-start';
        messageElement.innerHTML = `
            <div class="max-w-4xl">
                <div class="bg-white border border-gray-200 rounded-lg shadow-sm">
                    <div class="p-4">
                        <div class="prose prose-sm max-w-none" id="response-content">
                            <p class="text-gray-500 italic">Analizuję dokumenty...</p>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        chatMessages.appendChild(messageElement);
        this.scrollToBottom();
    }
    
    hideTypingIndicator() {
        document.getElementById('typingIndicator').classList.add('hidden');
    }
    
    updateConnectionStatus(connected) {
        const statusElement = document.getElementById('connectionStatus');
        if (connected) {
            statusElement.className = 'w-3 h-3 bg-green-400 rounded-full animate-pulse';
        } else {
            statusElement.className = 'w-3 h-3 bg-red-400 rounded-full';
        }
    }
    
    scrollToBottom() {
        const chatMessages = document.getElementById('chatMessages');
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    formatTime(timestamp) {
        if (!timestamp) return '';
        const date = new Date(timestamp);
        return date.toLocaleTimeString('pl-PL', { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
    }
    
    loadHistory() {
        fetch('/api/history')
            .then(response => response.json())
            .then(data => {
                if (data.history && data.history.length > 0) {
                    // Clear welcome message
                    document.getElementById('chatMessages').innerHTML = '';
                    
                    data.history.forEach(message => {
                        this.addMessage(message.content, message.role, message.timestamp);
                    });
                    
                    this.messageCount = data.history.filter(m => m.role === 'user').length;
                    document.getElementById('messageCount').textContent = this.messageCount;
                }
            })
            .catch(error => {
                console.error('Błąd ładowania historii:', error);
            });
    }
    
    clearHistory() {
        fetch('/api/history', { method: 'DELETE' })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    document.getElementById('chatMessages').innerHTML = `
                        <div class="text-center text-gray-500 py-12">
                            <div class="w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-6">
                                <span class="text-blue-600 text-3xl">✈</span>
                            </div>
                            <h3 class="text-xl font-semibold text-gray-700 mb-3">Historia wyczyszczona</h3>
                            <p class="text-gray-600 max-w-md mx-auto leading-relaxed">
                                Możesz rozpocząć nową rozmowę.
                            </p>
                        </div>
                    `;
                    this.messageCount = 0;
                    document.getElementById('messageCount').textContent = this.messageCount;
                }
            })
            .catch(error => {
                console.error('Błąd czyszczenia historii:', error);
            });
    }
    
    showError(message) {
        const chatMessages = document.getElementById('chatMessages');
        const errorElement = document.createElement('div');
        errorElement.className = 'flex justify-center';
        errorElement.innerHTML = `
            <div class="max-w-md">
                <div class="bg-red-100 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
                    <div class="flex items-center">
                        <span class="text-red-500 mr-2">⚠️</span>
                        <span class="font-medium">Błąd:</span>
                    </div>
                    <p class="mt-1 text-sm">${message}</p>
                </div>
            </div>
        `;
        
        chatMessages.appendChild(errorElement);
        this.scrollToBottom();
    }
}

// Export for use in HTML
window.ChatApp = ChatApp;
