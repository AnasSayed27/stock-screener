/* ============================================
   StockLens — DiscoveryLens Module
   ============================================ */

// Module-level state
let _discoveryStrategies = [];
let _selectedStrategyId = 'government_policy';
let _savedDiscoveries = [];
let _activeDiscovery = null;
let _discoveryRunning = false;

// Master Synthesis State
let _synthesisRunning = false;
let _synthesisAbortController = null;
let _savedSyntheses = [];


/**
 * Render the Discovery page.
 */
async function renderDiscovery(param) {
    const main = document.getElementById('main-content');
    
    // Initial HTML shell
    main.innerHTML = `
        <div class="fade-in">
            <div class="page-header">
                <h1 class="page-title">Stock <span class="gradient-text">Discovery</span></h1>
                <p class="page-subtitle">
                    Scan the Indian markets using agentic AI. Select a strategy, enter context, 
                    and watch the AI search the web, analyze supply chains, and build investment hypotheses.
                </p>
            </div>

            <!-- Discovery Dashboard Grid -->
            <div class="discovery-grid" style="display: grid; grid-template-columns: 1fr; gap: 24px; margin-bottom: 40px;">
                <!-- Main Control Panel -->
                <div class="card" style="padding: 24px;">
                    <h3 style="margin-top: 0; margin-bottom: 20px; color: var(--text-secondary); display: flex; align-items: center; gap: 8px;">
                        <span>◈</span> Run AI Discovery Strategy
                    </h3>
                    
                    <div style="display: grid; grid-template-columns: 1fr; gap: 20px; margin-bottom: 20px;">
                        <div class="select-container" style="max-width: 100%;">
                            <label class="select-label">Select Discovery Strategy</label>
                            <select id="discovery-strategy-select" class="select-input" onchange="onDiscoveryStrategyChanged(this.value)">
                                <option value="" disabled>Loading strategies...</option>
                            </select>
                        </div>
                        
                        <div id="discovery-input-wrapper">
                            <!-- Rendered dynamically -->
                        </div>
                    </div>

                    <div style="display: flex; gap: 12px; align-items: center; margin-top: 20px; flex-wrap: wrap;">
                        <button id="discovery-run-btn" class="btn btn-primary btn-lg" onclick="startDiscovery()">
                            <span class="btn-icon">⚡</span> Run Agentic Scan
                        </button>
                        <button id="discovery-stop-btn" class="btn btn-danger btn-lg" onclick="stopDiscovery()" style="display: none; background: #ef4444; color: #ffffff; border: none; padding: 10px 20px; border-radius: var(--radius-md); cursor: pointer; font-weight: 600; align-items: center; gap: 8px;">
                            <span class="btn-icon">🛑</span> Stop Process
                        </button>
                        <span id="tavily-notice" class="text-muted" style="font-size: 12px;">
                            Requires TAVILY_API_KEY in .env · Scans NSE/BSE listed equities
                        </span>
                    </div>
                </div>

                <div id="discovery-progress-card" class="card" style="display: none; padding: 24px; border-left: 4px solid var(--accent-cyan);">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                        <h4 id="discovery-progress-title" style="margin: 0; display: flex; align-items: center; gap: 8px;">
                            <span class="spinner" style="width: 16px; height: 16px; border-width: 2px;"></span>
                            AI Agent is researching...
                        </h4>
                        <button id="discovery-card-stop-btn" class="btn btn-secondary btn-sm" onclick="stopDiscovery()" style="background: rgba(239, 68, 68, 0.15); color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.4); padding: 4px 12px; border-radius: 6px; cursor: pointer; font-size: 12px; font-weight: 600; display: flex; align-items: center; gap: 4px;">
                            🛑 Stop Research
                        </button>
                    </div>
                    <div id="discovery-progress-steps" style="display:flex; justify-content: space-between; margin-bottom: 16px; background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); padding: 12px; border-radius: var(--radius-sm); font-size: 11px; flex-wrap: wrap; gap: 8px;">
                        <span class="step-badge" id="step-1" style="color: var(--text-muted);">○ Phase 1: Scan</span>
                        <span class="step-badge" id="step-2" style="color: var(--text-muted);">○ Phase 2: Correct</span>
                        <span class="step-badge" id="step-3" style="color: var(--text-muted);">○ Phase 3: Deep Dive</span>
                        <span class="step-badge" id="step-4" style="color: var(--text-muted);">○ Phase 4: Verify</span>
                        <span class="step-badge" id="step-5" style="color: var(--text-muted);">○ Phase 5: Synthesis</span>
                    </div>
                    <div id="discovery-search-log" style="background: rgba(0,0,0,0.2); border-radius: var(--border-radius); padding: 16px; font-family: monospace; font-size: 13px; max-height: 200px; overflow-y: auto; display: flex; flex-direction: column; gap: 8px; border: 1px solid rgba(255,255,255,0.05);">
                        <!-- Logs appended here -->
                    </div>
                </div>

                <!-- Active Discovery Results -->
                <div id="discovery-results-area"></div>

                <!-- History / Saved Discoveries -->
                <div class="card" style="padding: 24px;">
                    <h3 style="margin-top: 0; margin-bottom: 20px; color: var(--text-secondary); display: flex; align-items: center; gap: 8px;">
                        <span>📂</span> Discovery History
                    </h3>
                    <div id="discovery-history-list" class="history-grid" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 16px;">
                        <!-- History loaded dynamically -->
                    </div>
                </div>

                <!-- Master Synthesis Section -->
                <div class="card" style="padding: 24px; border: 1px solid rgba(255, 215, 0, 0.2); background: linear-gradient(135deg, rgba(255,215,0,0.01) 0%, rgba(0,0,0,0) 100%);">
                    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 12px; margin-bottom: 20px;">
                        <div>
                            <h3 style="margin: 0; color: #ffd700; display: flex; align-items: center; gap: 8px; font-weight:700;">
                                <span>🏆</span> Master Cross-Strategy Synthesis
                            </h3>
                            <p class="text-muted" style="font-size: 13px; margin: 4px 0 0 0;">
                                Select at least 7 strategy results from history to aggregate and discover Ultimate Picks using Master AI reasoning.
                            </p>
                        </div>
                        <button id="synthesis-toggle-btn" class="btn btn-secondary" onclick="toggleSynthesisPanel()" style="display: flex; align-items: center; gap: 6px; border-color: rgba(255,215,0,0.3); color: #ffd700;">
                            <span>📋</span> Select Strategies for Synthesis
                        </button>
                    </div>

                    <!-- Selection Panel (hidden by default) -->
                    <div id="synthesis-selection-panel" style="display: none; background: rgba(0,0,0,0.3); border: 1px solid rgba(255,215,0,0.15); border-radius: var(--border-radius); padding: 20px; margin-bottom: 20px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; flex-wrap: wrap; gap: 8px;">
                            <div style="display: flex; gap: 8px; align-items: center; flex-wrap: wrap;">
                                <button class="btn btn-secondary btn-sm" onclick="toggleAllSynthesisSelections(true)">Select All</button>
                                <button class="btn btn-secondary btn-sm" onclick="toggleAllSynthesisSelections(false)">Deselect All</button>
                                <span id="synthesis-selection-count" style="font-size: 13px; font-weight: 600; color: var(--accent-cyan); margin-left: 6px;">
                                    Selected: 0/0 (Min 7 required)
                                </span>
                            </div>
                            <div style="display: flex; gap: 8px; align-items: center;">
                                <button id="synthesis-run-btn" class="btn btn-primary" onclick="startSynthesis()" disabled style="background: linear-gradient(135deg, #ffd700, #ff8c00); color: #000; font-weight: 700; padding: 8px 18px;">
                                    🚀 Run Master Synthesis
                                </button>
                                <button id="synthesis-stop-btn" class="btn btn-danger" onclick="stopSynthesis()" style="display: none; background: #ef4444; color: #fff; font-weight: 600; padding: 8px 18px;">
                                    🛑 Stop Synthesis
                                </button>
                            </div>
                        </div>

                        <div id="synthesis-checkbox-grid" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 10px; max-height: 320px; overflow-y: auto; padding: 6px; background: rgba(0,0,0,0.2); border-radius: 6px; border: 1px solid rgba(255,255,255,0.03);">
                            <!-- Dynamically populated from _savedDiscoveries -->
                        </div>
                    </div>

                    <!-- Synthesis Progress Card -->
                    <div id="synthesis-progress-card" class="card" style="display: none; padding: 20px; border-left: 4px solid #ffd700; margin-bottom: 20px; background: rgba(255,215,0,0.02);">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                            <h4 id="synthesis-progress-title" style="margin: 0; display: flex; align-items: center; gap: 8px; color: #ffd700;">
                                <span class="spinner" style="width: 16px; height: 16px; border-width: 2px;"></span>
                                Master AI is synthesizing strategy findings...
                            </h4>
                            <button class="btn btn-secondary btn-sm" onclick="stopSynthesis()" style="background: rgba(239,68,68,0.15); color: #ef4444; border: 1px solid rgba(239,68,68,0.4);">
                                🛑 Stop
                            </button>
                        </div>
                        <div id="synthesis-search-log" style="background: rgba(0,0,0,0.4); border-radius: 4px; padding: 12px; font-family: monospace; font-size: 12px; color: var(--text-secondary); max-height: 150px; overflow-y: auto; display: flex; flex-direction: column; gap: 4px; border: 1px solid rgba(255,255,255,0.05);">
                        </div>
                    </div>

                    <!-- Active Synthesis Results -->
                    <div id="synthesis-results-area" style="margin-bottom: 24px;"></div>

                    <!-- Synthesis History -->
                    <div>
                        <h4 style="margin-top: 0; margin-bottom: 12px; color: var(--text-secondary); font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px;">
                            📜 Synthesis History
                        </h4>
                        <div id="synthesis-history-list" class="history-grid" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 12px;">
                            <!-- Loaded dynamically -->
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;

    // 1. Fetch available strategies
    await loadDiscoveryStrategies();

    // 2. Fetch history
    await loadDiscoveryHistory();
    await loadSynthesisHistory();

    // 3. Handle parameter if navigated from direct ID
    if (param && param !== 'new') {
        loadSavedDiscovery(param);
    }
}

/**
 * Loads available strategies from backend
 */
async function loadDiscoveryStrategies() {
    try {
        const data = await apiFetch('/discovery/strategies');
        _discoveryStrategies = data;
        
        const select = document.getElementById('discovery-strategy-select');
        if (!select) return;

        select.innerHTML = data.map(s => {
            const isExp = s.id === 'scuttlebutt' ? ' [EXPERIMENTAL]' : '';
            return `<option value="${s.id}" ${s.id === _selectedStrategyId ? 'selected' : ''}>${escapeHtml(s.name)}${isExp}</option>`;
        }).join('');

        renderDiscoveryInput();
    } catch (err) {
        showToast('Failed to load discovery strategies: ' + err.message, 'error');
    }
}

/**
 * Handles dropdown changes
 */
function onDiscoveryStrategyChanged(strategyId) {
    _selectedStrategyId = strategyId;
    renderDiscoveryInput();
}

/**
 * Renders the dynamic input fields
 */
function renderDiscoveryInput() {
    const wrapper = document.getElementById('discovery-input-wrapper');
    if (!wrapper) return;

    const strategy = _discoveryStrategies.find(s => s.id === _selectedStrategyId);
    if (!strategy) return;

    if (strategy.input_type === 'none') {
        wrapper.innerHTML = `<p class="text-muted" style="font-size: 13px;">This strategy runs globally. No additional inputs required.</p>`;
        return;
    }

    const placeholder = strategy.id === 'government_policy' 
        ? 'e.g. India Government raises PLI scheme budget for electric components by 50% or anti-dumping duty on imports of chemicals.'
        : strategy.id === 'freeform'
        ? 'e.g. What companies are positioned to supply components for the upgradation of Indian railways?'
        : 'Enter keywords, sector, or brand...';

    const inputHtml = strategy.input_type === 'textarea'
        ? `<textarea id="discovery-context-input" class="textarea-input" rows="4" placeholder="${placeholder}" style="width:100%; border-radius: var(--border-radius); border: 1px solid rgba(255,255,255,0.1); background: rgba(0,0,0,0.2); padding: 12px; color: var(--text-primary); font-family: inherit; font-size:14px; resize:vertical;"></textarea>`
        : `<input type="text" id="discovery-context-input" class="text-input" placeholder="${placeholder}" style="width:100%; border-radius: var(--border-radius); border: 1px solid rgba(255,255,255,0.1); background: rgba(0,0,0,0.2); padding: 12px; color: var(--text-primary); font-size:14px;">`;

    wrapper.innerHTML = `
        <div style="display: flex; flex-direction: column; gap: 8px;">
            <label class="select-label" style="font-weight: 500;">
                ${escapeHtml(strategy.input_label)} ${strategy.required ? '<span style="color: var(--color-danger);">*</span>' : '(Optional)'}
            </label>
            ${inputHtml}
            <p class="text-muted" style="font-size: 12px; margin-top: 2px;">
                ${escapeHtml(strategy.description)}
            </p>
        </div>
    `;
}

let _discoveryAbortController = null;

/**
 * Stops an active discovery process
 */
async function stopDiscovery() {
    if (!_discoveryRunning) return;
    
    appendSearchLog("🛑 Stop signal requested by user. Aborting active research tasks...");
    showToast('Stopping discovery process...', 'info');

    // 1. Abort local fetch stream reader
    if (_discoveryAbortController) {
        _discoveryAbortController.abort();
        _discoveryAbortController = null;
    }

    // 2. Notify backend to trigger thread-level cancellation event
    try {
        await fetch('/api/discovery/stop', { method: 'POST' });
    } catch (err) {
        console.warn("Failed to send stop signal to backend:", err);
    }
}

/**
 * Starts the agentic discovery run
 */
async function startDiscovery() {
    if (_discoveryRunning) return;
    
    const strategy = _discoveryStrategies.find(s => s.id === _selectedStrategyId);
    const inputEl = document.getElementById('discovery-context-input');
    const contextVal = inputEl ? inputEl.value.trim() : '';

    if (strategy && strategy.required && !contextVal) {
        showToast('Please enter the required context details.', 'warning');
        if (inputEl) inputEl.focus();
        return;
    }

    const runBtn = document.getElementById('discovery-run-btn');
    const stopBtn = document.getElementById('discovery-stop-btn');
    const cardStopBtn = document.getElementById('discovery-card-stop-btn');
    const logCard = document.getElementById('discovery-progress-card');
    const logArea = document.getElementById('discovery-search-log');
    const resultsArea = document.getElementById('discovery-results-area');

    _discoveryRunning = true;
    _discoveryAbortController = new AbortController();

    if (runBtn) {
        runBtn.style.display = 'none';
    }
    if (stopBtn) {
        stopBtn.style.display = 'inline-flex';
    }
    if (cardStopBtn) {
        cardStopBtn.style.display = 'inline-flex';
    }
    if (logCard) {
        logCard.style.display = 'block';
        const titleEl = document.getElementById('discovery-progress-title');
        if (titleEl) {
            titleEl.innerHTML = '<span class="spinner" style="width: 16px; height: 16px; border-width: 2px;"></span> AI Agent is researching...';
        }
    }
    
    // Reset phase step styles
    for (let i = 1; i <= 5; i++) {
        const stepEl = document.getElementById(`step-${i}`);
        if (stepEl) {
            stepEl.style.color = 'var(--text-muted)';
            stepEl.style.fontWeight = 'normal';
            const baseText = stepEl.textContent.replace(/^[○●✓]\s*/, '');
            stepEl.textContent = `○ ${baseText}`;
        }
    }
    
    if (logArea) logArea.innerHTML = `<div class="log-line" style="color: var(--accent-cyan);">[System] Initializing Gemini Agent with ${escapeHtml(strategy ? strategy.name : '')} strategy...</div>`;
    if (resultsArea) resultsArea.innerHTML = '';

    try {
        const response = await fetch('/api/discovery/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ strategy_id: _selectedStrategyId, context: contextVal }),
            signal: _discoveryAbortController.signal
        });

        if (!response.ok) {
            let errorMsg = `HTTP ${response.status}`;
            try {
                const errData = await response.json();
                errorMsg = errData.detail || errData.message || errorMsg;
            } catch (_) {}
            throw new Error(errorMsg);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop();

            for (const line of lines) {
                if (!line.trim()) continue;
                try {
                    const event = JSON.parse(line);
                    if (event.type === 'progress' || event.type === 'log') {
                        appendSearchLog(event.message);
                    } else if (event.type === 'result') {
                        showToast('Discovery completed successfully!', 'success');
                        renderDiscoveryResult(event.data);
                        await loadDiscoveryHistory();
    await loadSynthesisHistory(); // reload history
                    } else if (event.type === 'cancelled') {
                        showToast('Discovery process stopped.', 'info');
                        appendSearchLog("🛑 Process cancelled by user.");
                    } else if (event.type === 'error') {
                        throw new Error(event.message);
                    }
                } catch (e) {
                    if (e.message !== 'The user aborted a request.' && !e.message.includes('aborted')) {
                        console.error('Failed to parse line or process event:', line, e);
                    }
                }
            }
        }
    } catch (err) {
        if (err.name === 'AbortError' || err.message.includes('aborted')) {
            showToast('Discovery process stopped by user.', 'info');
            if (logArea) {
                logArea.innerHTML += `<div class="log-line" style="color: #ef4444; font-weight: 600;">🛑 Discovery process stopped by user.</div>`;
            }
        } else {
            showToast('Discovery run failed: ' + err.message, 'error');
            if (resultsArea) {
                resultsArea.innerHTML = `
                    <div class="card" style="text-align: center; padding: 40px; border: 1px solid rgba(239, 68, 68, 0.2);">
                        <span style="font-size: 40px; display: block; margin-bottom: 12px;">⚠️</span>
                        <h3 style="color: var(--color-danger); margin-top:0; margin-bottom: 8px;">Discovery Failed</h3>
                        <p class="text-muted" style="margin-bottom: 16px;">${escapeHtml(err.message)}</p>
                        <button class="btn btn-secondary" onclick="startDiscovery()">Try Again</button>
                    </div>
                `;
            }
        }
    } finally {
        _discoveryRunning = false;
        _discoveryAbortController = null;
        if (runBtn) {
            runBtn.style.display = 'inline-flex';
            runBtn.disabled = false;
            runBtn.innerHTML = '<span class="btn-icon">⚡</span> Run Agentic Scan';
        }
        if (stopBtn) {
            stopBtn.style.display = 'none';
        }
        if (cardStopBtn) {
            cardStopBtn.style.display = 'none';
        }
        if (logCard) {
            const titleEl = document.getElementById('discovery-progress-title');
            if (titleEl) titleEl.innerHTML = '<span>✓</span> Research Stream Completed / Stopped';
        }
        if (window.updateAPIUsageStats) {
            window.updateAPIUsageStats();
        }
    }
}

function appendSearchLog(msg) {
    const logArea = document.getElementById('discovery-search-log');
    if (!logArea) return;

    // Detect phase transitions in stream
    const phaseMatch = msg.match(/━━━ Phase (\d)\/5/);
    if (phaseMatch) {
        const activePhase = parseInt(phaseMatch[1]);
        for (let i = 1; i <= 5; i++) {
            const stepEl = document.getElementById(`step-${i}`);
            if (stepEl) {
                if (i < activePhase) {
                    stepEl.style.color = 'var(--color-success)';
                    stepEl.style.fontWeight = '500';
                    const baseText = stepEl.textContent.replace(/^[○●✓]\s*/, '');
                    stepEl.textContent = `✓ ${baseText}`;
                } else if (i === activePhase) {
                    stepEl.style.color = 'var(--accent-cyan)';
                    stepEl.style.fontWeight = 'bold';
                    const baseText = stepEl.textContent.replace(/^[○●✓]\s*/, '');
                    stepEl.textContent = `● ${baseText}`;
                } else {
                    stepEl.style.color = 'var(--text-muted)';
                    stepEl.style.fontWeight = 'normal';
                    const baseText = stepEl.textContent.replace(/^[○●✓]\s*/, '');
                    stepEl.textContent = `○ ${baseText}`;
                }
            }
        }
    }

    const line = document.createElement('div');
    line.className = 'log-line';
    
    if (msg.startsWith('━━━')) {
        line.style.color = 'var(--accent-cyan)';
        line.style.fontWeight = 'bold';
        line.style.marginTop = '12px';
        line.style.borderBottom = '1px solid rgba(0, 212, 255, 0.1)';
        line.style.paddingBottom = '4px';
        line.innerHTML = escapeHtml(msg);
    } else if (msg.includes('Rate limit reached') || msg.includes('Pausing')) {
        line.style.color = 'var(--color-warning)';
        line.style.fontWeight = '500';
        line.innerHTML = `⏳ ${escapeHtml(msg)}`;
    } else if (msg.startsWith('Phase') && msg.includes('complete')) {
        line.style.color = 'var(--color-success)';
        line.style.fontWeight = '500';
        line.style.marginBottom = '8px';
        line.innerHTML = `✓ ${escapeHtml(msg)}`;
    } else if (msg.includes('[Ticker Resolution]')) {
        line.style.color = '#c084fc';
        line.style.fontWeight = '500';
        line.innerHTML = escapeHtml(msg);
    } else if (msg.includes('[Financial Audit]')) {
        line.style.color = '#34d399';
        line.style.fontWeight = '500';
        line.innerHTML = escapeHtml(msg);
    } else if (msg.includes('[Quality Scorecard]')) {
        line.style.color = '#fbbf24';
        line.style.fontWeight = '500';
        line.innerHTML = escapeHtml(msg);
    } else if (msg.includes('[Web Search]')) {
        line.style.color = '#60a5fa';
        line.innerHTML = escapeHtml(msg);
    } else if (msg.startsWith('⚠️')) {
        line.style.color = '#f87171';
        line.innerHTML = escapeHtml(msg);
    } else {
        line.style.color = '#94a3b8';
        line.innerHTML = escapeHtml(msg);
    }
    
    logArea.appendChild(line);
    logArea.scrollTop = logArea.scrollHeight;
}

/**
 * Loads history summaries from backend
 */
async function loadDiscoveryHistory() {
    const list = document.getElementById('discovery-history-list');
    if (!list) return;

    try {
        const data = await apiFetch('/discovery/saved');
        _savedDiscoveries = data;

        if (data.length === 0) {
            list.innerHTML = `<div style="grid-column: 1/-1; text-align: center; padding: 24px;" class="text-muted">No discovery history found. Run a scan above to start.</div>`;
            return;
        }

        list.innerHTML = data.map(d => {
            const dateStr = d.created_at ? new Date(d.created_at).toLocaleDateString('en-IN', {
                day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit'
            }) : '—';
            
            return `
                <div class="card history-card" style="padding: 16px; display: flex; flex-direction: column; justify-content: space-between; border: 1px solid rgba(255,255,255,0.05); hover: border-color: var(--color-accent);">
                    <div>
                        <h4 style="margin-top:0; margin-bottom: 6px; font-weight:600; color: var(--text-primary);">${escapeHtml(d.strategy_name)}</h4>
                        <p class="text-muted" style="font-size: 13px; margin-bottom: 12px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; height: 36px;">
                            ${escapeHtml(d.user_input_preview)}
                        </p>
                    </div>
                    <div style="display:flex; justify-content: space-between; align-items:center; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 12px; margin-top:8px;">
                        <span style="font-size:11px;" class="text-muted">${dateStr} · <strong>${d.candidate_count}</strong> ideas</span>
                        <div style="display:flex; gap: 8px;">
                            <button class="btn btn-secondary btn-sm" onclick="loadSavedDiscovery('${d.id}')">View</button>
                            <button class="btn btn-danger btn-sm" onclick="deleteSavedDiscovery('${d.id}', event)">Delete</button>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    } catch (err) {
        list.innerHTML = `<div style="grid-column: 1/-1; color: var(--color-danger);">Failed to load history: ${escapeHtml(err.message)}</div>`;
    }
}

