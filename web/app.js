// App Controller for TokenBar Liquid Glass Edition

let currentData = null;

function formatNum(num) {
  if (num >= 1000000) return (num / 1000000).toFixed(2) + ' M';
  if (num >= 1000) return (num / 1000).toFixed(1) + ' k';
  return num.toLocaleString();
}

function formatCost(cost) {
  return `$${cost.toFixed(2)} USD`;
}

async function fetchData() {
  try {
    const res = await fetch('/api/data');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    currentData = await res.json();
    renderAll(currentData);
  } catch (err) {
    console.error('Error cargando API:', err);
    document.getElementById('footer-status').textContent = '⚠️ Error conectando con API';
  }
}

function renderAll(data) {
  if (!data) return;

  // Header & Overview
  document.getElementById('header-speed').textContent = `⚡ ${data.tokens_per_min || 0} tok/min`;
  document.getElementById('card-today-tok').textContent = formatNum(data.today_tokens || 0);
  document.getElementById('card-today-cost').textContent = formatCost(data.today_cost || 0);

  document.getElementById('card-7d-tok').textContent = formatNum(data.seven_day_tokens || 0);
  document.getElementById('card-7d-cost').textContent = formatCost(data.seven_day_cost || 0);

  document.getElementById('card-speed').textContent = (data.tokens_per_min || 0).toFixed(1);

  document.getElementById('card-total-tok').textContent = formatNum(data.total_tokens || 0);
  document.getElementById('card-total-cost').textContent = formatCost(data.total_cost || 0);

  // Overview Agents
  const overviewAgentsList = document.getElementById('overview-agents-list');
  overviewAgentsList.innerHTML = '';
  const agents = data.agents || [];
  document.getElementById('agents-count-badge').textContent = `${agents.length} activos`;

  agents.forEach(ag => {
    const div = document.createElement('div');
    div.className = 'item-card';
    div.innerHTML = `
      <div class="item-header">
        <span>🤖 ${ag.agent}</span>
        <span>${ag.percentage}%</span>
      </div>
      <div class="progress-track">
        <div class="progress-fill" style="width: ${ag.percentage}%"></div>
      </div>
      <div class="item-meta">
        ${ag.tokens.toLocaleString()} tokens consumidos · Costo estimado: $${ag.cost.toFixed(4)} USD
      </div>
    `;
    overviewAgentsList.appendChild(div);
  });

  // Heatmap
  renderHeatmap(data.heatmap || []);

  // Models
  renderModels(data.models || []);

  // Agents
  renderAgents(data.agents || []);

  // Stats
  renderStats(data.hourly_distribution || [], data.daily_distribution || []);

  // Quotas
  renderQuotas(data.claude_quota || {}, data.antigravity_quota || {});

  // Footer
  document.getElementById('footer-status').textContent = '🟢 Sincronizado en vivo';
  const now = new Date();
  document.getElementById('footer-updated-at').textContent = `Última actualización: ${now.toLocaleTimeString()}`;
}

function renderHeatmap(matrix) {
  const container = document.getElementById('heatmap-container');
  container.innerHTML = '';

  matrix.forEach(item => {
    const cell = document.createElement('div');
    cell.className = `hm-cell lvl-${item.intensity}`;
    cell.title = `${item.date}: ${item.tokens.toLocaleString()} tokens ($${item.cost.toFixed(4)})`;

    cell.addEventListener('click', () => {
      document.getElementById('heatmap-detail').innerHTML = `
        <span class="detail-icon">📅</span>
        <span class="detail-text"><strong>${item.date}</strong>: ${item.tokens.toLocaleString()} tokens consumidos · Costo estimado: $${item.cost.toFixed(4)} USD</span>
      `;
    });

    container.appendChild(cell);
  });
}

function renderModels(models) {
  const container = document.getElementById('models-container');
  container.innerHTML = '';

  models.forEach(m => {
    const card = document.createElement('div');
    card.className = 'item-card';
    card.innerHTML = `
      <div class="item-header">
        <span>🔹 ${m.model}</span>
        <span>${m.percentage}%</span>
      </div>
      <div class="progress-track">
        <div class="progress-fill" style="width: ${m.percentage}%"></div>
      </div>
      <div class="item-meta">
        ${m.tokens.toLocaleString()} tokens · Costo estimado: $${m.cost.toFixed(4)} USD
      </div>
    `;
    container.appendChild(card);
  });
}

