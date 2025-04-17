// Namespace global
var PersonaAI = PersonaAI || {};

// Komponen ChatSocket
PersonaAI.ChatSocket = function(options) {
    this.sessionId = options.sessionId;
    this.onOpen = options.onOpen || function() {};
    this.onMessage = options.onMessage || function() {};
    this.onClose = options.onClose || function() {};
    this.onError = options.onError || function() {};
    this.socket = null;
    this.baseUrl = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 3000;
};

// Menambahkan method ke prototype
PersonaAI.ChatSocket.prototype = {
    connect: function() {
        var self = this;
        
        if (this.socket && this.socket.readyState !== WebSocket.CLOSED) {
            PersonaAI.utils.log('WebSocket connection already exists', 'info');
            return;
        }
        
        PersonaAI.utils.log('Connecting to WebSocket...', 'info');
        this.socket = new WebSocket(this.baseUrl + window.location.host + '/ws/chat/' + this.sessionId + '/');
        
        this.socket.onopen = function() {
            PersonaAI.utils.log('WebSocket connection established', 'info');
            self.reconnectAttempts = 0;
            self.onOpen();
        };
        
        this.socket.onmessage = function(e) {
            try {
                var data = JSON.parse(e.data);
                self.onMessage(data);
            } catch (error) {
                PersonaAI.utils.log('Invalid WebSocket message: ' + error, 'error');
                self.onError(error);
            }
        };
        
        this.socket.onclose = function(e) {
            PersonaAI.utils.log('WebSocket connection closed: ' + e.code + ', ' + e.reason, 'warn');
            
            if (self.reconnectAttempts < self.maxReconnectAttempts) {
                self.reconnectAttempts++;
                setTimeout(function() {
                    self.connect();
                }, self.reconnectDelay);
            }
            
            self.onClose(e);
        };
        
        this.socket.onerror = function(e) {
            PersonaAI.utils.log('WebSocket error', 'error');
            self.onError(e);
        };
    },
    
    sendMessage: function(data) {
        if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
            PersonaAI.utils.log('WebSocket is not connected', 'error');
            this.onError(new Error('WebSocket is not connected'));
            return;
        }
        
        // Validasi data
        if (!data || (typeof data !== 'object' && typeof data !== 'string')) {
            PersonaAI.utils.log('Invalid message format', 'error');
            this.onError(new Error('Invalid message format'));
            return;
        }
        
        // Jika data adalah string (pesan pengguna), konversi ke format { message }
        var payload = typeof data === 'string' 
            ? { message: data, session_id: this.sessionId } 
            : Object.assign({}, data, { session_id: this.sessionId });
        
        this.socket.send(JSON.stringify(payload));
    },
    
    close: function() {
        if (this.socket) {
            this.socket.close();
        }
    }
};