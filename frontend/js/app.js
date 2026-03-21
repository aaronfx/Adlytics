/**
 * ADLYTICS - App Utilities
 * Additional helper functions for the application
 */

// API endpoint configuration
const getApiUrl = () => {
    // Auto-detect based on hostname
    const hostname = window.location.hostname;
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
        return 'http://localhost:8000/api';
    }
    // Production - same origin or relative
    return '/api';
};

// Utility: Format currency based on location
const formatCurrency = (amount, location = 'nigeria') => {
    if (location.toLowerCase().includes('nigeria') || location.toLowerCase().includes('naija')) {
        return '₦' + amount.toLocaleString();
    }
    return '$' + amount.toLocaleString();
};

// Utility: Copy to clipboard
const copyToClipboard = async (text) => {
    try {
        await navigator.clipboard.writeText(text);
        return true;
    } catch (err) {
        console.error('Failed to copy:', err);
        return false;
    }
};

// Utility: Debounce function
const debounce = (func, wait) => {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
};

// Utility: Validate ad copy length
const validateAdCopy = (text) => {
    const minLength = 10;
    const maxLength = 5000;

    if (text.length < minLength) {
        return { valid: false, error: `Ad copy too short (min ${minLength} chars)` };
    }
    if (text.length > maxLength) {
        return { valid: false, error: `Ad copy too long (max ${maxLength} chars)` };
    }
    return { valid: true };
};

// Utility: Estimate reading time
const estimateReadingTime = (text) => {
    const wordsPerSecond = 3; // Fast scrolling speed
    const words = text.trim().split(/\s+/).length;
    const seconds = Math.ceil(words / wordsPerSecond);
    return seconds;
};

// Utility: Score color helper
const getScoreColor = (score) => {
    if (score >= 70) return 'text-green-400';
    if (score >= 50) return 'text-yellow-400';
    return 'text-red-400';
};

// Utility: Platform icon mapping
const getPlatformIcon = (platform) => {
    const icons = {
        tiktok: '🎵',
        facebook: '👥',
        instagram: '📷',
        youtube: '🎬',
        linkedin: '💼',
        twitter: '🐦',
        google: '🔍'
    };
    return icons[platform] || '📱';
};

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        getApiUrl,
        formatCurrency,
        copyToClipboard,
        debounce,
        validateAdCopy,
        estimateReadingTime,
        getScoreColor,
        getPlatformIcon
    };
}
