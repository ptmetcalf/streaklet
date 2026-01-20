/**
 * Streaklet Utility Functions
 *
 * Consolidated formatting and helper functions used across templates.
 * This file reduces duplication and provides a single source of truth for common operations.
 */

// ============================================================================
// DATE & TIME FORMATTERS
// ============================================================================

/**
 * Format a due date with relative time indicators
 * @param {string|Date} dueDate - ISO date string (YYYY-MM-DD) or Date object
 * @param {Object} options - Configuration options
 * @param {boolean} options.showEmoji - Show emoji indicators (default: true)
 * @param {boolean} options.warnOverdue - Show warning emoji for overdue items (default: true)
 * @returns {string} Formatted due date string
 */
window.formatDueDate = function(dueDate, options = {}) {
    const { showEmoji = true, warnOverdue = true } = options;
    if (!dueDate) return '';

    const due = new Date(dueDate + 'T00:00:00');
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const diffTime = due - today;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    const calendarEmoji = showEmoji ? '📅 ' : '';
    const warnEmoji = showEmoji && warnOverdue && diffDays < 0 ? '⚠️ ' : '';

    if (diffDays < 0) {
        const absDays = Math.abs(diffDays);
        return `${warnEmoji}${absDays} day${absDays !== 1 ? 's' : ''} overdue`;
    }
    if (diffDays === 0) return `${calendarEmoji}Due today`;
    if (diffDays === 1) return `${calendarEmoji}Due tomorrow`;
    if (diffDays <= 7) return `${calendarEmoji}Due in ${diffDays} day${diffDays !== 1 ? 's' : ''}`;

    return `${calendarEmoji}Due ${due.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}`;
};

/**
 * Format a completed date/time with relative time
 * @param {string|Date} completedAt - ISO timestamp or Date object
 * @returns {string} Formatted relative time string
 */
window.formatCompletedDate = function(completedAt) {
    if (!completedAt) return '';

    const completed = new Date(completedAt);
    const today = new Date();
    const diffMs = today - completed;
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return 'today';
    if (diffDays === 1) return 'yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;

    return completed.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
};

/**
 * Format a date for display (long format)
 * @param {string|Date} dateStr - ISO date string or Date object
 * @returns {string} Formatted date string
 */
window.formatDateDisplay = function(dateStr) {
    if (!dateStr) return '';

    const date = new Date(dateStr + 'T00:00:00');
    return date.toLocaleDateString('en-US', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
};

/**
 * Format a sync timestamp with relative time
 * @param {string|Date} timestamp - ISO timestamp or Date object
 * @returns {string} Formatted relative time or absolute time
 */
window.formatSyncTime = function(timestamp) {
    if (!timestamp) return '';

    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 1) return 'just now';
    if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;

    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;

    const diffDays = Math.floor(diffHours / 24);
    if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;

    // For older timestamps, show absolute time
    return date.toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
    });
};

/**
 * Format a date for API calls or storage (YYYY-MM-DD)
 * Ensures proper local date formatting without UTC conversion issues
 * @param {Date} date - Date object
 * @returns {string} ISO date string (YYYY-MM-DD)
 */
window.formatDateLocal = function(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
};

/**
 * Parse a date string without UTC timezone conversion
 * @param {string} dateStr - Date string in YYYY-MM-DD format
 * @returns {Date} Date object with local midnight time
 */
window.parseDateOnly = function(dateStr) {
    if (!dateStr) return null;
    return new Date(dateStr + 'T00:00:00');
};

// ============================================================================
// METRIC & NUMBER FORMATTERS
// ============================================================================

/**
 * Format a number with thousands separators
 * @param {number|null} value - Number to format
 * @returns {string} Formatted number or '-' if null
 */
window.formatNumber = function(value) {
    if (value == null) return '-';
    return Math.round(value).toLocaleString('en-US');
};

/**
 * Format a decimal number to a fixed number of places
 * @param {number|null} value - Number to format
 * @param {number} places - Number of decimal places (default: 2)
 * @returns {string} Formatted decimal or '-' if null
 */
