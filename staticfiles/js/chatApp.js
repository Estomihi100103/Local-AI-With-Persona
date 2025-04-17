/**
 * Mengkoordinasikan ChatSocket (untuk WebSocket) dan ChatUI (untuk UI dan responsivitas).
 **/

import ChatSocket from './chatSocket.js';
import ChatUI from './chatUI.js';
import personaToggle from './personaToggle.js';
import { sanitizeInput } from './utils.js';

export default function chatApp() {
    return {
        // State
        messageText: '',
        isTyping: false,
        hasConnectedMessage: false,

        // Modul
        socket: null,
        ui: null,

        // Inisialisasi
        init() {
            console.log('Initializing chat application');

            // Inisialisasi socket
            this.socket = new ChatSocket({
                sessionId: document.querySelector('[data-session-id]').getAttribute('data-session-id'),
                onOpen: () => this.handleSocketOpen(),
                onMessage: (data) => this.handleSocketMessage(data),
                onClose: (e) => this.handleSocketClose(e),
                onError: (e) => this.handleSocketError(e),
            });

            // Inisialisasi UI
            this.ui = new ChatUI({
                messageContainer: this.$refs.messageContainer,
                messageInput: this.$refs.messageInput,
                onSidebarToggle: () => this.toggleSidebar(),
            });

            // Setup awal
            this.socket.connect();
            this.ui.scrollToBottom();
            this.ui.focusInput();

            // Daftarkan personaToggle dengan socket
            Alpine.data('personaToggle', () => personaToggle(this.socket));
        },

        // Handler untuk WebSocket
        handleSocketOpen() {
            if (!this.hasConnectedMessage) {
                this.ui.addSystemMessage('Connected to chat session');
                this.hasConnectedMessage = true;
            }
        },

        handleSocketMessage(data) {
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
                    this.$dispatch('session-info', data);
                    break;
                default:
                    console.log('Ignoring message type:', data.type);
            }
        },

        handleSocketClose(e) {
            const reason = e.wasClean ? 'Connection closed cleanly' : 'Connection interrupted';
            this.ui.addSystemMessage(`Chat connection closed (${reason}). Reconnecting...`);
            setTimeout(() => this.socket.connect(), 3000);
        },

        handleSocketError(e) {
            this.ui.addSystemMessage('Error with chat connection. Please check your network.');
            console.error('WebSocket error:', e);
        },

        // Handler untuk UI
        sendMessage() {
            const message = sanitizeInput(this.messageText.trim());
            if (!message) return;

            this.ui.addUserMessage(message);
            this.ui.showTypingIndicator();
            this.socket.sendMessage({ message });
            this.messageText = '';
            this.ui.resizeInput();
            this.ui.scrollToBottom();
        },

        toggleSidebar() {
            this.ui.toggleSidebar();
        },

        handleEnterKey(e) {
            if (e.shiftKey) return;
            e.preventDefault();
            this.sendMessage();
        },

        clearAllChats() {
            if (confirm('Are you sure you want to delete all your chat sessions? This cannot be undone.')) {
                window.location.href = "{% url 'chat_home' %}";
            }
        },
    };
}