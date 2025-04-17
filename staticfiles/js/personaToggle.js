export default function personaToggle(socket) {
    return {
        // State
        enabled: false,
        disabled: false,

        // Inisialisasi
        init() {
            console.log('Initializing persona toggle');

            // Simpan referensi ke socket dari chatApp
            this.socket = socket;

            // Dengarkan event session-info dari chatApp
            this.$watch('$dispatch', (event) => {
                if (event.name === 'session-info') {
                    this.enabled = event.detail.use_persona;
                    this.disabled = event.detail.disable_toggle;
                    console.log('Toggle state updated:', {
                        enabled: this.enabled,
                        disabled: this.disabled,
                    });
                }
            });

            // Dengarkan event update-persona
            window.addEventListener('update-persona', (event) => {
                this.handlePersonaUpdate(event.detail);
            });
        },

        // Handler untuk update toggle
        handlePersonaUpdate(enabled) {
            if (this.disabled) {
                console.log('Toggle is locked, cannot change.');
                this.dispatchError('Toggle is locked due to existing messages.');
                return;
            }

            this.enabled = enabled;
            this.sendPersonaUpdate();
        },

        // Kirim pembaruan use_persona ke server
        sendPersonaUpdate() {
            if (!this.socket) {
                console.warn('Socket not available. Cannot send toggle update.');
                this.dispatchError('Cannot connect to server. Please try again.');
                return;
            }

            const sessionId = document.querySelector('[data-session-id]')?.getAttribute('data-session-id');
            if (!sessionId) {
                console.error('Session ID not found.');
                this.dispatchError('Invalid session. Please refresh the page.');
                return;
            }

            console.log('Sending toggle update to server:', this.enabled);
            this.socket.sendMessage({ use_persona: this.enabled, session_id: sessionId });
        },

        // Dispatch error ke chatApp untuk ditampilkan
        dispatchError(message) {
            this.$dispatch('error', { message });
        },
    };
}