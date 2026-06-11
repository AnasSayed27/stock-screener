/* ============================================
   StockLens — Analyzer Page
   ============================================ */

// Module-level state
let _analyzerData = null;
let _analyzerTicker = null;
let _activeTab = 'scorecard';

/**
 * Render the Analyzer page.
 * @param {string} [ticker] - stock ticker to analyze
 */
async function renderAnalyzer(ticker) {
    const main = document.getElementById('main-content');
    _analyzerTicker = ticker || null;

    if (!ticker) {
        // Show search view
        main.innerHTML = `
            <div class="fade-in">
                <div class="page-header">
                    <h1 class="page-title">Stock <span class="gradient-text">Analyzer</span></h1>
                    <p class="page-subtitle">
                        Enter a ticker symbol to view the full scorecard, valuation metrics,
                        governance checklist, and build your investment thesis.
                    </p>
                </div>
                <div class="card" style="max-width: 560px; margin: 40px auto; text-align: center; padding: 48px 32px;">
                    <span style="font-size: 56px; display: block; margin-bottom: 20px; opacity: 0.3;">◉</span>
                    <h3 style="margin-bottom: 20px; color: var(--text-secondary);">Search for a Stock</h3>
                    <div class="search-container" style="max-width: 100%;">
                        <span class="search-icon">🔍</span>
                        <input type="text" id="analyzer-search-input" class="search-input"
                               placeholder="Enter ticker symbol (e.g. TCS, INFY, RELIANCE)"
                               autofocus
                               onkeydown="if(event.key==='Enter'){ const v=this.value.trim().toUpperCase(); if(v) navigateTo('analyzer', v); }">
                    </div>
                    <p class="text-muted mt-2" style="font-size: 13px;">
                        Use NSE ticker symbols. Append .NS if needed by the API.
                    </p>
                </div>
            </div>
        `;
        return;
    }

    // Show loading
    main.innerHTML = `
        <div class="fade-in">
            <div class="page-header">
                <h1 class="page-title">Analyzing <span class="gradient-text">${escapeHtml(ticker)}</span></h1>
            </div>
            ${getLoadingHTML('Fetching data and running analysis… This may take a moment.')}
        </div>
    `;

    try {
        const data = await apiFetch(`/stock/${encodeURIComponent(ticker)}`);
        _analyzerData = data;
        _activeTab = 'scorecard';
        _renderAnalyzerFull(ticker, data);
    } catch (err) {
        main.innerHTML = `
            <div class="fade-in">
                <div class="page-header">
                    <h1 class="page-title">Analyzer</h1>
                </div>
                <div class="card" style="text-align: center; padding: 48px;">
                    <span style="font-size: 48px; display:block; margin-bottom: 12px;">⚠️</span>
                    <h3 style="color: var(--color-danger); margin-bottom: 8px;">Analysis Failed</h3>
                    <p class="text-muted" style="margin-bottom: 20px;">${escapeHtml(err.message)}</p>
                    <div class="quick-actions" style="justify-content: center;">
                        <button class="btn btn-secondary" onclick="navigateTo('analyzer', '${escapeHtml(ticker)}')">Retry</button>
                        <button class="btn btn-secondary" onclick="navigateTo('analyzer')">Search Another</button>
                    </div>
                </div>
            </div>
        `;
        showToast('Analysis failed: ' + err.message, 'error');
    }
}

/**
 * Render the full analyzer view with tabs.
 */
