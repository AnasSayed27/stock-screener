/* ============================================
   StockLens — App Router & Initialization
   ============================================ */

/**
 * Route definitions.
 * Each key maps a hash segment to a render function.
 */
const routes = {
    '':          renderDashboard,
    'dashboard': renderDashboard,
    'screener':  renderScreener,
    'discovery': renderDiscovery,
    'analyzer':  renderAnalyzer,
    'thesis':    renderThesisBoard,
};

/**
 * Main router — called on hash change and initial load.
 */
function router() {
    const hash = window.location.hash.slice(1) || 'dashboard';
    const [page, ...params] = hash.split('/');
    const param = params.join('/') || undefined;

    const renderFn = routes[page];
    if (!renderFn) {
        // Unknown route — redirect to dashboard
        navigateTo('dashboard');
        return;
    }

    // Update active nav item
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.toggle('active', item.dataset.page === page);
    });

    // Close mobile sidebar if open
    _closeMobileSidebar();

    // Clear main content and render
    const main = document.getElementById('main-content');
    main.innerHTML = '';
    main.scrollTop = 0;
    window.scrollTo(0, 0);

    // Call render function (may be async)
    renderFn(param);
}

/**
 * Navigate to a page programmatically.
 * @param {string} page - route name
 * @param {string} [param] - optional parameter (e.g., ticker)
 */
function navigateTo(page, param) {
    window.location.hash = param ? `${page}/${param}` : page;
}

/* ============================================
   MOBILE SIDEBAR & COLLAPSIBLE SIDEBAR
   ============================================ */

function _initMobileSidebar() {
    const toggle = document.getElementById('sidebar-toggle');
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');

    if (toggle) {
        toggle.addEventListener('click', () => {
            sidebar.classList.toggle('open');
            overlay.classList.toggle('active');
            toggle.classList.toggle('active');
        });
    }

    if (overlay) {
        overlay.addEventListener('click', _closeMobileSidebar);
    }
}

function _closeMobileSidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    const toggle = document.getElementById('sidebar-toggle');

    if (sidebar) sidebar.classList.remove('open');
    if (overlay) overlay.classList.remove('active');
    if (toggle) toggle.classList.remove('active');
}

function _initCollapsibleSidebar() {
    const collapseBtn = document.getElementById('sidebar-collapse-btn');
    const collapseIcon = document.getElementById('collapse-icon');
    
    if (collapseBtn) {
        // Load preference from localStorage
        const isCollapsed = localStorage.getItem('sidebar-collapsed') === 'true';
        if (isCollapsed) {
            document.body.classList.add('sidebar-collapsed');
            if (collapseIcon) collapseIcon.textContent = '▶';
        }
        
        collapseBtn.addEventListener('click', () => {
            const willCollapse = !document.body.classList.contains('sidebar-collapsed');
            document.body.classList.toggle('sidebar-collapsed', willCollapse);
            localStorage.setItem('sidebar-collapsed', willCollapse ? 'true' : 'false');
            if (collapseIcon) {
                collapseIcon.textContent = willCollapse ? '▶' : '◀';
            }
        });
    }
}

async function updateAPIUsageStats() {
    try {
        const response = await fetch('/api/usage');
        if (!response.ok) return;
        const data = await response.json();
        
        const sumGemini = document.getElementById('api-sum-gemini');
        const sumTavily = document.getElementById('api-sum-tavily');
        if (sumGemini) sumGemini.textContent = data.gemini_count || 0;
        if (sumTavily) sumTavily.textContent = data.tavily_count || 0;
        
        const detGemini = document.getElementById('api-det-gemini');
        const detTavily = document.getElementById('api-det-tavily');
        if (detGemini) detGemini.textContent = data.gemini_count || 0;
        if (detTavily) detTavily.textContent = data.tavily_count || 0;
    } catch (err) {
        console.error('Error fetching API usage stats:', err);
    }
}

function _initAPIUsage() {
    const header = document.getElementById('api-usage-header');
    const details = document.getElementById('api-usage-details');
    const arrow = document.getElementById('api-usage-arrow');
    
    if (header && details) {
        header.addEventListener('click', () => {
            const isHidden = details.style.display === 'none';
            details.style.display = isHidden ? 'flex' : 'none';
            if (arrow) {
                arrow.style.transform = isHidden ? 'rotate(180deg)' : 'rotate(0deg)';
            }
        });
    }
    
    updateAPIUsageStats();
    setInterval(updateAPIUsageStats, 30000);
}

/* ============================================
   INITIALIZE
   ============================================ */

window.addEventListener('hashchange', router);
window.addEventListener('DOMContentLoaded', () => {
    _initMobileSidebar();
    _initCollapsibleSidebar();
    _initAPIUsage();
    router();
});
