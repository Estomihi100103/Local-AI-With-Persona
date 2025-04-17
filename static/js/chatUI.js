// Namespace global
var PersonaAI = PersonaAI || {};

// Komponen ChatUI
PersonaAI.ChatUI = function(options) {
    this.messageContainer = options.messageContainer;
    this.messageInput = options.messageInput;
    this.onSidebarToggle = options.onSidebarToggle || function() {};
    this.sidebarOpen = options.sidebarOpen !== undefined ? options.sidebarOpen : (window.innerWidth >= 768);
    this.typingIndicator = null;
    this.assistantMessageElement = null;
    
    this.setupEventListeners();
};

// Menambahkan method ke prototype
PersonaAI.ChatUI.prototype = {
    setupEventListeners: function() {
        var self = this;
        
        window.addEventListener('resize', function() {
            if (window.innerWidth >= 768 && !self.sidebarOpen) {
                self.sidebarOpen = true;
                self.onSidebarToggle();
            }
        });
    },
    
    addUserMessage: function(content) {
        var element = document.createElement('div');
        element.className = 'message user-message';
        element.textContent = content;
        element.setAttribute('aria-label', 'User message: ' + content);
        this.messageContainer.appendChild(element);
        this.scrollToBottom();
    },
    
    addSystemMessage: function(text) {
        var element = document.createElement('div');
        element.className = 'message system-message';
        element.textContent = text;
        this.messageContainer.appendChild(element);
        this.scrollToBottom();
    },
    
    showTypingIndicator: function() {
        this.typingIndicator = document.createElement('div');
        this.typingIndicator.className = 'typing-indicator';
        this.typingIndicator.setAttribute('aria-hidden', 'true');
        this.typingIndicator.innerHTML = 
            '<div class="typing-dot"></div>' +
            '<div class="typing-dot"></div>' +
            '<div class="typing-dot"></div>';
        this.messageContainer.appendChild(this.typingIndicator);
        this.scrollToBottom();
    },
    
    clearTypingIndicator: function() {
        if (this.typingIndicator) {
            this.typingIndicator.remove();
            this.typingIndicator = null;
        }
    },
    
    createAssistantMessage: function() {
        this.assistantMessageElement = document.createElement('div');
        this.assistantMessageElement.className = 'message assistant-message';
        this.messageContainer.appendChild(this.assistantMessageElement);
        this.scrollToBottom();
    },
    
    appendAssistantMessage: function(content) {
        if (this.assistantMessageElement) {
            this.assistantMessageElement.innerHTML += content;
            this.scrollToBottom();
        }
    },
    
    finalizeAssistantMessage: function() {
        this.assistantMessageElement = null;
        this.scrollToBottom();
    },
    
    scrollToBottom: function() {
        var self = this;
        setTimeout(function() {
            if (self.messageContainer) {
                self.messageContainer.scrollTop = self.messageContainer.scrollHeight;
            }
        }, 50);
    },
    
    resizeInput: function() {
        this.messageInput.style.height = 'auto';
        this.messageInput.style.height = Math.min(this.messageInput.scrollHeight, 200) + 'px';
    },
    
    focusInput: function() {
        var self = this;
        setTimeout(function() {
            self.messageInput.focus();
        }, 0);
    },
    
    toggleSidebar: function() {
        const sidebar = document.getElementById('sidebar');
        if (!sidebar) {
            console.warn('Sidebar element not found');
            return this.sidebarOpen;
        }
    
        this.sidebarOpen = !this.sidebarOpen;
    
        if (this.sidebarOpen) {
            sidebar.classList.remove('sidebar-hidden');
        } else {
            sidebar.classList.add('sidebar-hidden');
        }
    
        // Notify parent (jika ingin trigger sesuatu di `chatApp`)
        this.onSidebarToggle();
    
        return this.sidebarOpen;
    },

    //method sidebarOpen
    openSidebar: function() {
        this.sidebarOpen = true;
        this.updateSidebarVisibility();
    },

    closeSidebar: function() {
        this.sidebarOpen = false;
        this.updateSidebarVisibility();
    },

    updateSidebarVisibility: function() {
        var sidebar = document.querySelector('.sidebar');
        if (!sidebar) return;

        if (this.sidebarOpen) {
            sidebar.classList.remove('sidebar-hidden');
        } else {
            sidebar.classList.add('sidebar-hidden');
        }
    },
};