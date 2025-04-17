// Namespace global
var PersonaAI = PersonaAI || {};

// Component ChatApp untuk Alpine
PersonaAI.createChatApp = function() {
    return {
        // State
        messageText: '',
        isTyping: false,
        hasConnectedMessage: false,
        sidebarOpen: window.innerWidth >= 768,
        selectedModel: null,
        disableModelSelect: false,
        
        // Komponen
        socket: null,
        ui: null,
        
        // Inisialisasi
        init: function() {
            PersonaAI.utils.log('Initializing chat application', 'info');
            var self = this;
            
            // Ambil session ID
            var sessionId = document.querySelector('[data-session-id]').getAttribute('data-session-id');
            
            // Inisialisasi WebSocket
            this.socket = new PersonaAI.ChatSocket({
                sessionId: sessionId,
                onOpen: function() { self.handleSocketOpen(); },
                onMessage: function(data) { self.handleSocketMessage(data); },
                onClose: function(e) { self.handleSocketClose(e); },
                onError: function(e) { self.handleSocketError(e); }
            });
            
            // Inisialisasi UI
            this.ui = new PersonaAI.ChatUI({
                messageContainer: this.$refs.messageContainer,
                messageInput: this.$refs.messageInput,
                onSidebarToggle: function() { self.handleSidebarToggle(); },
                sidebarOpen: this.sidebarOpen
            });
            
            // Simpan referensi socket untuk personaToggle
            window.chatSocket = this.socket;
            
            // Setup awal
            this.socket.connect();
            this.ui.scrollToBottom();
            this.ui.focusInput();
            
            // Setup event listener untuk error dari personaToggle
            document.addEventListener('chat-error', function(event) {
                self.ui.addSystemMessage(event.detail.message);
            });
        },
        
        // Handler untuk WebSocket
        handleSocketOpen: function() {
            if (!this.hasConnectedMessage) {
                this.ui.addSystemMessage('Connected to chat session');
                this.hasConnectedMessage = true;
            }
        },
        
        handleSocketMessage: function(data) {
            switch (data.type) {
                case 'assistant_response_start':
                    this.isTyping = false;
                    this.ui.clearTypingIndicator();
                    this.ui.createAssistantMessage();
                    break;
                    
                case 'assistant_response_chunk':
                    this.ui.appendAssistantMessage(data.message);
                    break;
                    
                case 'assistant_response_end':
                    this.ui.finalizeAssistantMessage();
                    this.ui.focusInput();
                    break;
                    
                case 'error':
                    this.ui.addSystemMessage(data.message);
                    break;
                    
                case 'session_info':
                    if (data.disable_model_select){
                        this.disableModelSelect=true;
                    }
                    // Dispatch event untuk personaToggle
                    var sessionInfoEvent = new CustomEvent('session-info', {
                        detail: data,
                        bubbles: true
                    });
                    document.dispatchEvent(sessionInfoEvent);
                    break;
                case 'model_selected':
                    this.selectedModel = data.model;
                    this.ui.addSystemMessage(`Model changed to ${data.model}`);
                    break;
                default:
                    PersonaAI.utils.log('Ignoring message type: ' + data.type, 'debug');
            }
        },
        
        handleSocketClose: function(e) {
            var reason = e.wasClean ? 'Connection closed cleanly' : 'Connection interrupted';
            this.ui.addSystemMessage('Chat connection closed (' + reason + '). Reconnecting...');
        },
        
        handleSocketError: function(e) {
            this.ui.addSystemMessage('Error with chat connection. Please check your network.');
            PersonaAI.utils.log('WebSocket error', 'error');
        },
        
        // Handler untuk UI
        sendMessage: function() {
            var message = PersonaAI.utils.sanitizeInput(this.messageText.trim());
            if (!message) return;
            
            this.ui.addUserMessage(message);
            this.ui.showTypingIndicator();
            this.socket.sendMessage({ message: message });
            this.messageText = '';
            this.ui.resizeInput();
            this.ui.scrollToBottom();
        },

        selectModel: function(model) {
            if(!model) return;
            this.selectedModel = model;
            this.socket.sendMessage({type:"select_model", model: model});
            PersonaAI.utils.log(`Model selected: ${model}`, 'info');
        },

        toggleSidebar: function() {
            this.ui.toggleSidebar();
            this.sidebarOpen = this.ui.sidebarOpen;
        },

        handleSidebarToggle: function() {
            this.sidebarOpen = this.ui.sidebarOpen;
        },
        
        handleSidebarToggle: function() {
            this.sidebarOpen = this.ui.sidebarOpen;
        },
        
        handleEnterKey: function(e) {
            if (e.shiftKey) return;
            e.preventDefault();
            this.sendMessage();
        },
        
        autoResizeTextarea: function() {
            this.ui.resizeInput();
        },
        
        clearAllChats: function() {
            if (confirm('Are you sure you want to delete all your chat sessions? This cannot be undone.')) {
                window.location.href = window.chatAppConfig.chatHomeUrl;
            }
        }
    };
};