window.formatDecimal = function(value, places = 2) {
    if (value == null) return '-';
    return value.toFixed(places);
};

/**
 * Format sleep minutes as hours and minutes
 * @param {number|null} minutes - Sleep duration in minutes
 * @returns {string} Formatted as "Xh Ym" or '-' if null
 */
window.formatSleepHours = function(minutes) {
    if (!minutes) return '-';
    const hours = Math.floor(minutes / 60);
    const mins = Math.round(minutes % 60);
    return `${hours}h ${mins}m`;
};

/**
 * Format Fitbit progress (current/goal with optional unit)
 * @param {Object} task - Task object with Fitbit metrics
 * @param {number} task.fitbit_current_value - Current metric value
 * @param {number} task.fitbit_goal_value - Goal metric value
 * @param {string} task.fitbit_metric_type - Type of metric
 * @param {string} task.fitbit_unit - Unit of measurement
 * @returns {string} Formatted progress string
 */
window.formatFitbitProgress = function(task) {
    if (!task || !task.fitbit_current_value || !task.fitbit_goal_value) return '';

    const current = task.fitbit_current_value;
    const goal = task.fitbit_goal_value;
    const unit = task.fitbit_unit || '';

    // Format sleep minutes specially
    if (task.fitbit_metric_type === 'sleep_minutes') {
        const formatMinutes = (mins) => {
            const hours = Math.floor(mins / 60);
            const minutes = Math.round(mins % 60);
            return `${hours}h ${minutes}m`;
        };
        return `${formatMinutes(current)} / ${formatMinutes(goal)}`;
    }

    // Format numbers with commas for readability
    const formatValue = (num) => {
        if (num >= 1000) {
            return num.toLocaleString('en-US');
        }
        return Math.round(num).toString();
    };

    const currentStr = formatValue(current);
    const goalStr = formatValue(goal);

    // Add unit if available
    if (unit) {
        return `${currentStr} / ${goalStr} ${unit}`;
    }

    return `${currentStr} / ${goalStr}`;
};

/**
 * Format a metric value based on its type
 * @param {number|null} value - Metric value
 * @param {string} metricType - Type of metric (steps, sleep_minutes, distance, etc.)
 * @returns {string} Formatted value appropriate for the metric type
 */
window.formatMetricValue = function(value, metricType) {
    if (value == null) return '-';

    switch(metricType) {
        case 'sleep_minutes':
        case 'sleep_deep_minutes':
        case 'sleep_light_minutes':
        case 'sleep_rem_minutes':
        case 'sleep_wake_minutes':
            return formatSleepHours(value);

        case 'distance':
        case 'cardio_fitness_score':
        case 'spo2_avg':
        case 'breathing_rate':
        case 'temp_skin':
            return formatDecimal(value);

        default:
            return formatNumber(value);
    }
};

/**
 * Format a metric name for display
 * @param {string} key - Metric key (e.g., 'resting_heart_rate')
 * @returns {string} Human-readable metric name
 */
window.formatMetricName = function(key) {
    const names = {
        'steps': 'Steps',
        'sleep_minutes': 'Sleep Duration',
        'sleep_score': 'Sleep Score',
        'active_minutes': 'Active Minutes',
        'calories_burned': 'Calories Burned',
        'distance': 'Distance',
        'floors': 'Floors Climbed',
        'resting_heart_rate': 'Resting Heart Rate',
        'hrv_rmssd': 'Heart Rate Variability (RMSSD)',
        'hrv_deep_rmssd': 'HRV Deep Sleep (RMSSD)',
        'cardio_fitness_score': 'VO2 Max / Cardio Fitness',
        'spo2_avg': 'Blood Oxygen (SpO2) Average',
        'spo2_min': 'Blood Oxygen (SpO2) Minimum',
        'spo2_max': 'Blood Oxygen (SpO2) Maximum',
        'breathing_rate': 'Breathing Rate',
        'temp_skin': 'Skin Temperature Variation',
        'sleep_deep_minutes': 'Deep Sleep',
        'sleep_light_minutes': 'Light Sleep',
        'sleep_rem_minutes': 'REM Sleep',
        'sleep_wake_minutes': 'Awake Time'
    };

    return names[key] || key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
};