/**
 * Loads a specific discovery run from history
 */
async function loadSavedDiscovery(id) {
    const resultsArea = document.getElementById('discovery-results-area');
    if (resultsArea) {
        resultsArea.innerHTML = getLoadingHTML('Loading saved discovery...');
        resultsArea.scrollIntoView({ behavior: 'smooth' });
    }

    try {
        const data = await apiFetch(`/discovery/saved/${id}`);
        _activeDiscovery = data;
        
        // Match selection UI
        const select = document.getElementById('discovery-strategy-select');
        if (select) {
            select.value = data.strategy_id;
            _selectedStrategyId = data.strategy_id;
            renderDiscoveryInput();
            const inputEl = document.getElementById('discovery-context-input');
            if (inputEl) inputEl.value = data.user_params?.context || '';
        }
        
        // Hide running logs card if visible
        const logCard = document.getElementById('discovery-progress-card');
        if (logCard) logCard.style.display = 'none';

        renderDiscoveryResult(data);
    } catch (err) {
        showToast('Failed to load discovery: ' + err.message, 'error');
        if (resultsArea) resultsArea.innerHTML = '';
    }
}

/**
 * Deletes a saved discovery run
 */
async function deleteSavedDiscovery(id, event) {
    if (event) event.stopPropagation();
    if (!confirm('Are you sure you want to delete this discovery run from history?')) return;

    try {
        await apiFetch(`/discovery/saved/${id}`, { method: 'DELETE' });
        showToast('Discovery deleted.', 'success');
        
        // If active discovery was deleted, clear it
        if (_activeDiscovery && _activeDiscovery.id === id) {
            _activeDiscovery = null;
            const resultsArea = document.getElementById('discovery-results-area');
            if (resultsArea) resultsArea.innerHTML = '';
        }
        
        await loadDiscoveryHistory();
    await loadSynthesisHistory();
    } catch (err) {
        showToast('Delete failed: ' + err.message, 'error');
    }
}

