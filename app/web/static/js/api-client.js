/**
 * Streaklet API Client
 *
 * Unified API wrapper that standardizes all HTTP requests across the application.
 * Provides consistent error handling, loading states, and response processing.
 */

/**
 * API Client class for making HTTP requests
 */
class ApiClient {
    /**
     * Make a GET request
     * @param {string} url - API endpoint
     * @param {Object} options - Request options
     * @returns {Promise<Object>} Response data
     */
    static async get(url, options = {}) {
        return this.request(url, { ...options, method: 'GET' });
    }

    /**
     * Make a POST request
     * @param {string} url - API endpoint
     * @param {Object} data - Request body
     * @param {Object} options - Request options
     * @returns {Promise<Object>} Response data
     */
    static async post(url, data = null, options = {}) {
        return this.request(url, {
            ...options,
            method: 'POST',
            body: data ? JSON.stringify(data) : null,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        });
    }

    /**
     * Make a PUT request
     * @param {string} url - API endpoint
     * @param {Object} data - Request body
     * @param {Object} options - Request options
     * @returns {Promise<Object>} Response data
     */
    static async put(url, data = null, options = {}) {
        return this.request(url, {
            ...options,
            method: 'PUT',
            body: data ? JSON.stringify(data) : null,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        });
    }

    /**
     * Make a DELETE request
     * @param {string} url - API endpoint
     * @param {Object} options - Request options
     * @returns {Promise<Object>} Response data
     */
    static async delete(url, options = {}) {
        return this.request(url, { ...options, method: 'DELETE' });
    }

    /**
     * Make a PATCH request
     * @param {string} url - API endpoint
     * @param {Object} data - Request body
     * @param {Object} options - Request options
     * @returns {Promise<Object>} Response data
     */
    static async patch(url, data = null, options = {}) {
        return this.request(url, {
            ...options,
            method: 'PATCH',
            body: data ? JSON.stringify(data) : null,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        });
    }

    /**
     * Core request method
     * @param {string} url - API endpoint
     * @param {Object} options - Request options
     * @returns {Promise<Object>} Response data
     */
    static async request(url, options = {}) {
        const {
            useProfile = true,
            onSuccess = null,
            onError = null,
            errorMessage = null,
            skipJsonParse = false,
            ...fetchOptions
        } = options;

        try {
            // Use fetchWithProfile or regular fetch
            const fetchFn = useProfile ? window.fetchWithProfile : fetch;
            const response = await fetchFn(url, fetchOptions);

            // Handle non-OK responses
            if (!response.ok) {
                const error = await this.handleError(response, errorMessage);
                if (onError) {
                    onError(error);
                }
                throw error;
            }

            // Parse response
            let data;
            if (skipJsonParse) {
                data = response;
            } else {
                // Handle 204 No Content responses (common for DELETE operations)
                if (response.status === 204) {
                    data = null;
                } else {
                    const contentType = response.headers.get('content-type');
                    if (contentType && contentType.includes('application/json')) {
                        data = await response.json();
                    } else {
                        data = await response.text();
                    }
                }
            }

            // Success callback
            if (onSuccess) {
                onSuccess(data);
            }

            return data;
        } catch (error) {
            // Network or parsing errors
            console.error(`API Error [${fetchOptions.method || 'GET'} ${url}]:`, error);
            if (onError && error !== 'handled') {
                onError(error);
            }
            throw error;
        }
    }

    /**
     * Handle API error responses
     * @param {Response} response - Fetch response object
     * @param {string} customMessage - Custom error message
     * @returns {Promise<Error>} Error object
     */
    static async handleError(response, customMessage = null) {
        let message = customMessage || `Request failed with status ${response.status}`;

        try {
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                const errorData = await response.json();
                message = errorData.detail || errorData.message || message;
            } else {
                const text = await response.text();
                if (text) {
                    message = text;
                }
            }
        } catch (e) {
            // Failed to parse error response, use default message
        }

        const error = new Error(message);
        error.status = response.status;
        error.response = response;
        return error;
    }

    /**
     * Helper method for toggling task completion
     * @param {string} endpoint - API endpoint template
     * @param {number} taskId - Task ID
     * @param {boolean} completed - Current completion status
     * @returns {Promise<Object>} Response data
     */
    static async toggleTask(endpoint, taskId, completed) {
        const url = endpoint.replace(':id', taskId);
        const method = completed ? 'DELETE' : 'POST';
        return this.request(url, { method });
    }

    /**
     * Helper method for fetching paginated data
     * @param {string} url - API endpoint
     * @param {Object} params - Query parameters
     * @returns {Promise<Object>} Response data
     */
    static async fetchPaginated(url, params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const fullUrl = queryString ? `${url}?${queryString}` : url;
        return this.get(fullUrl);
    }

    /**
     * Helper method for file uploads
     * @param {string} url - API endpoint
     * @param {FormData} formData - Form data with files
     * @param {Object} options - Request options
     * @returns {Promise<Object>} Response data
     */
    static async upload(url, formData, options = {}) {
        return this.request(url, {
            ...options,
            method: 'POST',
            body: formData,
            // Don't set Content-Type header - browser will set it with boundary
        });
    }
}

// Export for global use
window.ApiClient = ApiClient;

