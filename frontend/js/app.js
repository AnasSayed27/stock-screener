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
   MOBILE SIDEBAR
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

/* ============================================
   INITIALIZE
   ============================================ */

window.addEventListener('hashchange', router);
window.addEventListener('DOMContentLoaded', () => {
    _initMobileSidebar();
    router();
});