/**
 * Render the parsed discovery result into the dashboard
 */
function renderDiscoveryResult(meta) {
    const resultsArea = document.getElementById('discovery-results-area');
    if (!resultsArea) return;

    const res = meta.result || {};
    const candidates = res.candidates || [];
    
    if (candidates.length === 0) {
        resultsArea.innerHTML = `
            <div class="card" style="padding: 32px; text-align: center; border: 1px solid rgba(255,255,255,0.05);">
                <h3 style="margin-top:0; color: var(--text-secondary);">No Candidates Found</h3>
                <p class="text-muted" style="margin-bottom:0;">
                    The AI completed its research but found no companies fitting this specific strategy and context.
                </p>
                ${res.limitations && res.limitations.length > 0 ? `
                    <div style="margin-top: 16px; text-align: left; max-width: 500px; margin-left: auto; margin-right: auto; padding: 12px; background: rgba(255,255,255,0.02); border-radius: var(--border-radius); border: 1px solid rgba(255,255,255,0.05);">
                        <strong style="font-size:12px; text-transform:uppercase; color: var(--text-secondary);">AI Limitations:</strong>
                        <ul style="margin: 8px 0 0 16px; padding:0; font-size:13px;" class="text-muted">
                            ${res.limitations.map(l => `<li>${escapeHtml(l)}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
            </div>
        `;
        resultsArea.scrollIntoView({ behavior: 'smooth' });
        return;
    }

    // Build the candidates HTML
    const candidatesHtml = candidates.map((c, index) => {
        const cardId = `candidate-card-${index}`;
        const confidenceClass = `badge-${c.confidence || 'medium'}`;
        const tickerDisplay = c.ticker ? `<span class="ticker-badge" style="background: rgba(0, 212, 255, 0.1); color: var(--accent-cyan); font-weight:600; padding: 3px 8px; border-radius: 4px; font-size:12px; margin-left: 8px;">${escapeHtml(c.ticker)}</span>` : '';
        
        // Generate confidence evolution HTML if present
        let confidenceEvolutionHtml = '';
        if (c.confidence_evolution && c.confidence_evolution.length > 0) {
            const stepsBadges = c.confidence_evolution.map(step => {
                const parts = step.split(':');
                const label = parts[0].trim();
                const val = parts[1] ? parts[1].trim() : '';
                return `<span class="confidence-step-badge" style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); padding: 2px 6px; border-radius: 4px; font-size:10px; color: var(--text-secondary);" title="${escapeHtml(step)}">
                    <span style="color: var(--text-muted);">${escapeHtml(label)}:</span> <strong>${escapeHtml(val)}</strong>
                </span>`;
            }).join(' <span style="color:var(--text-muted); font-size:9px;">→</span> ');
            
            confidenceEvolutionHtml = `
                <div style="display:flex; align-items:center; gap: 6px; flex-wrap:wrap; margin-top: 8px;">
                    <span style="font-size:10px; font-weight:600; text-transform:uppercase;" class="text-muted">Confidence Flow:</span>
                    ${stepsBadges}
                </div>
            `;
        }

        // Generate lists
        const risksList = c.risks && c.risks.length > 0
            ? c.risks.map(r => `<li>${escapeHtml(r)}</li>`).join('')
            : '<li class="text-muted">No specific risks flagged.</li>';
            
        const verifyList = c.what_to_verify && c.what_to_verify.length > 0
            ? c.what_to_verify.map(v => `<li>${escapeHtml(v)}</li>`).join('')
            : '<li class="text-muted">No verification items suggested.</li>';

        // Generate sources
        const sourcesButtons = c.sources && c.sources.length > 0
            ? c.sources.map((s, idx) => {
                let label = 'Source';
                try {
                    const host = new URL(s).hostname.replace('www.', '');
                    label = host;
                } catch(_) {}
                return `<a href="${escapeHtml(sanitizeUrl(s))}" target="_blank" rel="noopener noreferrer" class="source-link-btn" style="display:inline-flex; align-items:center; gap: 4px; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); padding: 5px 10px; border-radius: 4px; font-size: 12px; color: var(--text-secondary); text-decoration: none; hover: background: rgba(255,255,255,0.08); transition: background 0.2s;">
                    <span>🔗</span> ${escapeHtml(label)}
                </a>`;
            }).join(' ')
            : '<span class="text-muted" style="font-size:12px;">No specific URLs provided.</span>';

        return `
            <div class="card candidate-card" id="${cardId}" style="padding: 24px; border: 1px solid rgba(255,255,255,0.05); display: flex; flex-direction: column; gap: 20px;">
                <!-- Header -->
                <div style="display:flex; justify-content: space-between; align-items: flex-start; gap: 16px; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 16px;">
                    <div>
                        <div style="display:flex; align-items:center; gap: 4px; flex-wrap: wrap;">
                            <h3 style="margin:0; font-size: 20px; font-weight:700; color: var(--text-primary);">${escapeHtml(c.company_name)}</h3>
                            ${tickerDisplay}
                        </div>
                        <p class="text-muted" style="font-size:13px; margin: 4px 0 0 0;">
                            Connection: <strong style="color: var(--text-secondary);">${escapeHtml(c.connection_type)}</strong>
                        </p>
                        ${confidenceEvolutionHtml}
                    </div>
                    <span class="badge ${confidenceClass}">${c.confidence.toUpperCase()} CONFIDENCE</span>
                </div>

                <!-- Timing Block ("Why Now") -->
                ${c.why_now ? `
                    <div class="why-now-box" style="background: rgba(138, 180, 248, 0.03); border: 1px solid rgba(138, 180, 248, 0.1); border-radius: var(--border-radius); padding: 14px 16px;">
                        <strong style="color: var(--accent-cyan); font-size:12px; text-transform:uppercase; letter-spacing:0.5px; display:block; margin-bottom: 4px;">⏰ Why Now?</strong>
                        <p style="margin:0; font-size:13px; line-height:1.4;" class="text-muted">${escapeHtml(c.why_now)}</p>
                    </div>
                ` : ''}

                <!-- Tabs (Reasoning / Self-Critique / Disproving) -->
                <div>
                    <div class="tabs-header" style="display:flex; border-bottom: 1px solid rgba(255,255,255,0.05); margin-bottom: 12px; gap: 4px;">
                        <button class="tab-btn active" onclick="switchCandidateTab('${cardId}', 'reasoning')">Reasoning Thesis</button>
                        <button class="tab-btn" onclick="switchCandidateTab('${cardId}', 'self-critique')">Why It Might Fail</button>
                        <button class="tab-btn" onclick="switchCandidateTab('${cardId}', 'disproving')">Disproving Signals</button>
                    </div>
                    <div class="tab-content reasoning active" style="font-size: 14px; line-height: 1.5; color: var(--text-secondary);">
                        ${escapeHtml(c.reasoning).replace(/\n/g, '<br>')}
                    </div>
                    <div class="tab-content self-critique" style="display:none; font-size: 14px; line-height: 1.5; color: var(--text-secondary); border-left: 3px solid #ff7b72; padding-left: 12px; font-style: italic;">
                        ${escapeHtml(c.self_critique || 'No self-critique offered.').replace(/\n/g, '<br>')}
                    </div>
                    <div class="tab-content disproving" style="display:none; font-size: 14px; line-height: 1.5; color: var(--text-secondary); border-left: 3px solid #f2cc60; padding-left: 12px;">
                        <strong>What would disprove this hypothesis:</strong><br>
                        ${escapeHtml(c.disproving_evidence || 'No disproving signals defined.').replace(/\n/g, '<br>')}
                    </div>
                </div>

                <!-- Split Risks / What to Verify -->
                <div style="display: grid; grid-template-columns: 1fr; gap: 16px; margin-top: 4px;">
                    <div style="background: rgba(255,255,255,0.01); border: 1px solid rgba(255,255,255,0.03); border-radius: var(--border-radius); padding: 14px;">
                        <strong style="font-size: 12px; color: var(--text-secondary); text-transform:uppercase; letter-spacing:0.5px; display:block; margin-bottom: 8px;">⚠️ Risks Flagged</strong>
                        <ul style="margin:0 0 0 16px; padding:0; font-size: 13px;" class="text-muted">
                            ${risksList}
                        </ul>
                    </div>
                    <div style="background: rgba(255,255,255,0.01); border: 1px solid rgba(255,255,255,0.03); border-radius: var(--border-radius); padding: 14px;">
                        <strong style="font-size: 12px; color: var(--text-secondary); text-transform:uppercase; letter-spacing:0.5px; display:block; margin-bottom: 8px;">📋 Items to Verify</strong>
                        <ul style="margin:0 0 0 16px; padding:0; font-size: 13px;" class="text-muted">
                            ${verifyList}
                        </ul>
                    </div>
                </div>

                <!-- Action Footer -->
                <div style="display:flex; justify-content: space-between; align-items:center; flex-wrap:wrap; gap: 12px; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 16px; margin-top: 8px;">
                    <div style="display:flex; align-items:center; gap: 8px; flex-wrap:wrap;">
                        <span style="font-size:12px; font-weight:600;" class="text-muted">References:</span>
                        ${sourcesButtons}
                    </div>
                    <button class="btn btn-secondary" onclick="analyzeCandidate('${escapeHtml(c.company_name)}', ${c.ticker ? `'${escapeHtml(c.ticker)}'` : 'null'})" style="display:flex; align-items:center; gap: 6px;">
                        🔍 Analyze in StockLens →
                    </button>
                </div>
            </div>
        `;
    }).join('');

    // Group searches by phase
    let groupedSearchesHtml = '';
    if (res.searches_performed && res.searches_performed.length > 0) {
        const searchesByPhase = {};
        res.searches_performed.forEach(s => {
            const phaseName = s.phase || "Unspecified Phase";
            if (!searchesByPhase[phaseName]) {
                searchesByPhase[phaseName] = [];
            }
            searchesByPhase[phaseName].push(s);
        });

        groupedSearchesHtml = Object.keys(searchesByPhase).map(phaseName => {
            const phaseSearches = searchesByPhase[phaseName];
            const phaseSearchesHtml = phaseSearches.map((s, i) => {
                let badge = '<span style="font-size:10px; font-weight:700; padding:2px 6px; border-radius:4px; background:rgba(0, 229, 255, 0.12); color:var(--accent-cyan);">🔍 WEB SEARCH</span>';
                let qText = s.query || '';
                if (qText.includes("resolve_ticker")) {
                    badge = '<span style="font-size:10px; font-weight:700; padding:2px 6px; border-radius:4px; background:rgba(255, 171, 0, 0.15); color:#ffab00;">🏷️ RESOLVE TICKER</span>';
                } else if (qText.includes("get_stock_financials")) {
                    badge = '<span style="font-size:10px; font-weight:700; padding:2px 6px; border-radius:4px; background:rgba(0, 230, 118, 0.15); color:#00e676;">📊 AUDITED FINANCIALS</span>';
                } else if (qText.includes("get_quality_scorecard")) {
                    badge = '<span style="font-size:10px; font-weight:700; padding:2px 6px; border-radius:4px; background:rgba(187, 134, 252, 0.15); color:#bb86fc;">📈 QUALITY SCORECARD</span>';
                }

                return `
                <div style="font-size: 13px; padding: 10px; background: rgba(255,255,255,0.01); border-radius: 4px; border: 1px solid rgba(255,255,255,0.04); margin-bottom: 8px;">
                    <div style="font-weight:600; font-family: monospace; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:6px;">
                        <div style="display:flex; align-items:center; gap:8px;">
                            ${badge}
                            <span style="color:var(--text-primary); font-size:12px;">${escapeHtml(qText)}</span>
                        </div>
                        ${s.sources && s.sources.length > 0 ? `<span style="font-size:11px; color:var(--text-muted); font-weight:normal;">(${s.sources.length} sources)</span>` : ''}
                    </div>
                    <div class="text-muted" style="margin-top: 6px; font-size: 12px; line-height: 1.4; padding-left: 8px; border-left: 2px solid rgba(255,255,255,0.05); white-space:pre-wrap;">
                        <strong>Findings:</strong> ${escapeHtml(s.findings || 'No text recorded.')}
                    </div>
                    ${s.sources && s.sources.length > 0 ? `
                        <div style="margin-top: 6px; display:flex; gap: 6px; flex-wrap:wrap; padding-left:8px;">
                            ${s.sources.slice(0, 3).map(url => `<span style="font-size: 10px; color: var(--text-muted); font-family: monospace; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 250px;">🔗 ${escapeHtml(url)}</span>`).join('')}
                            ${s.sources.length > 3 ? `<span style="font-size: 10px; color: var(--text-muted);">+${s.sources.length - 3} more</span>` : ''}
                        </div>
                    ` : ''}
                </div>
            `;
            }).join('');

            return `
                <div style="margin-bottom: 16px;">
                    <div style="font-size: 11px; font-weight: 700; color: var(--text-secondary); text-transform: uppercase; margin-bottom: 8px; border-left: 3px solid var(--accent-cyan); padding-left: 8px; letter-spacing:0.5px;">
                        ${escapeHtml(phaseName)} (${phaseSearches.length} tool calls / searches)
                    </div>
                    <div style="padding-left: 8px; border-left: 1px dashed rgba(255,255,255,0.03); margin-left: 4px;">
                        ${phaseSearchesHtml}
                    </div>
                </div>
            `;
        }).join('');
    }

    // Renders the overall discovery info
    const totalSearches = res.total_search_count || (res.searches_performed ? res.searches_performed.length : 0);
    const phasesCompleted = res.phases_completed || 5;

    resultsArea.innerHTML = `
        <div class="fade-in" style="display: flex; flex-direction: column; gap: 24px;">
            <div class="card" style="padding: 24px; border: 1px solid rgba(138, 180, 248, 0.15); background: linear-gradient(135deg, rgba(138,180,248,0.02) 0%, rgba(0,0,0,0) 100%);">
                <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap: 12px; margin-bottom:6px;">
                    <h3 style="margin:0; color: var(--accent-cyan); font-weight:700;">Discovery Results</h3>
                    <button class="btn btn-secondary btn-sm" onclick="closeDiscoveryResult()" style="display:flex; align-items:center; gap: 6px; padding: 5px 12px; border-radius: 6px; font-size: 12px; font-weight: 600; cursor: pointer;">
                        ✖ Close Report
                    </button>
                </div>
                <div style="display:flex; gap: 12px; margin-bottom: 12px; font-size: 11px; color: var(--text-muted); flex-wrap:wrap; align-items:center;">
                    <span>📂 Phases: <strong>${phasesCompleted}/5</strong></span>
                    <span>•</span>
                    <span>🛠️ Total Tools & Searches: <strong>${totalSearches}</strong></span>
                    <span>•</span>
                    <span>📅 Created: <strong>${meta.created_at ? new Date(meta.created_at).toLocaleDateString('en-IN', {day:'2-digit', month:'short', year:'numeric'}) : '—'}</strong></span>
                </div>
                <p style="font-size: 14px; line-height: 1.5; margin:0;" class="text-secondary">
                    ${escapeHtml(res.analysis_summary || 'Analysis complete. Key hypotheses have been synthesized.')}
                </p>
                ${res.limitations && res.limitations.length > 0 ? `
                    <div style="margin-top: 16px; padding: 12px 16px; background: rgba(255,255,255,0.02); border-radius: var(--border-radius); border-left: 3px solid var(--text-muted);">
                        <strong style="font-size:11px; text-transform:uppercase; color: var(--text-secondary);">Research Gaps / Limitations:</strong>
                        <ul style="margin: 6px 0 0 16px; padding:0; font-size:12px;" class="text-muted">
                            ${res.limitations.map(l => `<li>${escapeHtml(l)}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
            </div>

            <!-- Searched Log Details -->
            ${groupedSearchesHtml ? `
                <div class="card" style="padding: 16px; border: 1px solid rgba(255,255,255,0.02); background: rgba(0,0,0,0.1);">
                    <summary style="font-size: 12px; font-weight:600; cursor: pointer; color: var(--text-secondary); display:flex; align-items:center; gap: 6px; user-select:none;" onclick="toggleSearchAudit(this)">
                        <span>▶</span> Click to audit AI Tool & Search Trail (${totalSearches} tools & searches executed)
                    </summary>
                    <div class="search-audit-details" style="display:none; margin-top: 12px; display: flex; flex-direction: column; gap: 8px;">
                        ${groupedSearchesHtml}
                    </div>
                </div>
            ` : ''}

            <!-- Candidates list -->
            <div style="display: flex; flex-direction: column; gap: 24px;">
                ${candidatesHtml}
            </div>
            
            <div class="text-muted" style="font-size:12px; text-align:center; margin-top: 12px;">
                ⚠️ ${escapeHtml(res.disclaimer)}
            </div>
        </div>
    `;

    resultsArea.scrollIntoView({ behavior: 'smooth' });
}

/**
 * Handles Tab Switching in Candidate Cards
 */
function switchCandidateTab(cardId, tabName) {
    const card = document.getElementById(cardId);
    if (!card) return;

    // Switch active button class
    const buttons = card.querySelectorAll('.tab-btn');
    buttons.forEach(btn => {
        const isMatched = (tabName === 'reasoning' && btn.textContent.includes('Thesis')) ||
                          (tabName === 'self-critique' && btn.textContent.includes('Fail')) ||
                          (tabName === 'disproving' && btn.textContent.includes('Signals'));
        btn.classList.toggle('active', isMatched);
    });

    // Switch visible tab panel
    const panels = card.querySelectorAll('.tab-content');
    panels.forEach(p => {
        const isMatched = p.classList.contains(tabName);
        p.style.display = isMatched ? 'block' : 'none';
    });
}

function toggleSearchAudit(summaryEl) {
    const details = summaryEl.nextElementSibling;
    const arrow = summaryEl.querySelector('span');
    if (!details) return;

    const isHidden = details.style.display === 'none' || !details.style.display;
    details.style.display = isHidden ? 'flex' : 'none';
    if (arrow) arrow.textContent = isHidden ? '▼' : '▶';
}

/**
 * Navigate to Analyzer: direct if ticker exists, search name fallback if null
 */
function analyzeCandidate(companyName, ticker) {
    if (ticker) {
        navigateTo('analyzer', ticker);
    } else {
        // Redirect to analyzer page and pass search/ query format
        showToast(`Searching for '${companyName}' in StockLens...`, 'info');
        navigateTo('analyzer', 'search/' + encodeURIComponent(companyName));
    }
}


/* ===========================================================================
   Master Cross-Strategy Synthesis Frontend Functions
   =========================================================================== */

function toggleSynthesisPanel() {
    const panel = document.getElementById('synthesis-selection-panel');
    if (!panel) return;
    const isHidden = panel.style.display === 'none' || !panel.style.display;
    panel.style.display = isHidden ? 'block' : 'none';
    if (isHidden) {
        populateSynthesisCheckboxes();
    }
}

function populateSynthesisCheckboxes() {
    const grid = document.getElementById('synthesis-checkbox-grid');
    if (!grid) return;

    if (!_savedDiscoveries || _savedDiscoveries.length === 0) {
        grid.innerHTML = `<div style="grid-column: 1/-1; padding: 16px; text-align: center;" class="text-muted">No discovery results available in history yet.</div>`;
        updateSynthesisSelectionCount();
        return;
    }

    grid.innerHTML = _savedDiscoveries.map(d => {
        const dateStr = d.created_at ? new Date(d.created_at).toLocaleDateString('en-IN', {
            day: '2-digit', month: 'short', year: 'numeric'
        }) : '—';

        return `
            <label class="synthesis-checkbox-card" style="display: flex; align-items: flex-start; gap: 10px; padding: 10px; background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); border-radius: 6px; cursor: pointer; transition: background 0.2s;" onchange="updateSynthesisSelectionCount()">
                <input type="checkbox" class="synthesis-disc-checkbox" value="${d.id}" style="margin-top: 3px; accent-color: #ffd700; cursor: pointer;">
                <div style="flex: 1; min-width: 0;">
                    <div style="font-weight: 600; font-size: 13px; color: var(--text-primary); text-overflow: ellipsis; overflow: hidden; white-space: nowrap;">
                        ${escapeHtml(d.strategy_name)}
                    </div>
                    <div style="font-size: 11px; color: var(--text-muted); margin-top: 2px;">
                        ${dateStr} · <strong>${d.candidate_count}</strong> candidates
                    </div>
                </div>
            </label>
        `;
    }).join('');

    updateSynthesisSelectionCount();
}

function updateSynthesisSelectionCount() {
    const checkboxes = document.querySelectorAll('.synthesis-disc-checkbox');
    const checked = Array.from(checkboxes).filter(cb => cb.checked);
    const countEl = document.getElementById('synthesis-selection-count');
    const runBtn = document.getElementById('synthesis-run-btn');

    const total = checkboxes.length;
    const selectedCount = checked.length;

    if (countEl) {
        countEl.textContent = `Selected: ${selectedCount}/${total} (Min 7 required)`;
        countEl.style.color = selectedCount >= 7 ? '#00d4ff' : '#ff7b72';
    }

    if (runBtn) {
        runBtn.disabled = selectedCount < 7 || _synthesisRunning;
        runBtn.style.opacity = (selectedCount >= 7 && !_synthesisRunning) ? '1' : '0.5';
    }
}

function toggleAllSynthesisSelections(selectState) {
    const checkboxes = document.querySelectorAll('.synthesis-disc-checkbox');
    checkboxes.forEach(cb => { cb.checked = selectState; });
    updateSynthesisSelectionCount();
}

async function startSynthesis() {
    if (_synthesisRunning) return;

    const checkboxes = document.querySelectorAll('.synthesis-disc-checkbox');
    const selectedIds = Array.from(checkboxes).filter(cb => cb.checked).map(cb => cb.value);

    if (selectedIds.length < 7) {
        showToast('Please select at least 7 strategy results for Master Synthesis.', 'warning');
        return;
    }

    _synthesisRunning = true;
    _synthesisAbortController = new AbortController();

    const runBtn = document.getElementById('synthesis-run-btn');
    const stopBtn = document.getElementById('synthesis-stop-btn');
    const progressCard = document.getElementById('synthesis-progress-card');
    const logArea = document.getElementById('synthesis-search-log');
    const resultsArea = document.getElementById('synthesis-results-area');

    if (runBtn) runBtn.disabled = true;
    if (stopBtn) stopBtn.style.display = 'inline-flex';
    if (progressCard) progressCard.style.display = 'block';
    if (logArea) logArea.innerHTML = '<div style="color: #ffd700;">🚀 Initiating Master Synthesis pipeline...</div>';
    if (resultsArea) resultsArea.innerHTML = '';

    try {
        const response = await fetch('/api/synthesis/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ discovery_ids: selectedIds }),
            signal: _synthesisAbortController.signal
        });

        if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.detail || 'Synthesis failed to start');
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop(); // Keep last partial line

            for (const line of lines) {
                if (!line.trim()) continue;
                try {
                    const msg = JSON.parse(line);
                    if (msg.type === 'progress') {
                        if (logArea) {
                            const entry = document.createElement('div');
                            entry.textContent = `[${new Date().toLocaleTimeString()}] ${msg.message}`;
                            logArea.appendChild(entry);
                            logArea.scrollTop = logArea.scrollHeight;
                        }
                    } else if (msg.type === 'result') {
                        showToast('Master Synthesis complete!', 'success');
                        renderSynthesisResult(msg.data);
                        await loadSynthesisHistory();
                    } else if (msg.type === 'cancelled') {
                        showToast('Master Synthesis stopped.', 'info');
                    } else if (msg.type === 'error') {
                        showToast('Synthesis Error: ' + msg.message, 'error');
                    }
                } catch (_) {}
            }
        }
    } catch (err) {
        if (err.name !== 'AbortError') {
            showToast('Synthesis failed: ' + err.message, 'error');
        }
    } finally {
        _synthesisRunning = false;
        if (runBtn) {
            runBtn.disabled = false;
            runBtn.style.opacity = '1';
        }
        if (stopBtn) stopBtn.style.display = 'none';
        if (progressCard) progressCard.style.display = 'none';
        updateSynthesisSelectionCount();
    }
}

async function stopSynthesis() {
    if (!_synthesisRunning) return;
    showToast('Stopping Master Synthesis...', 'info');

    if (_synthesisAbortController) {
        _synthesisAbortController.abort();
        _synthesisAbortController = null;
    }

    try {
        await fetch('/api/synthesis/stop', { method: 'POST' });
    } catch (_) {}

    _synthesisRunning = false;
    const stopBtn = document.getElementById('synthesis-stop-btn');
    const progressCard = document.getElementById('synthesis-progress-card');
    if (stopBtn) stopBtn.style.display = 'none';
    if (progressCard) progressCard.style.display = 'none';
    updateSynthesisSelectionCount();
}

let _activeSynthesisMeta = null;

function renderSynthesisResult(meta) {
    const resultsArea = document.getElementById('synthesis-results-area');
    if (!resultsArea || !meta || !meta.result) return;

    _activeSynthesisMeta = meta;

    const res = meta.result;
    const picks = res.ultimate_picks || [];

    const picksHtml = picks.map((p, idx) => {
        const cardId = `synth-pick-card-${idx}`;
        const convictionClass = p.composite_conviction === 'Very High' ? 'badge-high' : (p.composite_conviction === 'High' ? 'badge-high' : 'badge-medium');
        const tickerDisplay = p.ticker ? `<span class="ticker-badge" style="background: rgba(255, 215, 0, 0.15); color: #ffd700; font-weight:700; padding: 3px 8px; border-radius: 4px; font-size:12px; margin-left: 8px;">${escapeHtml(p.ticker)}</span>` : '';
        const convergenceBadge = p.convergence_count > 1 
            ? `<span style="background: rgba(255,140,0,0.15); border: 1px solid rgba(255,140,0,0.4); color: #ff8c00; font-weight:700; padding: 3px 8px; border-radius: 4px; font-size: 11px;">🔥 Found in ${p.convergence_count} Strategies</span>`
            : `<span style="background: rgba(255,255,255,0.05); color: var(--text-muted); padding: 3px 8px; border-radius: 4px; font-size: 11px;">1 Strategy</span>`;

        // Visual Catalyst Timeline rendering (handles both structured window objects and legacy strings)
        let catalystsHtml = '';
        if (p.key_catalysts && p.key_catalysts.length > 0) {
            catalystsHtml = `<div class="catalyst-timeline-container">` + p.key_catalysts.map(c => {
                if (typeof c === 'object' && c !== null) {
                    const win = c.window || '0-6m';
                    let winClass = 'catalyst-window-near';
                    let badgeClass = 'badge-near';
                    let winLabel = '⚡ Near-Term (0-6m)';
                    if (win === '6-18m') {
                        winClass = 'catalyst-window-mid';
                        badgeClass = 'badge-mid';
                        winLabel = '📅 Mid-Term (6-18m)';
                    } else if (win === '18m+') {
                        winClass = 'catalyst-window-long';
                        badgeClass = 'badge-long';
                        winLabel = '🔭 Long-Term (18m+)';
                    }
                    return `
                        <div class="catalyst-timeline-item ${winClass}">
                            <div>
                                <span class="catalyst-window-badge ${badgeClass}">${winLabel}</span>
                                <strong style="color: var(--text-primary);">${escapeHtml(c.catalyst || '')}</strong>
                            </div>
                            ${c.reason ? `<div style="font-size: 11px; color: var(--text-muted); margin-top: 4px; padding-left: 2px;">• ${escapeHtml(c.reason)}</div>` : ''}
                        </div>
                    `;
                } else {
                    return `
                        <div class="catalyst-timeline-item">
                            <span class="catalyst-window-badge badge-untimed">📌 Untimed</span>
                            <span>${escapeHtml(String(c))}</span>
                        </div>
                    `;
                }
            }).join('') + `</div>`;
        } else {
            catalystsHtml = '<div class="text-muted" style="font-size:12px;">No specific catalysts specified.</div>';
        }

        const risksList = p.key_risks && p.key_risks.length > 0
            ? p.key_risks.map(r => `<li>${escapeHtml(r)}</li>`).join('')
            : '<li class="text-muted">No key risks specified.</li>';

        const actionList = p.action_items && p.action_items.length > 0
            ? p.action_items.map(a => `<li>${escapeHtml(a)}</li>`).join('')
            : '<li class="text-muted">No action items specified.</li>';

        const strategySnapshotsHtml = p.per_strategy_detail && p.per_strategy_detail.length > 0
            ? p.per_strategy_detail.map(sd => `
                <div style="background: rgba(255,255,255,0.02); border-left: 2px solid var(--accent-cyan); padding: 8px 12px; margin-bottom: 6px; font-size: 12px;">
                    <div style="font-weight:600; color: var(--text-secondary); display:flex; justify-content:space-between;">
                        <span>${escapeHtml(sd.strategy_name)}</span>
                        <span style="font-size:10px; text-transform:uppercase;" class="text-muted">Confidence: ${escapeHtml(sd.confidence || 'medium')}</span>
                    </div>
                    <div style="margin-top: 4px; color: var(--text-muted);">${escapeHtml(sd.key_takeaway || 'Selected candidate.')}</div>
                </div>
            `).join('')
            : '';

        const safeCompanyName = escapeHtml(p.company_name).replace(/'/g, "\\'");

        return `
            <div class="card candidate-card" id="${cardId}" style="padding: 24px; border: 1px solid rgba(255,215,0,0.2); display: flex; flex-direction: column; gap: 20px; background: linear-gradient(135deg, rgba(255,215,0,0.02) 0%, rgba(0,0,0,0) 100%);">
                <!-- Header -->
                <div style="display:flex; justify-content: space-between; align-items: flex-start; gap: 16px; border-bottom: 1px solid rgba(255,255,255,0.05); padding-bottom: 16px;">
                    <div>
                        <div style="display:flex; align-items:center; gap: 8px; flex-wrap: wrap;">
                            <span style="background: #ffd700; color: #000; font-weight: 800; padding: 2px 8px; border-radius: 4px; font-size: 13px;">#${p.rank || idx+1}</span>
                            <h3 style="margin:0; font-size: 20px; font-weight:700; color: var(--text-primary);">${escapeHtml(p.company_name)}</h3>
                            ${tickerDisplay}
                            ${convergenceBadge}
                        </div>
                        <div style="font-size: 12px; margin-top: 6px; color: var(--text-muted); display:flex; gap: 6px; flex-wrap:wrap;">
                            <span>Strategies: <strong>${(p.strategies_found_in || []).map(s => escapeHtml(s)).join(', ')}</strong></span>
                        </div>
                    </div>
                    <span class="badge ${convictionClass}">${escapeHtml(p.composite_conviction).toUpperCase()} CONVICTION</span>
                </div>

                <!-- Unified Thesis -->
                <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05); border-radius: var(--border-radius); padding: 16px;">
                    <strong style="color: #ffd700; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; display: block; margin-bottom: 6px;">💡 Master Unified Thesis</strong>
                    <p style="margin: 0; font-size: 14px; line-height: 1.6; color: var(--text-secondary);">${escapeHtml(p.unified_thesis).replace(/\n/g, '<br>')}</p>
                </div>

                <!-- Contrarian View -->
                ${p.contrarian_view ? `
                    <div style="background: rgba(255, 123, 114, 0.03); border: 1px solid rgba(255, 123, 114, 0.15); border-radius: var(--border-radius); padding: 14px 16px;">
                        <strong style="color: #ff7b72; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; display: block; margin-bottom: 4px;">⚡ Contrarian View (What Could Go Wrong)</strong>
                        <p style="margin: 0; font-size: 13px; line-height: 1.4; color: var(--text-secondary); font-style: italic;">${escapeHtml(p.contrarian_view)}</p>
                    </div>
                ` : ''}

                <!-- Catalysts & Risks Grid -->
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
                    <div style="background: rgba(255,255,255,0.01); border: 1px solid rgba(255,255,255,0.04); border-radius: var(--border-radius); padding: 14px;">
                        <strong style="font-size: 12px; color: var(--accent-cyan); text-transform: uppercase; display: block; margin-bottom: 8px;">🚀 Catalyst Timeline</strong>
                        ${catalystsHtml}
                    </div>
                    <div style="background: rgba(255,255,255,0.01); border: 1px solid rgba(255,255,255,0.04); border-radius: var(--border-radius); padding: 14px;">
                        <strong style="font-size: 12px; color: #ff7b72; text-transform: uppercase; display: block; margin-bottom: 8px;">⚠️ Cross-Validated Risks</strong>
                        <ul style="margin: 0 0 0 16px; padding: 0; font-size: 13px;" class="text-muted">${risksList}</ul>
                    </div>
                </div>

                <!-- Per-Strategy Breakdown (Collapsible) -->
                ${strategySnapshotsHtml ? `
                    <details style="background: rgba(0,0,0,0.1); border: 1px solid rgba(255,255,255,0.03); border-radius: var(--border-radius); padding: 10px 14px;">
                        <summary style="font-size: 12px; font-weight: 600; cursor: pointer; color: var(--text-secondary); user-select: none;">
                            🔍 View Breakdown across ${(p.strategies_found_in || []).length} Individual Strategies
                        </summary>
                        <div style="margin-top: 10px;">${strategySnapshotsHtml}</div>
                    </details>
                ` : ''}

                <!-- Action Footer -->
                <div style="display:flex; justify-content: space-between; align-items:center; flex-wrap:wrap; gap: 12px; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 16px;">
                    <div style="font-size:12px;" class="text-muted">
                        <strong>StockLens Verification:</strong> ${actionList}
                    </div>
                    <button class="btn btn-primary btn-sm" onclick="analyzeCandidate('${escapeHtml(p.company_name)}', ${p.ticker ? `'${escapeHtml(p.ticker)}'` : 'null'})" style="display:flex; align-items:center; gap: 6px; background: linear-gradient(135deg, var(--accent-cyan), #0077ff); border: none; color: #fff; font-weight:600;">
                        🔍 Analyze in StockLens →
                    </button>
                </div>
            </div>
        `;
    }).join('');

    const honorableMentionsHtml = res.honorable_mentions && res.honorable_mentions.length > 0
        ? `
            <div style="margin-top: 10px; padding: 18px; background: rgba(255,255,255,0.01); border: 1px dashed rgba(255,255,255,0.08); border-radius: var(--border-radius);">
                <h4 style="margin-top:0; margin-bottom: 12px; color: var(--text-secondary); font-size:14px;">🌟 Honorable Mentions (Watchlist Candidates)</h4>
                <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 10px;">
                    ${res.honorable_mentions.map(hm => `
                        <div style="padding: 10px; background: rgba(0,0,0,0.2); border-radius: 6px; border: 1px solid rgba(255,255,255,0.03);">
                            <div style="font-weight:600; color: var(--text-primary); font-size:13px;">${escapeHtml(hm.company_name)} ${hm.ticker ? `<span class="text-muted" style="font-size:11px;">(${escapeHtml(hm.ticker)})</span>` : ''}</div>
                            <div style="font-size:11px; color: var(--accent-cyan); margin-top:2px;">Strategy: ${escapeHtml(hm.strategy_name || 'N/A')}</div>
                            <div style="font-size:12px; color: var(--text-muted); margin-top:4px;">${escapeHtml(hm.reason_for_watching || '')}</div>
                        </div>
                    `).join('')}
                </div>
            </div>
        ` : '';

    resultsArea.innerHTML = `
        <div class="fade-in" style="display: flex; flex-direction: column; gap: 20px;">
            <div class="card" style="padding: 24px; border: 1px solid rgba(255, 215, 0, 0.25); background: linear-gradient(135deg, rgba(255,215,0,0.03) 0%, rgba(0,0,0,0) 100%);">
                <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap: 12px; margin-bottom:12px;">
                    <div>
                        <h2 style="margin:0; color: #ffd700; font-size: 22px; font-weight:700;">🏆 Ultimate Portfolio Picks</h2>
                        <span class="text-muted" style="font-size:12px;">Synthesized across ${res.total_strategies_used} strategies (${res.total_candidates_analyzed} findings)</span>
                    </div>
                    <div style="display:flex; gap: 8px; align-items:center;">
                        <button class="btn btn-secondary btn-sm no-print" onclick="exportSynthesisPDF()" style="display:flex; align-items:center; gap: 6px; padding: 6px 14px; border-radius: 6px; font-size: 12px; font-weight: 600; cursor: pointer; border-color: rgba(255,215,0,0.4); color: #ffd700;">
                            📄 Download PDF
                        </button>
                        <button class="btn btn-secondary btn-sm no-print" onclick="closeSynthesisResult()" style="display:flex; align-items:center; gap: 6px; padding: 6px 14px; border-radius: 6px; font-size: 12px; font-weight: 600; cursor: pointer; border-color: rgba(255,255,255,0.15);">
                            ✖ Close Report
                        </button>
                    </div>
                </div>

                ${res.market_narrative ? `
                    <div style="background: rgba(255,215,0,0.03); border-left: 3px solid #ffd700; padding: 12px 16px; border-radius: var(--radius-sm); margin-bottom: 14px;">
                        <strong style="color: #ffd700; font-size: 11px; text-transform: uppercase; letter-spacing:0.5px;">🌐 Macro Market Narrative</strong>
                        <p style="margin: 6px 0 0 0; font-size: 13px; line-height: 1.5; color: var(--text-secondary);">${escapeHtml(res.market_narrative)}</p>
                    </div>
                ` : ''}

                ${res.portfolio_considerations ? `
                    <div style="background: rgba(0, 212, 255, 0.03); border-left: 3px solid var(--accent-cyan); padding: 12px 16px; border-radius: var(--radius-sm); margin-bottom: 14px;">
                        <strong style="color: var(--accent-cyan); font-size: 11px; text-transform: uppercase; letter-spacing:0.5px;">📊 Portfolio & Sector Balance</strong>
                        <p style="margin: 6px 0 0 0; font-size: 13px; line-height: 1.5; color: var(--text-secondary);">${escapeHtml(res.portfolio_considerations)}</p>
                    </div>
                ` : ''}
            </div>

            <div style="display: flex; flex-direction: column; gap: 20px;">
                ${picksHtml}
            </div>

            ${honorableMentionsHtml}

            <!-- Report-Level Master Verification Chat & Comparative Thesis Studio -->
            <div class="card" style="padding: 24px; border: 1px solid rgba(255, 215, 0, 0.3); background: linear-gradient(135deg, rgba(10,15,26,0.95) 0%, rgba(0,0,0,0) 100%);">
                <div style="display:flex; justify-content:space-between; align-items:center; border-bottom: 1px solid rgba(255,215,0,0.2); padding-bottom: 12px; margin-bottom: 16px;">
                    <div>
                        <h3 style="margin:0; color: #ffd700; font-size: 18px; font-weight:700; display:flex; align-items:center; gap: 8px;">
                            💬 Master Synthesis Verification Chat & Thesis Studio
                        </h3>
                        <span class="text-muted" style="font-size:12px;">Compare all ${picks.length} ultimate picks, stress-test your pick against all other options, and generate a battle-tested thesis.</span>
                    </div>
                </div>

                <div id="master-synth-chat-container-${meta.id}"></div>
            </div>
        </div>
    `;

    // Automatically load report-level chat session
    loadMasterSynthesisChat(meta.id, picks, res.honorable_mentions || []);

    resultsArea.scrollIntoView({ behavior: 'smooth' });
}

async function loadSynthesisHistory() {
    const list = document.getElementById('synthesis-history-list');
    if (!list) return;

    try {
        const data = await apiFetch('/synthesis/saved');
        _savedSyntheses = data;

        if (data.length === 0) {
            list.innerHTML = `<div style="grid-column: 1/-1; padding: 16px; text-align: center;" class="text-muted">No synthesis runs saved yet. Select 7+ strategies above to run Master Synthesis.</div>`;
            return;
        }

        list.innerHTML = data.map(s => {
            const dateStr = s.created_at ? new Date(s.created_at).toLocaleDateString('en-IN', {
                day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit'
            }) : '—';

            return `
                <div class="card history-card" style="padding: 14px; border: 1px solid rgba(255,215,0,0.15); display: flex; flex-direction: column; justify-content: space-between;">
                    <div>
                        <div style="font-weight: 700; color: #ffd700; font-size: 14px;">🏆 Master Synthesis</div>
                        <div style="font-size: 12px; color: var(--text-secondary); margin-top: 4px;">
                            Top Pick: <strong>${escapeHtml(s.top_pick_name)}</strong>
                        </div>
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 8px; margin-top: 10px; font-size: 11px;" class="text-muted">
                        <span>${dateStr} · <strong>${s.pick_count}</strong> picks (${s.strategies_used} strats)</span>
                        <div style="display: flex; gap: 6px;">
                            <button class="btn btn-secondary btn-sm" onclick="loadSavedSynthesis('${s.id}')">View</button>
                            <button class="btn btn-danger btn-sm" onclick="deleteSavedSynthesis('${s.id}', event)">Delete</button>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    } catch (err) {
        list.innerHTML = `<div style="grid-column: 1/-1; color: var(--color-danger);">Failed to load synthesis history: ${escapeHtml(err.message)}</div>`;
    }
}

async function loadSavedSynthesis(id) {
    const resultsArea = document.getElementById('synthesis-results-area');
    if (resultsArea) {
        resultsArea.innerHTML = getLoadingHTML('Loading saved synthesis...');
        resultsArea.scrollIntoView({ behavior: 'smooth' });
    }

    try {
        const data = await apiFetch(`/synthesis/saved/${id}`);
        renderSynthesisResult(data);
    } catch (err) {
        showToast('Failed to load synthesis: ' + err.message, 'error');
        if (resultsArea) resultsArea.innerHTML = '';
    }
}

async function deleteSavedSynthesis(id, event) {
    if (event) event.stopPropagation();
    if (!confirm('Are you sure you want to delete this synthesis run from history?')) return;

    try {
        await apiFetch(`/synthesis/saved/${id}`, { method: 'DELETE' });
        showToast('Synthesis run deleted.', 'success');
        await loadSynthesisHistory();
    } catch (err) {
        showToast('Delete failed: ' + err.message, 'error');
    }
}

function closeSynthesisResult() {
    const resultsArea = document.getElementById('synthesis-results-area');
    if (resultsArea) {
        resultsArea.innerHTML = '';
    }
}

function closeDiscoveryResult() {
    const resultsArea = document.getElementById('discovery-results-area');
    if (resultsArea) {
        resultsArea.innerHTML = '';
    }
    _activeDiscovery = null;
}

// ---------------------------------------------------------------------------
// Report-Level Master Verification Chat & Thesis Studio (UI Helpers)
// ---------------------------------------------------------------------------

const _masterGeneratedTheses = {};

async function loadMasterSynthesisChat(synthesisId, picks, honorableMentions = []) {
    const containerId = `master-synth-chat-container-${synthesisId}`;
    const container = document.getElementById(containerId);
    if (!container) return;

    container.innerHTML = getLoadingHTML('Loading Master Verification Studio session...');

    try {
        const session = await apiFetch(`/synthesis/chat/${synthesisId}`);
        renderMasterSynthesisChatPanel(container, synthesisId, picks, honorableMentions, session);
    } catch (err) {
        showToast('Failed to load chat session: ' + err.message, 'error');
        container.innerHTML = `<div class="text-danger">Failed to load chat: ${escapeHtml(err.message)}</div>`;
    }
}

function renderMasterSynthesisChatPanel(container, synthesisId, picks, honorableMentions = [], session) {
    const messages = (session && session.messages) ? session.messages : [];
    const generatedThesis = session ? session.generated_thesis : null;

    let msgsHtml = '';
    if (messages.length === 0) {
        const picksListStr = picks.map(p => `• Rank #${p.rank}: ${p.company_name} (${p.ticker || 'N/A'})`).join('\n');
        const hmsListStr = (honorableMentions && honorableMentions.length > 0)
            ? '\n🌟 Watchlist Candidates:\n' + honorableMentions.map(h => `• ${h.company_name} (${h.ticker || 'N/A'}) — ${h.strategy_name}`).join('\n')
            : '';
        msgsHtml = `
            <div class="synthesis-chat-msg synthesis-chat-msg-assistant">
                👋 <strong>CIO & Devils Advocate AI:</strong> I have full context of all ${picks.length} ultimate picks and watchlist candidates in this report:<br>
                <div style="font-size: 11px; margin: 6px 0; color: var(--text-secondary); white-space: pre-wrap;">${escapeHtml(picksListStr + hmsListStr)}</div>
                Explain your investment reasoning or ask me to compare options (e.g. <em>"Why pick #1 over #3?"</em> or <em>"Should I consider an honorable mention like ${honorableMentions[0]?.company_name || 'candidate'}?"</em>). I will stress-test your choice factually across all candidates.
            </div>
        `;
    } else {
        msgsHtml = messages.map(m => {
            const roleClass = m.role === 'user' ? 'synthesis-chat-msg-user' : 'synthesis-chat-msg-assistant';
            const roleLabel = m.role === 'user' ? 'You' : 'CIO & Devils Advocate AI';
            return `
                <div class="synthesis-chat-msg ${roleClass}">
                    <div style="font-size: 10px; opacity: 0.7; margin-bottom: 2px;">${roleLabel} • ${escapeHtml(m.timestamp || '')}</div>
                    <div>${escapeHtml(m.content).replace(/\n/g, '<br>')}</div>
                </div>
            `;
        }).join('');
    }

    // Build select options for thesis target stock (ultimate picks + honorable mentions)
    const hmOptionsHtml = (honorableMentions && honorableMentions.length > 0) ? honorableMentions.map(hm => `
        <option value="${escapeHtml(hm.company_name)}" style="background: #0f172a; color: #ffd700; padding: 8px;">🌟 Watchlist: ${escapeHtml(hm.company_name)} (${hm.ticker || 'N/A'})</option>
    `).join('') : '';

    const pickOptionsHtml = picks.map(p => `
        <option value="${escapeHtml(p.company_name)}" style="background: #0f172a; color: #f8fafc; padding: 8px;">Rank #${p.rank}: ${escapeHtml(p.company_name)} (${p.ticker || 'N/A'})</option>
    `).join('') + hmOptionsHtml;

    let thesisPreviewHtml = '';
    if (generatedThesis) {
        _masterGeneratedTheses[synthesisId] = generatedThesis;
        thesisPreviewHtml = renderMasterGeneratedThesisPreviewHTML(synthesisId, generatedThesis);
    }

    container.innerHTML = `
        <div class="synthesis-chat-panel fade-in" style="margin-top: 0;">
            <div class="synthesis-chat-messages" id="master-synth-chat-msgs-${synthesisId}">
                ${msgsHtml}
            </div>

            <div id="master-synth-chat-status-${synthesisId}" class="synthesis-chat-msg-status" style="display:none;"></div>

            <div class="chat-input-area" style="display: flex; gap: 8px; margin-top: 4px;">
                <input type="text" id="master-synth-chat-input-${synthesisId}" class="form-control" placeholder="Ask to compare stocks or explain your pick reasoning..." onkeypress="if(event.key==='Enter') sendMasterSynthesisChatMessage('${synthesisId}')" style="flex:1; font-size: 13px; background: rgba(0,0,0,0.3); border-color: rgba(255,215,0,0.2);">
                <button class="btn btn-primary btn-sm" id="master-synth-chat-send-${synthesisId}" onclick="sendMasterSynthesisChatMessage('${synthesisId}')" style="padding: 6px 16px; font-weight:600;">Send</button>
            </div>

            <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid rgba(255,255,255,0.05); padding-top: 12px; margin-top: 6px; flex-wrap: wrap; gap: 10px;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span class="text-muted" style="font-size: 11px;">Finalize Thesis for:</span>
                    <select id="master-synth-target-stock-${synthesisId}" class="form-control form-control-sm" style="font-size: 12px; width: auto; background: #0f172a; border: 1px solid rgba(255, 215, 0, 0.4); color: #ffd700; font-weight: 600; padding: 5px 12px; border-radius: 6px; cursor: pointer; outline: none;">
                        ${pickOptionsHtml}
                    </select>
                </div>
                <button class="btn btn-secondary btn-sm" id="master-synth-genbtn-${synthesisId}" onclick="generateMasterSynthesisThesis('${synthesisId}')" style="border-color: rgba(0, 212, 170, 0.4); color: var(--color-success); font-weight:600; font-size: 12px; padding: 6px 14px;">
                    📝 Generate Comparative Thesis & Sell Checklist
                </button>
            </div>

            <div id="master-synth-thesis-preview-${synthesisId}">
                ${thesisPreviewHtml}
            </div>
        </div>
    `;

    const msgsDiv = document.getElementById(`master-synth-chat-msgs-${synthesisId}`);
    if (msgsDiv) msgsDiv.scrollTop = msgsDiv.scrollHeight;
}

async function sendMasterSynthesisChatMessage(synthesisId) {
    const inputEl = document.getElementById(`master-synth-chat-input-${synthesisId}`);
    const msgsDiv = document.getElementById(`master-synth-chat-msgs-${synthesisId}`);
    const statusDiv = document.getElementById(`master-synth-chat-status-${synthesisId}`);
    const sendBtn = document.getElementById(`master-synth-chat-send-${synthesisId}`);

    if (!inputEl || !inputEl.value.trim()) return;

    const userText = inputEl.value.trim();
    inputEl.value = '';

    const userMsgHtml = `
        <div class="synthesis-chat-msg synthesis-chat-msg-user">
            <div style="font-size: 10px; opacity: 0.7; margin-bottom: 2px;">You • Now</div>
            <div>${escapeHtml(userText).replace(/\n/g, '<br>')}</div>
        </div>
    `;
    msgsDiv.insertAdjacentHTML('beforeend', userMsgHtml);
    msgsDiv.scrollTop = msgsDiv.scrollHeight;

    inputEl.disabled = true;
    if (sendBtn) sendBtn.disabled = true;
    if (statusDiv) {
        statusDiv.style.display = 'block';
        statusDiv.textContent = '🤖 CIO is analyzing reasoning against all report candidates...';
    }

    try {
        const resp = await fetch('/api/synthesis/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                synthesis_id: synthesisId,
                user_message: userText,
                action: 'chat'
            })
        });

        if (!resp.ok) throw new Error(`HTTP error ${resp.status}`);

        const reader = resp.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop();

            for (const line of lines) {
                if (!line.trim()) continue;
                try {
                    const chunk = JSON.parse(line);
                    if (chunk.type === 'status' && statusDiv) {
                        statusDiv.textContent = chunk.message;
                    } else if (chunk.type === 'chat_update' && chunk.session) {
                        const lastMsg = chunk.session.messages[chunk.session.messages.length - 1];
                        if (lastMsg && lastMsg.role === 'assistant') {
                            const aiMsgHtml = `
                                <div class="synthesis-chat-msg synthesis-chat-msg-assistant">
                                    <div style="font-size: 10px; opacity: 0.7; margin-bottom: 2px;">CIO & Devils Advocate AI • ${escapeHtml(lastMsg.timestamp || '')}</div>
                                    <div>${escapeHtml(lastMsg.content).replace(/\n/g, '<br>')}</div>
                                </div>
                            `;
                            msgsDiv.insertAdjacentHTML('beforeend', aiMsgHtml);
                            msgsDiv.scrollTop = msgsDiv.scrollHeight;
                        }
                    } else if (chunk.type === 'error') {
                        showToast(chunk.message, 'error');
                    }
                } catch (e) {
                    console.error('Failed to parse chat chunk', e);
                }
            }
        }
    } catch (err) {
        showToast('Chat failed: ' + err.message, 'error');
    } finally {
        inputEl.disabled = false;
        if (sendBtn) sendBtn.disabled = false;
        if (statusDiv) statusDiv.style.display = 'none';
        inputEl.focus();
    }
}