/**
 * Format a trend percentage value
 * @param {number|null} value - Trend percentage (-100 to 100)
 * @returns {string} Formatted trend with arrow indicator
 */
window.formatTrend = function(value) {
    if (value == null || value === 0) return '—';
    const sign = value >= 0 ? '↑' : '↓';
    return `${sign} ${Math.abs(Math.round(value))}%`;
};

// ============================================================================
// TASK & RECURRENCE FORMATTERS
// ============================================================================

/**
 * Format a recurrence pattern for display
 * @param {Object} task - Task object with recurrence_pattern
 * @returns {string} Human-readable recurrence description
 */
window.formatRecurrence = function(task) {
    if (!task || !task.recurrence_pattern) return '';

    const pattern = task.recurrence_pattern;
    const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

    if (pattern.type === 'weekly') {
        return `📅 Weekly on ${days[pattern.day_of_week]}`;
    }

    if (pattern.type === 'monthly') {
        const nth = (n) => {
            const s = ['th', 'st', 'nd', 'rd'];
            const v = n % 100;
            return n + (s[(v - 20) % 10] || s[v] || s[0]);
        };
        return `📅 Monthly on ${nth(pattern.day_of_month)}`;
    }

    if (pattern.type === 'days') {
        return `📅 Every ${pattern.interval} day${pattern.interval !== 1 ? 's' : ''}`;
    }

    return '';
};

/**
 * Format a frequency label for household tasks
 * @param {string} frequency - Frequency type (weekly, monthly, quarterly, annual, todo)
 * @returns {string} Capitalized frequency label
 */
window.formatFrequency = function(frequency) {
    const labels = {
        'todo': 'To-Do',
        'weekly': 'Weekly',
        'monthly': 'Monthly',
        'quarterly': 'Quarterly',
        'annual': 'Annual'
    };
    return labels[frequency] || frequency.charAt(0).toUpperCase() + frequency.slice(1);
};

// ============================================================================
// TASK TYPE HELPERS
// ============================================================================

/**
 * Get task type label for display
 * @param {string} taskType - Task type (daily, punch_list, scheduled)
 * @returns {string} Human-readable label
 */
window.getTaskTypeLabel = function(taskType) {
    if (taskType === 'punch_list') return 'Todo';
    if (taskType === 'scheduled') return 'Scheduled';
    return 'Daily';
};

/**
 * Get task type badge class
 * @param {string} taskType - Task type (daily, punch_list, scheduled)
 * @returns {string} CSS class name
 */
window.getTaskTypeBadgeClass = function(taskType) {
    if (taskType === 'punch_list') return 'badge-todo';
    if (taskType === 'scheduled') return 'badge-scheduled';
    return 'badge-daily';
};

// ============================================================================
// VALIDATION & UTILITY HELPERS
// ============================================================================

/**
 * Check if a task is overdue
 * @param {Object} task - Task object with due_date and completed_at
 * @returns {boolean} True if task is overdue
 */
window.isTaskOverdue = function(task) {
    if (!task || !task.due_date || task.completed_at) return false;
    const today = new Date().toISOString().split('T')[0];
    return task.due_date < today;
};

/**
 * Get streak badge CSS class based on streak length
 * @param {number} streak - Streak length in days
 * @returns {string} CSS class name for styling
 */
window.getStreakBadgeClass = function(streak) {
    if (streak >= 100) return 'streak-legendary';  // Gold
    if (streak >= 60) return 'streak-epic';        // Purple
    if (streak >= 30) return 'streak-amazing';     // Blue
    if (streak >= 14) return 'streak-great';       // Green
    if (streak >= 7) return 'streak-good';         // Light green
    return 'streak-building';                       // Gray
};

/**
 * Clamp a value between min and max
 * @param {number} value - Value to clamp
 * @param {number} min - Minimum value
 * @param {number} max - Maximum value
 * @returns {number} Clamped value
 */
