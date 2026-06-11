/* ============================================
   StockLens — Dashboard Page
   ============================================ */

/**
 * Render the dashboard page.
 */
async function renderDashboard() {
    const main = document.getElementById('main-content');
    main.innerHTML = `
        <div class="fade-in">
            <!-- Welcome Banner -->
            <div class="welcome-banner">
                <h1>Welcome to <span class="gradient-text">StockLens</span></h1>
                <p>
                    A premium stock screening and fundamental analysis tool for Indian equities.
                    Screen stocks using quality-based criteria, deep-dive into financials, build
                    investment theses, and learn from past decisions.
                </p>
            </div>

            <!-- Stats Grid -->
            <div class="stats-grid" id="dashboard-stats">
                <div class="stat-card card-animated">
                    <span class="stat-icon">📊</span>
                    <div class="stat-value" id="stat-stocks">—</div>
                    <div class="stat-label">Nifty 200 Stocks</div>
                </div>
                <div class="stat-card card-animated">
                    <span class="stat-icon">📝</span>
                    <div class="stat-value" id="stat-theses">—</div>
                    <div class="stat-label">Active Theses</div>
                </div>
                <div class="stat-card card-animated">
                    <span class="stat-icon">📖</span>
                    <div class="stat-value" id="stat-postmortems">—</div>
                    <div class="stat-label">Postmortems</div>
                </div>
                <div class="stat-card card-animated">
                    <span class="stat-icon">🎯</span>
                    <div class="stat-value" id="stat-quality">11</div>
                    <div class="stat-label">Quality Criteria</div>
                </div>
            </div>

            <!-- Quick Actions -->
            <div class="card mb-3">
                <h2 class="section-title">Quick Actions</h2>
                <div class="quick-actions">
                    <a href="#screener" class="btn btn-primary btn-lg">
                        <span class="btn-icon">⏣</span>
                        Run Stock Screener
                    </a>
                    <a href="#thesis" class="btn btn-secondary btn-lg">
                        <span class="btn-icon">⬢</span>
                        View Thesis Board
                    </a>
                    <a href="#analyzer" class="btn btn-secondary btn-lg">
                        <span class="btn-icon">◉</span>
                        Analyze a Stock
                    </a>
                </div>
            </div>

            <!-- How it Works -->
            <div class="card mb-3">
                <h2 class="section-title">How StockLens Works</h2>
                <div class="stats-grid" style="margin-bottom: 0;">
                    <div style="padding: 8px 0;">
                        <h4 style="color: var(--accent-cyan); margin-bottom: 6px;">① Screen</h4>
                        <p class="text-muted" style="font-size: 13px; line-height: 1.7;">
                            Run the screener to evaluate all Nifty 200 stocks against 11 fundamental quality criteria
                            inspired by value investing principles.
                        </p>
                    </div>
                    <div style="padding: 8px 0;">
                        <h4 style="color: var(--accent-cyan); margin-bottom: 6px;">② Analyze</h4>
                        <p class="text-muted" style="font-size: 13px; line-height: 1.7;">
                            Deep dive into any stock's scorecard, valuation (Graham, DCF, PEG), and governance
                            checklist. Review financial trends with interactive charts.
                        </p>
                    </div>
                    <div style="padding: 8px 0;">
                        <h4 style="color: var(--accent-cyan); margin-bottom: 6px;">③ Decide</h4>
                        <p class="text-muted" style="font-size: 13px; line-height: 1.7;">
                            Write your investment thesis, define sell conditions, and track your conviction.
                            When you sell, create a postmortem to capture lessons learned.
                        </p>
                    </div>
                </div>
            </div>

            <!-- Disclaimer -->
            <div class="disclaimer">
                <span class="disclaimer-icon">⚠️</span>
                <strong>Data Disclaimer:</strong> Financial data is sourced from Yahoo Finance (yfinance).
                This data may be incomplete, delayed, or inaccurate for some stocks — especially Indian
                equities. Always cross-verify with the company's annual report and BSE/NSE filings before
                making investment decisions. This tool is for educational and analytical purposes only.
            </div>
        </div>
    `;

    // Fetch stats asynchronously
    _loadDashboardStats();
}

/**
 * Load live counts for dashboard stat cards.
 */
async function _loadDashboardStats() {
    // Theses count
    try {
        const theses = await apiFetch('/theses');
        const count = Array.isArray(theses) ? theses.length : 0;
        document.getElementById('stat-theses').textContent = count;
    } catch (e) {
        document.getElementById('stat-theses').textContent = '—';
    }

    // Postmortems count
    try {
        const pms = await apiFetch('/postmortems');
        const count = Array.isArray(pms) ? pms.length : 0;
        document.getElementById('stat-postmortems').textContent = count;
    } catch (e) {
        document.getElementById('stat-postmortems').textContent = '—';
    }

    // Stocks count — use a static approximation since we may not have a list endpoint
    const statStocks = document.getElementById('stat-stocks');
    if (statStocks) statStocks.textContent = '200';
}