async function generateMasterSynthesisThesis(synthesisId) {
    const statusDiv = document.getElementById(`master-synth-chat-status-${synthesisId}`);
    const previewDiv = document.getElementById(`master-synth-thesis-preview-${synthesisId}`);
    const genBtn = document.getElementById(`master-synth-genbtn-${synthesisId}`);
    const targetSelect = document.getElementById(`master-synth-target-stock-${synthesisId}`);

    const targetStock = targetSelect ? targetSelect.value : '';

    if (genBtn) genBtn.disabled = true;
    if (statusDiv) {
        statusDiv.style.display = 'block';
        statusDiv.textContent = `⚡ Synthesizing verified thesis & sell checklist for ${targetStock}...`;
    }

    try {
        const resp = await fetch('/api/synthesis/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                synthesis_id: synthesisId,
                action: 'generate_thesis',
                target_stock: targetStock
            })
        });

        if (!resp.ok) throw new Error(`HTTP error ${resp.status}`);

        const reader = resp.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop();

            for (const line of lines) {
                if (!line.trim()) continue;
                try {
                    const chunk = JSON.parse(line);
                    if (chunk.type === 'status' && statusDiv) {
                        statusDiv.textContent = chunk.message;
                    } else if (chunk.type === 'thesis_generated' && chunk.thesis) {
                        const thesisData = {
                            ...chunk.thesis,
                            target_company: chunk.company_name,
                            target_ticker: chunk.ticker,
                            target_rank: chunk.rank
                        };
                        _masterGeneratedTheses[synthesisId] = thesisData;
                        if (previewDiv) {
                            previewDiv.innerHTML = renderMasterGeneratedThesisPreviewHTML(synthesisId, thesisData);
                            previewDiv.scrollIntoView({ behavior: 'smooth' });
                        }
                        showToast(`Battle-tested thesis generated for ${chunk.company_name}!`, 'success');
                    } else if (chunk.type === 'error') {
                        showToast(chunk.message, 'error');
                    }
                } catch (e) {
                    console.error('Failed to parse thesis chunk', e);
                }
            }
        }
    } catch (err) {
        showToast('Thesis generation failed: ' + err.message, 'error');
    } finally {
        if (genBtn) genBtn.disabled = false;
        if (statusDiv) statusDiv.style.display = 'none';
    }
}

