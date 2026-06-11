/* ============================================
   StockLens — Utility Functions
   ============================================ */

// API base URL
const API_BASE = '/api';

/**
 * API fetch helper with error handling.
 * @param {string} path - API endpoint path (e.g., '/stock/TCS')
 * @param {object} options - fetch options
 * @returns {Promise<any>} parsed JSON response
 */
async function apiFetch(path, options = {}) {
    const url = `${API_BASE}${path}`;
    const defaultHeaders = { 'Content-Type': 'application/json' };

    try {
        const response = await fetch(url, {
            headers: { ...defaultHeaders, ...options.headers },
            ...options,
        });

        if (!response.ok) {
            let errorMsg = `HTTP ${response.status}`;
            try {
                const errData = await response.json();
                errorMsg = errData.detail || errData.message || errorMsg;
            } catch (_) {}
            throw new Error(errorMsg);
        }

        // Handle 204 No Content
        if (response.status === 204) return null;

        return await response.json();
    } catch (err) {
        if (err.name === 'TypeError' && err.message.includes('fetch')) {
            throw new Error('Cannot connect to server. Ensure the API is running on localhost:8000.');
        }
        throw err;
    }
}

/**
 * Format number as Indian currency (₹).
 * e.g., 3950.5 → ₹3,950.50
 */
function formatCurrency(num) {
    if (num == null || isNaN(num)) return '—';
    return '₹' + formatIndianNumber(Math.abs(num), 2, num < 0);
}

/**
 * Format large numbers in Crore notation.
 * e.g., 452100000000 → ₹4,521 Cr
 */
function formatCrore(num) {
    if (num == null || isNaN(num)) return '—';
    const crore = num / 10000000;
    const sign = crore < 0 ? '-' : '';
    const abs = Math.abs(crore);
    if (abs >= 100) {
        return `${sign}₹${Math.round(abs).toLocaleString('en-IN')} Cr`;
    }
    return `${sign}₹${abs.toFixed(1).replace(/\.0$/, '')} Cr`;
}

/**
 * Format percentage with sign and color indicator.
 * e.g., 21.5 → +21.5%, -14.2 → -14.2%
 */
function formatPercent(num) {
    if (num == null || isNaN(num)) return '—';
    const sign = num >= 0 ? '+' : '';
    return `${sign}${num.toFixed(1)}%`;
}

/**
 * Format number with Indian comma system.
 * e.g., 100000 → 1,00,000
 */
function formatIndianNumber(num, decimals = 0, negative = false) {
    if (num == null || isNaN(num)) return '—';
    const n = Math.abs(Number(num));
    const fixed = decimals > 0 ? n.toFixed(decimals) : Math.round(n).toString();
    const parts = fixed.split('.');
    let intPart = parts[0];
    const decPart = parts[1] ? '.' + parts[1] : '';

    // Indian number formatting: last 3 digits, then groups of 2
    if (intPart.length > 3) {
        const last3 = intPart.slice(-3);
        let remaining = intPart.slice(0, -3);
        const groups = [];
        while (remaining.length > 2) {
            groups.unshift(remaining.slice(-2));
            remaining = remaining.slice(0, -2);
        }
        if (remaining.length > 0) groups.unshift(remaining);
        intPart = groups.join(',') + ',' + last3;
    }

    const prefix = (negative || num < 0) ? '-' : '';
    return prefix + intPart + decPart;
}

/**
 * Get conviction color based on label.
 */
function getConvictionColor(conviction) {
    if (!conviction) return '#94a3b8';
    const c = conviction.toLowerCase().trim();
    if (c === 'strong candidate') return '#00d4ff';
    if (c === 'candidate') return '#00d4aa';
    if (c === 'watchlist') return '#ffa502';
    if (c === 'needs work') return '#ffa502';
    if (c === 'avoid') return '#ff4757';
    return '#94a3b8';
}

/**
 * Get conviction CSS class.
 */
