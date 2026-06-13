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
                <button class="tab-btn" data-tab="ai-research" onclick="_switchTab('ai-research')">
                    🤖 AI Research
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
            <div id="tab-ai-research" class="tab-content">
                ${_renderAIResearchTab(ticker)}
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

    // Initialize AI Research tab
    _initAIResearch(ticker);
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

/* ============================================
   AI RESEARCH TAB FUNCTIONS
   ============================================ */

let _aiSelectedFiles = [];
let _aiActiveSessionFiles = [];

function _renderAIResearchTab(ticker) {
    return `
        <div id="ai-research-container" data-ticker="${escapeHtml(ticker)}">
            <div style="padding: 40px; text-align: center;">
                <div class="loading-spinner mb-2" style="margin: 0 auto;"></div>
                <p class="text-muted">Loading AI Research Assistant...</p>
            </div>
        </div>
    `;
}

async function _initAIResearch(ticker) {
    const container = document.getElementById('ai-research-container');
    if (!container) return;

    // Reset selected files for this session
    _aiSelectedFiles = [];
    _aiActiveSessionFiles = [];

    try {
        const status = await apiFetch('/ai/status');
        if (!status.enabled) {
            container.innerHTML = `
                <div class="ai-not-configured fade-in" style="max-width: 600px; margin: 30px auto; text-align: center;">
                    <span style="font-size: 56px; display: block; margin-bottom: 16px;">🤖</span>
                    <h3 style="margin-bottom: 12px; color: var(--text-primary);">AI Research Assistant — Disabled</h3>
                    <p class="text-muted" style="margin-bottom: 24px; font-size: 14px; line-height: 1.6;">
                        The AI Research module is optional and requires a Gemini API key.
                        It allows you to upload company documents (Annual Reports, Earnings Call Transcripts, etc.)
                        and analyze them natively with Gemini's large context window.
                    </p>
                    <div style="background: rgba(255, 255, 255, 0.02); border: 1px solid var(--border-light); border-radius: var(--radius-md); padding: 24px; text-align: left; font-family: monospace; font-size: 13px; margin: 0 auto; box-shadow: var(--shadow-sm);">
                        <p style="color: var(--accent-cyan); margin-bottom: 8px;"># To enable, add your Gemini API key to your .env file:</p>
                        <p style="color: var(--text-primary); font-weight: bold;">GEMINI_API_KEY=your_api_key_here</p>
                        <hr style="border: 0; border-top: 1px solid var(--border-light); margin: 16px 0;">
                        <p style="color: var(--text-muted); font-size: 12px;">Get a free API key at <a href="https://aistudio.google.com/apikey" target="_blank" style="color: var(--accent-cyan); text-decoration: underline;">aistudio.google.com/apikey</a></p>
                    </div>
                </div>
            `;
            return;
        }

        container.innerHTML = `
            <div class="ai-research-wrapper fade-in">
                <!-- Source Documents -->
                <div id="ai-docs-section" class="card mb-3">
                    <h3 class="card-title mb-2">📎 Source Documents</h3>
                    <p class="text-muted mb-3" style="font-size: 13px;">
                        Upload up to 3 PDFs (Annual Report, Earnings Call Transcript, Investor Presentation) for session-scoped analysis.
                    </p>
                    
                    <div id="ai-uploaded-files-list" class="mb-3">
                        <p class="text-muted" style="font-size: 13px; font-style: italic;">No active session files uploaded.</p>
                    </div>
                    
                    <div id="ai-upload-zone" class="ai-upload-zone" onclick="document.getElementById('ai-file-input').click()">
                        <span style="font-size: 32px; display: block; margin-bottom: 8px;">📂</span>
                        <p style="margin-bottom: 4px; font-weight: 500;">Drag & drop PDFs here, or click to browse</p>
                        <p class="text-muted" style="font-size: 11px;">PDFs only, maximum 3 files, max 50MB each</p>
                        <input type="file" id="ai-file-input" multiple accept=".pdf" style="display: none;">
                    </div>
                    
                    <div id="ai-upload-actions" class="mt-2 flex-between" style="display: none;">
                        <div id="ai-upload-status" class="text-muted" style="font-size: 12px;"></div>
                        <div>
                            <button class="btn btn-secondary btn-sm" id="ai-clear-session-btn" onclick="_clearAISession('${escapeHtml(ticker)}')">Clear Session</button>
                            <button class="btn btn-primary btn-sm" id="ai-upload-btn" onclick="_uploadAIFiles('${escapeHtml(ticker)}')">🚀 Upload to Gemini</button>
                        </div>
                    </div>
                </div>

                <!-- Saved Reports List -->
                <div id="ai-saved-reports-card" class="card mb-3" style="display: none;">
                    <h3 class="card-title mb-2">📄 Previously Generated Reports</h3>
                    <div class="ai-saved-reports-grid" id="ai-saved-reports-list" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 12px;"></div>
                </div>

                <!-- Action Grid -->
                <div id="ai-actions-section" class="card mb-3" style="display: none;">
                    <h3 class="card-title mb-2">🏢 Document Analysis</h3>
                    <p class="text-muted mb-3" style="font-size: 13px;">
                        Trigger structured analysis of the uploaded documents. Analysis typically takes 15-30 seconds.
                    </p>
                    <div class="ai-action-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px;">
                        <button class="ai-action-card" id="ai-btn-business" onclick="_runAIAnalysis('${escapeHtml(ticker)}', 'business')">
                            <span class="ai-action-icon">🏢</span>
                            <span class="ai-action-title">Business Overview</span>
                            <span class="ai-action-desc">Analyze business model, segment details, moats, and growth drivers.</span>
                        </button>
                        <button class="ai-action-card" id="ai-btn-governance" onclick="_runAIAnalysis('${escapeHtml(ticker)}', 'governance')">
                            <span class="ai-action-icon">🏛️</span>
                            <span class="ai-action-title">Governance Red Flags</span>
                            <span class="ai-action-desc">Extract auditor details, pledge, RPTs, contingent liabilities, and litigation.</span>
                        </button>
                        <button class="ai-action-card" id="ai-btn-risks" onclick="_runAIAnalysis('${escapeHtml(ticker)}', 'risks')">
                            <span class="ai-action-icon">⚠️</span>
                            <span class="ai-action-title">Risk Analysis</span>
                            <span class="ai-action-desc">Identify bull/bear cases and customer/geographic dependencies.</span>
                        </button>
                        <button class="ai-action-card" id="ai-btn-thesis" onclick="_runAIAnalysis('${escapeHtml(ticker)}', 'thesis')">
                            <span class="ai-action-icon">📝</span>
                            <span class="ai-action-title">Draft Thesis</span>
                            <span class="ai-action-desc">Draft an investment thesis based on the financials and documents.</span>
                        </button>
                    </div>
                </div>

                <!-- Q&A Section -->
                <div id="ai-qa-section" class="card mb-3" style="display: none;">
                    <h3 class="card-title mb-2">💬 Ask Follow-up Questions</h3>
                    <p class="text-muted mb-3" style="font-size: 13px;">
                        Ask specific questions about details in the documents. Answers are derived strictly from the text.
                    </p>
                    <div id="ai-qa-history" style="max-height: 400px; overflow-y: auto; margin-bottom: 16px; display: flex; flex-direction: column; gap: 12px; padding-right: 8px;"></div>
                    <div class="ai-qa-input" style="display: flex; gap: 12px;">
                        <input type="text" id="ai-question-input" class="search-input" style="flex: 1; border-radius: var(--radius-md);" placeholder="E.g., What are the details of the capital expenditure plan for FY26?" onkeydown="if(event.key==='Enter') _askAIQuestion('${escapeHtml(ticker)}')">
                        <button class="btn btn-primary" id="ai-qa-submit-btn" style="min-width: 80px;" onclick="_askAIQuestion('${escapeHtml(ticker)}')">Ask →</button>
                    </div>
                </div>

                <!-- Results display wrapper -->
                <div id="ai-results-wrapper" style="display: none; margin-top: 24px;">
                    <div class="flex-between mb-2">
                        <h3 class="card-title" style="margin: 0;" id="ai-results-title">Analysis Result</h3>
                        <button class="btn btn-secondary btn-sm" onclick="document.getElementById('ai-results-wrapper').scrollIntoView({behavior: 'smooth'})">Scroll to Results</button>
                    </div>
                    <div id="ai-results-content"></div>
                </div>
            </div>
        `;

        // Initialize drop zone events
        _initAIDropZone(ticker);

        // Fetch saved reports from disk
        _loadAISavedReports(ticker);

    } catch (err) {
        container.innerHTML = `
            <div style="padding: 24px; text-align: center; color: var(--color-danger);">
                <p>Failed to check AI status: ${escapeHtml(err.message)}</p>
            </div>
        `;
    }
}