function _renderAnalyzerFull(ticker, data) {
    const main = document.getElementById('main-content');
    const sc = data.scorecard || {};
    const val = data.valuation || {};
    const isFinancial = sc.is_financial_sector || false;
    const companyName = sc.company_name || data.name || ticker;

    // Load existing thesis if any
    let existingThesis = null;

    main.innerHTML = `
        <div class="fade-in">
            <!-- Header -->
            <div class="page-header" style="margin-bottom: 16px;">
                <div class="flex-between" style="flex-wrap: wrap; gap: 12px;">
                    <div>
                        <h1 class="page-title" style="margin-bottom: 4px;">
                            <span class="gradient-text">${escapeHtml(ticker)}</span>
                            <span style="font-weight: 400; font-size: 18px; color: var(--text-secondary); margin-left: 8px;">
                                ${escapeHtml(companyName)}
                            </span>
                        </h1>
                        <p style="font-size: 13px; color: var(--text-muted);">
                            ${escapeHtml(sc.sector || data.sector || '')}
                            ${sc.current_price ? ' · CMP: ' + formatCurrency(sc.current_price) : ''}
                            ${sc.market_cap ? ' · MCap: ' + formatCrore(sc.market_cap) : ''}
                        </p>
                    </div>
                    <div>
                        ${getConvictionBadge(sc.conviction || data.conviction)}
                    </div>
                </div>
            </div>

            ${isFinancial ? `
                <div class="financial-warning-banner mb-3">
                    <span class="warning-icon">🏦</span>
                    <h3>Financial Sector Stock</h3>
                    <p>
                        Traditional quality metrics (debt-to-equity, FCF, interest coverage) do not apply
                        to banks, NBFCs, and insurance companies. The scorecard and valuation tabs are not
                        applicable. You can still create an investment thesis below.
                    </p>
                </div>
            ` : ''}

            <!-- Tabs -->
            <div class="tabs" id="analyzer-tabs">
                <button class="tab-btn active" data-tab="scorecard" onclick="_switchTab('scorecard')">
                    📊 Scorecard
                </button>
                <button class="tab-btn" data-tab="valuation" onclick="_switchTab('valuation')">
                    💰 Valuation
                </button>
                <button class="tab-btn" data-tab="governance" onclick="_switchTab('governance')">
                    🏛️ Governance
                </button>
            </div>

            <!-- Tab Contents -->
            <div id="tab-scorecard" class="tab-content active">
                ${isFinancial ? _renderFinancialPlaceholder() : _renderScorecardTab(sc, data)}
            </div>
            <div id="tab-valuation" class="tab-content">
                ${isFinancial ? _renderFinancialPlaceholder() : _renderValuationTab(val, sc)}
            </div>
            <div id="tab-governance" class="tab-content">
                ${_renderGovernanceTab(ticker)}
            </div>

            <!-- Thesis Section -->
            <div class="mt-4" id="analyzer-thesis-section">
                ${_renderThesisForm(ticker, data)}
            </div>
        </div>
    `;

    // Initialize charts after DOM is ready
    if (!isFinancial) {
        requestAnimationFrame(() => _initTrendCharts(data));
    }

    // Load existing thesis
    _loadExistingThesis(ticker);
}

/**
 * Switch between analyzer tabs.
 */
function _switchTab(tab) {
    _activeTab = tab;
    // Update tab buttons
    document.querySelectorAll('#analyzer-tabs .tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tab);
    });
    // Update tab content
    document.querySelectorAll('.tab-content').forEach(el => {
        el.classList.toggle('active', el.id === `tab-${tab}`);
    });
}

/**
 * Render placeholder for financial sector stocks.
 */
function _renderFinancialPlaceholder() {
    return `
        <div class="empty-state" style="padding: 40px;">
            <span class="empty-state-icon">🏦</span>
            <h3 class="empty-state-title">Not Applicable</h3>
            <p class="empty-state-desc">
                This section does not apply to financial sector stocks. Banks, NBFCs, and insurance
                companies require specialized valuation frameworks.
            </p>
        </div>
    `;
}

/* ============================================
   TAB 1: SCORECARD
   ============================================ */