function renderMasterGeneratedThesisPreviewHTML(synthesisId, thesisData) {
    const companyName = thesisData.target_company || 'Stock Pick';
    const ticker = thesisData.target_ticker;
    const rank = thesisData.target_rank || 1;

    const checklist = thesisData.sell_checklist || [];
    const checklistRows = checklist.map(item => `
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

    const assumptionsList = (thesisData.key_assumptions || []).map(a => `<li>${escapeHtml(a)}</li>`).join('');
    const risksList = (thesisData.major_risks || []).map(r => `<li>${escapeHtml(r)}</li>`).join('');

    return `
        <div class="thesis-preview-card fade-in">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <div>
                    <strong style="color: #ffd700; font-size: 14px;">📝 Verified Investment Thesis & Sell Checklist — Rank #${rank}: ${escapeHtml(companyName)}</strong>
                    ${ticker ? `<span class="ticker-badge" style="background: rgba(255,215,0,0.15); color: #ffd700; font-size:11px; margin-left:6px;">${escapeHtml(ticker)}</span>` : ''}
                </div>
                <button class="btn btn-primary btn-sm" onclick="saveMasterGeneratedThesisToBoard('${synthesisId}')" style="background: linear-gradient(135deg, #00e676, #00ab55); border:none; color:#000; font-weight:700;">
                    💾 Save to Thesis Board
                </button>
            </div>

            <div style="margin-bottom: 10px;">
                <strong style="font-size:11px; text-transform:uppercase; color: var(--accent-cyan);">Core Investment Thesis:</strong>
                <p style="margin:4px 0 0 0; font-size:13px; line-height:1.5; color: var(--text-secondary);">${escapeHtml(thesisData.why_interested || '')}</p>
            </div>

            <div style="margin-bottom: 10px;">
                <strong style="font-size:11px; text-transform:uppercase; color: #ff7b72;">What Would Make Me Wrong:</strong>
                <p style="margin:4px 0 0 0; font-size:13px; line-height:1.5; color: var(--text-secondary);">${escapeHtml(thesisData.what_would_make_me_wrong || '')}</p>
            </div>

            ${checklist.length > 0 ? `
                <div style="margin-bottom: 10px;">
                    <strong style="font-size:11px; text-transform:uppercase; color: #ffd700;">🚨 Sell Checklist (When & Why to Sell):</strong>
                    <table class="sell-checklist-table">
                        <thead>
                            <tr>
                                <th>Sell Condition Trigger</th>
                                <th>Breaks Assumption</th>
                                <th>Action</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${checklistRows}
                        </tbody>
                    </table>
                </div>
            ` : ''}

            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 10px; font-size: 12px;">
                ${assumptionsList ? `
                    <div>
                        <strong class="text-muted" style="text-transform:uppercase; font-size:10px;">Key Assumptions:</strong>
                        <ul style="margin:4px 0 0 14px; padding:0;" class="text-muted">${assumptionsList}</ul>
                    </div>
                ` : ''}
                ${risksList ? `
                    <div>
                        <strong class="text-muted" style="text-transform:uppercase; font-size:10px;">Major Risks:</strong>
                        <ul style="margin:4px 0 0 14px; padding:0;" class="text-muted">${risksList}</ul>
                    </div>
                ` : ''}
            </div>
        </div>
    `;
}

async function saveMasterGeneratedThesisToBoard(synthesisId) {
    const thesisData = _masterGeneratedTheses[synthesisId];
    if (!thesisData) {
        showToast('No generated thesis found to save.', 'error');
        return;
    }

    const companyName = thesisData.target_company || 'Stock Pick';
    const ticker = thesisData.target_ticker;

    const resolvedTicker = ticker || companyName.toUpperCase().replace(/[^A-Z0-9]/g, '').slice(0, 10);

    const payload = {
        ticker: resolvedTicker,
        why_interested: thesisData.why_interested || '',
        what_would_make_me_wrong: thesisData.what_would_make_me_wrong || '',
        sell_conditions: (thesisData.sell_checklist || []).map(c => `${c.condition} (Breaks: ${c.linked_assumption}) [${c.severity}]`).join('\n'),
        sell_checklist: thesisData.sell_checklist || [],
        key_assumptions: thesisData.key_assumptions || [],
        major_risks: thesisData.major_risks || [],
        source: 'synthesis_chat',
        synthesis_id: synthesisId,
        snapshot: {
            company_name: companyName,
            conviction: 'High'
        }
    };

    try {
        await apiFetch('/theses', {
            method: 'POST',
            body: JSON.stringify(payload)
        });

        showToast(`Thesis for ${companyName} saved to Thesis Board!`, 'success');
    } catch (err) {
        showToast('Failed to save thesis: ' + err.message, 'error');
    }
}

function exportSynthesisPDF() {
    if (!_activeSynthesisMeta || !_activeSynthesisMeta.result) {
        showToast('No active synthesis report found to export.', 'error');
        return;
    }

    const meta = _activeSynthesisMeta;
    const res = meta.result;
    const picks = res.ultimate_picks || [];
    const createdDate = meta.created_at
        ? new Date(meta.created_at).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
        : new Date().toLocaleDateString();

    // --- Build pick cards ---
    let picksHtml = '';
    for (let i = 0; i < picks.length; i++) {
        const p = picks[i];

        let catalystItems = '';
        if (p.key_catalysts && p.key_catalysts.length > 0) {
            for (let j = 0; j < p.key_catalysts.length; j++) {
                const c = p.key_catalysts[j];
                if (typeof c === 'object' && c !== null) {
                    catalystItems += '<div style="font-size:11px;background:#f8fafc;padding:5px 8px;border-radius:4px;border-left:3px solid #0284c7;margin-top:4px;color:#334155;"><b style="color:#0284c7;">[' + esc(c.window || '0-6m') + ']</b> ' + esc(c.catalyst || '') + (c.reason ? ' — ' + esc(c.reason) : '') + '</div>';
                } else {
                    catalystItems += '<div style="font-size:11px;background:#f8fafc;padding:5px 8px;border-radius:4px;border-left:3px solid #0284c7;margin-top:4px;color:#334155;">' + esc(String(c)) + '</div>';
                }
            }
        }

        let riskItems = '';
        if (p.key_risks && p.key_risks.length > 0) {
            for (let j = 0; j < p.key_risks.length; j++) {
                riskItems += (j > 0 ? '<br>' : '') + '• ' + esc(p.key_risks[j]);
            }
        }

        picksHtml += '<div style="page-break-inside:avoid;border:1px solid #cbd5e1;border-radius:8px;padding:16px;margin-bottom:16px;">';
        picksHtml += '<div style="display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #e2e8f0;padding-bottom:8px;margin-bottom:10px;">';
        picksHtml += '<div><span style="background:#0f172a;color:#fbbf24;font-weight:800;font-size:12px;padding:3px 8px;border-radius:4px;margin-right:8px;">Rank #' + p.rank + '</span>';
        picksHtml += '<b style="font-size:16px;color:#0f172a;">' + esc(p.company_name) + '</b>';
        if (p.ticker) picksHtml += ' <span style="font-size:12px;color:#64748b;">(' + esc(p.ticker) + ')</span>';
        picksHtml += '</div>';
        picksHtml += '<div style="font-size:11px;background:#ecfdf5;color:#047857;font-weight:700;padding:3px 10px;border-radius:12px;border:1px solid #a7f3d0;">' + esc(p.composite_conviction || 'High') + '</div>';
        picksHtml += '</div>';

        picksHtml += '<div style="font-size:11px;color:#475569;margin-bottom:10px;"><b>Convergence:</b> ' + (p.convergence_count || 1) + ' strategies — ' + (p.strategies_found_in || []).join(', ') + '</div>';

        picksHtml += '<div style="margin-bottom:10px;"><b style="font-size:10px;color:#0f172a;text-transform:uppercase;">Thesis</b>';
        picksHtml += '<p style="margin:4px 0 0;font-size:12px;line-height:1.5;color:#334155;">' + esc(p.unified_thesis || '') + '</p></div>';

        if (catalystItems) {
            picksHtml += '<div style="margin-bottom:10px;"><b style="font-size:10px;color:#0f172a;text-transform:uppercase;">Catalysts</b>' + catalystItems + '</div>';
        }

        picksHtml += '<table style="width:100%;border-collapse:collapse;margin-top:10px;"><tr>';
        picksHtml += '<td style="width:50%;vertical-align:top;padding-right:5px;"><div style="background:#fff1f2;border:1px solid #fecdd3;padding:8px 10px;border-radius:6px;"><b style="font-size:10px;color:#be123c;text-transform:uppercase;">Risks</b><div style="font-size:11px;color:#4c0519;margin-top:3px;line-height:1.4;">' + (riskItems || 'None flagged') + '</div></div></td>';
        picksHtml += '<td style="width:50%;vertical-align:top;padding-left:5px;"><div style="background:#f8fafc;border:1px solid #e2e8f0;padding:8px 10px;border-radius:6px;"><b style="font-size:10px;color:#475569;text-transform:uppercase;">Contrarian View</b><div style="font-size:11px;color:#334155;margin-top:3px;line-height:1.4;">' + esc(p.contrarian_view || 'N/A') + '</div></div></td>';
        picksHtml += '</tr></table>';

        picksHtml += '</div>';
    }

    // --- Build honorable mentions ---
    let hmHtml = '';
    if (res.honorable_mentions && res.honorable_mentions.length > 0) {
        hmHtml += '<div style="margin-top:20px;page-break-inside:avoid;"><h3 style="color:#0f172a;font-size:14px;font-weight:700;border-bottom:1px solid #e2e8f0;padding-bottom:6px;margin-bottom:10px;">Watchlist Candidates</h3>';
        hmHtml += '<table style="width:100%;border-collapse:collapse;font-size:11px;"><thead><tr style="background:#f1f5f9;color:#475569;"><th style="padding:6px 8px;border:1px solid #cbd5e1;text-align:left;">Company</th><th style="padding:6px 8px;border:1px solid #cbd5e1;text-align:left;">Strategy</th><th style="padding:6px 8px;border:1px solid #cbd5e1;text-align:left;">Reason</th></tr></thead><tbody>';
        for (let i = 0; i < res.honorable_mentions.length; i++) {
            const hm = res.honorable_mentions[i];
            hmHtml += '<tr><td style="padding:6px 8px;border:1px solid #cbd5e1;font-weight:600;color:#0f172a;">' + esc(hm.company_name || '') + (hm.ticker ? ' (' + esc(hm.ticker) + ')' : '') + '</td>';
            hmHtml += '<td style="padding:6px 8px;border:1px solid #cbd5e1;color:#0284c7;">' + esc(hm.strategy_name || 'N/A') + '</td>';
            hmHtml += '<td style="padding:6px 8px;border:1px solid #cbd5e1;color:#334155;">' + esc(hm.reason_for_watching || '') + '</td></tr>';
        }
        hmHtml += '</tbody></table></div>';
    }

    // --- Assemble full page HTML ---
    const fullPage = '<!DOCTYPE html><html><head><meta charset="UTF-8"><title>StockLens Master Synthesis Report</title>'
        + '<style>@import url("https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap");'
        + 'body{font-family:Inter,-apple-system,sans-serif;color:#1e293b;margin:0;padding:28px;background:#fff;font-size:12px;line-height:1.5;}'
        + '@media print{body{padding:0;margin:0;} @page{margin:15mm 12mm;}}'
        + '</style></head><body>'
        + '<div style="border-bottom:2px solid #0f172a;padding-bottom:12px;margin-bottom:18px;">'
        + '<h1 style="margin:0;color:#0f172a;font-size:22px;font-weight:800;">StockLens Master Synthesis Report</h1>'
        + '<div style="font-size:12px;color:#64748b;margin-top:4px;">Date: ' + esc(createdDate) + ' &nbsp;|&nbsp; Strategies: ' + (res.total_strategies_used || 0) + ' &nbsp;|&nbsp; Candidates: ' + (res.total_candidates_analyzed || 0) + '</div>'
        + '</div>'
        + (res.market_narrative ? '<div style="background:#fffbeb;border-left:4px solid #d97706;padding:10px 14px;margin-bottom:14px;border-radius:4px;"><b style="color:#b45309;font-size:11px;text-transform:uppercase;">Market Narrative</b><p style="margin:4px 0 0;font-size:12px;line-height:1.5;color:#334155;">' + esc(res.market_narrative) + '</p></div>' : '')
        + (res.portfolio_considerations ? '<div style="background:#f0f9ff;border-left:4px solid #0284c7;padding:10px 14px;margin-bottom:18px;border-radius:4px;"><b style="color:#0369a1;font-size:11px;text-transform:uppercase;">Portfolio Balance</b><p style="margin:4px 0 0;font-size:12px;line-height:1.5;color:#334155;">' + esc(res.portfolio_considerations) + '</p></div>' : '')
        + '<h2 style="color:#0f172a;font-size:15px;font-weight:700;border-bottom:1px solid #e2e8f0;padding-bottom:6px;margin-bottom:14px;">Ultimate Portfolio Picks</h2>'
        + picksHtml
        + hmHtml
        + '<div style="margin-top:24px;padding-top:12px;border-top:1px solid #cbd5e1;font-size:10px;color:#94a3b8;text-align:center;">Generated by StockLens Master AI Synthesis</div>'
        + '</body></html>';

    // --- Open new window and print ---
    const printWin = window.open('', '_blank', 'width=900,height=700');
    if (!printWin) {
        showToast('Pop-up blocked! Please allow pop-ups for this site and try again.', 'error');
        return;
    }
    printWin.document.write(fullPage);
    printWin.document.close();

    // Wait for fonts/content to load, then trigger print dialog
    printWin.onload = function() {
        setTimeout(function() {
            printWin.focus();
            printWin.print();
        }, 500);
    };

    showToast('Report opened — use "Save as PDF" in the print dialog.', 'info');
}

// Helper: simple HTML escaper for PDF export (avoids dependency on escapeHtml for the print window)
function esc(str) {
    if (!str) return '';
    return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
