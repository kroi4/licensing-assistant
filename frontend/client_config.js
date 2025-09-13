// Configuration constants
const API_BASE_URL = 'http://localhost:8000';
const ASSESS_API = 'api/assess';

// Export for use in other modules
window.CONFIG = {
    API_BASE_URL,
    ASSESS_API
};

console.log('Configuration loaded:', window.CONFIG);