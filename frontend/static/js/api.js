/**
 * Receipt Lens - API Client
 * Handles all API communication with the backend
 */

const API_BASE_URL = '/api';

/**
 * API Client Class
 */
class APIClient {
    constructor() {
        this.token = localStorage.getItem('token');
    }

    /**
     * Set authentication token
     */
    setToken(token) {
        this.token = token;
        if (token) {
            localStorage.setItem('token', token);
        } else {
            localStorage.removeItem('token');
        }
    }

    /**
     * Get authentication token
     */
    getToken() {
        return this.token;
    }

    /**
     * Check if user is authenticated
     */
    isAuthenticated() {
        return !!this.token;
    }

    /**
     * Clear authentication
     */
    clearAuth() {
        this.token = null;
        localStorage.removeItem('token');
        localStorage.removeItem('user');
    }

    /**
     * Make HTTP request
     */
    async request(endpoint, options = {}) {
        const url = `${API_BASE_URL}${endpoint}`;
        const headers = {
            ...options.headers,
        };

        // Add authorization header if token exists
        if (this.token && !options.skipAuth) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }

        // Add content type for JSON requests
        if (options.body && !(options.body instanceof FormData)) {
            headers['Content-Type'] = 'application/json';
        }

        try {
            const response = await fetch(url, {
                ...options,
                headers,
                body: options.body instanceof FormData
                    ? options.body
                    : options.body
                        ? JSON.stringify(options.body)
                        : undefined,
            });

            // Check for authentication errors
            if (response.status === 401) {
                this.clearAuth();
                window.location.href = '/login.html';
                throw new Error('Authentication required');
            }

            // Parse JSON response
            const data = await response.json();

            // Handle API error responses
            if (!response.ok) {
                throw new Error(data.error || `HTTP error! status: ${response.status}`);
            }

            return data;
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    /**
     * GET request
     */
    async get(endpoint, options = {}) {
        return this.request(endpoint, {
            ...options,
            method: 'GET',
        });
    }

    /**
     * POST request
     */
    async post(endpoint, body, options = {}) {
        return this.request(endpoint, {
            ...options,
            method: 'POST',
            body,
        });
    }

    /**
     * PUT request
     */
    async put(endpoint, body, options = {}) {
        return this.request(endpoint, {
            ...options,
            method: 'PUT',
            body,
        });
    }

    /**
     * PATCH request
     */
    async patch(endpoint, body, options = {}) {
        return this.request(endpoint, {
            ...options,
            method: 'PATCH',
            body,
        });
    }

    /**
     * DELETE request
     */
    async delete(endpoint, options = {}) {
        return this.request(endpoint, {
            ...options,
            method: 'DELETE',
        });
    }

    // ==================== Auth Endpoints ====================

    /**
     * Register new user
     */
    async register(username, email, password) {
        const response = await this.post('/auth/register', {
            username,
            email,
            password,
        }, { skipAuth: true });

        if (response.success) {
            // Auto-login after registration
            const token = response.data.token.access_token;
            this.setToken(token);
            localStorage.setItem('user', JSON.stringify(response.data.user));
        }

        return response;
    }

    /**
     * Login user
     */
    async login(username, password) {
        const response = await this.post('/auth/login', {
            username,
            password,
        }, { skipAuth: true });

        if (response.success) {
            const token = response.data.token.access_token;
            this.setToken(token);
            localStorage.setItem('user', JSON.stringify(response.data.user));
        }

        return response;
    }

    /**
     * Logout user
     */
    logout() {
        this.clearAuth();
        window.location.href = '/login.html';
    }

    /**
     * Get current user
     */
    async getCurrentUser() {
        const response = await this.get('/auth/me');
        if (response.success) {
            localStorage.setItem('user', JSON.stringify(response.data));
        }
        return response;
    }

    /**
     * Get cached user from localStorage
     */
    getCachedUser() {
        const userStr = localStorage.getItem('user');
        return userStr ? JSON.parse(userStr) : null;
    }

    // ==================== Receipts Endpoints ====================

    /**
     * Upload receipt
     */
    async uploadReceipt(file) {
        const formData = new FormData();
        formData.append('file', file);
        return this.post('/receipts/upload', formData);
    }

    /**
     * Upload multiple receipt images for a single long receipt
     */
    async uploadMultipleReceipts(files) {
        const formData = new FormData();
        // Append each file to the FormData
        for (let i = 0; i < files.length; i++) {
            formData.append('files', files[i]);
        }
        return this.post('/receipts/upload-multiple', formData);
    }

    /**
     * Get receipts list (paginated)
     */
    async getReceipts(page = 1, pageSize = 20) {
        return this.get(`/receipts?page=${page}&page_size=${pageSize}`);
    }

    /**
     * Get receipt by ID
     */
    async getReceipt(id) {
        return this.get(`/receipts/${id}`);
    }

    /**
     * Update receipt
     */
    async updateReceipt(id, updateData) {
        return this.patch(`/receipts/${id}`, updateData);
    }

    /**
     * Delete receipt
     */
    async deleteReceipt(id) {
        return this.delete(`/receipts/${id}`);
    }

    /**
     * Get unique store names
     */
    async getStores() {
        return this.get('/receipts/stores');
    }

    // ==================== Analytics Endpoints ====================

    /**
     * Get monthly summary
     */
    async getMonthlySummary(month, year) {
        return this.get(`/analytics/monthly-summary?month=${month}&year=${year}`);
    }

    /**
     * Get all-time summary (all receipts)
     */
    async getAllTimeSummary() {
        return this.get('/analytics/all-time-summary');
    }

    /**
     * Get store comparison
     */
    async getStoreComparison(months = 6) {
        return this.get(`/analytics/store-comparison?months=${months}`);
    }

    /**
     * Get price evolution for a product
     */
    async getPriceEvolution(product, months = 6) {
        const encodedProduct = encodeURIComponent(product);
        return this.get(`/analytics/price-evolution?product=${encodedProduct}&months=${months}`);
    }

    // ==================== Health Endpoints ====================

    /**
     * Health check
     */
    async healthCheck() {
        return this.get('/health', { skipAuth: true });
    }
}

// Create global API instance
window.api = new APIClient();
