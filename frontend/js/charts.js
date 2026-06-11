/* ============================================
   StockLens — Chart.js Configuration & Helpers
   ============================================ */

// --- Global Chart.js Defaults (Dark Theme) ---
Chart.defaults.color = '#94a3b8';
Chart.defaults.borderColor = 'rgba(255, 255, 255, 0.06)';
Chart.defaults.font.family = "'Inter', sans-serif";
Chart.defaults.font.size = 12;
Chart.defaults.plugins.legend.labels.usePointStyle = true;
Chart.defaults.plugins.legend.labels.pointStyleWidth = 10;
Chart.defaults.plugins.legend.labels.padding = 16;
Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(17, 24, 39, 0.95)';
Chart.defaults.plugins.tooltip.borderColor = 'rgba(255, 255, 255, 0.1)';
Chart.defaults.plugins.tooltip.borderWidth = 1;
Chart.defaults.plugins.tooltip.cornerRadius = 8;
Chart.defaults.plugins.tooltip.padding = 12;
Chart.defaults.plugins.tooltip.titleFont = { weight: '600', size: 13 };
Chart.defaults.plugins.tooltip.bodyFont = { size: 12 };
Chart.defaults.scale.grid = { color: 'rgba(255, 255, 255, 0.04)' };

// Track active chart instances by canvas ID for cleanup
const _chartInstances = {};

/**
 * Destroy chart on a canvas if it already exists (prevents reuse errors).
 * @param {string} canvasId
 */
function destroyChart(canvasId) {
    if (_chartInstances[canvasId]) {
        _chartInstances[canvasId].destroy();
        delete _chartInstances[canvasId];
    }
}

/**
 * Generate a gradient fill for a line chart.
 */
function _createGradient(ctx, color, height = 300) {
    const grad = ctx.createLinearGradient(0, 0, 0, height);
    grad.addColorStop(0, color.replace(')', ', 0.25)').replace('rgb', 'rgba'));
    grad.addColorStop(1, color.replace(')', ', 0.0)').replace('rgb', 'rgba'));
    return grad;
}

/**
 * Preset color palette for chart datasets.
 */
const CHART_COLORS = {
    cyan:    '#00d4ff',
    purple:  '#a855f7',
    green:   '#00d4aa',
    red:     '#ff4757',
    amber:   '#ffa502',
    blue:    '#3b82f6',
};

const CHART_COLOR_ARRAY = Object.values(CHART_COLORS);

/**
 * Create a trend chart (line chart) for financial data.
 *
 * @param {string} canvasId - ID of the <canvas> element
 * @param {string[]} labels - X-axis labels (e.g., years)
 * @param {Array<{label: string, data: number[], color?: string}>} datasets
 * @param {object} options - extra chart options
 * @returns {Chart} the chart instance
 */
function createTrendChart(canvasId, labels, datasets, options = {}) {
    destroyChart(canvasId);

    const canvas = document.getElementById(canvasId);
    if (!canvas) {
        console.warn(`Canvas #${canvasId} not found.`);
        return null;
    }
    const ctx = canvas.getContext('2d');

    const chartDatasets = datasets.map((ds, i) => {
        const color = ds.color || CHART_COLOR_ARRAY[i % CHART_COLOR_ARRAY.length];
        return {
            label: ds.label,
            data: ds.data,
            borderColor: color,
            backgroundColor: (context) => {
                const chart = context.chart;
                const { ctx: c, chartArea } = chart;
                if (!chartArea) return color;
                const grad = c.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);
                grad.addColorStop(0, color + '40');
                grad.addColorStop(1, color + '00');
                return grad;
            },
            fill: true,
            tension: 0.35,
            borderWidth: 2.5,
            pointRadius: 4,
            pointHoverRadius: 7,
            pointBackgroundColor: color,
            pointBorderColor: '#111827',
            pointBorderWidth: 2,
            pointHoverBackgroundColor: '#fff',
            pointHoverBorderColor: color,
            pointHoverBorderWidth: 2,
        };
    });

    const chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: chartDatasets,
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        boxWidth: 12,
                        boxHeight: 12,
                    },
                },
                tooltip: {
                    callbacks: {
                        label: function (ctx) {
                            let val = ctx.parsed.y;
                            if (Math.abs(val) >= 10000000) {
                                val = (val / 10000000).toFixed(1) + ' Cr';
                            } else if (Math.abs(val) >= 100000) {
                                val = (val / 100000).toFixed(1) + ' L';
                            } else {
                                val = val.toLocaleString('en-IN');
                            }
                            return `${ctx.dataset.label}: ₹${val}`;
                        }
                    }
                },
            },
            scales: {
                x: {
                    ticks: { font: { size: 11 } },
                },
                y: {
                    beginAtZero: false,
                    ticks: {
                        font: { size: 11 },
                        callback: function (value) {
                            if (Math.abs(value) >= 10000000) return '₹' + (value / 10000000).toFixed(0) + ' Cr';
                            if (Math.abs(value) >= 100000) return '₹' + (value / 100000).toFixed(0) + ' L';
                            return '₹' + value.toLocaleString('en-IN');
                        }
                    },
                },
            },
            ...options,
        },
    });

    _chartInstances[canvasId] = chart;
    return chart;
}

/**
 * Create a score bar (rendered via DOM, not Chart.js).
 *
 * @param {string} containerId - ID of the container element
 * @param {number} score - current score
 * @param {number} maxScore - maximum possible score
 */
function createScoreBar(containerId, score, maxScore) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const pct = maxScore > 0 ? Math.min(100, (score / maxScore) * 100) : 0;

    container.innerHTML = `
        <div class="score-bar-container">
            <div class="score-bar">
                <div class="score-bar-fill" style="width: ${pct}%"></div>
            </div>
            <span class="score-bar-label">${score}/${maxScore}</span>
        </div>
    `;

    // Animate the bar fill
    requestAnimationFrame(() => {
        const fill = container.querySelector('.score-bar-fill');
        if (fill) fill.style.width = pct + '%';
    });
}

/**
 * Create an inline score bar HTML string (no container lookup needed).
 */
function getScoreBarHTML(score, maxScore) {
    const pct = maxScore > 0 ? Math.min(100, (score / maxScore) * 100) : 0;
    return `
        <div class="score-bar-container">
            <div class="score-bar">
                <div class="score-bar-fill" style="width: ${pct}%"></div>
            </div>
            <span class="score-bar-label">${score}/${maxScore}</span>
        </div>
    `;
}