function _renderScorecardTab(sc, data) {
    const criteria = sc.criteria || [];
    const totalScore = sc.total_score ?? 0;
    const maxScore = sc.max_score ?? 11;

    return `
        <!-- Large Score Display -->
        <div class="card mb-3">
            <div class="score-display-large">
                <div class="score-value-large">${totalScore}<span class="score-max-large">/${maxScore}</span></div>
                <div class="score-bar-large">
                    <div class="score-bar-fill" style="width: ${maxScore > 0 ? (totalScore / maxScore * 100) : 0}%"></div>
                </div>
                <p class="text-muted mt-2" style="font-size: 13px;">Quality Score</p>
            </div>
        </div>

        <!-- Criteria Table -->
        <div class="card mb-3">
            <h3 class="card-title mb-2">Criteria Breakdown</h3>
            <div class="table-container">
                <table class="data-table criteria-table">
                    <thead>
                        <tr>
                            <th>Criterion</th>
                            <th>Result</th>
                            <th>Value</th>
                            <th>Threshold</th>
                            <th>Weight</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${criteria.map(c => `
                            <tr>
                                <td style="font-weight: 500;">${escapeHtml(c.name || c.criterion || '—')}</td>
                                <td>${getPassFailBadge(c.passed)}</td>
                                <td class="criteria-value">${_formatCriterionValue(c.value, c.name)}</td>
                                <td class="criteria-threshold">${escapeHtml(c.threshold || '—')}</td>
                                <td class="criteria-weight">${c.weight ?? 1}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Trend Charts -->
        <div class="card mb-3">
            <h3 class="card-title mb-2">Financial Trends</h3>
            <div class="charts-grid">
                <div class="chart-container">
                    <canvas id="chart-revenue"></canvas>
                </div>
                <div class="chart-container">
                    <canvas id="chart-net-income"></canvas>
                </div>
                <div class="chart-container">
                    <canvas id="chart-fcf"></canvas>
                </div>
                <div class="chart-container">
                    <canvas id="chart-debt"></canvas>
                </div>
            </div>
        </div>

        <div class="disclaimer">
            <span class="disclaimer-icon">⚠️</span>
            <strong>Data Disclaimer:</strong> Financial history limited to ~4 years (yfinance). This is insufficient for full Graham-style 10-year analysis. Cross-check against Screener.in or annual reports. Phase 2 will add 10-year data.
        </div>
    `;
}

/**
 * Format a criterion value contextually.
 */
function _formatCriterionValue(value, name) {
    if (value == null) return '—';
    const n = (name || '').toLowerCase();
    if (n.includes('roe') || n.includes('margin') || n.includes('yield') || n.includes('growth') || n.includes('cagr'))
        return formatPercent(value);
    if (n.includes('ratio') || n.includes('coverage') || n.includes('peg'))
        return Number(value).toFixed(2);
    if (n.includes('debt'))
        return Number(value).toFixed(2);
    if (typeof value === 'boolean')
        return value ? 'Yes' : 'No';
    if (typeof value === 'number')
        return value >= 10000000 ? formatCrore(value) : Number(value).toFixed(2);
    return escapeHtml(String(value));
}

/**
 * Initialize trend charts with scorecard data.
 */
function _initTrendCharts(data) {
    const trends = data.trends || data.scorecard?.trends || {};

    // Revenue chart
    if (trends.revenue && trends.years) {
        createTrendChart('chart-revenue', trends.years, [
            { label: 'Revenue', data: trends.revenue, color: CHART_COLORS.cyan }
        ]);
    }

    // Net Income chart
    if (trends.net_income && trends.years) {
        createTrendChart('chart-net-income', trends.years, [
            { label: 'Net Income', data: trends.net_income, color: CHART_COLORS.green }
        ]);
    }

    // FCF chart
    if (trends.fcf && trends.years) {
        createTrendChart('chart-fcf', trends.years, [
            { label: 'Free Cash Flow', data: trends.fcf, color: CHART_COLORS.purple }
        ]);
    }

    // Debt chart
    if (trends.total_debt && trends.years) {
        createTrendChart('chart-debt', trends.years, [
            { label: 'Total Debt', data: trends.total_debt, color: CHART_COLORS.red }
        ]);
    }
}

/* ============================================
   TAB 2: VALUATION
   ============================================ */

function _renderValuationTab(val, sc) {
    const currentPrice = sc.current_price || val.current_price || 0;
    const graham = val.graham_number;
    const earningsYield = val.earnings_yield;
    const peg = val.peg_ratio;
    const dcf = val.dcf || {};
    const mos = val.margin_of_safety_pct;

    return `
        <!-- Key Valuation Metrics -->
        <div class="valuation-grid mb-3">
            <div class="valuation-card card-animated">
                <div class="val-label">Current Price</div>
                <div class="val-value">${formatCurrency(currentPrice)}</div>
            </div>
            <div class="valuation-card card-animated">
                <div class="val-label">Graham Number</div>
                <div class="val-value">${graham != null ? formatCurrency(graham) : '—'}</div>
            </div>
            <div class="valuation-card card-animated">
                <div class="val-label">Earnings Yield</div>
                <div class="val-value">${earningsYield != null ? formatPercent(earningsYield) : '—'}</div>
                <p class="text-muted" style="font-size: 11px; margin-top: 4px;">
                    ${earningsYield != null && earningsYield > 7
                        ? '✅ Above risk-free rate'
                        : earningsYield != null ? '⚠️ Below typical risk-free rate' : ''}
                </p>
            </div>
            <div class="valuation-card card-animated">
                <div class="val-label">PEG Ratio</div>
                <div class="val-value">${peg != null ? peg.toFixed(2) : '—'}</div>
                <p class="text-muted" style="font-size: 11px; margin-top: 4px;">
                    ${peg != null ? (peg <= 1 ? '✅ Possibly undervalued' : peg <= 2 ? '⚠️ Fairly valued' : '❌ Possibly overvalued') : ''}
                </p>
            </div>
        </div>

        ${peg != null ? `
            <div class="disclaimer mb-3">
                <span class="disclaimer-icon">⚠️</span>
                <strong>PEG Note:</strong> PEG ratio is a supplementary metric. It relies on growth estimates
                which can be unreliable for Indian stocks via yfinance. Use as directional guidance only.
            </div>
        ` : ''}

        <!-- DCF Section -->
        ${Object.keys(dcf).length > 0 ? _renderDCFSection(dcf, currentPrice) : `
            <div class="card mb-3">
                <h3 class="card-title">DCF Valuation</h3>
                <p class="text-muted mt-1">DCF data not available for this stock.</p>
            </div>
        `}

        <!-- Margin of Safety -->
        <div class="card mb-3">
            <h3 class="card-title mb-2">Margin of Safety</h3>
            <div style="text-align: center; padding: 16px;">
                <div style="font-size: 36px; font-weight: 800; ${mos != null ? (mos >= 0 ? 'color: var(--color-success)' : 'color: var(--color-danger)') : ''}">
                    ${mos != null ? formatPercent(mos) : '—'}
                </div>
                <p class="text-muted mt-1" style="font-size: 13px; max-width: 400px; margin: 8px auto 0;">
                    ${mos != null
                        ? (mos >= 25 ? 'Attractive margin of safety — stock appears undervalued.'
                            : mos >= 0 ? 'Some margin of safety exists, but limited.'
                            : 'Negative margin of safety — stock appears overvalued.')
                        : 'Unable to calculate margin of safety.'
                    }
                </p>
            </div>
        </div>

        <div class="disclaimer">
            <span class="disclaimer-icon">⚠️</span>
            <strong>DCF Sensitivity:</strong> Discounted Cash Flow models are highly sensitive to growth rate,
            discount rate, and terminal growth assumptions. Small changes can significantly affect the output.
            Treat these as rough estimates, not precise targets.
        </div>
    `;
}

function _renderDCFSection(dcf, currentPrice) {
    const assumptions = dcf.assumptions || {};
    const scenarios = dcf.scenarios || {};
    const bear = scenarios.bear || {};
    const base = scenarios.base || {};
    const bull = scenarios.bull || {};

    // Price range bar calculation
    const prices = [bear.fair_value, base.fair_value, bull.fair_value].filter(p => p != null);
    const minP = Math.min(...prices, currentPrice) * 0.9;
    const maxP = Math.max(...prices, currentPrice) * 1.1;
    const range = maxP - minP;
    const currentPct = range > 0 ? ((currentPrice - minP) / range * 100) : 50;

    return `
        <div class="card mb-3">
            <h3 class="card-title mb-2">DCF Valuation</h3>

            <!-- Assumptions -->
            <div style="display: flex; gap: 24px; flex-wrap: wrap; margin-bottom: 20px; padding: 12px 16px; background: rgba(255,255,255,0.02); border-radius: var(--radius-md);">
                <div>
                    <span class="text-muted" style="font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;">Growth Rate</span>
                    <div style="font-weight: 600;">${assumptions.growth_rate != null ? formatPercent(assumptions.growth_rate) : '—'}</div>
                </div>
                <div>
                    <span class="text-muted" style="font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;">Discount Rate</span>
                    <div style="font-weight: 600;">${assumptions.discount_rate != null ? formatPercent(assumptions.discount_rate) : '—'}</div>
                </div>
                <div>
                    <span class="text-muted" style="font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;">Terminal Growth</span>
                    <div style="font-weight: 600;">${assumptions.terminal_growth != null ? formatPercent(assumptions.terminal_growth) : '—'}</div>
                </div>
            </div>

            <!-- Scenario Cards -->
            <div class="scenarios-grid">
                <div class="scenario-card scenario-bear">
                    <div class="scenario-label">🐻 Bear Case</div>
                    <div class="scenario-value">${bear.fair_value != null ? formatCurrency(bear.fair_value) : '—'}</div>
                    <div class="scenario-detail">${bear.growth_rate != null ? 'Growth: ' + formatPercent(bear.growth_rate) : ''}</div>
                </div>
                <div class="scenario-card scenario-base">
                    <div class="scenario-label">📊 Base Case</div>
                    <div class="scenario-value">${base.fair_value != null ? formatCurrency(base.fair_value) : '—'}</div>
                    <div class="scenario-detail">${base.growth_rate != null ? 'Growth: ' + formatPercent(base.growth_rate) : ''}</div>
                </div>
                <div class="scenario-card scenario-bull">
                    <div class="scenario-label">🐂 Bull Case</div>
                    <div class="scenario-value">${bull.fair_value != null ? formatCurrency(bull.fair_value) : '—'}</div>
                    <div class="scenario-detail">${bull.growth_rate != null ? 'Growth: ' + formatPercent(bull.growth_rate) : ''}</div>
                </div>
            </div>

            <!-- Price Range Visual -->
            ${prices.length > 0 ? `
                <div class="price-range-container">
                    <div style="text-align: center; margin-bottom: 8px;">
                        <span class="text-muted" style="font-size: 12px;">Current Price Position</span>
                    </div>
                    <div class="price-range-bar">
                        <div class="price-range-marker" style="left: ${Math.min(100, Math.max(0, currentPct))}%"
                             data-label="CMP ${formatCurrency(currentPrice)}"></div>
                    </div>
                    <div class="price-range-labels">
                        <span>Bear: ${formatCurrency(bear.fair_value)}</span>
                        <span>Base: ${formatCurrency(base.fair_value)}</span>
                        <span>Bull: ${formatCurrency(bull.fair_value)}</span>
                    </div>
                </div>
            ` : ''}
        </div>
    `;
}

/* ============================================
   TAB 3: GOVERNANCE
   ============================================ */

const GOVERNANCE_ITEMS = [
    { id: 'promoter_holding', label: 'Promoter holding > 50%?' },
    { id: 'promoter_pledge', label: 'Promoter pledge < 10% (or zero)?' },
    { id: 'promoter_stable', label: 'Promoter holding stable/increasing?' },
    { id: 'reputable_auditor', label: 'Big-4 or reputable auditor?' },
    { id: 'related_party', label: 'Related-party transactions minimal?' },
    { id: 'contingent_liability', label: 'No contingent liability red flags?' },
    { id: 'capital_allocation', label: 'Rational capital allocation?' },
    { id: 'no_dilution', label: 'No frequent equity dilution?' },
];

function _renderGovernanceTab(ticker) {
    return `
        <div class="card mb-3">
            <h3 class="card-title mb-1">Governance Checklist</h3>
            <p class="text-muted mb-3" style="font-size: 13px;">
                📝 Check these items after reading the company's annual report. These are qualitative
                checks that cannot be automated. No numerical score is assigned.
            </p>
            <div id="governance-checklist">
                ${GOVERNANCE_ITEMS.map(item => `
                    <label class="checkbox-item">
                        <input type="checkbox" id="gov-${item.id}" data-gov-id="${item.id}">
                        <span class="checkbox-label">${escapeHtml(item.label)}</span>
                    </label>
                `).join('')}
            </div>
            <div class="mt-3">
                <button class="btn btn-secondary" onclick="_saveGovernance('${escapeHtml(ticker)}')">
                    💾 Save Governance Checks
                </button>
                <span class="text-muted" style="font-size: 12px; margin-left: 12px;">
                    (Saved alongside your thesis)
                </span>
            </div>
        </div>
    `;
}

function _saveGovernance(ticker) {
    const checks = {};
    GOVERNANCE_ITEMS.forEach(item => {
        const el = document.getElementById(`gov-${item.id}`);
        if (el) checks[item.id] = el.checked;
    });
    // Store in localStorage for now
    localStorage.setItem(`governance_${ticker}`, JSON.stringify(checks));
    showToast('Governance checks saved locally.', 'success');
}

function _loadGovernance(ticker) {
    try {
        const stored = localStorage.getItem(`governance_${ticker}`);
        if (stored) {
            const checks = JSON.parse(stored);
            Object.entries(checks).forEach(([id, val]) => {
                const el = document.getElementById(`gov-${id}`);
                if (el) el.checked = val;
            });
        }
    } catch (e) {}
}

/* ============================================
   THESIS FORM
   ============================================ */

function _renderThesisForm(ticker, data) {
    const sc = data.scorecard || {};
    return `
        <div class="card">
            <div class="card-header">
                <h3 class="card-title">📝 Investment Thesis</h3>
                <div id="thesis-status"></div>
            </div>
            <div id="thesis-form-container">
                <div class="two-col">
                    <div class="form-group">
                        <label class="form-label">Why am I interested in this stock?</label>
                        <textarea id="thesis-why" class="form-textarea" rows="4"
                                  placeholder="What attracted you to this company? What's the core thesis?"></textarea>
                    </div>
                    <div class="form-group">
                        <label class="form-label">What would make me wrong?</label>
                        <textarea id="thesis-wrong" class="form-textarea" rows="4"
                                  placeholder="What risks or scenarios would invalidate your thesis?"></textarea>
                    </div>
                </div>
                <div class="form-group">
                    <label class="form-label">Sell conditions (when would I exit?)</label>
                    <textarea id="thesis-sell" class="form-textarea" rows="3"
                              placeholder="Define clear sell conditions before buying. E.g., thesis breaks, overvalued by 50%, better opportunity, etc."></textarea>
                </div>
                <div class="flex gap-2 mt-2">
                    <button class="btn btn-primary" onclick="_saveThesis('${escapeHtml(ticker)}')">
                        💾 Save Thesis
                    </button>
                    <button class="btn btn-danger btn-sm" id="thesis-delete-btn" style="display:none;"
                            onclick="_deleteThesis('${escapeHtml(ticker)}')">
                        🗑️ Delete Thesis
                    </button>
                </div>
            </div>
        </div>
    `;
}

/**
 * Load existing thesis from the API and populate the form.
 */
async function _loadExistingThesis(ticker) {
    try {
        const theses = await apiFetch('/theses');
        if (Array.isArray(theses)) {
            const thesis = theses.find(t => t.ticker === ticker);
            if (thesis) {
                const whyEl = document.getElementById('thesis-why');
                const wrongEl = document.getElementById('thesis-wrong');
                const sellEl = document.getElementById('thesis-sell');
                const delBtn = document.getElementById('thesis-delete-btn');
                const status = document.getElementById('thesis-status');

                if (whyEl) whyEl.value = thesis.why_interested || '';
                if (wrongEl) wrongEl.value = thesis.what_would_make_me_wrong || '';
                if (sellEl) sellEl.value = thesis.sell_conditions || '';
                if (delBtn) delBtn.style.display = '';
                if (status) status.innerHTML = `<span class="badge badge-pass">Thesis Saved</span>`;

                // Load governance checks too
                if (thesis.governance) {
                    Object.entries(thesis.governance).forEach(([id, val]) => {
                        const el = document.getElementById(`gov-${id}`);
                        if (el) el.checked = val;
                    });
                }
            }
        }
    } catch (e) {
        // silently fail — thesis may not exist
    }

    // Also load local governance
    _loadGovernance(ticker);
}

/**
 * Save thesis to the API.
 */
async function _saveThesis(ticker) {
    const why = document.getElementById('thesis-why')?.value?.trim();
    const wrong = document.getElementById('thesis-wrong')?.value?.trim();
    const sell = document.getElementById('thesis-sell')?.value?.trim();

    if (!why) {
        showToast('Please fill in why you are interested in this stock.', 'warning');
        return;
    }

    // Collect governance checks
    const governance = {};
    GOVERNANCE_ITEMS.forEach(item => {
        const el = document.getElementById(`gov-${item.id}`);
        if (el) governance[item.id] = el.checked;
    });

    // Save governance locally too
    localStorage.setItem(`governance_${ticker}`, JSON.stringify(governance));

    // Build thesis payload
    const sc = _analyzerData?.scorecard || {};
    const val = _analyzerData?.valuation || {};

    const payload = {
        ticker: ticker,
        why_interested: why,
        what_would_make_me_wrong: wrong || '',
        sell_conditions: sell || '',
        governance: governance,
        snapshot: {
            quality_score: sc.total_score,
            max_score: sc.max_score,
            conviction: sc.conviction,
            current_price: sc.current_price,
            margin_of_safety: val.margin_of_safety_pct,
            sector: sc.sector,
            company_name: sc.company_name,
        },
    };

    try {
        await apiFetch('/theses', {
            method: 'POST',
            body: JSON.stringify(payload),
        });
        showToast('Thesis saved successfully!', 'success');

        const delBtn = document.getElementById('thesis-delete-btn');
        const status = document.getElementById('thesis-status');
        if (delBtn) delBtn.style.display = '';
        if (status) status.innerHTML = `<span class="badge badge-pass">Thesis Saved</span>`;
    } catch (err) {
        showToast('Failed to save thesis: ' + err.message, 'error');
    }
}

/**
 * Delete thesis after confirmation.
 */
async function _deleteThesis(ticker) {
    const confirmed = await showConfirmModal(
        'Delete Thesis',
        `Are you sure you want to delete your thesis for ${ticker}? This action cannot be undone.`
    );

    if (!confirmed) return;

    try {
        await apiFetch(`/theses/${encodeURIComponent(ticker)}`, { method: 'DELETE' });
        showToast('Thesis deleted.', 'info');

        // Clear form
        const whyEl = document.getElementById('thesis-why');
        const wrongEl = document.getElementById('thesis-wrong');
        const sellEl = document.getElementById('thesis-sell');
        const delBtn = document.getElementById('thesis-delete-btn');
        const status = document.getElementById('thesis-status');

        if (whyEl) whyEl.value = '';
        if (wrongEl) wrongEl.value = '';
        if (sellEl) sellEl.value = '';
        if (delBtn) delBtn.style.display = 'none';
        if (status) status.innerHTML = '';
    } catch (err) {
        showToast('Failed to delete thesis: ' + err.message, 'error');
    }
}