// Convenience aliases for common patterns
window.api = {
    get: (...args) => ApiClient.get(...args),
    post: (...args) => ApiClient.post(...args),
    put: (...args) => ApiClient.put(...args),
    delete: (...args) => ApiClient.delete(...args),
    patch: (...args) => ApiClient.patch(...args),

    // Task-specific helpers
    tasks: {
        list: () => ApiClient.get('/api/tasks'),
        get: (id) => ApiClient.get(`/api/tasks/${id}`),
        create: (data) => ApiClient.post('/api/tasks', data),
        update: (id, data) => ApiClient.put(`/api/tasks/${id}`, data),
        delete: (id) => ApiClient.delete(`/api/tasks/${id}`),
    },

    // Daily task helpers
    daily: {
        today: () => ApiClient.get('/api/days/today'),
        get: (date) => ApiClient.get(`/api/days/${date}`),
        toggleTask: (date, taskId, checked) =>
            ApiClient.put(`/api/days/${date}/checks/${taskId}`, { checked }),
    },

    // Punch list helpers
    punchList: {
        list: () => ApiClient.get('/api/punch-list'),
        create: (data) => ApiClient.post('/api/punch-list', data),
        complete: (id) => ApiClient.post(`/api/punch-list/${id}/complete`),
        uncomplete: (id) => ApiClient.delete(`/api/punch-list/${id}/complete`),
        delete: (id) => ApiClient.delete(`/api/punch-list/${id}`),
    },

    // Scheduled task helpers
    scheduled: {
        dueToday: () => ApiClient.get('/api/scheduled/due-today'),
        create: (data) => ApiClient.post('/api/scheduled', data),
        complete: (id) => ApiClient.post(`/api/scheduled/${id}/complete`),
        delete: (id) => ApiClient.delete(`/api/scheduled/${id}`),
    },

    // Household task helpers
    household: {
        list: () => ApiClient.get('/api/household/tasks', { useProfile: false }),
        get: (id) => ApiClient.get(`/api/household/tasks/${id}`, { useProfile: false }),
        create: (data) => ApiClient.post('/api/household/tasks', data, { useProfile: false }),
        update: (id, data) => ApiClient.put(`/api/household/tasks/${id}`, data, { useProfile: false }),
        complete: (id) => ApiClient.post(`/api/household/tasks/${id}/complete`, null, { useProfile: false }),
        undo: (id) => ApiClient.post(`/api/household/tasks/${id}/undo`, null, { useProfile: false }),
        delete: (id) => ApiClient.delete(`/api/household/tasks/${id}`, { useProfile: false }),
    },

    // Streak helpers
    streak: {
        get: () => ApiClient.get('/api/streak'),
    },

    // History helpers
    history: {
        getMonth: (year, month) => ApiClient.get(`/api/history/${year}/${month}`),
    },

    // Fitbit helpers
    fitbit: {
        connection: () => ApiClient.get('/api/fitbit/connection'),
        connect: () => ApiClient.get('/api/fitbit/connect'),
        disconnect: () => ApiClient.delete('/api/fitbit/connection'),
        preferences: () => ApiClient.get('/api/fitbit/preferences'),
        updatePreferences: (data) => ApiClient.put('/api/fitbit/preferences', data),
        resetPreferences: () => ApiClient.post('/api/fitbit/preferences/reset'),
        sync: () => ApiClient.post('/api/fitbit/sync'),
        dailySummary: (date) => ApiClient.get(`/api/fitbit/daily-summary?date=${date}`),
        metricsHistory: (startDate, endDate, metricTypes) => {
            const types = Array.isArray(metricTypes) ? metricTypes.join(',') : metricTypes;
            return ApiClient.get(`/api/fitbit/metrics/history?start_date=${startDate}&end_date=${endDate}&metric_types=${types}`);
        },
        visibleMetrics: () => ApiClient.get('/api/fitbit/preferences/visible-metrics'),
    },

    // Profile helpers
    profiles: {
        list: () => ApiClient.get('/api/profiles', { useProfile: false }),
        get: (id) => ApiClient.get(`/api/profiles/${id}`, { useProfile: false }),
        create: (data) => ApiClient.post('/api/profiles', data, { useProfile: false }),
        update: (id, data) => ApiClient.put(`/api/profiles/${id}`, data, { useProfile: false }),
        delete: (id) => ApiClient.delete(`/api/profiles/${id}`, { useProfile: false }),
        export: (id) => ApiClient.get(`/api/profiles/${id}/export`, { useProfile: false }),
        import: (id, data) => ApiClient.post(`/api/profiles/${id}/import`, data, { useProfile: false }),
    }
};

// Console info
if (typeof console !== 'undefined' && console.info) {
    console.info('%c🌐 API Client Loaded', 'color: #06b6d4; font-weight: bold;');
    console.info('Available methods:', {
        'Direct usage': 'api.get(), api.post(), api.put(), api.delete()',
        'Task shortcuts': 'api.tasks.list(), api.tasks.create(data)',
        'Daily shortcuts': 'api.daily.today(), api.daily.toggleTask()',
        'Punch list': 'api.punchList.list(), api.punchList.complete(id)',
        'Household': 'api.household.list(), api.household.complete(id)',
        'Fitbit': 'api.fitbit.connection(), api.fitbit.dailySummary(date)',
        'Low-level': 'ApiClient.request(url, options)'
    });
}