function _initAIDropZone(ticker) {
    const dropZone = document.getElementById('ai-upload-zone');
    const fileInput = document.getElementById('ai-file-input');

    if (!dropZone || !fileInput) return;

    // Trigger click on file input
    fileInput.addEventListener('change', (e) => {
        _handleAIFilesSelected(ticker, Array.from(e.target.files));
    });

    // Drag-and-drop events
    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.add('dragover');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropZone.classList.remove('dragover');
        }, false);
    });

    dropZone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        _handleAIFilesSelected(ticker, Array.from(files));
    });
}

function _handleAIFilesSelected(ticker, files) {
    // Validate PDFs only, <= 50MB, max 3 files total
    const validFiles = [];
    const errors = [];

    for (const f of files) {
        if (!f.name.toLowerCase().endsWith('.pdf')) {
            errors.push(`File '${f.name}' is not a PDF.`);
            continue;
        }
        if (f.size > 50 * 1024 * 1024) {
            errors.push(`File '${f.name}' exceeds the 50MB limit.`);
            continue;
        }
        validFiles.push(f);
    }

    if (errors.length > 0) {
        showToast(errors.join(' '), 'warning');
    }

    if (validFiles.length === 0) return;

    // Combine with already selected files
    _aiSelectedFiles = _aiSelectedFiles.concat(validFiles).slice(0, 3); // cap at 3

    _renderSelectedFilesList(ticker);
}

function _renderSelectedFilesList(ticker) {
    const listContainer = document.getElementById('ai-uploaded-files-list');
    const uploadActions = document.getElementById('ai-upload-actions');
    const uploadStatus = document.getElementById('ai-upload-status');
    const uploadZone = document.getElementById('ai-upload-zone');

    if (!listContainer || !uploadActions) return;

    if (_aiSelectedFiles.length === 0 && _aiActiveSessionFiles.length === 0) {
        listContainer.innerHTML = `<p class="text-muted" style="font-size: 13px; font-style: italic;">No active session files uploaded.</p>`;
        uploadActions.style.display = 'none';
        uploadZone.style.display = 'block';
        return;
    }

    let html = '';

    // Show active uploaded files first
    if (_aiActiveSessionFiles.length > 0) {
        html += `
            <div style="margin-bottom: 12px;">
                <strong style="font-size: 12px; color: var(--color-success); display: block; margin-bottom: 4px;">✓ ACTIVE SESSION DOCUMENTS (Gemini Cloud):</strong>
                ${_aiActiveSessionFiles.map((name, i) => `
                    <div class="ai-file-item flex-between" style="padding: 8px 12px; background: rgba(16, 185, 129, 0.05); border: 1px dashed rgba(16, 185, 129, 0.2); border-radius: var(--radius-sm); margin-bottom: 6px; font-size: 13px;">
                        <span>📄 ${escapeHtml(name)}</span>
                        <span style="font-size: 11px; color: var(--color-success); font-weight: 500;">ACTIVE</span>
                    </div>
                `).join('')}
            </div>
        `;
    }

    // Show files pending upload
    if (_aiSelectedFiles.length > 0) {
        html += `
            <div>
                <strong style="font-size: 12px; color: var(--accent-cyan); display: block; margin-bottom: 4px;">📂 FILES PENDING UPLOAD (Click Upload to send to Gemini):</strong>
                ${_aiSelectedFiles.map((f, i) => `
                    <div class="ai-file-item flex-between" style="padding: 8px 12px; background: rgba(255,255,255,0.02); border: 1px solid var(--border-light); border-radius: var(--radius-sm); margin-bottom: 6px; font-size: 13px;">
                        <span>📄 ${escapeHtml(f.name)} (${(f.size / (1024*1024)).toFixed(2)} MB)</span>
                        <button class="btn btn-link btn-sm" style="color: var(--color-danger); padding: 0;" onclick="_removeSelectedFile(${i}, '${escapeHtml(ticker)}')">✕ Remove</button>
                    </div>
                `).join('')}
            </div>
        `;
    }

    listContainer.innerHTML = html;
    uploadActions.style.display = 'flex';

    if (uploadStatus) {
        if (_aiSelectedFiles.length > 0) {
            uploadStatus.textContent = `${_aiSelectedFiles.length} file(s) pending upload.`;
            document.getElementById('ai-upload-btn').style.display = '';
        } else {
            uploadStatus.textContent = 'Documents are ready for analysis.';
            document.getElementById('ai-upload-btn').style.display = 'none';
        }
    }

    // Hide drag zone if 3 files are already uploaded/selected
    if (_aiSelectedFiles.length + _aiActiveSessionFiles.length >= 3) {
        uploadZone.style.display = 'none';
    } else {
        uploadZone.style.display = 'block';
    }
}

