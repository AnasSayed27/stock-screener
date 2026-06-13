/* ============================================
   StockLens — Screener Page
   ============================================ */

// Module-level state
let _screenerResults = [];
let _screenerSortKey = 'quality_score';
let _screenerSortAsc = false;

/**
 * Render the Screener page.
 */
function renderScreener() {
    const main = document.getElementById('main-content');
    main.innerHTML = `
        <div class="fade-in">
            <div class="page-header">
                <h1 class="page-title">Stock <span class="gradient-text">Screener</span></h1>
                <p class="page-subtitle">
                    Evaluate Nifty 500 stocks against 11 fundamental quality criteria. Scores, conviction
                    levels, and margin of safety are calculated automatically.
                </p>
            </div>

            <!-- Actions Row -->
            <div class="action-row">
                <div class="select-container">
                    <label class="select-label">Universe</label>
                    <select id="screener-universe" class="select-input">
                        <option value="nifty50">Nifty 50</option>
                        <option value="niftynext50">Nifty Next 50</option>
                        <option value="niftymidcap150">Nifty Midcap 150</option>
                        <option value="niftysmallcap250">Nifty Smallcap 250</option>
                        <option value="fno">F&O Stocks</option>
                        <option value="nifty500" selected>Nifty 500</option>
                    </select>
                </div>
                <button id="screener-run-btn" class="btn btn-primary btn-lg" onclick="runScreening()">
                    <span class="btn-icon">🔍</span>
                    Run Full Scan
                </button>
                <div class="search-container" style="flex:1; max-width: 320px;">
                    <span class="search-icon">🏷️</span>
                    <input type="text" id="screener-ticker-input" class="search-input"
                           placeholder="Or enter a ticker (e.g. TCS)"
                           onkeydown="if(event.key==='Enter') runScreening(this.value.trim().toUpperCase())">
                </div>
            </div>

            <!-- Results Area -->
            <div id="screener-results-area"></div>
        </div>
    `;

    // If we have cached results, display them
    if (_screenerResults.length > 0) {
        renderScreenerTable(_screenerResults);
    }
}

let _screenerAbortController = null;

/**
 * Cancel the active screening scan.
 */
function cancelScreening() {
    if (_screenerAbortController) {
        _screenerAbortController.abort();
        _screenerAbortController = null;
        showToast('Screening cancelled.', 'info');
    }
}

/**
 * Run the stock screening scan.
 * @param {string} [ticker] - optional specific ticker to scan
 */
async function runScreening(ticker) {
    const area = document.getElementById('screener-results-area');
    const btn = document.getElementById('screener-run-btn');

    if (!area) return;

    // Show loading with a cancel button
    const universeLabel = document.getElementById('screener-universe')?.selectedOptions[0]?.text || 'Nifty 500';
    area.innerHTML = `
        ${getLoadingHTML(
            ticker
                ? `Analyzing ${ticker}… This may take a moment.`
                : `Scanning all ${universeLabel} stocks… This may take a few minutes.`
        )}
        <div style="text-align: center; margin-top: -12px; margin-bottom: 24px;">
            <button id="screener-cancel-btn" class="btn btn-secondary btn-sm" onclick="cancelScreening()">
                ⏹️ Cancel Scan
            </button>
        </div>
    `;
    if (btn) { btn.disabled = true; btn.innerHTML = '<span class="btn-icon">⏳</span> Scanning…'; }

    _screenerAbortController = new AbortController();

    try {
        let data;
        if (ticker) {
            // Single stock analysis — wrap in array for table rendering
            const result = await apiFetch(`/stock/${encodeURIComponent(ticker)}`, {
                signal: _screenerAbortController.signal
            });
            data = [_mapAnalysisToScreenerRow(result, ticker)];
        } else {
            // Full screening — get selected universe
            const universeSelect = document.getElementById('screener-universe');
            const universe = universeSelect ? universeSelect.value : 'nifty500';
            data = await apiFetch('/screen', {
                method: 'POST',
                body: JSON.stringify({ tickers: [], universe: universe }),
                signal: _screenerAbortController.signal
            });
        }

        if (!Array.isArray(data) || data.length === 0) {
            area.innerHTML = getEmptyStateHTML('🔍', 'No Results',
                'The screening returned no results. Try running a full scan or check the server.');
            return;
        }

        _screenerResults = data;
        _screenerSortKey = 'quality_score';
        _screenerSortAsc = false;
        _sortScreenerResults();
        renderScreenerTable(_screenerResults);
        showToast(`Screening complete — ${data.length} stock${data.length > 1 ? 's' : ''} analyzed.`, 'success');
    } catch (err) {
        if (err.name === 'AbortError') {
            area.innerHTML = getEmptyStateHTML('🔍', 'Screening Cancelled', 'The screening scan was cancelled by the user.');
            return;
        }
        area.innerHTML = `
            <div class="card" style="text-align: center; padding: 40px;">
                <span style="font-size: 40px; display: block; margin-bottom: 12px;">⚠️</span>
                <h3 style="color: var(--color-danger); margin-bottom: 8px;">Screening Failed</h3>
                <p class="text-muted" style="margin-bottom: 16px;">${escapeHtml(err.message)}</p>
                <button class="btn btn-secondary" onclick="runScreening()">Try Again</button>
            </div>
        `;
        showToast('Screening failed: ' + err.message, 'error');
    } finally {
        _screenerAbortController = null;
        if (btn) { btn.disabled = false; btn.innerHTML = '<span class="btn-icon">🔍</span> Run Full Scan'; }
    }
}

