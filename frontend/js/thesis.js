/* ============================================
   StockLens — Thesis Board Page
   ============================================ */

/**
 * Render the Thesis Board page.
 */
async function renderThesisBoard() {
    const main = document.getElementById('main-content');
    main.innerHTML = `
        <div class="fade-in">
            <div class="page-header">
                <h1 class="page-title">Thesis <span class="gradient-text">Board</span></h1>
                <p class="page-subtitle">
                    Track your active investment theses and review past decisions through postmortems.
                    Building a log of your thinking helps you learn and improve.
                </p>
            </div>

            <!-- Active Theses Section -->
            <div class="mb-4">
                <h2 class="section-title">📝 Active Theses</h2>
                <div id="theses-container">
                    ${getLoadingHTML('Loading theses…')}
                </div>
            </div>

            <!-- Postmortems Section -->
            <div>
                <h2 class="section-title">📖 Postmortems</h2>
                <div id="postmortems-container">
                    ${getLoadingHTML('Loading postmortems…')}
                </div>
            </div>
        </div>
    `;

    // Fetch data
    await Promise.all([
        _loadTheses(),
        _loadPostmortems(),
    ]);
}

/* ============================================
   THESES
   ============================================ */

async function _loadTheses() {
    const container = document.getElementById('theses-container');
    if (!container) return;

    try {
        const theses = await apiFetch('/theses');

        if (!Array.isArray(theses) || theses.length === 0) {
            container.innerHTML = getEmptyStateHTML(
                '📝',
                'No Active Theses',
                'You haven\'t written any investment theses yet. Analyze a stock and create your first thesis!',
                '<a href="#analyzer" class="btn btn-primary">Analyze a Stock</a>'
            );
            return;
        }

        container.innerHTML = `
            <div class="cards-grid">
                ${theses.map((t, i) => _renderThesisCard(t, i)).join('')}
            </div>
        `;
    } catch (err) {
        container.innerHTML = `
            <div class="card" style="text-align: center; padding: 32px;">
                <p class="text-danger">Failed to load theses: ${escapeHtml(err.message)}</p>
                <button class="btn btn-secondary mt-2" onclick="renderThesisBoard()">Retry</button>
            </div>
        `;
    }
}

