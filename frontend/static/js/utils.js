/**
 * Receipt Lens - Utility Functions
 */

/**
 * Show toast notification
 */
function showToast(message, type = 'info', duration = 3000) {
    const toast = document.createElement('div');
    toast.className = `alert alert-${type}`;
    toast.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
        min-width: 300px;
        animation: slideInRight 0.3s ease;
    `;
    toast.textContent = message;

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'slideOutRight 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

/**
 * Show loading spinner
 */
function showLoading(element, text = 'Loading...') {
    const spinner = document.createElement('div');
    spinner.className = 'flex items-center justify-center gap-4 p-5';
    spinner.innerHTML = `
        <div class="spinner"></div>
        <span class="text-secondary">${text}</span>
    `;
    element.innerHTML = '';
    element.appendChild(spinner);
}

/**
 * Format currency
 */
function formatCurrency(amount) {
    return new Intl.NumberFormat('es-ES', {
        style: 'currency',
        currency: 'EUR',
    }).format(amount);
}

/**
 * Format date
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('es-ES', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
    }).format(date);
}

/**
 * Format date and time
 */
function formatDateTime(dateString) {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('es-ES', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
    }).format(date);
}

/**
 * Format relative time
 */
function formatRelativeTime(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Hace un momento';
    if (diffMins < 60) return `Hace ${diffMins} minuto${diffMins > 1 ? 's' : ''}`;
    if (diffHours < 24) return `Hace ${diffHours} hora${diffHours > 1 ? 's' : ''}`;
    if (diffDays < 7) return `Hace ${diffDays} día${diffDays > 1 ? 's' : ''}`;
    return formatDate(dateString);
}

/**
 * Validate email
 */
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

/**
 * Validate password strength
 */
function validatePassword(password) {
    if (password.length < 8) {
        return { valid: false, message: 'La contraseña debe tener al menos 8 caracteres' };
    }
    if (!/[A-Z]/.test(password)) {
        return { valid: false, message: 'La contraseña debe contener al menos una mayúscula' };
    }
    if (!/[0-9]/.test(password)) {
        return { valid: false, message: 'La contraseña debe contener al menos un número' };
    }
    return { valid: true, message: 'Contraseña válida' };
}

/**
 * Debounce function
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Format file size
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

/**
 * Get category color
 */
function getCategoryColor(category) {
    const colors = {
        'bebidas': '#3b82f6',
        'carne': '#ef4444',
        'verduras': '#10b981',
        'lácteos': '#f59e0b',
        'panadería': '#f97316',
        'limpieza': '#8b5cf6',
        'ocio': '#ec4899',
        'otros': '#6b7280',
    };
    return colors[category.toLowerCase()] || colors['otros'];
}

/**
 * Parse query string
 */
function parseQuery() {
    const params = {};
    const queryString = window.location.search.substring(1);
    const pairs = queryString.split('&');
    for (const pair of pairs) {
        const [key, value] = pair.split('=');
        if (key) {
            params[decodeURIComponent(key)] = decodeURIComponent(value || '');
        }
    }
    return params;
}

/**
 * Navigate to page
 */
function navigate(url) {
    window.location.href = url;
}

/**
 * Check authentication and redirect if needed
 */
function requireAuth() {
    if (!window.api.isAuthenticated()) {
        navigate('/login.html');
        return false;
    }
    return true;
}

/**
 * Modal helper
 */
class Modal {
    constructor(modalId) {
        this.modal = document.getElementById(modalId);
        if (!this.modal) {
            console.error(`Modal ${modalId} not found`);
            return;
        }

        // Close on background click
        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) {
                this.close();
            }
        });

        // Close on close button click
        const closeBtn = this.modal.querySelector('.modal-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => this.close());
        }
    }

    open() {
        if (this.modal) {
            this.modal.classList.add('active');
            document.body.style.overflow = 'hidden';
        }
    }

    close() {
        if (this.modal) {
            this.modal.classList.remove('active');
            document.body.style.overflow = 'auto';
        }
    }

    setContent(content) {
        const body = this.modal.querySelector('.modal-body');
        if (body) {
            body.innerHTML = content;
        }
    }
}

/**
 * Chart helpers
 */
const ChartHelpers = {
    /**
     * Get default chart options
     */
    getDefaultOptions() {
        return {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'bottom',
                },
            },
        };
    },

    /**
     * Create category chart
     */
    createCategoryChart(ctx, data) {
        return new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: data.map(item => item.category),
                datasets: [{
                    data: data.map(item => item.total),
                    backgroundColor: data.map(item => getCategoryColor(item.category)),
                }],
            },
            options: {
                ...this.getDefaultOptions(),
                plugins: {
                    ...this.getDefaultOptions().plugins,
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                const label = context.label || '';
                                const value = formatCurrency(context.raw);
                                const percentage = ((context.raw / data.reduce((sum, item) => sum + item.total, 0)) * 100).toFixed(1);
                                return `${label}: ${value} (${percentage}%)`;
                            },
                        },
                    },
                },
            },
        });
    },

    /**
     * Create price evolution chart
     */
    createPriceChart(ctx, data) {
        const datasets = Object.keys(data).map(store => ({
            label: store,
            data: data[store].map(item => ({
                x: item.date,
                y: item.price,
            })),
            borderColor: getCategoryColor(store),
            backgroundColor: getCategoryColor(store) + '20',
            tension: 0.4,
        }));

        return new Chart(ctx, {
            type: 'line',
            data: { datasets },
            options: {
                ...this.getDefaultOptions(),
                scales: {
                    x: {
                        type: 'time',
                        time: {
                            unit: 'day',
                        },
                    },
                    y: {
                        ticks: {
                            callback: (value) => formatCurrency(value),
                        },
                    },
                },
            },
        });
    },
};

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }

    @keyframes slideOutRight {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);