function _removeSelectedFile(index, ticker) {
    _aiSelectedFiles.splice(index, 1);
    _renderSelectedFilesList(ticker);
}

async function _uploadAIFiles(ticker) {
    const uploadBtn = document.getElementById('ai-upload-btn');
    const clearBtn = document.getElementById('ai-clear-session-btn');
    const uploadStatus = document.getElementById('ai-upload-status');

    if (_aiSelectedFiles.length === 0) return;

    if (uploadBtn) {
        uploadBtn.disabled = true;
        uploadBtn.textContent = 'Uploading...';
    }
    if (clearBtn) clearBtn.disabled = true;
    if (uploadStatus) uploadStatus.textContent = 'Sending documents to Gemini Files API... (this may take up to a minute)';

    const formData = new FormData();
    formData.append('ticker', ticker);
    _aiSelectedFiles.forEach(file => {
        formData.append('files', file);
    });

    try {
        const response = await fetch(`${API_BASE}/ai/upload`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.detail || 'Upload failed');
        }

        const data = await response.json();
        showToast(`Successfully uploaded ${data.files_uploaded} file(s) to Gemini session!`, 'success');

        _aiActiveSessionFiles = data.file_names;
        _aiSelectedFiles = [];

        // Update view
        _renderSelectedFilesList(ticker);
        
        // Show the Actions Section and Q&A Section
        document.getElementById('ai-actions-section').style.display = 'block';
        document.getElementById('ai-qa-section').style.display = 'block';

    } catch (err) {
        showToast('Upload failed: ' + err.message, 'error');
        if (uploadStatus) uploadStatus.textContent = 'Upload failed. Please try again.';
    } finally {
        if (uploadBtn) {
            uploadBtn.disabled = false;
            uploadBtn.textContent = '🚀 Upload to Gemini';
        }
        if (clearBtn) clearBtn.disabled = false;
    }
}

async function _clearAISession(ticker) {
    const confirmed = await showConfirmModal(
        'Clear Session',
        'Are you sure you want to clear this active session? This will remove all files from Gemini Cloud storage. Saved reports on your local disk will not be deleted.'
    );

    if (!confirmed) return;

    const clearBtn = document.getElementById('ai-clear-session-btn');
    if (clearBtn) {
        clearBtn.disabled = true;
        clearBtn.textContent = 'Clearing...';
    }

    try {
        await apiFetch(`/ai/session/${encodeURIComponent(ticker)}`, { method: 'DELETE' });
        showToast('Session cleared successfully!', 'info');

        _aiSelectedFiles = [];
        _aiActiveSessionFiles = [];

        _renderSelectedFilesList(ticker);

        // Hide analysis and Q&A sections
        document.getElementById('ai-actions-section').style.display = 'none';
        document.getElementById('ai-qa-section').style.display = 'none';
        document.getElementById('ai-results-wrapper').style.display = 'none';
        document.getElementById('ai-qa-history').innerHTML = '';

    } catch (err) {
        showToast('Failed to clear session: ' + err.message, 'error');
    } finally {
        if (clearBtn) {
            clearBtn.disabled = false;
            clearBtn.textContent = 'Clear Session';
        }
    }
}

async function _runAIAnalysis(ticker, mode) {
    const cards = document.querySelectorAll('.ai-action-card');
    const targetCard = document.getElementById(`ai-btn-${mode}`);
    const resultsWrapper = document.getElementById('ai-results-wrapper');
    const resultsContent = document.getElementById('ai-results-content');
    const resultsTitle = document.getElementById('ai-results-title');

    // Disable all action cards during analysis
    cards.forEach(card => card.disabled = true);
    if (targetCard) {
        targetCard.classList.add('loading');
        const titleSpan = targetCard.querySelector('.ai-action-title');
        if (titleSpan) titleSpan.textContent += ' (Analyzing...)';
    }

    resultsWrapper.style.display = 'block';
    resultsContent.innerHTML = `
        <div class="card card-animated" style="text-align: center; padding: 48px; border: 1px dashed var(--accent-cyan); background: rgba(6, 182, 212, 0.02);">
            <div class="loading-spinner mb-2" style="margin: 0 auto;"></div>
            <h4 style="color: var(--accent-cyan);">Running AI Analysis...</h4>
            <p class="text-muted" style="font-size: 13px; margin-top: 4px;">Gemini is reading your document(s). This may take 15-30 seconds depending on the file sizes.</p>
        </div>
    `;
    resultsWrapper.scrollIntoView({ behavior: 'smooth' });

    // Build context if running thesis
    let context = {};
    if (mode === 'thesis' && _analyzerData) {
        const sc = _analyzerData.scorecard || {};
        const val = _analyzerData.valuation || {};
        context = {
            quality_score: sc.total_score,
            max_score: sc.max_score,
            conviction: sc.conviction,
            current_price: sc.current_price,
            margin_of_safety: val.margin_of_safety_pct,
            sector: sc.sector,
            company_name: sc.company_name,
        };
    }

    try {
        const data = await apiFetch('/ai/analyze', {
            method: 'POST',
            body: JSON.stringify({
                ticker: ticker,
                mode: mode,
                context: context
            })
        });

        // Update titles
        const titles = {
            'business': '🏢 Business Overview — AI Report',
            'governance': '🏛️ Governance Red Flags — AI Report',
            'risks': '⚠️ Risk Analysis — AI Report',
            'thesis': '📝 Thesis Draft — AI Preview'
        };
        resultsTitle.textContent = titles[mode] || 'Analysis Result';

        // Render report
        _displayAIReport(mode, data, ticker);
        
        // Refresh saved reports list in background
        _loadAISavedReports(ticker);

    } catch (err) {
        resultsContent.innerHTML = `
            <div class="card" style="text-align: center; padding: 48px; border: 1px solid var(--color-danger); background: rgba(239, 68, 68, 0.02);">
                <span style="font-size: 40px; display: block; margin-bottom: 12px;">⚠️</span>
                <h4 style="color: var(--color-danger); margin-bottom: 8px;">Analysis Failed</h4>
                <p class="text-muted" style="font-size: 13px; margin-bottom: 16px;">${escapeHtml(err.message)}</p>
                <button class="btn btn-secondary btn-sm" onclick="_runAIAnalysis('${escapeHtml(ticker)}', '${mode}')">Retry Analysis</button>
            </div>
        `;
    } finally {
        cards.forEach(card => card.disabled = false);
        if (targetCard) {
            targetCard.classList.remove('loading');
            const titleSpan = targetCard.querySelector('.ai-action-title');
            if (titleSpan) {
                // Restore original title text
                const titlesOrig = {
                    'business': 'Business Overview',
                    'governance': 'Governance Red Flags',
                    'risks': 'Risk Analysis',
                    'thesis': 'Draft Thesis'
                };
                titleSpan.textContent = titlesOrig[mode];
            }
        }
    }
}