function _renderThesisCard(thesis, index) {
    const snap = thesis.snapshot || {};
    const ticker = thesis.ticker || '—';
    const date = formatDate(thesis.created_at || thesis.date_created || thesis.date);
    const score = snap.quality_score ?? '—';
    const maxScore = snap.max_score ?? 11;
    const conviction = snap.conviction || thesis.conviction || '—';
    const mos = snap.margin_of_safety;
    const isSynthesisVerified = thesis.source === 'synthesis_chat';

    const checklist = thesis.sell_checklist || [];
    let checklistHtml = '';
    if (checklist.length > 0) {
        const rows = checklist.map(item => `
            <tr>
                <td style="color: #ff7b72; font-weight:600;">${escapeHtml(item.condition || '')}</td>
                <td class="text-muted">${escapeHtml(item.linked_assumption || '')}</td>
                <td>
                    <span class="badge ${item.severity === 'full_exit' ? 'badge-low' : 'badge-medium'}" style="font-size:10px;">
                        ${item.severity === 'full_exit' ? '🚨 FULL EXIT' : '⚠️ PARTIAL TRIM'}
                    </span>
                </td>
            </tr>
        `).join('');
        checklistHtml = `
            <div class="thesis-section">
                <div class="thesis-section-title" style="color: #ffd700;">🚨 Sell Checklist (When & Why to Sell)</div>
                <table class="sell-checklist-table">
                    <thead>
                        <tr>
                            <th>Trigger</th>
                            <th>Breaks Assumption</th>
                            <th>Action</th>
                        </tr>
                    </thead>
                    <tbody>${rows}</tbody>
                </table>
            </div>
        `;
    } else if (thesis.sell_conditions) {
        checklistHtml = `
            <div class="thesis-section">
                <div class="thesis-section-title">Sell Conditions</div>
                <div class="thesis-section-text">${escapeHtml(thesis.sell_conditions)}</div>
            </div>
        `;
    }

    const assumptionsList = (thesis.key_assumptions || []).map(a => `<li>${escapeHtml(a)}</li>`).join('');
    const risksList = (thesis.major_risks || []).map(r => `<li>${escapeHtml(r)}</li>`).join('');

    return `
        <div class="thesis-card card-animated" onclick="_toggleThesisExpand(${index})" style="animation-delay: ${index * 0.08}s;">
            <div class="thesis-card-header">
                <div style="display:flex; align-items:center; gap: 8px;">
                    <span class="thesis-ticker">${escapeHtml(ticker)}</span>
                    ${isSynthesisVerified ? `<span style="background: rgba(255,215,0,0.15); color: #ffd700; font-size:10px; font-weight:700; padding: 2px 6px; border-radius: 4px;">💬 Verified Chat Thesis</span>` : ''}
                </div>
                <span class="thesis-date">${date}</span>
            </div>
            <div class="thesis-meta">
                <div class="thesis-meta-item">Quality: <span>${score}/${maxScore}</span></div>
                ${mos != null ? `<div class="thesis-meta-item">MoS: <span class="${mos >= 0 ? 'text-success' : 'text-danger'}">${formatPercent(mos)}</span></div>` : ''}
                <div class="thesis-meta-item">${getConvictionBadge(conviction)}</div>
            </div>

            ${thesis.why_interested ? `
                <p style="font-size: 13px; color: var(--text-secondary); overflow: hidden; text-overflow: ellipsis; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;">
                    ${escapeHtml(thesis.why_interested)}
                </p>
            ` : ''}

            <div class="thesis-expanded" id="thesis-expand-${index}">
                ${thesis.why_interested ? `
                    <div class="thesis-section">
                        <div class="thesis-section-title">Why Interested</div>
                        <div class="thesis-section-text">${escapeHtml(thesis.why_interested)}</div>
                    </div>
                ` : ''}
                ${thesis.what_would_make_me_wrong ? `
                    <div class="thesis-section">
                        <div class="thesis-section-title">What Would Make Me Wrong</div>
                        <div class="thesis-section-text">${escapeHtml(thesis.what_would_make_me_wrong)}</div>
                    </div>
                ` : ''}
                
                ${checklistHtml}

                ${assumptionsList ? `
                    <div class="thesis-section">
                        <div class="thesis-section-title">Key Assumptions</div>
                        <ul style="margin:4px 0 0 16px; padding:0; font-size:13px;" class="text-muted">${assumptionsList}</ul>
                    </div>
                ` : ''}

                ${risksList ? `
                    <div class="thesis-section">
                        <div class="thesis-section-title" style="color: #ff7b72;">Major Risks</div>
                        <ul style="margin:4px 0 0 16px; padding:0; font-size:13px;" class="text-muted">${risksList}</ul>
                    </div>
                ` : ''}

                <div class="thesis-actions" onclick="event.stopPropagation();">
                    <a href="#analyzer/${escapeHtml(ticker)}" class="btn btn-secondary btn-sm">
                        ◉ View Analysis
                    </a>
                    <button class="btn btn-secondary btn-sm" onclick="_openPostmortemForm('${escapeHtml(ticker)}', ${index})">
                        📖 Create Postmortem
                    </button>
                    <button class="btn btn-danger btn-sm" onclick="_deleteThesisFromBoard('${escapeHtml(ticker)}')">
                        🗑️ Delete
                    </button>
                </div>
            </div>
        </div>
    `;
}

function _toggleThesisExpand(index) {
    const el = document.getElementById(`thesis-expand-${index}`);
    if (el) el.classList.toggle('open');
}

async function _deleteThesisFromBoard(ticker) {
    const confirmed = await showConfirmModal(
        'Delete Thesis',
        `Delete your thesis for ${ticker}? This action cannot be undone.`
    );
    if (!confirmed) return;

    try {
        await apiFetch(`/theses/${encodeURIComponent(ticker)}`, { method: 'DELETE' });
        showToast('Thesis deleted.', 'info');
        _loadTheses();
    } catch (err) {
        showToast('Failed to delete thesis: ' + err.message, 'error');
    }
}

/* ============================================
   POSTMORTEMS
   ============================================ */

async function _loadPostmortems() {
    const container = document.getElementById('postmortems-container');
    if (!container) return;

    try {
        const pms = await apiFetch('/postmortems');

        if (!Array.isArray(pms) || pms.length === 0) {
            container.innerHTML = getEmptyStateHTML(
                '📖',
                'No Postmortems Yet',
                'When you sell a stock, create a postmortem from your active thesis to capture lessons learned and track your decision quality.',
                ''
            );
            return;
        }

        container.innerHTML = `
            <div class="cards-grid">
                ${pms.map((pm, i) => _renderPostmortemCard(pm, i)).join('')}
            </div>
        `;
    } catch (err) {
        container.innerHTML = `
            <div class="card" style="text-align: center; padding: 32px;">
                <p class="text-danger">Failed to load postmortems: ${escapeHtml(err.message)}</p>
                <button class="btn btn-secondary mt-2" onclick="renderThesisBoard()">Retry</button>
            </div>
        `;
    }
}

