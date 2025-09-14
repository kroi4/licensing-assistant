/**
 * API Service Layer
 * Handles all API communications and data transformations
 */

class ApiService {
    constructor() {
        // Ensure config is loaded
        if (!window.CONFIG) {
            throw new Error('Configuration not loaded. Make sure client_config is loaded first.');
        }
        
        this.baseUrl = window.CONFIG.API_BASE_URL;
        this.assessEndpoint = window.CONFIG.ASSESS_API;
    }

    /**
     * Generic fetch wrapper with error handling
     * @param {string} url - The URL to fetch
     * @param {Object} options - Fetch options
     * @returns {Promise<Object>} - The response data
     */
    async fetchWithErrorHandling(url, options = {}) {
        try {
            const response = await fetch(url, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });

            if (!response.ok) {
                // Surface server-provided error message when available (e.g., AI required)
                const serverMessage = data && (data.error || data.message);
                if (serverMessage) {
                    throw new Error(serverMessage);
                }
                throw new Error(`שגיאה בתקשורת עם השרת (סטטוס ${response.status}).`);
            }

            const data = await response.json();
            return data;
        } catch (error) {
            console.error('API Error:', error);
            
            // Handle different types of errors
            if (error.name === 'TypeError' && error.message.includes('fetch')) {
                throw new Error(`לא ניתן להתחבר לשרת. אנא וודא שהשרת פועל על ${this.baseUrl}`);
            }
            
            if (error.message.includes('HTTP error')) {
                throw new Error('שגיאה בתקשורת עם השרת. אנא נסה שוב.');
            }
            
            throw error;
        }
    }

    /**
     * Assess business licensing requirements
     * @param {Object} businessData - Business information
     * @param {number} businessData.area - Business area in square meters
     * @param {number} businessData.seats - Number of seats
     * @param {string[]} businessData.features - Array of business features
     * @returns {Promise<Object>} - Assessment results
     */
    async assessBusiness(businessData) {
        const url = `${this.baseUrl}/${this.assessEndpoint}`;
        
        // Validate input data
        this.validateBusinessData(businessData);
        
        const options = {
            method: 'POST',
            body: JSON.stringify(businessData)
        };

        return await this.fetchWithErrorHandling(url, options);
    }

    /**
     * Validate business data before sending to API
     * @param {Object} businessData - Business data to validate
     * @throws {Error} - If validation fails
     */
    validateBusinessData(businessData) {
        const { area, seats, features } = businessData;

        if (!area || area <= 0) {
            throw new Error('שטח העסק חייב להיות גדול מ-0');
        }

        if (seats === undefined || seats < 0) {
            throw new Error('מספר מקומות ישיבה חייב להיות 0 או יותר');
        }

        if (!Array.isArray(features)) {
            throw new Error('מאפיינים חייבים להיות מערך');
        }

        // Additional business logic validations
        if (area > 10000) {
            console.warn('שטח גדול מאוד - אנא וודא שהנתון נכון');
        }

        if (seats > 1000) {
            console.warn('מספר מקומות גדול מאוד - אנא וודא שהנתון נכון');
        }
    }

    /**
     * Health check endpoint
     * @returns {Promise<Object>} - Health status
     */
    async healthCheck() {
        const url = `${this.baseUrl}/health`;
        return await this.fetchWithErrorHandling(url);
    }

    /**
     * Reload rules (development endpoint)
     * @returns {Promise<Object>} - Reload status
     */
    async reloadRules() {
        const url = `${this.baseUrl}/api/reload-rules`;
        const options = { method: 'POST' };
        return await this.fetchWithErrorHandling(url, options);
    }

    /**
     * Get current rules (development endpoint)
     * @returns {Promise<Object>} - Current rules
     */
    async getRules() {
        const url = `${this.baseUrl}/api/rules`;
        return await this.fetchWithErrorHandling(url);
    }
}

// Initialize service when DOM is ready or immediately if config exists
function initializeApiService() {
    try {
        if (window.CONFIG) {
            const apiService = new ApiService();
            window.ApiService = apiService;
            console.log('ApiService initialized successfully');
        } else {
            console.error('CONFIG not found, retrying in 100ms...');
            setTimeout(initializeApiService, 100);
        }
    } catch (error) {
        console.error('Failed to initialize ApiService:', error);
        setTimeout(initializeApiService, 100);
    }
}

// Try to initialize immediately
initializeApiService();
