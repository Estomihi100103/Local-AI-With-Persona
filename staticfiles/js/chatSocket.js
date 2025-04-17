/**
 * Mengelola koneksi WebSocket dan komunikasi dengan server.
 **/

export default class ChatSocket {
    constructor({ sessionId, onOpen, onMessage, onClose, onError }) {
        this.sessionId = sessionId;
        this.onOpen = onOpen;
        this.onMessage = onMessage;
        this.onClose = onClose;
        this.onError = onError;
        this.socket = null;
        this.baseUrl = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
    }

    connect() {
        if (this.socket && this.socket.readyState !== WebSocket.CLOSED) {
            console.log('WebSocket connection already exists');
            return;
        }

        this.socket = new WebSocket(`${this.baseUrl}${window.location.host}/ws/chat/${this.sessionId}/`);

        this.socket.onopen = () => {
            console.log('WebSocket connection established');
            this.onOpen();
        };

        this.socket.onmessage = (e) => {
            try {
                const data = JSON.parse(e.data);
                this.onMessage(data);
            } catch (error) {
                console.error('Invalid WebSocket message:', error);
                this.onError(error);
            }
        };

        this.socket.onclose = (e) => {
            console.log('WebSocket connection closed:', e.code, e.reason);
            this.onClose(e);
        };

        this.socket.onerror = (e) => {
            console.error('WebSocket error:', e);
            this.onError(e);
        };
    }

    sendMessage(data) {
        if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
            console.error('WebSocket is not connected');
            this.onError(new Error('WebSocket is not connected'));
            return;
        }

        // Validasi data
        if (!data || (typeof data !== 'object' && typeof data !== 'string')) {
            console.error('Invalid message format');
            this.onError(new Error('Invalid message format'));
            return;
        }

        // Jika data adalah string (pesan pengguna), konversi ke format { message }
        const payload = typeof data === 'string' ? { message: data, session_id: this.sessionId } : { ...data, session_id: this.sessionId };

        this.socket.send(JSON.stringify(payload));
    }

    close() {
        if (this.socket) {
            this.socket.close();
        }
    }
}