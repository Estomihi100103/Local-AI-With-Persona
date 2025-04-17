// Namespace global
var PersonaAI = PersonaAI || {};

// Component PersonaToggle untuk Alpine
PersonaAI.createPersonaToggle = function() {
    return {
        // State
        enabled: false,
        disabled: false,
        chatSocket: null,
        
        // Inisialisasi
        init: function() {
            PersonaAI.utils.log('Initializing persona toggle', 'info');
            
            // Mendapatkan instance socket
            this.chatSocket = window.chatSocket;
            
            // Setup event listeners
            var self = this;
            
            // Dengarkan event session-info
            document.addEventListener('session-info', function(event) {
                self.enabled = event.detail.use_persona;
                self.disabled = event.detail.disable_toggle;
                PersonaAI.utils.log('Toggle state updated: ' + JSON.stringify({
                    enabled: self.enabled,
                    disabled: self.disabled
                }), 'debug');
            });
            
            // Dengarkan event update-persona
            document.addEventListener('update-persona', function(event) {
                self.handlePersonaUpdate(event.detail);
            });
        },
        
        // Handler untuk update toggle
        handlePersonaUpdate: function(enabled) {
            if (this.disabled) {
                PersonaAI.utils.log('Toggle is locked, cannot change', 'warn');
                this.dispatchError('Toggle is locked due to existing messages.');
                return;
            }
            
            this.enabled = enabled;
            this.sendPersonaUpdate();
        },
        
        // Kirim pembaruan use_persona ke server
        sendPersonaUpdate: function() {
            if (!this.chatSocket) {
                PersonaAI.utils.log('Socket not available. Cannot send toggle update', 'warn');
                this.dispatchError('Cannot connect to server. Please try again.');
                return;
            }
            
            var sessionId = document.querySelector('[data-session-id]')?.getAttribute('data-session-id');
            if (!sessionId) {
                PersonaAI.utils.log('Session ID not found', 'error');
                this.dispatchError('Invalid session. Please refresh the page.');
                return;
            }
            
            PersonaAI.utils.log('Sending toggle update to server: ' + this.enabled, 'info');
            this.chatSocket.sendMessage({ use_persona: this.enabled, session_id: sessionId });
        },
        
        // Dispatch error ke chatApp untuk ditampilkan
        dispatchError: function(message) {
            var errorEvent = new CustomEvent('chat-error', { 
                detail: { message: message },
                bubbles: true
            });
            document.dispatchEvent(errorEvent);
        }
    };
};