window.clamp = function(value, min, max) {
    return Math.min(Math.max(value, min), max);
};

/**
 * Debounce a function call
 * @param {Function} func - Function to debounce
 * @param {number} wait - Wait time in milliseconds
 * @returns {Function} Debounced function
 */
window.debounce = function(func, wait) {
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

// ============================================================================
// ICON PICKER UTILITIES
// ============================================================================

/**
 * Shared icon picker utilities for filtering and selection
 * Used by both personal task and household task icon pickers
 */
window.iconPickerUtils = {
    /**
     * Filter icons by search term
     * @param {Object} categories - Icon categories object
     * @param {string} searchTerm - Search query
     * @returns {Object} Filtered categories
     */
    filterCategories(categories, searchTerm) {
        if (!searchTerm || searchTerm.trim() === '') {
            return categories;
        }

        const search = searchTerm.toLowerCase().trim();
        const filtered = {};

        for (const [category, icons] of Object.entries(categories)) {
            const matchingIcons = icons.filter(icon =>
                icon.toLowerCase().includes(search) ||
                category.toLowerCase().includes(search)
            );

            if (matchingIcons.length > 0) {
                filtered[category] = matchingIcons;
            }
        }

        return filtered;
    },

    /**
     * Check if any icons match the search term
     * @param {Object} categories - Icon categories
     * @param {string} searchTerm - Search query
     * @returns {boolean}
     */
    hasVisibleIcons(categories, searchTerm) {
        const filtered = this.filterCategories(categories, searchTerm);
        return Object.keys(filtered).length > 0;
    },

    /**
     * Get icon display name (converts snake_case to Title Case)
     * @param {string} iconName - Icon name in snake_case
     * @returns {string} Display name
     */
    getIconDisplayName(iconName) {
        return iconName
            .split('-')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
    }
};

// ============================================================================
// TOAST NOTIFICATION SYSTEM
// ============================================================================

/**
 * Toast notification manager
 * Provides a modern, non-blocking alternative to alert() dialogs
 */
window.toast = (function() {
    let toastCounter = 0;
    const ICONS = {
        success: '✓',
        error: '✕',
        warning: '⚠',
        info: 'ℹ'
    };

    /**
     * Get or create the toast container
     * @returns {HTMLElement} Toast container element
     */
    function getContainer() {
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'toast-container';
            document.body.appendChild(container);
        }
        return container;
    }

    /**
     * Create a toast notification
     * @param {string} message - Toast message
     * @param {Object} options - Toast options
     * @returns {HTMLElement} Toast element
     */
    function createToast(message, options = {}) {
        const {
            type = 'info',
            title = null,
            duration = 4000,
            dismissible = true
        } = options;

        const toastId = `toast-${++toastCounter}`;
        const toast = document.createElement('div');
        toast.id = toastId;
        toast.className = `toast toast--${type}`;

        // Build toast HTML
        let html = `
            <div class="toast__icon">${ICONS[type] || ICONS.info}</div>
            <div class="toast__content">
                ${title ? `<div class="toast__title">${escapeHtml(title)}</div>` : ''}
                <div class="toast__message">${escapeHtml(message)}</div>
            </div>
        `;

        if (dismissible) {
            html += '<button class="toast__close" aria-label="Close">×</button>';
        }

        toast.innerHTML = html;

        // Add close button handler
        if (dismissible) {
            const closeBtn = toast.querySelector('.toast__close');
            closeBtn.addEventListener('click', () => dismissToast(toastId));
        }

        // Auto-dismiss
        if (duration > 0) {
            setTimeout(() => dismissToast(toastId), duration);
        }

        return toast;
    }

    /**
     * Dismiss a toast notification
     * @param {string} toastId - Toast element ID
     */
    function dismissToast(toastId) {
        const toast = document.getElementById(toastId);
        if (!toast) return;

        // Add removal animation
        toast.classList.add('toast--removing');

        // Remove from DOM after animation
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }

            // Clean up empty container
            const container = document.getElementById('toast-container');
            if (container && container.children.length === 0) {
                container.remove();
            }
        }, 300); // Match CSS animation duration
    }

    /**
     * Escape HTML to prevent XSS
     * @param {string} text - Text to escape
     * @returns {string} Escaped text
     */
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Show a toast notification
     * @param {string} message - Toast message
     * @param {Object} options - Toast options
     */
    function show(message, options = {}) {
        const container = getContainer();
        const toast = createToast(message, options);
        container.appendChild(toast);
    }

    // Public API
    return {
        /**
         * Show a success toast
         * @param {string} message - Success message
         * @param {Object} options - Additional options
         */
        success(message, options = {}) {
            show(message, { ...options, type: 'success' });
        },

        /**
         * Show an error toast
         * @param {string} message - Error message
         * @param {Object} options - Additional options
         */
        error(message, options = {}) {
            show(message, { ...options, type: 'error', duration: 5000 });
        },

        /**
         * Show a warning toast
         * @param {string} message - Warning message
         * @param {Object} options - Additional options
         */
        warning(message, options = {}) {
            show(message, { ...options, type: 'warning', duration: 4500 });
        },

        /**
         * Show an info toast
         * @param {string} message - Info message
         * @param {Object} options - Additional options
         */
        info(message, options = {}) {
            show(message, { ...options, type: 'info' });
        },

        /**
         * Dismiss a specific toast
         * @param {string} toastId - Toast element ID
         */
        dismiss: dismissToast
    };
})();