function renderAgents(agents) {
  const container = document.getElementById('agents-container');
  container.innerHTML = '';

  agents.forEach(a => {
    const card = document.createElement('div');
    card.className = 'item-card';
    card.innerHTML = `
      <div class="item-header">
        <span>🛠️ ${a.agent}</span>
        <span>${a.percentage}%</span>
      </div>
      <div class="progress-track">
        <div class="progress-fill" style="width: ${a.percentage}%"></div>
      </div>
      <div class="item-meta">
        ${a.tokens.toLocaleString()} tokens · Costo: $${a.cost.toFixed(4)} USD
      </div>
    `;
    container.appendChild(card);
  });
}

function renderStats(hourly, daily) {
  const hourlyChart = document.getElementById('hourly-chart');
  hourlyChart.innerHTML = '';
  const maxH = Math.max(...hourly, 1);

  hourly.forEach((tok, h) => {
    if (tok === 0) return;
    const pct = ((tok / maxH) * 100).toFixed(1);
    const card = document.createElement('div');
    card.className = 'item-card';
    card.innerHTML = `
      <div class="item-header">
        <span>⏰ ${String(h).padStart(2, '0')}:00 - ${String(h).padStart(2, '0')}:59</span>
        <span>${tok.toLocaleString()} tokens</span>
      </div>
      <div class="progress-track">
        <div class="progress-fill" style="width: ${pct}%"></div>
      </div>
    `;
    hourlyChart.appendChild(card);
  });

  const dailyChart = document.getElementById('daily-chart');
  dailyChart.innerHTML = '';
  const daysNames = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"];
  const maxD = Math.max(...daily, 1);

  daily.forEach((tok, d) => {
    const pct = ((tok / maxD) * 100).toFixed(1);
    const card = document.createElement('div');
    card.className = 'item-card';
    card.innerHTML = `
      <div class="item-header">
        <span>📅 ${daysNames[d]}</span>
        <span>${tok.toLocaleString()} tokens</span>
      </div>
      <div class="progress-track">
        <div class="progress-fill" style="width: ${pct}%"></div>
      </div>
    `;
    dailyChart.appendChild(card);
  });
}

function renderQuotas(claude, antigravity) {
  const claudeContainer = document.getElementById('claude-quotas-container');
  claudeContainer.innerHTML = '';
  if (claude.error) {
    claudeContainer.innerHTML = `<div class="item-meta">⚠️ ${claude.error}</div>`;
  } else {
    (claude.windows || []).forEach(w => {
      claudeContainer.appendChild(createQuotaCard(w.label, w.remaining_pct, w.resets_at));
    });
  }

  const agContainer = document.getElementById('antigravity-quotas-container');
  agContainer.innerHTML = '';
  if (antigravity.error) {
    agContainer.innerHTML = `<div class="item-meta">⚠️ ${antigravity.error}</div>`;
  } else {
    (antigravity.models || []).forEach(m => {
      agContainer.appendChild(createQuotaCard(m.label, m.remaining_pct, m.resets_at));
    });
  }
}

function createQuotaCard(label, remainingPct, resetsAt) {
  const div = document.createElement('div');
  div.className = 'quota-card';
  let lvlClass = 'pct-good';
  if (remainingPct < 25) lvlClass = 'pct-alert';
  else if (remainingPct < 50) lvlClass = 'pct-warn';

  let resetText = '—';
  if (resetsAt) {
    const dt = new Date(resetsAt);
    resetText = dt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  div.innerHTML = `
    <div class="quota-header">
      <span style="font-weight:700;">${label}</span>
      <span class="quota-pct ${lvlClass}">${remainingPct.toFixed(0)}% restante</span>
    </div>
    <div class="progress-track">
      <div class="progress-fill" style="width: ${remainingPct}%"></div>
    </div>
    <div class="item-meta">Reset programado: ${resetText}</div>
  `;
  return div;
}

// Navigation Tabs
document.querySelectorAll('.nav-tab').forEach(tab => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.lens-page').forEach(p => p.classList.remove('active'));

    tab.classList.add('active');
    const lensId = `lens-${tab.dataset.lens}`;
    const targetPage = document.getElementById(lensId);
    if (targetPage) targetPage.classList.add('active');
  });
});

document.getElementById('refresh-btn').addEventListener('click', () => {
  fetchData();
});

// Auto-refresh cada 5 segundos
fetchData();
setInterval(fetchData, 5000);