function _renderPostmortemCard(pm, index) {
    const ticker = pm.ticker || '—';
    const entryDate = formatDate(pm.entry_date);
    const exitDate = formatDate(pm.exit_date);
    const ret = calcReturn(pm.entry_price, pm.exit_price);
    const retClass = ret != null ? (ret >= 0 ? 'return-positive' : 'return-negative') : '';
    const holdingDays = pm.entry_date && pm.exit_date
        ? Math.round((new Date(pm.exit_date) - new Date(pm.entry_date)) / 86400000)
        : null;

    return `
        <div class="postmortem-card ${retClass} card-animated" onclick="_togglePMExpand(${index})" style="animation-delay: ${index * 0.08}s;">
            <div class="thesis-card-header">
                <span class="thesis-ticker">${escapeHtml(ticker)}</span>
                ${ret != null ? `<span class="postmortem-return">${formatPercent(ret)}</span>` : ''}
            </div>
            <div class="thesis-meta">
                <div class="thesis-meta-item">Entry: <span>${entryDate}</span></div>
                <div class="thesis-meta-item">Exit: <span>${exitDate}</span></div>
                ${holdingDays != null ? `<div class="thesis-meta-item">Held: <span>${holdingDays} days</span></div>` : ''}
            </div>
            <div class="thesis-meta">
                ${pm.entry_price ? `<div class="thesis-meta-item">Buy: <span>${formatCurrency(pm.entry_price)}</span></div>` : ''}
                ${pm.exit_price ? `<div class="thesis-meta-item">Sell: <span>${formatCurrency(pm.exit_price)}</span></div>` : ''}
            </div>

            <div class="thesis-expanded" id="pm-expand-${index}">
                ${pm.why_bought ? `
                    <div class="thesis-section">
                        <div class="thesis-section-title">Why I Bought</div>
                        <div class="thesis-section-text">${escapeHtml(pm.why_bought)}</div>
                    </div>
                ` : ''}
                ${pm.why_sold ? `
                    <div class="thesis-section">
                        <div class="thesis-section-title">Why I Sold</div>
                        <div class="thesis-section-text">${escapeHtml(pm.why_sold)}</div>
                    </div>
                ` : ''}
                ${pm.was_thesis_right ? `
                    <div class="thesis-section">
                        <div class="thesis-section-title">Was My Thesis Right?</div>
                        <div class="thesis-section-text">${escapeHtml(pm.was_thesis_right)}</div>
                    </div>
                ` : ''}
                ${pm.key_lessons ? `
                    <div class="thesis-section">
                        <div class="thesis-section-title">Key Lessons</div>
                        <div class="thesis-section-text">${escapeHtml(pm.key_lessons)}</div>
                    </div>
                ` : ''}
                ${pm.mistakes ? `
                    <div class="thesis-section">
                        <div class="thesis-section-title">Mistakes</div>
                        <div class="thesis-section-text">${escapeHtml(pm.mistakes)}</div>
                    </div>
                ` : ''}
                <div style="margin-top: 12px; display: flex; justify-content: flex-end;">
                    <button class="btn btn-secondary btn-sm" style="color: #ff7b72; border-color: rgba(255,123,114,0.3);" onclick="event.stopPropagation(); _deletePostmortem('${escapeHtml(pm.id || '')}', '${escapeHtml(ticker)}')">
                        🗑️ Delete Postmortem
                    </button>
                </div>
            </div>
        </div>
    `;
}

async function _deletePostmortem(id, ticker) {
    if (!id) return;
    const confirmed = await showConfirmModal(
        'Delete Postmortem',
        `Are you sure you want to permanently delete the postmortem for ${ticker}?`
    );
    if (!confirmed) return;

    try {
        await apiFetch(`/postmortems/${encodeURIComponent(id)}`, { method: 'DELETE' });
        showToast('Postmortem deleted successfully', 'success');
        _loadPostmortems();
    } catch (err) {
        showToast('Failed to delete postmortem: ' + err.message, 'error');
    }
}

function _togglePMExpand(index) {
    const el = document.getElementById(`pm-expand-${index}`);
    if (el) el.classList.toggle('open');
}

/* ============================================
   POSTMORTEM FORM (Modal)
   ============================================ */