/**
 * Map a full analysis response to a screener table row.
 */
function _mapAnalysisToScreenerRow(analysis, ticker) {
    const sc = analysis.scorecard || {};
    const val = analysis.valuation || {};
    return {
        ticker: ticker || analysis.ticker || sc.ticker || '—',
        name: analysis.name || sc.company_name || '—',
        sector: analysis.sector || sc.sector || '—',
        quality_score: sc.total_score ?? 0,
        max_score: sc.max_score ?? 11,
        quality_pct: sc.percentage ?? (sc.max_score > 0 ? Math.round(sc.total_score / sc.max_score * 100) : 0),
        margin_of_safety: val.margin_of_safety_pct ?? null,
        conviction: sc.conviction || analysis.conviction || '—',
        is_financial_sector: sc.is_financial_sector || false,
    };
}

/**
 * Render the screener results table.
 */
function renderScreenerTable(results) {
    const area = document.getElementById('screener-results-area');
    if (!area) return;

    const passedCount = results.filter(r => {
        const c = (r.conviction || '').toLowerCase();
        return c.includes('strong') || c.includes('candidate');
    }).length;

    area.innerHTML = `
        <div class="result-count">
            Showing <strong>${results.length}</strong> stock${results.length !== 1 ? 's' : ''}
            ${passedCount > 0 ? ` · <strong>${passedCount}</strong> passed screening` : ''}
        </div>
        <div class="table-container">
            <table class="data-table" id="screener-table">
                <thead>
                    <tr>
                        ${_thCol('ticker', 'Ticker')}
                        ${_thCol('name', 'Company')}
                        ${_thCol('sector', 'Sector')}
                        ${_thCol('quality_score', 'Quality Score')}
                        ${_thCol('margin_of_safety', 'Margin of Safety')}
                        ${_thCol('conviction', 'Conviction')}
                    </tr>
                </thead>
                <tbody>
                    ${results.map(r => _renderScreenerRow(r)).join('')}
                </tbody>
            </table>
        </div>
    `;
}

/**
 * Generate a sortable table header cell.
 */
function _thCol(key, label) {
    const isActive = _screenerSortKey === key;
    const arrow = isActive ? (_screenerSortAsc ? '▲' : '▼') : '⇅';
    return `<th class="${isActive ? 'sort-active' : ''}" onclick="_sortScreenerBy('${key}')">
        ${label} <span class="sort-arrow">${arrow}</span>
    </th>`;
}

/**
 * Render a single row in the screener table.
 */
function _renderScreenerRow(r) {
    const isFinancial = r.is_financial_sector;
    const rowClass = isFinancial ? 'financial-row clickable-row' : 'clickable-row';
    const qualityPct = r.quality_pct ?? (r.max_score > 0 ? Math.round(r.quality_score / r.max_score * 100) : 0);
    const mosText = r.margin_of_safety != null ? formatPercent(r.margin_of_safety) : '—';
    const mosClass = r.margin_of_safety != null
        ? (r.margin_of_safety >= 0 ? 'text-success' : 'text-danger')
        : '';

    return `
        <tr class="${rowClass}" onclick="navigateTo('analyzer', '${escapeHtml(r.ticker)}')">
            <td class="ticker-cell">
                ${escapeHtml(r.ticker)}${isFinancial ? ' <span title="Financial sector — scorecard not applicable">⚠️</span>' : ''}
            </td>
            <td>${escapeHtml(r.name)}</td>
            <td><span class="text-muted">${escapeHtml(r.sector)}</span></td>
            <td>
                ${isFinancial
                    ? '<span class="text-muted" title="Not applicable for financials">N/A</span>'
                    : getScoreBarHTML(qualityPct, 100)
                }
            </td>
            <td class="${mosClass}" style="font-weight:600;">${mosText}</td>
            <td>${getConvictionBadge(r.conviction)}</td>
        </tr>
    `;
}

/**
 * Sort screener results by column.
 */
function _sortScreenerBy(key) {
    if (_screenerSortKey === key) {
        _screenerSortAsc = !_screenerSortAsc;
    } else {
        _screenerSortKey = key;
        _screenerSortAsc = key === 'ticker' || key === 'name' || key === 'sector';
    }
    _sortScreenerResults();
    renderScreenerTable(_screenerResults);
}

function _sortScreenerResults() {
    _screenerResults.sort((a, b) => {
        let va = a[_screenerSortKey];
        let vb = b[_screenerSortKey];
        if (va == null) va = _screenerSortAsc ? Infinity : -Infinity;
        if (vb == null) vb = _screenerSortAsc ? Infinity : -Infinity;
        if (typeof va === 'string') va = va.toLowerCase();
        if (typeof vb === 'string') vb = vb.toLowerCase();
        if (va < vb) return _screenerSortAsc ? -1 : 1;
        if (va > vb) return _screenerSortAsc ? 1 : -1;
        return 0;
    });
}
