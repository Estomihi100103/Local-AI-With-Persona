/**
 * Mengelola semua aspek UI, termasuk pembuatan pesan, typing indicator, scroll, dan responsivitas.
 * 
 */
export default class ChatUI {
    constructor({ messageContainer, messageInput, onSidebarToggle }) {
        this.messageContainer = messageContainer;
        this.messageInput = messageInput;
        this.onSidebarToggle = onSidebarToggle;
        this.sidebarOpen = window.innerWidth >= 768;
        this.typingIndicator = null;
        this.assistantMessageElement = null;

        this.setupEventListeners();
    }

    setupEventListeners() {
        window.addEventListener('resize', () => {
            if (window.innerWidth >= 768 && !this.sidebarOpen) {
                this.sidebarOpen = true;
                this.onSidebarToggle();
            }
        });
    }

    addUserMessage(content) {
        const element = document.createElement('div');
        element.className = 'message user-message';
        element.textContent = content;
        element.setAttribute('aria-label', `User message: ${content}`);
        this.messageContainer.appendChild(element);
        this.scrollToBottom();
    }

    addSystemMessage(text) {
        const element = document.createElement('div');
        element.className = 'message system-message';
        element.textContent = text;
        this.messageContainer.appendChild(element);
        this.scrollToBottom();
    }

    showTypingIndicator() {
        this.typingIndicator = document.createElement('div');
        this.typingIndicator.className = 'typing-indicator';
        this.typingIndicator.setAttribute('aria-hidden', 'true');
        this.typingIndicator.innerHTML = `
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        `;
        this.messageContainer.appendChild(this.typingIndicator);
        this.scrollToBottom();
    }

    clearTypingIndicator() {
        if (this.typingIndicator) {
            this.typingIndicator.remove();
            this.typingIndicator = null;
        }
    }

    createAssistantMessage() {
        this.assistantMessageElement = document.createElement('div');
        this.assistantMessageElement.className = 'message assistant-message';
        this.messageContainer.appendChild(this.assistantMessageElement);
        this.scrollToBottom();
    }

    appendAssistantMessage(content) {
        if (this.assistantMessageElement) {
            this.assistantMessageElement.innerHTML += content;
            this.scrollToBottom();
        }
    }

    finalizeAssistantMessage() {
        this.assistantMessageElement = null;
        this.scrollToBottom();
    }

    scrollToBottom() {
        setTimeout(() => {
            if (this.messageContainer) {
                this.messageContainer.scrollTop = this.messageContainer.scrollHeight;
            }
        }, 50);
    }

    resizeInput() {
        this.messageInput.style.height = 'auto';
        this.messageInput.style.height = `${Math.min(this.messageInput.scrollHeight, 200)}px`;
    }

    focusInput() {
        setTimeout(() => {
            this.messageInput.focus();
        }, 0);
    }

    toggleSidebar() {
        this.sidebarOpen = !this.sidebarOpen;
        this.onSidebarToggle();
    }
}