async function _openPostmortemForm(ticker, thesisIndex) {
    // Get thesis data
    let thesis = null;
    try {
        const theses = await apiFetch('/theses');
        thesis = (theses || []).find(t => t.ticker === ticker);
    } catch (e) {}

    const snap = thesis?.snapshot || {};
    const now = new Date().toISOString().split('T')[0];

    // Create modal
    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay';
    overlay.id = 'postmortem-modal';
    overlay.innerHTML = `
        <div class="modal-card modal-card-lg">
            <h3>📖 Create Postmortem — <span class="gradient-text">${escapeHtml(ticker)}</span></h3>
            <p class="text-muted mb-3">Record what you learned from this investment decision.</p>

            <div class="two-col mb-2">
                <div class="form-group">
                    <label class="form-label">Entry Date</label>
                    <input type="date" id="pm-entry-date" class="form-input" value="${escapeHtml(thesis?.created_at?.split('T')[0] || '')}">
                </div>
                <div class="form-group">
                    <label class="form-label">Exit Date</label>
                    <input type="date" id="pm-exit-date" class="form-input" value="${now}">
                </div>
            </div>
            <div class="two-col mb-2">
                <div class="form-group">
                    <label class="form-label">Entry Price (₹)</label>
                    <input type="number" id="pm-entry-price" class="form-input" step="0.01"
                           placeholder="e.g. 3500" value="${snap.current_price || ''}">
                </div>
                <div class="form-group">
                    <label class="form-label">Exit Price (₹)</label>
                    <input type="number" id="pm-exit-price" class="form-input" step="0.01"
                           placeholder="e.g. 4200">
                </div>
            </div>
            <div class="form-group">
                <label class="form-label">Why I Bought</label>
                <textarea id="pm-why-bought" class="form-textarea" rows="3">${escapeHtml(thesis?.why_interested || '')}</textarea>
            </div>
            <div class="form-group">
                <label class="form-label">Why I Sold</label>
                <textarea id="pm-why-sold" class="form-textarea" rows="3" placeholder="What triggered the sale?"></textarea>
            </div>
            <div class="form-group">
                <label class="form-label">Was My Thesis Right?</label>
                <textarea id="pm-thesis-right" class="form-textarea" rows="3" placeholder="Did the thesis play out as expected?"></textarea>
            </div>
            <div class="form-group">
                <label class="form-label">Key Lessons</label>
                <textarea id="pm-lessons" class="form-textarea" rows="3" placeholder="What did you learn from this investment?"></textarea>
            </div>
            <div class="form-group">
                <label class="form-label">Mistakes (if any)</label>
                <textarea id="pm-mistakes" class="form-textarea" rows="2" placeholder="What would you do differently?"></textarea>
            </div>

            <div class="modal-actions">
                <button class="btn btn-secondary" onclick="_closePostmortemForm()">Cancel</button>
                <button class="btn btn-primary" onclick="_savePostmortem('${escapeHtml(ticker)}')">
                    💾 Save Postmortem
                </button>
            </div>
        </div>
    `;

    document.body.appendChild(overlay);
}

function _closePostmortemForm() {
    const modal = document.getElementById('postmortem-modal');
    if (modal) modal.remove();
}

async function _savePostmortem(ticker) {
    const payload = {
        ticker: ticker,
        entry_date: document.getElementById('pm-entry-date')?.value || null,
        exit_date: document.getElementById('pm-exit-date')?.value || null,
        entry_price: parseFloat(document.getElementById('pm-entry-price')?.value) || null,
        exit_price: parseFloat(document.getElementById('pm-exit-price')?.value) || null,
        why_bought: document.getElementById('pm-why-bought')?.value?.trim() || '',
        why_sold: document.getElementById('pm-why-sold')?.value?.trim() || '',
        was_thesis_right: document.getElementById('pm-thesis-right')?.value?.trim() || '',
        key_lessons: document.getElementById('pm-lessons')?.value?.trim() || '',
        mistakes: document.getElementById('pm-mistakes')?.value?.trim() || '',
    };

    if (!payload.why_sold) {
        showToast('Please fill in why you sold.', 'warning');
        return;
    }

    try {
        await apiFetch('/postmortems', {
            method: 'POST',
            body: JSON.stringify(payload),
        });
        showToast('Postmortem saved successfully!', 'success');
        _closePostmortemForm();

        // Optionally delete the thesis
        const deleteThesis = await showConfirmModal(
            'Remove Active Thesis?',
            `Would you like to remove the active thesis for ${ticker} since you've sold the position?`
        );
        if (deleteThesis) {
            try {
                await apiFetch(`/theses/${encodeURIComponent(ticker)}`, { method: 'DELETE' });
                showToast('Thesis archived.', 'info');
            } catch (e) {}
        }

        // Reload
        _loadTheses();
        _loadPostmortems();
    } catch (err) {
        showToast('Failed to save postmortem: ' + err.message, 'error');
    }
}
