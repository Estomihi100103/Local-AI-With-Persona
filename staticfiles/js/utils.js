/**
 * Menyediakan fungsi untuk sanitasi input demi keamanan.
 */

export function sanitizeInput(input) {
    // Sederhana: ganti karakter berbahaya, idealnya gunakan library seperti DOMPurify
    return input.replace(/[<>&"']/g, (match) => ({
        '<': '&lt;',
        '>': '&gt;',
        '&': '&amp;',
        '"': '&quot;',
        "'": '&#x27;',
    })[match]);
}