async function _askAIQuestion(ticker) {
    const input = document.getElementById('ai-question-input');
    const submitBtn = document.getElementById('ai-qa-submit-btn');
    const historyContainer = document.getElementById('ai-qa-history');

    if (!input || !input.value.trim()) return;

    const question = input.value.trim();
    input.value = '';

    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = 'Thinking...';
    }

    // Append question to history immediately
    const userMsgId = 'qa-' + Date.now();
    historyContainer.innerHTML += `
        <div class="ai-qa-bubble qa-user" style="align-self: flex-end; background: rgba(6, 182, 212, 0.15); border: 1px solid rgba(6, 182, 212, 0.3); border-radius: var(--radius-md); padding: 10px 14px; max-width: 80%; font-size: 13px; border-bottom-right-radius: 2px;">
            <strong>You:</strong> <p style="margin-top: 4px; white-space: pre-wrap;">${escapeHtml(question)}</p>
        </div>
    `;
    historyContainer.scrollTop = historyContainer.scrollHeight;

    // Append temporary typing bubble
    const typingId = 'typing-' + Date.now();
    historyContainer.innerHTML += `
        <div id="${typingId}" class="ai-qa-bubble qa-assistant" style="align-self: flex-start; background: rgba(255,255,255,0.02); border: 1px solid var(--border-light); border-radius: var(--radius-md); padding: 10px 14px; max-width: 80%; font-size: 13px; border-top-left-radius: 2px;">
            <strong>Gemini:</strong> <p style="margin-top: 4px; font-style: italic;" class="typing-placeholder">Reading source documents and writing answer...</p>
        </div>
    `;
    historyContainer.scrollTop = historyContainer.scrollHeight;

    try {
        const response = await apiFetch('/ai/ask', {
            method: 'POST',
            body: JSON.stringify({
                ticker: ticker,
                question: question
            })
        });

        // Replace typing placeholder with actual answer
        const typingBubble = document.getElementById(typingId);
        if (typingBubble) {
            typingBubble.innerHTML = `
                <div class="flex-between mb-1" style="align-items: center;">
                    <strong>Gemini:</strong> 
                    ${response.confidence ? _getConfidenceBadgeHTML(response.confidence) : ''}
                </div>
                <p style="margin-top: 4px; white-space: pre-wrap; line-height: 1.5;">${escapeHtml(response.answer || 'No response.')}</p>
                ${response.citations && response.citations.length > 0 ? `<div style="margin-top: 10px; border-top: 1px dashed var(--border-light); padding-top: 6px;">${_formatAICitations(response.citations)}</div>` : ''}
            `;
        }

    } catch (err) {
        const typingBubble = document.getElementById(typingId);
        if (typingBubble) {
            typingBubble.innerHTML = `
                <strong>Gemini:</strong>
                <p style="margin-top: 4px; color: var(--color-danger);">Failed to get answer: ${escapeHtml(err.message)}</p>
            `;
        }
    } finally {
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Ask →';
        }
        historyContainer.scrollTop = historyContainer.scrollHeight;
    }
}

async function _loadAISavedReports(ticker) {
    const card = document.getElementById('ai-saved-reports-card');
    const list = document.getElementById('ai-saved-reports-list');

    if (!card || !list) return;

    try {
        const reports = await apiFetch(`/ai/reports/${encodeURIComponent(ticker)}`);
        const keys = Object.keys(reports);

        if (keys.length === 0) {
            card.style.display = 'none';
            return;
        }

        card.style.display = 'block';
        
        const modeLabels = {
            'business': '🏢 Business Overview',
            'governance': '🏛️ Governance Red Flags',
            'risks': '⚠️ Risk Analysis',
            'thesis': '📝 Thesis Draft'
        };

        list.innerHTML = keys.map(key => {
            const meta = reports[key];
            const dateStr = meta.generated_at ? new Date(meta.generated_at).toLocaleDateString(undefined, {month: 'short', day: 'numeric', year: 'numeric'}) : 'Unknown Date';
            return `
                <div class="ai-saved-report-item" style="padding: 12px; background: rgba(255,255,255,0.02); border: 1px solid var(--border-light); border-radius: var(--radius-sm); transition: border-color 0.2s, background-color 0.2s;">
                    <div style="font-weight: 600; font-size: 13px; color: var(--text-primary); margin-bottom: 4px;">${escapeHtml(modeLabels[key] || key)}</div>
                    <div style="font-size: 11px; color: var(--text-muted); margin-bottom: 8px;">Generated: ${escapeHtml(dateStr)}</div>
                    <button class="btn btn-secondary btn-sm" style="width: 100%;" onclick="_viewSavedReport('${escapeHtml(ticker)}', '${escapeHtml(key)}')">View Report</button>
                </div>
            `;
        }).join('');

    } catch (err) {
        console.error('Error loading saved reports list', err);
    }
}

async function _viewSavedReport(ticker, mode) {
    const resultsWrapper = document.getElementById('ai-results-wrapper');
    const resultsContent = document.getElementById('ai-results-content');
    const resultsTitle = document.getElementById('ai-results-title');

    if (!resultsWrapper || !resultsContent) return;

    resultsWrapper.style.display = 'block';
    resultsContent.innerHTML = `
        <div style="padding: 24px; text-align: center;">
            <div class="loading-spinner" style="margin: 0 auto;"></div>
        </div>
    `;
    resultsWrapper.scrollIntoView({ behavior: 'smooth' });

    try {
        const reports = await apiFetch(`/ai/reports/${encodeURIComponent(ticker)}`);
        const meta = reports[mode];

        if (!meta || !meta.report) {
            throw new Error('Report data not found');
        }

        const modeLabels = {
            'business': '🏢 Business Overview — Saved AI Report',
            'governance': '🏛️ Governance Red Flags — Saved AI Report',
            'risks': '⚠️ Risk Analysis — Saved AI Report',
            'thesis': '📝 Thesis Draft — Saved AI Preview'
        };
        resultsTitle.textContent = modeLabels[mode] || 'Saved Report';

        _displayAIReport(mode, meta.report, ticker);

    } catch (err) {
        resultsContent.innerHTML = `
            <div style="padding: 24px; text-align: center; color: var(--color-danger);">
                <p>Failed to load saved report: ${escapeHtml(err.message)}</p>
            </div>
        `;
    }
}

