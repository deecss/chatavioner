class ChatApp {
    constructor() {
        this.socket = null;
        this.sessionId = null;
        this.isConnected = false;
        this.messageIdCounter = 0;
        this.currentTypingMessageId = null;
        this.messageCount = 0;
        this.questionsAsked = 0;
        this.documentsUsed = 0;
        this.sessionStartTime = Date.now();
        this.currentFeedback = null;
        this.init();
    }

    init() {
        this.initSocket();
        this.initElements();
        this.bindEvents();
        this.startSession();
    }

    initSocket() {
        console.log('🔌 Inicjalizuje Socket.io...');
        this.socket = io();
        
        this.socket.on('connect', () => {
            this.isConnected = true;
            this.updateConnectionStatus(true);
            console.log('✅ Połączono z serwerem');
            console.log('🔗 Socket ID:', this.socket.id);
        });
        
        this.socket.on('connected', (data) => {
            console.log('🔌 Otrzymano potwierdzenie połączenia:', data);
        });

        this.socket.on('disconnect', () => {
            this.isConnected = false;
            this.updateConnectionStatus(false);
            console.log('❌ Rozłączono z serwerem');
        });

        this.socket.on('response_chunk', (data) => {
            console.log('📨 Otrzymano response_chunk:', data);
            this.handleResponseChunk(data);
        });

        this.socket.on('response_complete', (data) => {
            console.log('✅ Otrzymano response_complete:', data);
            this.handleResponseComplete(data);
        });

        this.socket.on('error', (data) => {
            console.error('❌ Otrzymano error:', data);
            this.handleError(data);
        });

        this.socket.on('feedback_saved', (data) => {
            console.log('💾 Otrzymano feedback_saved:', data);
            this.handleFeedbackSaved(data);
        });

        this.socket.on('documents_used', (data) => {
            console.log('📄 Otrzymano documents_used:', data);
            this.updateDocumentsUsed(data.count);
        });
        
        // Dodaj obsługę innych eventów
        this.socket.on('message_received', (data) => {
            console.log('📨 Otrzymano message_received:', data);
        });
        
        this.socket.on('generating_start', (data) => {
            console.log('🔄 Otrzymano generating_start:', data);
        });
        
        // Obsługa aktualizacji tytułu sesji
        this.socket.on('session_title_updated', (data) => {
            console.log('🏷️ Otrzymano session_title_updated:', data);
            this.handleSessionTitleUpdated(data);
        });
    }

    initElements() {
        console.log('🔧 Inicjalizuje elementy...');
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.chatMessages = document.getElementById('chatMessages');
        this.connectionStatus = document.getElementById('connectionStatus');
        this.connectionStatusText = document.getElementById('connectionStatusText');
        this.messageCounter = document.getElementById('messageCounter');
        this.questionsCount = document.getElementById('questionsCount');
        this.documentsCount = document.getElementById('documentsCount');
        this.sessionTime = document.getElementById('sessionTime');
        this.feedbackModal = document.getElementById('feedbackModal');
        this.feedbackDescription = document.getElementById('feedbackDescription');
        this.uploadBtn = document.getElementById('uploadBtn');
        this.uploadModal = document.getElementById('uploadModal');
        this.uploadForm = document.getElementById('uploadForm');
        
        // Sprawdź czy kluczowe elementy istnieją
        console.log('📝 MessageInput:', this.messageInput);
        console.log('📤 SendButton:', this.sendButton);
        console.log('💬 ChatMessages:', this.chatMessages);
        console.log('🔗 ConnectionStatus:', this.connectionStatus);
        
        this.startSessionTimer();
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

        // Feedback modal
        this.initFeedbackModal();

        // Szybkie akcje
        document.querySelectorAll('.quick-action-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                console.log('🖱️ Kliknięto szybką akcję');
                const question = e.currentTarget.dataset.question;
                console.log('❓ Pytanie:', question);
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
        // Użyj current_session_id z nowego systemu sesji
        this.sessionId = window.CURRENT_SESSION_ID || null;
        console.log(`🔄 Rozpoczęto sesję: ${this.sessionId}`);
        console.log(`🔄 Źródło session_id: ${window.CURRENT_SESSION_ID ? 'system sesji' : 'brak sesji'}`);
        
        // Sprawdź czy sesja została ustawiona
        if (!this.sessionId) {
            console.warn('⚠️ Brak aktywnej sesji - oczekiwanie na ustawienie przez SessionManager');
        }
    }
    
    // Metoda do aktualizacji sesji z SessionManager
    updateSessionId(sessionId) {
        this.sessionId = sessionId;
        window.CURRENT_SESSION_ID = sessionId;
        console.log(`🔄 Zaktualizowano session ID: ${sessionId}`);
    }

    // Obsługa aktualizacji tytułu sesji
    handleSessionTitleUpdated(data) {
        console.log('🏷️ Obsługa aktualizacji tytułu sesji:', data);
        if (window.sessionManager && data.session_id && data.title) {
            window.sessionManager.updateSessionTitleInUI(data.session_id, data.title);
        }
    }

    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    sendMessage() {
        console.log('📨 sendMessage() wywołane');
        const message = this.messageInput?.value.trim();
        console.log('💬 Wiadomość:', message);
        console.log('🔗 Połączony:', this.isConnected);
        console.log('🔌 Socket:', this.socket);
        console.log('🆔 SessionId:', this.sessionId);
        console.log('🆔 CURRENT_SESSION_ID:', window.CURRENT_SESSION_ID);
        
        if (!message || !this.isConnected) {
            console.log('❌ Brak wiadomości lub brak połączenia');
            if (!message) console.log('❌ Pusta wiadomość');
            if (!this.isConnected) console.log('❌ Brak połączenia');
            return;
        }
        
        // Sprawdź czy mamy aktywną sesję
        if (!this.sessionId && !window.CURRENT_SESSION_ID) {
            console.log('❌ Brak aktywnej sesji - próbuję utworzyć nową');
            
            // Automatycznie utwórz nową sesję
            if (window.sessionManager) {
                window.sessionManager.createNewSession().then(() => {
                    console.log('✅ Utworzono nową sesję, ponawiam wysłanie wiadomości');
                    // Ponów wysłanie wiadomości po utworzeniu sesji
                    setTimeout(() => {
                        this.messageInput.value = message;
                        this.sendMessage();
                    }, 500);
                });
            } else {
                alert('Brak aktywnej sesji. Utwórz nową sesję.');
            }
            return;
        }
        
        // Użyj sesji z window.CURRENT_SESSION_ID jeśli dostępna
        const currentSessionId = window.CURRENT_SESSION_ID || this.sessionId;
        this.sessionId = currentSessionId;

        // Dodaj wiadomość użytkownika
        this.addMessage(message, 'user');
        
        // Wyczyść input
        this.messageInput.value = '';

        // Przygotuj wiadomość do asystenta
        const messageId = this.generateMessageId();
        this.currentTypingMessageId = messageId;
        console.log('🆔 Wygenerowano messageId:', messageId);
        
        // Dodaj wskaźnik pisania
        this.addTypingIndicator(messageId);

        // Wyślij do serwera
        const messageData = {
            message: message,
            session_id: this.sessionId,
            message_id: messageId,
            context: this.getContext()
        };
        
        console.log('📤 Wysyłam dane:', messageData);
        this.socket.emit('send_message', messageData);

        // Aktualizuj statystyki
        this.updateQuestionsAsked(message);
    }

    generateMessageId() {
        return 'msg_' + Date.now() + '_' + (++this.messageIdCounter);
    }

    addMessage(content, role, messageId = null) {
        console.log('📝 addMessage wywołane:', { content, role, messageId });
        console.log('📝 ChatMessages element:', this.chatMessages);
        
        if (!this.chatMessages) {
            console.error('❌ Brak elementu chatMessages!');
            return;
        }

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}-message message-enter`;
        if (messageId) {
            messageDiv.id = messageId;
        }

        console.log('📝 Utworzono messageDiv:', messageDiv);

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

        console.log('📝 HTML wiadomości ustawiony:', messageDiv.innerHTML);

        // Usuń welcome message przy pierwszej wiadomości
        if (role === 'user') {
            const welcomeMessage = this.chatMessages.querySelector('.text-center.py-12');
            if (welcomeMessage) {
                console.log('📝 Usuwam welcome message');
                welcomeMessage.remove();
            }
        }

        this.chatMessages.appendChild(messageDiv);
        console.log('📝 Wiadomość dodana do DOM');
        console.log('📝 Liczba dzieci w chatMessages:', this.chatMessages.children.length);
        
        this.scrollToBottom();
        this.updateMessageCounter();
    }

    addTypingIndicator(messageId) {
        console.log('⌨️ addTypingIndicator wywołane dla:', messageId);
        
        if (!this.chatMessages) {
            console.error('❌ Brak elementu chatMessages w addTypingIndicator!');
            return;
        }

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

        console.log('⌨️ Typing indicator utworzony:', typingDiv);
        this.chatMessages.appendChild(typingDiv);
        console.log('⌨️ Typing indicator dodany do DOM');
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
                    <div class="prose" id="content-${data.message_id}"></div>
                </div>
            `;
        }

        let contentElement = messageElement.querySelector(`#content-${data.message_id}`);
        if (!contentElement) {
            console.warn('⚠️ Nie znaleziono elementu zawartości:', data.message_id);
            return;
        }

        // Akumuluj surowy tekst markdown
        if (!contentElement.dataset.rawContent) {
            contentElement.dataset.rawContent = '';
        }
        contentElement.dataset.rawContent += data.chunk;
        
        // Konwertuj markdown do HTML na bieżąco
        contentElement.innerHTML = this.markdownToHtml(contentElement.dataset.rawContent);
        
        console.log('📝 Zaktualizowano zawartość tekstu, długość:', contentElement.textContent.length);
        this.scrollToBottom();
    }

    handleResponseComplete(data) {
        console.log('✅ Odpowiedź kompletna:', data);
        
        if (!data.message_id) return;

        const messageElement = document.getElementById(data.message_id);
        if (!messageElement) return;

        const contentElement = messageElement.querySelector(`#content-${data.message_id}`);
        if (!contentElement) return;

        // Ustaw finalną odpowiedź HTML z feedbackami przy każdym akapicie/nagłówku
        contentElement.innerHTML = this.addFeedbackToEachSection(data.full_response, data.message_id);

        this.scrollToBottom();
        this.updateMessageCounter();
        
        // Aktualizuj licznik dokumentów jeśli dostępny
        if (data.documents_used) {
            this.updateDocumentsUsed(data.documents_used);
        }
    }

    addFeedbackToEachSection(htmlContent, messageId) {
        // Parsuj HTML i dodaj feedback do każdego nagłówka i akapitu
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = htmlContent;
        
        let sectionId = 0;
        
        // Funkcja do dodania feedbacku
        const addFeedback = (element) => {
            const id = `${messageId}_section_${sectionId++}`;
            const wrapper = document.createElement('div');
            wrapper.className = 'content-section';
            wrapper.setAttribute('data-section-id', id);
            
            // Skopiuj element
            wrapper.appendChild(element.cloneNode(true));
            
            // Dodaj dyskretny feedback
            const feedbackDiv = document.createElement('div');
            feedbackDiv.className = 'section-feedback';
            feedbackDiv.innerHTML = `
                <button class="feedback-btn" onclick="chatApp.submitSectionFeedback('${id}', 'positive', '${element.tagName}')" title="Przydatne">👍</button>
                <button class="feedback-btn" onclick="chatApp.submitSectionFeedback('${id}', 'negative', '${element.tagName}')" title="Nieprzydatne">👎</button>
            `;
            wrapper.appendChild(feedbackDiv);
            
            return wrapper;
        };
        
        // Przetwórz wszystkie elementy
        Array.from(tempDiv.children).forEach(element => {
            const tagName = element.tagName.toLowerCase();
            
            if (['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p'].includes(tagName)) {
                // Dodaj feedback do nagłówków i akapitów
                const wrapped = addFeedback(element);
                element.parentNode.replaceChild(wrapped, element);
            }
        });
        
        return tempDiv.innerHTML;
    }

    submitSectionFeedback(sectionId, type, elementType) {
        console.log('💬 Otwieranie modalu feedback:', { sectionId, type, elementType });
        
        // Znajdź treść sekcji
        const sectionElement = document.querySelector(`[data-section-id="${sectionId}"]`);
        const content = sectionElement ? sectionElement.innerText.trim() : '';
        
        // Pokaż modal z polem komentarza
        this.showFeedbackModal(sectionId, type, elementType, content);
    }

    // Removed old showFeedbackModal function - using the new one above

    sendSectionFeedback(sectionId, type, elementType, content, comment) {
        console.log('💬 Wysyłam section feedback z komentarzem:', { sectionId, type, elementType, comment });
        console.log('🔌 Socket połączony:', this.socket && this.isConnected);
        console.log('🆔 Session ID:', this.sessionId);
        console.log('🆔 Current typing message ID:', this.currentTypingMessageId);
        
        if (this.socket && this.isConnected) {
            // Wyciągnij message_id z section_id (format: msg_timestamp_id_section_number)
            const messageId = sectionId.split('_section_')[0];
            console.log('🆔 Wyciągnięto message_id:', messageId, 'z sectionId:', sectionId);
            
            const feedbackData = {
                message_id: messageId,
                section_id: sectionId,
                session_id: this.sessionId,
                feedback_type: type,
                section_type: elementType.toLowerCase(),
                content: content,
                description: comment, // KOMENTARZ UŻYTKOWNIKA!
                timestamp: new Date().toISOString()
            };
            
            console.log('📤 Wysyłam event "feedback" z danymi:', feedbackData);
            this.socket.emit('feedback', feedbackData);
        } else {
            console.error('❌ Brak połączenia z socketem!');
        }
        
        // Pokaż potwierdzenie
        this.showNotification(
            type === 'positive' 
            ? `Dzięki za pozytywny feedback! ${comment ? 'Twój komentarz pomoże nam się poprawić.' : ''}` 
            : `Dzięki za feedback! ${comment ? 'Uwzględnimy Twoje sugestie.' : ''}`
        );
        
        // Wizualne potwierdzenie na przycisku sekcji
        const sectionElement = document.querySelector(`[data-section-id="${sectionId}"]`);
        if (sectionElement) {
            const feedbackDiv = sectionElement.querySelector('.section-feedback');
            if (feedbackDiv) {
                feedbackDiv.innerHTML = `<span class="text-sm ${type === 'positive' ? 'text-green-600' : 'text-red-600'}">✓ Zapisano</span>`;
                setTimeout(() => {
                    feedbackDiv.innerHTML = `
                        <button class="feedback-btn" onclick="chatApp.submitSectionFeedback('${sectionId}', 'positive', '${elementType}')" title="Przydatne">👍</button>
                        <button class="feedback-btn" onclick="chatApp.submitSectionFeedback('${sectionId}', 'negative', '${elementType}')" title="Nieprzydatne">👎</button>
                    `;
                }, 3000);
            }
        }
    }

    parseHtmlIntoDetailedSections(html) {
        // Bardziej szczegółowy parser HTML - każdy nagłówek i akapit osobno
        const sections = [];
        
        // Użyj DOMParser dla lepszego parsowania HTML
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');
        const elements = doc.body.children;
        
        Array.from(elements).forEach(element => {
            const tagName = element.tagName.toLowerCase();
            
            if (['h1', 'h2', 'h3', 'h4', 'h5', 'h6'].includes(tagName)) {
                // Każdy nagłówek jako osobna sekcja
                sections.push(element.outerHTML);
            } else if (tagName === 'p') {
                // Każdy akapit jako osobna sekcja
                sections.push(element.outerHTML);
            } else if (['ul', 'ol'].includes(tagName)) {
                // Każda lista jako osobna sekcja
                sections.push(element.outerHTML);
            } else if (tagName === 'div') {
                // Sprawdź czy div zawiera inne elementy
                const children = element.children;
                if (children.length > 0) {
                    // Jeśli div ma dzieci, podziel je na sekcje
                    Array.from(children).forEach(child => {
                        sections.push(child.outerHTML);
                    });
                } else {
                    // Jeśli div nie ma dzieci, traktuj jako jedną sekcję
                    sections.push(element.outerHTML);
                }
            } else {
                // Inne elementy też jako osobne sekcje
                sections.push(element.outerHTML);
            }
        });
        
        return sections.length > 0 ? sections : [html];
    }

    getSectionType(htmlContent) {
        // Bardziej precyzyjne określanie typu sekcji
        if (htmlContent.includes('<h1>') || htmlContent.includes('<h2>') || htmlContent.includes('<h3>') || 
            htmlContent.includes('<h4>') || htmlContent.includes('<h5>') || htmlContent.includes('<h6>')) {
            return 'header';
        } else if (htmlContent.includes('<p>')) {
            return 'paragraph';
        } else if (htmlContent.includes('<ul>') || htmlContent.includes('<ol>')) {
            return 'list';
        } else if (htmlContent.includes('<strong>') || htmlContent.includes('<em>')) {
            return 'emphasis';
        } else {
            return 'other';
        }
    }

    createSectionsWithFeedback(html, messageId) {
        // Podziel na sekcje - każdy nagłówek i każdy akapit osobno
        const sections = this.parseHtmlIntoDetailedSections(html);
        
        let result = '';
        sections.forEach((section, index) => {
            const sectionId = `${messageId}_section_${index}`;
            const sectionType = this.getSectionType(section);
            
            result += `
                <div class="content-section relative mb-3 p-2 rounded-lg hover:bg-gray-50 transition-colors group" data-section-id="${sectionId}">
                    <div class="section-content">${section}</div>
                    <div class="feedback-container opacity-0 group-hover:opacity-100 transition-opacity absolute top-2 right-2 flex space-x-1">
                        <button class="feedback-btn feedback-btn-positive text-xs" 
                                onclick="chatApp.showFeedbackModal('${sectionId}', '${sectionType}', 'positive')"
                                title="Przydatne">
                            <i class="fas fa-thumbs-up"></i>
                        </button>
                        <button class="feedback-btn feedback-btn-negative text-xs" 
                                onclick="chatApp.showFeedbackModal('${sectionId}', '${sectionType}', 'negative')"
                                title="Nieprzydatne">
                            <i class="fas fa-thumbs-down"></i>
                        </button>
                    </div>
                </div>
            `;
        });
        
        return result;
    }

    parseHtmlIntoDetailedSections(html) {
        // Bardziej szczegółowy parser - każdy nagłówek i akapit osobno
        const sections = [];
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = html;
        
        Array.from(tempDiv.childNodes).forEach(node => {
            if (node.nodeType === Node.ELEMENT_NODE) {
                const tagName = node.tagName.toLowerCase();
                
                if (['h1', 'h2', 'h3', 'h4', 'h5', 'h6'].includes(tagName)) {
                    // Każdy nagłówek jako osobna sekcja
                    sections.push(node.outerHTML);
                } else if (node.tagName.toLowerCase() === 'p') {
                    // Każdy akapit jako osobna sekcja
                    sections.push(node.outerHTML);
                } else if (['ul', 'ol'].includes(tagName)) {
                    // Każda lista jako osobna sekcja
                    sections.push(node.outerHTML);
                } else if (tagName === 'li') {
                    // Każdy element listy jako osobna sekcja
                    sections.push(`<ul>${node.outerHTML}</ul>`);
                } else {
                    // Inne elementy też jako osobne sekcje
                    sections.push(node.outerHTML);
                }
            }
        });
        
        return sections.length > 0 ? sections : [html];
    }

    getSectionType(htmlContent) {
        if (htmlContent.includes('<h1>') || htmlContent.includes('<h2>') || htmlContent.includes('<h3>')) {
            return 'header';
        } else if (htmlContent.includes('<p>')) {
            return 'paragraph';
        } else if (htmlContent.includes('<ul>') || htmlContent.includes('<ol>')) {
            return 'list';
        } else {
            return 'other';
        }
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

    // Metody do obsługi statystyk
    startSessionTimer() {
        setInterval(() => {
            this.updateSessionTime();
        }, 1000);
    }

    updateSessionTime() {
        const elapsed = Date.now() - this.sessionStartTime;
        const hours = Math.floor(elapsed / 3600000);
        const minutes = Math.floor((elapsed % 3600000) / 60000);
        const seconds = Math.floor((elapsed % 60000) / 1000);
        
        let timeStr = '';
        if (hours > 0) {
            timeStr = `${hours}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        } else {
            timeStr = `${minutes}:${seconds.toString().padStart(2, '0')}`;
        }
        
        if (this.sessionTime) {
            this.sessionTime.textContent = timeStr;
        }
    }

    updateQuestionsAsked(messageContent = null) {
        this.questionsAsked++;
        if (this.questionsCount) {
            this.questionsCount.textContent = this.questionsAsked;
        }
        
        // Aktualizuj tytuł sesji po pierwszym pytaniu
        if (this.questionsAsked === 1 && window.sessionManager) {
            window.sessionManager.onFirstMessage(messageContent);
        }
    }

    updateDocumentsUsed(count) {
        this.documentsUsed = count;
        if (this.documentsCount) {
            this.documentsCount.textContent = this.documentsUsed;
        }
    }

    // Metody do obsługi feedbacku
    initFeedbackModal() {
        const modal = this.feedbackModal;
        if (!modal) return;

        const positiveBtn = document.getElementById('feedbackPositive');
        const negativeBtn = document.getElementById('feedbackNegative');
        const cancelBtn = document.getElementById('feedbackCancel');
        const submitBtn = document.getElementById('feedbackSubmit');

        positiveBtn?.addEventListener('click', () => {
            this.selectFeedbackType('positive');
        });

        negativeBtn?.addEventListener('click', () => {
            this.selectFeedbackType('negative');
        });

        cancelBtn?.addEventListener('click', () => {
            this.hideFeedbackModal();
        });

        submitBtn?.addEventListener('click', () => {
            this.submitFeedback();
        });

        // Zamknij modal po kliknięciu tła
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                this.hideFeedbackModal();
            }
        });
    }

    // Funkcja usunięta - używamy nowszej wersji showFeedbackModal poniżej

    showFeedbackModal(sectionId, type, elementType, content) {
        // Ustaw dane feedback
        this.currentFeedback = {
            sectionId: sectionId,
            type: type,
            sectionType: elementType,
            content: content
        };
        
        // Pokaż fragment treści do oceny
        const contentPreview = document.getElementById('feedbackContentPreview');
        const contentContainer = document.getElementById('feedbackContent');
        if (contentPreview && contentContainer && content) {
            contentPreview.textContent = content.substring(0, 200) + (content.length > 200 ? '...' : '');
            contentContainer.style.display = 'block';
        }
        
        // Jeśli typ jest już ustawiony, zaktualizuj przycisk
        if (type) {
            this.selectFeedbackType(type);
        }
        
        // Pokaż modal
        this.feedbackModal.classList.remove('hidden');
        
        // Focus na textarea
        setTimeout(() => {
            this.feedbackDescription.focus();
        }, 100);
    }

    hideFeedbackModal() {
        this.feedbackModal.classList.add('hidden');
        this.currentFeedback = null;
        this.resetFeedbackForm();
        
        // Ukryj podgląd treści
        const contentContainer = document.getElementById('feedbackContent');
        if (contentContainer) {
            contentContainer.style.display = 'none';
        }
    }

    resetFeedbackForm() {
        const positiveBtn = document.getElementById('feedbackPositive');
        const negativeBtn = document.getElementById('feedbackNegative');
        
        positiveBtn?.classList.remove('bg-green-500', 'text-white');
        positiveBtn?.classList.add('bg-green-100', 'text-green-700');
        
        negativeBtn?.classList.remove('bg-red-500', 'text-white');
        negativeBtn?.classList.add('bg-red-100', 'text-red-700');
        
        this.feedbackDescription.value = '';
    }

    selectFeedbackType(type) {
        const positiveBtn = document.getElementById('feedbackPositive');
        const negativeBtn = document.getElementById('feedbackNegative');
        
        // Resetuj oba przyciski
        positiveBtn?.classList.remove('bg-green-500', 'text-white');
        positiveBtn?.classList.add('bg-green-100', 'text-green-700');
        
        negativeBtn?.classList.remove('bg-red-500', 'text-white');
        negativeBtn?.classList.add('bg-red-100', 'text-red-700');
        
        // Podświetl wybrany
        if (type === 'positive') {
            positiveBtn?.classList.remove('bg-green-100', 'text-green-700');
            positiveBtn?.classList.add('bg-green-500', 'text-white');
        } else {
            negativeBtn?.classList.remove('bg-red-100', 'text-red-700');
            negativeBtn?.classList.add('bg-red-500', 'text-white');
        }
        
        if (this.currentFeedback) {
            this.currentFeedback.type = type;
        }
    }

    submitFeedback() {
        if (!this.currentFeedback || !this.currentFeedback.type) {
            alert('Proszę wybrać typ opinii (pozytywna/negatywna)');
            return;
        }

        const description = this.feedbackDescription.value.trim();
        
        // Wyślij feedback do serwera używając tej samej funkcji co dla sekcji
        this.sendSectionFeedback(
            this.currentFeedback.sectionId,
            this.currentFeedback.type,
            this.currentFeedback.sectionType,
            this.currentFeedback.content,
            description
        );
        
        this.hideFeedbackModal();
    }

    markSectionAsRated(sectionId, type) {
        const section = document.querySelector(`[data-section-id="${sectionId}"]`);
        if (section) {
            section.classList.add('feedback-given');
            
            // Dodaj wskaźnik oceny
            const indicator = document.createElement('span');
            indicator.className = `feedback-indicator ${type === 'positive' ? 'text-green-600' : 'text-red-600'}`;
            indicator.innerHTML = type === 'positive' ? '<i class="fas fa-check"></i>' : '<i class="fas fa-times"></i>';
            indicator.title = type === 'positive' ? 'Oceniono jako przydatne' : 'Oceniono jako nieprzydatne';
            
            const feedbackContainer = section.querySelector('.feedback-container');
            if (feedbackContainer) {
                feedbackContainer.appendChild(indicator);
            }
        }
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

    // Funkcja usunięta - używamy nowszej wersji sendSectionFeedback poniżej

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
        
        // Pokaż powiadomienie o zapisaniu
        this.showNotification(
            data.feedback_type === 'positive' 
            ? '✅ Pozytywny feedback zapisany!' 
            : '✅ Feedback zapisany - uwzględnimy Twoje uwagi!'
        );
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

    updateDocumentsUsed(count) {
        this.documentsUsed = count || 0;
        if (this.documentsCount) {
            this.documentsCount.textContent = this.documentsUsed;
        }
    }

    updateConnectionStatus(connected) {
        if (!this.connectionStatus) return;

        if (connected) {
            this.connectionStatus.className = 'w-3 h-3 rounded-full status-connected';
            this.connectionStatus.title = 'Połączono';
            if (this.connectionStatusText) {
                this.connectionStatusText.textContent = 'Połączone';
                this.connectionStatusText.className = 'font-semibold text-green-600';
            }
        } else {
            this.connectionStatus.className = 'w-3 h-3 rounded-full status-disconnected';
            this.connectionStatus.title = 'Rozłączono';
            if (this.connectionStatusText) {
                this.connectionStatusText.textContent = 'Rozłączone';
                this.connectionStatusText.className = 'font-semibold text-red-600';
            }
        }
    }

    updateMessageCounter() {
        this.messageCount++;
        if (this.messageCounter) {
            this.messageCounter.textContent = this.messageCount;
        }
    }

    scrollToBottom() {
        console.log('📜 scrollToBottom wywołane');
        if (this.chatMessages) {
            console.log('📜 Scrolling do dołu:', this.chatMessages.scrollHeight);
            this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
        } else {
            console.error('❌ Brak elementu chatMessages w scrollToBottom!');
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

    submitFeedback(messageId, type, description) {
        console.log('💬 Wysyłam feedback:', { messageId, type, description });
        
        if (this.socket && this.isConnected) {
            this.socket.emit('feedback', {
                message_id: messageId,
                session_id: this.sessionId,
                feedback_type: type,
                description: description || '',
                timestamp: new Date().toISOString()
            });
        }
        
        // Pokaż krótkie potwierdzenie
        this.showNotification(type === 'positive' ? 'Dziękujemy za pozytywny feedback!' : 'Dziękujemy za feedback - pomaga nam się poprawić');
    }

    showNotification(message) {
        // Prosta notyfikacja
        const notification = document.createElement('div');
        notification.className = 'fixed top-4 right-4 bg-blue-600 text-white px-4 py-2 rounded-lg shadow-lg z-50 transition-all';
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        // Usuń po 3 sekundach
        setTimeout(() => {
            notification.style.opacity = '0';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }

    markdownToHtml(text) {
        // Prosta konwersja markdown do HTML
        let html = text
            // Nagłówki
            .replace(/^### (.*$)/gm, '<h3>$1</h3>')
            .replace(/^## (.*$)/gm, '<h2>$1</h2>')
            .replace(/^# (.*$)/gm, '<h1>$1</h1>')
            // Bold i italic
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            // Listy
            .replace(/^\* (.*$)/gm, '<li>$1</li>')
            .replace(/^\- (.*$)/gm, '<li>$1</li>')
            // Kod inline
            .replace(/`(.*?)`/g, '<code>$1</code>')
            // Nowe linie jako akapity
            .replace(/\n\n/g, '</p><p>')
            .replace(/\n/g, '<br>');
        
        // Owinij w akapity jeśli nie ma nagłówków
        if (!html.includes('<h1>') && !html.includes('<h2>') && !html.includes('<h3>')) {
            html = '<p>' + html + '</p>';
        }
        
        // Napraw listy
        html = html.replace(/(<li>.*?<\/li>)/gs, (match) => {
            return '<ul>' + match + '</ul>';
        });
        
        return html;
    }
}

// Inicjalizuj aplikację
let chatApp;
document.addEventListener('DOMContentLoaded', () => {
    chatApp = new ChatApp();
    window.chatApp = chatApp; // Eksportuj globalnie
});