function getConvictionClass(conviction) {
    if (!conviction) return '';
    const c = conviction.toLowerCase().trim();
    if (c === 'strong candidate') return 'conviction-strong-candidate';
    if (c === 'candidate') return 'conviction-candidate';
    if (c === 'watchlist') return 'conviction-watchlist';
    if (c === 'needs work') return 'conviction-needs-work';
    if (c === 'avoid') return 'conviction-avoid';
    return '';
}

/**
 * Get conviction badge HTML.
 */
function getConvictionBadge(conviction) {
    if (!conviction) return '<span class="conviction-badge">—</span>';
    const cls = getConvictionClass(conviction);
    return `<span class="conviction-badge ${cls}">${escapeHtml(conviction)}</span>`;
}

/**
 * Create pass/fail badge HTML.
 * @param {boolean|null} passed - true=pass, false=fail, null=N/A
 */
function getPassFailBadge(passed) {
    if (passed === true) return '<span class="badge badge-pass">✅ Pass</span>';
    if (passed === false) return '<span class="badge badge-fail">❌ Fail</span>';
    return '<span class="badge badge-na">— N/A</span>';
}

/**
 * Show a toast notification.
 * @param {string} message
 * @param {'success'|'error'|'warning'|'info'} type
 */
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    container.appendChild(toast);

    // Remove after animation
    setTimeout(() => {
        if (toast.parentNode) toast.parentNode.removeChild(toast);
    }, 4000);
}

/**
 * Show a confirmation modal.
 * @param {string} title
 * @param {string} message
 * @returns {Promise<boolean>}
 */
function showConfirmModal(title, message) {
    return new Promise((resolve) => {
        const overlay = document.getElementById('confirm-modal');
        const titleEl = document.getElementById('confirm-modal-title');
        const msgEl = document.getElementById('confirm-modal-message');
        const cancelBtn = document.getElementById('confirm-modal-cancel');
        const okBtn = document.getElementById('confirm-modal-ok');

        titleEl.textContent = title;
        msgEl.textContent = message;
        overlay.style.display = 'flex';

        function cleanup() {
            overlay.style.display = 'none';
            cancelBtn.removeEventListener('click', onCancel);
            okBtn.removeEventListener('click', onOk);
        }

        function onCancel() { cleanup(); resolve(false); }
        function onOk() { cleanup(); resolve(true); }

        cancelBtn.addEventListener('click', onCancel);
        okBtn.addEventListener('click', onOk);
    });
}

/**
 * Create a DOM element.
 */
function createElement(tag, className, innerHTML) {
    const el = document.createElement(tag);
    if (className) el.className = className;
    if (innerHTML) el.innerHTML = innerHTML;
    return el;
}

/**
 * Debounce function.
 */
function debounce(fn, delay = 300) {
    let timer;
    return function (...args) {
        clearTimeout(timer);
        timer = setTimeout(() => fn.apply(this, args), delay);
    };
}

/**
 * Escape HTML special characters.
 */
function escapeHtml(text) {
    if (!text) return '';
    const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
    return String(text).replace(/[&<>"']/g, m => map[m]);
}

/**
 * Get a loading spinner HTML.
 */
function getLoadingHTML(message = 'Loading...') {
    return `
        <div class="loading-container">
            <div class="spinner"></div>
            <p class="loading-text">${escapeHtml(message)}</p>
        </div>
    `;
}

/**
 * Get empty state HTML.
 */
function getEmptyStateHTML(icon, title, description, actionHTML = '') {
    return `
        <div class="empty-state">
            <span class="empty-state-icon">${icon}</span>
            <h3 class="empty-state-title">${escapeHtml(title)}</h3>
            <p class="empty-state-desc">${escapeHtml(description)}</p>
            ${actionHTML}
        </div>
    `;
}

/**
 * Format a date string to readable format.
 */
function formatDate(dateStr) {
    if (!dateStr) return '—';
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
}

/**
 * Calculate return percentage.
 */
function calcReturn(entry, exit) {
    if (!entry || !exit || entry === 0) return null;
    return ((exit - entry) / entry) * 100;
}