function _formatAICitations(citations) {
    if (!citations || citations.length === 0) return '';
    return citations.map(c => {
        const parts = [];
        if (c.document) parts.push(c.document);
        if (c.page) parts.push(`Page ${c.page}`);
        if (c.section) parts.push(c.section);
        
        let label = parts.join(' · ');
        if (c.citation_confidence) {
            label += ` (${c.citation_confidence} confidence)`;
        }
        
        const tooltip = c.quote ? `title="${escapeHtml(c.quote)}"` : '';
        return `
            <span class="ai-citation-tag" ${tooltip} style="display: inline-block; font-size: 11px; padding: 2px 6px; background: rgba(255,255,255,0.04); border: 1px solid var(--border-light); border-radius: 12px; color: var(--text-muted); margin-right: 6px; margin-bottom: 4px; cursor: help;">
                📄 ${escapeHtml(label)}
            </span>
        `;
    }).join('');
}

function _getConfidenceBadgeHTML(confidence) {
    if (!confidence) return '';
    const colors = {
        'high': { bg: 'rgba(16, 185, 129, 0.12)', border: 'rgba(16, 185, 129, 0.25)', text: 'var(--color-success)' },
        'medium': { bg: 'rgba(245, 158, 11, 0.12)', border: 'rgba(245, 158, 11, 0.25)', text: 'var(--color-warning)' },
        'low': { bg: 'rgba(239, 68, 68, 0.12)', border: 'rgba(239, 68, 68, 0.25)', text: 'var(--color-danger)' }
    };
    const c = colors[confidence.toLowerCase()] || colors['medium'];
    return `
        <span style="font-size: 11px; font-weight: 600; text-transform: uppercase; padding: 2px 8px; border-radius: 4px; background: ${c.bg}; border: 1px solid ${c.border}; color: ${c.text}; display: inline-flex; align-items: center; gap: 4px;">
            Confidence: ${escapeHtml(confidence)}
        </span>
    `;
}