// ============================================================================
// MODAL UTILITIES
// ============================================================================

/**
 * Modal keyboard handler
 * Handles ESC key to close modals
 */
window.modalKeyHandler = function(event, closeCallback) {
    if (event.key === 'Escape' && typeof closeCallback === 'function') {
        closeCallback();
    }
};

// ============================================================================
// FORM VALIDATION UTILITIES
// ============================================================================

/**
 * Common form validation helpers
 */
window.formValidation = {
    /**
     * Validate required field
     * @param {string} value - Field value
     * @param {string} fieldName - Field name for error message
     * @returns {string|null} Error message or null if valid
     */
    validateRequired(value, fieldName = 'This field') {
        if (!value || value.trim() === '') {
            return `${fieldName} is required`;
        }
        return null;
    },

    /**
     * Validate number range
     * @param {number} value - Number value
     * @param {number} min - Minimum value
     * @param {number} max - Maximum value
     * @returns {string|null} Error message or null if valid
     */
    validateRange(value, min, max) {
        if (value < min || value > max) {
            return `Value must be between ${min} and ${max}`;
        }
        return null;
    },

    /**
     * Show error message with toast notification
     * @param {string} message - Error message
     */
    showError(message) {
        window.toast.error(message);
    }
};

// ============================================================================
// CONSOLE INFO (Development Only)
// ============================================================================

if (typeof console !== 'undefined' && console.info) {
    console.info('%c✨ Streaklet Utils Loaded', 'color: #52c41a; font-weight: bold;');
    console.info('Available functions:', {
        'Date/Time': ['formatDueDate', 'formatCompletedDate', 'formatDateDisplay', 'formatSyncTime', 'formatDateLocal', 'parseDateOnly'],
        'Metrics': ['formatNumber', 'formatDecimal', 'formatSleepHours', 'formatFitbitProgress', 'formatMetricValue', 'formatMetricName', 'formatTrend'],
        'Tasks': ['formatRecurrence', 'formatFrequency', 'getTaskTypeLabel', 'getTaskTypeBadgeClass'],
        'Validation': ['isTaskOverdue', 'getStreakBadgeClass'],
        'Utilities': ['clamp', 'debounce'],
        'Icon Picker': ['iconPickerUtils.filterCategories', 'iconPickerUtils.hasVisibleIcons', 'iconPickerUtils.getIconDisplayName'],
        'Form Validation': ['formValidation.validateRequired', 'formValidation.validateRange', 'formValidation.showError'],
        'Toast Notifications': ['toast.success()', 'toast.error()', 'toast.warning()', 'toast.info()', 'toast.dismiss()'],
        'Modal Utilities': ['modalKeyHandler(event, closeCallback)']
    });
}
