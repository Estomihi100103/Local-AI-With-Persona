// Namespace global
var PersonaAI = PersonaAI || {};

// Utilitas
PersonaAI.utils = {
    // Sanitasi input untuk keamanan
    sanitizeInput: function(input) {
        if (!input) return '';
        return input.replace(/[<>&"']/g, function(match) {
            var replacements = {
                '<': '&lt;',
                '>': '&gt;',
                '&': '&amp;',
                '"': '&quot;',
                "'": '&#x27;'
            };
            return replacements[match];
        });
    },
    
    // Logger dengan level debug yang bisa dimatikan di production
    log: function(message, level) {
        var levels = {debug: 0, info: 1, warn: 2, error: 3};
        var currentLevel = levels.debug; // Ubah ke levels.info di production
        
        if (levels[level] >= currentLevel) {
            console[level](message);
        }
    }
};