function _displayAIReport(mode, data, ticker) {
    const resultsContent = document.getElementById('ai-results-content');
    if (!resultsContent) return;

    let html = '';

    if (mode === 'business') {
        const segments = data.revenue_segments || [];
        const products = data.products_services || [];
        const priorities = data.mgmt_priorities || [];
        const moats = data.competitive_advantages || [];
        const drivers = data.growth_drivers || [];
        const developments = data.recent_developments || [];

        html = `
            <div class="card ai-result-card fade-in">
                <!-- Overview -->
                <div class="mb-4">
                    <div class="flex-between mb-3" style="border-bottom: 1px solid var(--border-light); padding-bottom: 8px; margin-bottom: 12px; align-items: center;">
                        <h4 style="margin: 0; color: var(--accent-cyan);">🏢 Business Overview</h4>
                        ${_getConfidenceBadgeHTML(data.confidence)}
                    </div>
                    <p style="font-size: 14px; line-height: 1.6; white-space: pre-wrap;">${escapeHtml(data.company_overview || 'Not provided.')}</p>
                </div>

                <!-- Segments -->
                ${segments.length > 0 ? `
                    <div class="mb-4">
                        <h4 style="border-bottom: 1px solid var(--border-light); padding-bottom: 8px; margin-bottom: 12px; color: var(--accent-cyan);">📊 Revenue Segments</h4>
                        <div class="table-container">
                            <table class="data-table">
                                <thead>
                                    <tr>
                                        <th>Segment</th>
                                        <th style="text-align: right;">Revenue Share</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${segments.map(seg => `
                                        <tr>
                                            <td style="font-weight: 500;">${escapeHtml(seg.segment_name || '—')}</td>
                                            <td style="text-align: right; font-weight: bold; color: var(--text-primary);">${escapeHtml(seg.revenue_share || '—')}</td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        </div>
                    </div>
                ` : ''}

                <!-- Split Lists -->
                <div class="two-col mb-4">
                    <div>
                        <h4 style="border-bottom: 1px solid var(--border-light); padding-bottom: 8px; margin-bottom: 12px; color: var(--accent-cyan);">🛠️ Core Products & Services</h4>
                        ${products.length > 0 
                            ? `<ul class="bullet-list">${products.map(p => `<li>${escapeHtml(p)}</li>`).join('')}</ul>` 
                            : '<p class="text-muted" style="font-size: 13px;">None listed.</p>'}
                    </div>
                    <div>
                        <h4 style="border-bottom: 1px solid var(--border-light); padding-bottom: 8px; margin-bottom: 12px; color: var(--accent-cyan);">🎯 Management Priorities</h4>
                        ${priorities.length > 0 
                            ? `<ul class="bullet-list">${priorities.map(p => `<li>${escapeHtml(p)}</li>`).join('')}</ul>` 
                            : '<p class="text-muted" style="font-size: 13px;">None listed.</p>'}
                    </div>
                </div>

                <div class="two-col mb-4">
                    <div>
                        <h4 style="border-bottom: 1px solid var(--border-light); padding-bottom: 8px; margin-bottom: 12px; color: var(--accent-cyan);">🛡️ Competitive Advantages (Moats)</h4>
                        ${moats.length > 0 
                            ? `<ul class="bullet-list">${moats.map(m => `<li>${escapeHtml(m)}</li>`).join('')}</ul>` 
                            : '<p class="text-muted" style="font-size: 13px;">None listed.</p>'}
                    </div>
                    <div>
                        <h4 style="border-bottom: 1px solid var(--border-light); padding-bottom: 8px; margin-bottom: 12px; color: var(--accent-cyan);">🚀 Key Growth Drivers</h4>
                        ${drivers.length > 0 
                            ? `<ul class="bullet-list">${drivers.map(d => `<li>${escapeHtml(d)}</li>`).join('')}</ul>` 
                            : '<p class="text-muted" style="font-size: 13px;">None listed.</p>'}
                    </div>
                </div>

                <!-- Recent Developments -->
                <div class="mb-4">
                    <h4 style="border-bottom: 1px solid var(--border-light); padding-bottom: 8px; margin-bottom: 12px; color: var(--accent-cyan);">📢 Recent Key Developments</h4>
                    ${developments.length > 0 
                        ? `<ul class="bullet-list">${developments.map(d => `<li>${escapeHtml(d)}</li>`).join('')}</ul>` 
                        : '<p class="text-muted" style="font-size: 13px;">No recent developments listed.</p>'}
                </div>

                <!-- Citations -->
                ${data.citations && data.citations.length > 0 ? `
                    <div style="border-top: 1px dashed var(--border-light); padding-top: 16px; margin-top: 16px;">
                        <span style="font-size: 11px; text-transform: uppercase; color: var(--text-muted); display: block; margin-bottom: 6px;">Sources Cited:</span>
                        ${_formatAICitations(data.citations)}
                    </div>
                ` : ''}

                <!-- Disclaimer -->
                <div class="ai-disclaimer" style="margin-top: 20px; padding: 12px; background: rgba(245, 158, 11, 0.03); border: 1px solid rgba(245, 158, 11, 0.15); border-radius: var(--radius-sm); font-size: 12px; color: var(--text-secondary); display: flex; gap: 8px; align-items: flex-start;">
                    <span>⚠️</span>
                    <span><strong>AI Disclaimer:</strong> ${escapeHtml(data.disclaimer)}</span>
                </div>
            </div>
        `;
    } 
    else if (mode === 'governance') {
        const redFlags = data.red_flags || [];

        html = `
            <div class="card ai-result-card fade-in">
                <div class="flex-between mb-3" style="align-items: center; border-bottom: 1px solid var(--border-light); padding-bottom: 8px; margin-bottom: 16px;">
                    <h3 style="margin: 0; font-size: 16px; color: var(--text-primary);">🏛️ Corporate Governance Check</h3>
                    ${_getConfidenceBadgeHTML(data.confidence)}
                </div>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 16px; margin-bottom: 24px; margin-top: 12px;">
                    <div style="background: rgba(255,255,255,0.01); border: 1px solid var(--border-light); padding: 12px 16px; border-radius: var(--radius-sm);">
                        <span class="text-muted" style="font-size: 11px; text-transform: uppercase;">Promoter Holding</span>
                        <div style="font-weight: 600; margin-top: 4px; font-size: 14px;">${escapeHtml(data.promoter_holding || 'Not found.')}</div>
                    </div>
                    <div style="background: rgba(255,255,255,0.01); border: 1px solid var(--border-light); padding: 12px 16px; border-radius: var(--radius-sm);">
                        <span class="text-muted" style="font-size: 11px; text-transform: uppercase;">Promoter Pledge</span>
                        <div style="font-weight: 600; margin-top: 4px; font-size: 14px;">${escapeHtml(data.promoter_pledge || 'Not found.')}</div>
                    </div>
                    <div style="background: rgba(255,255,255,0.01); border: 1px solid var(--border-light); padding: 12px 16px; border-radius: var(--radius-sm);">
                        <span class="text-muted" style="font-size: 11px; text-transform: uppercase;">Auditor Details</span>
                        <div style="font-weight: 600; margin-top: 4px; font-size: 14px;">${escapeHtml(data.auditor_details || 'Not found.')}</div>
                    </div>
                </div>

                <div class="mb-4">
                    <h4 style="border-bottom: 1px solid var(--border-light); padding-bottom: 8px; margin-bottom: 12px; color: var(--accent-cyan);">🏛️ Governance Checkpoints</h4>
                    <div style="display: flex; flex-direction: column; gap: 16px; font-size: 13.5px; line-height: 1.6;">
                        <div>
                            <strong>Related-Party Transactions (RPT):</strong>
                            <p style="margin-top: 4px;">${escapeHtml(data.rpt_summary || 'Not found.')}</p>
                        </div>
                        <div>
                            <strong>Contingent Liabilities:</strong>
                            <p style="margin-top: 4px;">${escapeHtml(data.contingent_liabilities || 'Not found.')}</p>
                        </div>
                        <div>
                            <strong>Capital Allocation:</strong>
                            <p style="margin-top: 4px;">${escapeHtml(data.capital_allocation || 'Not found.')}</p>
                        </div>
                        <div>
                            <strong>Management Compensation:</strong>
                            <p style="margin-top: 4px;">${escapeHtml(data.mgmt_compensation || 'Not found.')}</p>
                        </div>
                        <div>
                            <strong>Equity Dilution:</strong>
                            <p style="margin-top: 4px;">${escapeHtml(data.equity_dilution || 'Not found.')}</p>
                        </div>
                        <div>
                            <strong>litigation & Legal Disputes:</strong>
                            <p style="margin-top: 4px;">${escapeHtml(data.litigation || 'Not found.')}</p>
                        </div>
                    </div>
                </div>

                <div class="mb-4" style="border-top: 1px solid var(--border-light); padding-top: 20px;">
                    <h4 style="margin-bottom: 12px; color: var(--color-warning);">⚠️ Possible Red Flags (AI Flags)</h4>
                    ${redFlags.length > 0 ? `
                        <div style="display: flex; flex-direction: column; gap: 12px;">
                            ${redFlags.map(flag => `
                                <div class="ai-red-flag" style="padding: 16px; background: rgba(245, 158, 11, 0.02); border: 1px solid rgba(245, 158, 11, 0.15); border-radius: var(--radius-sm); border-left: 4px solid var(--color-warning);">
                                    <div class="flex-between mb-2">
                                        <strong style="color: var(--color-warning); font-size: 13.5px;">${escapeHtml(flag.category)}</strong>
                                        <span style="font-size: 11px; text-transform: uppercase; background: rgba(245,158,11,0.1); padding: 2px 8px; border-radius: var(--radius-sm); color: var(--color-warning); border: 1px solid rgba(245,158,11,0.15);">Possible Red Flag</span>
                                    </div>
                                    <p style="font-size: 13px; line-height: 1.5; color: var(--text-primary);">${escapeHtml(flag.description)}</p>
                                    ${flag.evidence ? `
                                        <div style="margin-top: 10px; font-size: 12px; font-style: italic; color: var(--text-muted); border-left: 2px solid var(--border-light); padding-left: 8px;">
                                            "${escapeHtml(flag.evidence)}"
                                        </div>
                                    ` : ''}
                                    ${flag.citation ? `
                                        <div style="margin-top: 8px; text-align: right;">
                                            ${_formatAICitations([flag.citation])}
                                        </div>
                                    ` : ''}
                                </div>
                            `).join('')}
                        </div>
                    ` : `
                        <p class="text-muted" style="font-size: 13px; font-style: italic;">No red flags identified by AI in these documents.</p>
                    `}
                </div>

                <!-- Citations -->
                ${data.citations && data.citations.length > 0 ? `
                    <div style="border-top: 1px dashed var(--border-light); padding-top: 16px; margin-top: 16px;">
                        <span style="font-size: 11px; text-transform: uppercase; color: var(--text-muted); display: block; margin-bottom: 6px;">Sources Cited:</span>
                        ${_formatAICitations(data.citations)}
                    </div>
                ` : ''}

                <!-- Disclaimer -->
                <div class="ai-disclaimer" style="margin-top: 20px; padding: 12px; background: rgba(245, 158, 11, 0.03); border: 1px solid rgba(245, 158, 11, 0.15); border-radius: var(--radius-sm); font-size: 12px; color: var(--text-secondary); display: flex; gap: 8px; align-items: flex-start;">
                    <span>⚠️</span>
                    <span><strong>AI Disclaimer:</strong> ${escapeHtml(data.disclaimer)}</span>
                </div>
            </div>
        `;
    }
    else if (mode === 'risks') {
        const opportunities = data.opportunities || [];
        const mgmtRisks = data.mgmt_described_risks || [];
        const aiBull = data.ai_bull_case || [];
        const aiBear = data.ai_bear_case || [];

        const bulls = data.bull_case || [];
        const bears = data.bear_case || [];
        const keyRisks = data.key_risks || [];
        const threats = data.industry_threats || [];

        const isNewFormat = (opportunities.length > 0 || mgmtRisks.length > 0 || aiBull.length > 0 || aiBear.length > 0);

        html = `
            <div class="card ai-result-card fade-in">
                <div class="flex-between mb-3" style="align-items: center; border-bottom: 1px solid var(--border-light); padding-bottom: 8px; margin-bottom: 16px;">
                    <h3 style="margin: 0; font-size: 16px; color: var(--text-primary);">⚠️ Risk Assessment & Cases</h3>
                    ${_getConfidenceBadgeHTML(data.confidence)}
                </div>

                ${isNewFormat ? `
                    <!-- New Format: Management View vs AI Synthesis -->
                    <div class="two-col mb-4">
                        <div style="background: rgba(255,255,255,0.01); border: 1px solid var(--border-light); padding: 16px; border-radius: var(--radius-md);">
                            <h4 style="color: var(--accent-cyan); margin-bottom: 12px; display: flex; align-items: center; gap: 6px; border-bottom: 1px solid var(--border-light); padding-bottom: 8px;">📢 Management Opportunities</h4>
                            ${opportunities.length > 0 
                                ? `<ul class="bullet-list">${opportunities.map(o => `<li>${escapeHtml(o)}</li>`).join('')}</ul>` 
                                : '<p class="text-muted" style="font-size: 13px;">None listed.</p>'}
                        </div>
                        <div style="background: rgba(255,255,255,0.01); border: 1px solid var(--border-light); padding: 16px; border-radius: var(--radius-md);">
                            <h4 style="color: var(--accent-cyan); margin-bottom: 12px; display: flex; align-items: center; gap: 6px; border-bottom: 1px solid var(--border-light); padding-bottom: 8px;">⚠️ Management-Described Risks</h4>
                            ${mgmtRisks.length > 0 
                                ? `<ul class="bullet-list">${mgmtRisks.map(r => `<li>${escapeHtml(r)}</li>`).join('')}</ul>` 
                                : '<p class="text-muted" style="font-size: 13px;">None listed.</p>'}
                        </div>
                    </div>

                    <div class="two-col mb-4">
                        <div style="background: rgba(16, 185, 129, 0.01); border: 1px solid rgba(16, 185, 129, 0.1); padding: 16px; border-radius: var(--radius-md);">
                            <h4 style="color: var(--color-success); margin-bottom: 12px; display: flex; align-items: center; gap: 6px; border-bottom: 1px solid rgba(16, 185, 129, 0.15); padding-bottom: 8px;">🐂 AI Synthesized Bull Case</h4>
                            ${aiBull.length > 0 
                                ? `<ul class="bullet-list">${aiBull.map(b => `<li>${escapeHtml(b)}</li>`).join('')}</ul>` 
                                : '<p class="text-muted" style="font-size: 13px;">None listed.</p>'}
                        </div>
                        <div style="background: rgba(239, 68, 68, 0.01); border: 1px solid rgba(239, 68, 68, 0.1); padding: 16px; border-radius: var(--radius-md);">
                            <h4 style="color: var(--color-danger); margin-bottom: 12px; display: flex; align-items: center; gap: 6px; border-bottom: 1px solid rgba(239, 68, 68, 0.15); padding-bottom: 8px;">🐻 AI Synthesized Bear Case</h4>
                            ${aiBear.length > 0 
                                ? `<ul class="bullet-list">${aiBear.map(b => `<li>${escapeHtml(b)}</li>`).join('')}</ul>` 
                                : '<p class="text-muted" style="font-size: 13px;">None listed.</p>'}
                        </div>
                    </div>
                ` : `
                    <!-- Old Format Fallback -->
                    <div class="two-col mb-4">
                        <div style="background: rgba(16, 185, 129, 0.01); border: 1px solid rgba(16, 185, 129, 0.1); padding: 16px; border-radius: var(--radius-md);">
                            <h4 style="color: var(--color-success); margin-bottom: 12px; display: flex; align-items: center; gap: 6px; border-bottom: 1px solid rgba(16, 185, 129, 0.15); padding-bottom: 8px;">🐂 Bull Case (Positives)</h4>
                            ${bulls.length > 0 
                                ? `<ul class="bullet-list">${bulls.map(b => `<li>${escapeHtml(b)}</li>`).join('')}</ul>` 
                                : '<p class="text-muted" style="font-size: 13px;">None listed.</p>'}
                        </div>
                        <div style="background: rgba(239, 68, 68, 0.01); border: 1px solid rgba(239, 68, 68, 0.1); padding: 16px; border-radius: var(--radius-md);">
                            <h4 style="color: var(--color-danger); margin-bottom: 12px; display: flex; align-items: center; gap: 6px; border-bottom: 1px solid rgba(239, 68, 68, 0.15); padding-bottom: 8px;">🐻 Bear Case (Challenges)</h4>
                            ${bears.length > 0 
                                ? `<ul class="bullet-list">${bears.map(b => `<li>${escapeHtml(b)}</li>`).join('')}</ul>` 
                                : '<p class="text-muted" style="font-size: 13px;">None listed.</p>'}
                        </div>
                    </div>

                    <!-- Key Operational Risks -->
                    <div class="two-col mb-4">
                        <div>
                            <h4 style="border-bottom: 1px solid var(--border-light); padding-bottom: 8px; margin-bottom: 12px; color: var(--accent-cyan);">⚠️ Key Company Risks</h4>
                            ${keyRisks.length > 0 
                                ? `<ul class="bullet-list">${keyRisks.map(r => `<li>${escapeHtml(r)}</li>`).join('')}</ul>` 
                                : '<p class="text-muted" style="font-size: 13px;">None listed.</p>'}
                        </div>
                    </div>
                `}

                <!-- Industry Threats -->
                <div class="mb-4">
                    <h4 style="border-bottom: 1px solid var(--border-light); padding-bottom: 8px; margin-bottom: 12px; color: var(--accent-cyan);">🔥 Competitive & Industry Threats</h4>
                    ${threats.length > 0 
                        ? `<ul class="bullet-list">${threats.map(t => `<li>${escapeHtml(t)}</li>`).join('')}</ul>` 
                        : '<p class="text-muted" style="font-size: 13px;">None listed.</p>'}
                </div>

                <!-- Concentrations -->
                <div class="two-col mb-4" style="border-top: 1px solid var(--border-light); padding-top: 16px;">
                    <div>
                        <strong>Customer Concentration/Dependency:</strong>
                        <p style="margin-top: 4px; font-size: 13.5px; line-height: 1.5;">${escapeHtml(data.customer_dependency || 'Not found in provided documents.')}</p>
                    </div>
                    <div>
                        <strong>Geographic Concentration/Dependency:</strong>
                        <p style="margin-top: 4px; font-size: 13.5px; line-height: 1.5;">${escapeHtml(data.geographic_dependency || 'Not found in provided documents.')}</p>
                    </div>
                </div>

                <!-- Citations -->
                ${data.citations && data.citations.length > 0 ? `
                    <div style="border-top: 1px dashed var(--border-light); padding-top: 16px; margin-top: 16px;">
                        <span style="font-size: 11px; text-transform: uppercase; color: var(--text-muted); display: block; margin-bottom: 6px;">Sources Cited:</span>
                        ${_formatAICitations(data.citations)}
                    </div>
                ` : ''}

                <!-- Disclaimer -->
                <div class="ai-disclaimer" style="margin-top: 20px; padding: 12px; background: rgba(245, 158, 11, 0.03); border: 1px solid rgba(245, 158, 11, 0.15); border-radius: var(--radius-sm); font-size: 12px; color: var(--text-secondary); display: flex; gap: 8px; align-items: flex-start;">
                    <span>⚠️</span>
                    <span><strong>AI Disclaimer:</strong> ${escapeHtml(data.disclaimer)}</span>
                </div>
            </div>
        `;
    }
    else if (mode === 'thesis') {
        const assumptions = data.key_assumptions || [];
        const risks = data.major_risks || [];

        html = `
            <div class="card ai-result-card fade-in">
                <div style="background: rgba(6,182,212,0.02); border: 1px solid rgba(6,182,212,0.15); padding: 16px; border-radius: var(--radius-md); margin-bottom: 20px; display: flex; flex-direction: column; gap: 8px;">
                    <div style="font-weight: bold; font-size: 14px; color: var(--accent-cyan); display: flex; align-items: center; gap: 6px;">
                        <span>💡</span> Draft Preview
                    </div>
                    <p style="font-size: 13px; color: var(--text-muted); line-height: 1.4;">
                        This is an AI-generated thesis draft based on the company's documents and financial scorecard.
                        You can review the details below, edit them if needed, and click the button to pre-fill the
                        manual Thesis form at the bottom of the page.
                    </p>
                    <button class="btn btn-primary btn-sm mt-1" style="align-self: flex-start;" 
                            onclick="_copyThesisToForm(\`${escapeHtml(data.why_interested || '')}\`, \`${escapeHtml(data.what_would_make_me_wrong || '')}\`, \`${escapeHtml(data.sell_conditions || '')}\`)">
                        📝 Copy to Thesis Form
                    </button>
                </div>

                <div class="mb-4">
                    <h4 style="color: var(--text-primary); margin-bottom: 6px;">Why am I interested?</h4>
                    <div style="padding: 12px; background: rgba(255,255,255,0.01); border: 1px solid var(--border-light); border-radius: var(--radius-sm); font-size: 13.5px; line-height: 1.5; white-space: pre-wrap;">${escapeHtml(data.why_interested || '')}</div>
                </div>

                <div class="mb-4">
                    <h4 style="color: var(--text-primary); margin-bottom: 6px;">What would make me wrong?</h4>
                    <div style="padding: 12px; background: rgba(255,255,255,0.01); border: 1px solid var(--border-light); border-radius: var(--radius-sm); font-size: 13.5px; line-height: 1.5; white-space: pre-wrap;">${escapeHtml(data.what_would_make_me_wrong || '')}</div>
                </div>

                <div class="mb-4">
                    <h4 style="color: var(--text-primary); margin-bottom: 6px;">Sell conditions (Exit strategy)</h4>
                    <div style="padding: 12px; background: rgba(255,255,255,0.01); border: 1px solid var(--border-light); border-radius: var(--radius-sm); font-size: 13.5px; line-height: 1.5; white-space: pre-wrap;">${escapeHtml(data.sell_conditions || '')}</div>
                </div>

                <div class="two-col mb-4" style="border-top: 1px solid var(--border-light); padding-top: 16px;">
                    <div>
                        <h4 style="color: var(--text-primary); margin-bottom: 8px;">Key Assumptions</h4>
                        ${assumptions.length > 0 
                            ? `<ul class="bullet-list">${assumptions.map(a => `<li>${escapeHtml(a)}</li>`).join('')}</ul>` 
                            : '<p class="text-muted" style="font-size: 13px;">None listed.</p>'}
                    </div>
                    <div>
                        <h4 style="color: var(--text-primary); margin-bottom: 8px;">Major Risks to Monitor</h4>
                        ${risks.length > 0 
                            ? `<ul class="bullet-list">${risks.map(r => `<li>${escapeHtml(r)}</li>`).join('')}</ul>` 
                            : '<p class="text-muted" style="font-size: 13px;">None listed.</p>'}
                    </div>
                </div>

                <!-- Disclaimer -->
                <div class="ai-disclaimer" style="margin-top: 20px; padding: 12px; background: rgba(245, 158, 11, 0.03); border: 1px solid rgba(245, 158, 11, 0.15); border-radius: var(--radius-sm); font-size: 12px; color: var(--text-secondary); display: flex; gap: 8px; align-items: flex-start;">
                    <span>⚠️</span>
                    <span><strong>AI Disclaimer:</strong> ${escapeHtml(data.disclaimer)}</span>
                </div>
            </div>
        `;
    }

    resultsContent.innerHTML = html;
}

function _copyThesisToForm(why, wrong, sell) {
    const whyEl = document.getElementById('thesis-why');
    const wrongEl = document.getElementById('thesis-wrong');
    const sellEl = document.getElementById('thesis-sell');
    const formSection = document.getElementById('analyzer-thesis-section');

    if (whyEl) whyEl.value = why;
    if (wrongEl) wrongEl.value = wrong;
    if (sellEl) sellEl.value = sell;

    showToast('Thesis draft copied to the form below! Review and save it.', 'success');

    if (formSection) {
        formSection.scrollIntoView({ behavior: 'smooth' });
        // Highlight textarea briefly
        if (whyEl) {
            whyEl.style.boxShadow = '0 0 10px var(--accent-cyan)';
            setTimeout(() => {
                whyEl.style.boxShadow = '';
            }, 1000);
        }
    }
}
