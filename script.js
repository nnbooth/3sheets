/*
  script.js — The Fourth Sheet

  KEY LOCATIONS:
  - Report cards (edit this to add reports) .. REPORTS list, just below
  - Report card builder ...................... renderReports() / buildReportCard()
  - Loading message + 8-second fallback ...... watchEmbedLoad()
  - Game (load on Play) ...................... setupGameSlot()
  - Prices (switched off by default) ......... SHOW_PRICES / PRICES
  - Home-page sample dashboard ............... setupHeroDash() (data: dashboard-data.js)
  - Mobile menu + footer year ................ bottom of file (DOMContentLoaded)

  No frameworks or build step: this file is loaded as-is by index.html.
*/

/* ---------------------------------------------------------------------------
   REPORTS — one entry per report card in the "Reports" section.

   To add a report, copy one { ... } block and change the values:
     title     Card heading, e.g. 'Sales'.
     question  The one-line question the report answers.
     embedUrl  Power BI "Publish to web" link (starts with
               https://app.powerbi.com/view?r=...). Leave as '' while the
               report is still being built: the card then shows a mock
               dashboard outline and "In build — preview coming soon".
               Never paste the address you see while signed in to your
               own Power BI workspace: visitors can't sign in to it.
     status    Short label for the chip on the card, e.g. 'Live demo'.
               Ignored while embedUrl is empty (the chip says "In build").
     preview   Picture shown while embedUrl is empty, e.g. a screenshot of
               the report in progress. The current ones are mock-ups made by
               tools/render_mockups.py. Leave as '' for a plain grey outline.
--------------------------------------------------------------------------- */
const REPORTS = [
  {
    title: 'Sales',
    preview: 'media/mockups/report-sales.png',
    question: "What's selling, what's cancelling and what's in the pipeline",
    embedUrl: '',
    status: 'In build',
  },
  {
    title: 'Purchasing',
    preview: 'media/mockups/report-purchasing.png',
    question: 'Which suppliers are late, and where costs are moving',
    embedUrl: '',
    status: 'In build',
  },
  {
    title: 'Payroll & overtime',
    preview: 'media/mockups/report-payroll.png',
    question: 'Where overtime is growing, and why',
    embedUrl: '',
    status: 'In build',
  },
];

// How long an embedded sheet/report may take before we show the
// "taking longer than usual" message (milliseconds).
const EMBED_SLOW_AFTER_MS = 8000;

/* ---------------------------------------------------------------------------
   Report cards
--------------------------------------------------------------------------- */

// Small helper: create an element with a class and optional text.
// Uses textContent (not innerHTML) so report text can never inject HTML.
function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text) node.textContent = text;
  return node;
}

// The "In build" placeholder: a grey outline of a dashboard (KPI tiles,
// a bar chart and a table) drawn with plain divs styled in styles.css
// (search "REPORT MOCK"). `variant` just varies the bar heights per card.
function buildReportMock(variant) {
  const barSets = [
    [45, 60, 52, 70, 64, 82, 76],
    [70, 58, 66, 50, 62, 48, 55],
    [30, 38, 35, 48, 55, 61, 72],
  ];
  const bars = barSets[variant % barSets.length];

  const mock = el('div', 'report-mock');
  mock.setAttribute('aria-hidden', 'true'); // decorative only

  const kpis = el('div', 'mock-kpis');
  for (let i = 0; i < 3; i += 1) kpis.appendChild(el('span', 'mock-kpi'));

  const chart = el('div', 'mock-chart');
  bars.forEach((height) => {
    const bar = el('span', 'mock-bar');
    bar.style.height = `${height}%`;
    chart.appendChild(bar);
  });

  const rows = el('div', 'mock-rows');
  for (let i = 0; i < 3; i += 1) rows.appendChild(el('span', 'mock-row'));

  mock.append(kpis, chart, rows);
  return mock;
}

function buildReportCard(report, index) {
  const isLive = Boolean(report.embedUrl);

  const card = el('article', isLive ? 'report-card report-card--live' : 'report-card');

  const header = el('div', 'report-card-header');
  header.appendChild(el('h3', '', report.title));
  header.appendChild(el('span', 'status-chip', isLive ? report.status || 'Live demo' : 'In build'));
  card.appendChild(header);

  card.appendChild(el('p', 'report-question', report.question));

  const frame = el('div', 'report-frame');

  if (isLive) {
    // Real Power BI "Publish to web" report, loaded only when scrolled near.
    frame.setAttribute('data-embed', '');
    frame.dataset.slowMessage = 'This report is taking longer than usual to load. Try refreshing the page in a moment.';

    const status = el('div', 'embed-status');
    status.setAttribute('role', 'status');
    status.appendChild(el('span', 'spinner'));
    status.appendChild(el('span', 'embed-status-msg', 'Loading report…'));

    const iframe = document.createElement('iframe');
    iframe.src = report.embedUrl;
    iframe.title = `${report.title} report: interactive Power BI preview`;
    iframe.loading = 'lazy';
    iframe.allowFullscreen = true;

    frame.append(status, iframe);
  } else {
    // Nothing to embed yet: show the mock outline, never an empty iframe.
    frame.classList.add('report-frame--pending');
    if (report.preview) {
      // Preview image (a mock-up for now), opens full size in a new tab
      const link = document.createElement('a');
      link.href = report.preview;
      link.target = '_blank';
      link.rel = 'noopener';
      link.className = 'report-preview';
      const img = document.createElement('img');
      img.src = report.preview;
      img.alt = `${report.title} report preview with sample data.`;
      img.loading = 'lazy';
      img.width = 1600;
      img.height = 900;
      link.appendChild(img);
      frame.appendChild(link);
    } else {
      frame.appendChild(buildReportMock(index));
    }
    frame.appendChild(el('p', 'report-pending-msg', report.preview ? 'Sample data · live report coming soon' : 'Live report coming soon'));
  }

  card.appendChild(frame);
  return card;
}

function renderReports() {
  const grid = document.getElementById('report-grid');
  if (!grid) return;
  REPORTS.forEach((report, index) => grid.appendChild(buildReportCard(report, index)));
}

/* ---------------------------------------------------------------------------
   Loading state for embedded iframes (Power BI reports).

   Any element with a `data-embed` attribute that contains an <iframe> and an
   .embed-status box gets:
     - "is-loading" while waiting (spinner shown over the frame),
     - "is-loaded" once the iframe finishes loading (spinner hidden),
     - "is-slow" if it hasn't loaded EMBED_SLOW_AFTER_MS after scrolling
       into view (message swapped for the element's data-slow-message).
   The timer starts on scroll-into-view because the iframes are lazy-loaded
   and don't start downloading until then.
--------------------------------------------------------------------------- */
function watchEmbedLoad(container) {
  const iframe = container.querySelector('iframe');
  const message = container.querySelector('.embed-status-msg');
  if (!iframe) return;

  container.classList.add('is-loading');
  let slowTimer = null;

  iframe.addEventListener('load', () => {
    clearTimeout(slowTimer);
    container.classList.remove('is-loading', 'is-slow');
    container.classList.add('is-loaded');
  });

  const startTimer = () => {
    slowTimer = setTimeout(() => {
      if (container.classList.contains('is-loaded')) return;
      container.classList.add('is-slow');
      if (message && container.dataset.slowMessage) {
        message.textContent = container.dataset.slowMessage;
      }
    }, EMBED_SLOW_AFTER_MS);
  };

  if (!('IntersectionObserver' in window)) {
    startTimer();
    return;
  }

  const observer = new IntersectionObserver((entries) => {
    if (entries.some((entry) => entry.isIntersecting)) {
      observer.disconnect();
      startTimer();
    }
  });
  observer.observe(container);
}

/* ---------------------------------------------------------------------------
   GAME SLOT — "The Month-End Run".

   The page only loads the poster image. Pressing Play (on the poster or the
   button beside it) swaps the poster for the game in an iframe, so visitors
   who don't play never download it. The game tells us its height
   ('s3-game-height' message) so the iframe fits without scrollbars, and we
   ask it to pause ('s3:pause') when it's scrolled out of view.
--------------------------------------------------------------------------- */
function setupGameSlot() {
  const stage = document.querySelector('.game-stage');
  if (!stage) return;
  const grid = stage.closest('.game-grid');
  let frame = null;

  const play = () => {
    if (frame) return;
    frame = document.createElement('iframe');
    frame.className = 'game-frame';
    frame.src = stage.dataset.gameSrc;
    frame.title = 'The Month-End Run (game)';
    frame.allow = 'fullscreen';
    grid.classList.add('is-playing');
    // A first guess at the height until the game reports its real one
    frame.style.height = `${Math.round((grid.clientWidth * 9) / 16) + 120}px`;
    stage.replaceChildren(frame);
    frame.addEventListener('load', () => {
      // Same site, so we can put keyboard focus straight into the game
      try { frame.contentDocument.getElementById('game-canvas').focus({ preventScroll: true }); } catch { /* ignore */ }
    });
  };

  document.querySelectorAll('.game-play, [data-game-play]').forEach((btn) => btn.addEventListener('click', play));

  window.addEventListener('message', (event) => {
    if (!frame || event.origin !== location.origin || event.source !== frame.contentWindow) return;
    if (event.data && event.data.type === 's3-game-height') frame.style.height = `${event.data.height}px`;
  });

  if ('IntersectionObserver' in window) {
    new IntersectionObserver((entries) => {
      if (frame && !entries[0].isIntersecting) frame.contentWindow.postMessage('s3:pause', location.origin);
    }, { threshold: 0.2 }).observe(stage);
  }
}

/* ---------------------------------------------------------------------------
   PRICES — switched OFF by default.

   Each price on the page shows "Talk to me about pricing" (that text is in
   index.html, so it's what visitors see even without JavaScript). To show
   real prices: fill in PRICES below, then set SHOW_PRICES = true.
   A price still written like [[TOKEN]] is never shown.
--------------------------------------------------------------------------- */
const SHOW_PRICES = false;
const PRICES = {
  setup: '[[PRICE_SETUP]]',     // e.g. 'From $3,500'
  bedding: '[[PRICE_BEDDING]]', // e.g. '$5,500 over 3 months'
  monthly: '[[PRICE_MONTHLY]]', // e.g. 'From $900 a month'
};

function applyPrices() {
  if (!SHOW_PRICES) return;
  document.querySelectorAll('[data-price]').forEach((node) => {
    const value = PRICES[node.dataset.price];
    if (value && !/\[\[.*\]\]/.test(value)) node.textContent = value;
  });
}

/* ---------------------------------------------------------------------------
   HERO DASHBOARD — three invented sample organisations on the home page.

   The numbers come from dashboard-data.js, which is GENERATED by
   tools/financial_model.py (a driver-based model with built-in checks).
   Don't type numbers in here: change the assumptions in that file and run
   python3 tools/sample_data.py.

   Month-end: September 2026 against the prior month (August 2026), whole
   dollars, built up from individual jobs, engagements and grants.
   Tabs: The fourth sheet (always first, and shown by default), P&L,
   Balance sheet, Cash flow.
   Toggle: SME · trades, SME · services, Not-for-profit.
   Phones show headline lines; larger screens show every line (CSS hides
   .detail rows under 720px). The page re-checks that everything adds up
   before showing the "Balances" tick.
--------------------------------------------------------------------------- */
const dash = { org: 'trades', tab: 'fourth', view: 'pct' };

// Accounting format in whole dollars: 1,234 / (1,234) for negatives / - for zero
const acct = (n) => (n < 0 ? `(${Math.abs(n).toLocaleString('en-AU')})` : n === 0 ? '-' : n.toLocaleString('en-AU'));
const esc = (v) => String(v).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const CHART_FORMATS = {
  money0: (v) => (v < 0 ? `($${Math.round(-v).toLocaleString('en-AU')})` : `$${Math.round(v).toLocaleString('en-AU')}`),
  pct0: (v) => `${Math.round(v)}%`,
  pct1: (v) => `${Number(v).toFixed(1)}%`,
  cents_int: (v) => `${v}¢`,
  int: (v) => Math.round(v).toLocaleString('en-AU'),
  money_k: (v) => (Math.abs(v) >= 1000 ? `$${Math.round(v / 1000).toLocaleString('en-AU')}k` : `$${v}`),
};

// Re-check a statement: every subtotal equals the detail lines above it
function statementAddsUp(rows) {
  let pending = [];
  for (const r of rows) {
    if (r.level === 'heading') pending = [];
    else if (r.level === 'detail') pending.push(r);
    else if (r.level === 'subtotal' && pending.length) {
      for (let i = 0; i < 2; i++) if (pending.reduce((t, p) => t + p.values[i], 0) !== r.values[i]) return false;
      pending = [];
    }
  }
  return true;
}

// The headline ties: balance sheet balances, cash flow ends at the bank balance
function orgBalances(o) {
  const val = (rows, label) => (rows.find((r) => r.label === label) || {}).values;
  const bs = o.statements.bs.rows, cf = o.statements.cf.rows;
  const equity = val(bs, 'Total equity') || val(bs, 'Accumulated funds');
  const ok = ['pnl', 'bs', 'cf'].every((k) => statementAddsUp(o.statements[k].rows));
  return ok && [0, 1].every((i) => val(bs, 'Net assets')[i] === equity[i] && val(cf, 'Cash at end of month')[i] === val(bs, 'Cash at bank')[i]);
}

function renderStatement(o, st) {
  const rows = st.rows.map((r) => {
    if (r.level === 'heading') return `<tr class="st-heading"><th colspan="4" scope="rowgroup">${esc(r.label)}</th></tr>`;
    const change = r.values[0] - r.values[1];
    return `<tr class="st-${r.level}${r.level === 'detail' ? ' detail' : ''}"><td>${esc(r.label)}</td>${r.values.map((v) => `<td class="n">${acct(v)}</td>`).join('')}<td class="n st-change">${acct(change)}</td></tr>`;
  }).join('');
  const sts = window.FOURTH_SHEET_DASHBOARD.status.slice(0, 2).map((m) => `${m.label}: ${m.status.toLowerCase()}`).join(' · ');
  return `<p class="dash-chart-title">${esc(st.title)} · ${esc(o.name)}</p><p class="dash-status-line">${esc(sts)}</p>
    <div class="st-scroll"><table class="st-table"><thead><tr><th scope="col">$</th>${o.columns.map((c) => `<th scope="col" class="n">${c}</th>`).join('')}<th scope="col" class="n st-change">Change</th></tr></thead><tbody>${rows}</tbody></table></div>
    <p class="dash-phone-note">Headline lines shown. Every line is on a larger screen, and in the Excel and PDF downloads.</p>`;
}

function renderChart(ch) {
  // Categorical data -> horizontal bars (labels down the left), the default.
  // Every bar carries a small value label and opens its workings when clicked.
  // Amber/sand = below target (the only meaning of the colour), unless the
  // chart is "plain". "marks" = a small tick per bar (e.g. budget to date).
  const fmt = CHART_FORMATS[ch.format] || String;
  const W = 300, right = 268, top = 6, row = 15, bh = 9;
  const left = Math.min(140, 8 + Math.max(...ch.labels.map((l) => String(l).length)) * 3.9); // room for the longest name
  const n = ch.values.length, plotH = n * row;
  const below = (v, i) => !ch.plain && ((ch.target != null && v < ch.target) || (ch.below_marks && ch.marks && v < ch.marks[i]));
  const anyBelow = ch.values.some((v, i) => below(v, i));
  const H = top + plotH + (anyBelow || ch.marks ? 24 : ch.target != null ? 14 : 4);
  const max = Math.max(...ch.values, ch.target || 0, ...(ch.marks || [0])) * 1.1;
  const x = (v) => left + (v / max) * (right - left);
  let g = `<line class="dash-grid" x1="${left}" x2="${left}" y1="${top - 2}" y2="${top + plotH}"/>`;
  // bars sorted by value, largest first, whichever view is showing; i stays the bar's own index (for its workings)
  const order = ch.values.map((v, i) => i).sort((p, q) => ch.values[q] - ch.values[p]);
  order.forEach((i, pos) => {
    const v = ch.values[i];
    const y = top + pos * row + (row - bh) / 2;
    g += `<g class="dash-row" data-detail="${i}" tabindex="0" role="button" aria-label="${esc(ch.labels[i])}: ${fmt(v)}. Show the workings.">`
      + `<rect class="dash-hit" x="0" y="${(top + pos * row).toFixed(1)}" width="${W}" height="${row}"/>`
      + `<text class="dash-axis" x="${left - 5}" y="${(y + bh - 1.5).toFixed(1)}" text-anchor="end">${esc(ch.labels[i])}</text>`
      + `<rect class="dash-bar dash-bar--h${below(v, i) ? ' dash-bar--below' : ''}" x="${left}" y="${y.toFixed(1)}" width="${(x(v) - left).toFixed(1)}" height="${bh}" rx="1.5"/>`;
    if (ch.marks) g += `<line class="dash-mark" x1="${x(ch.marks[i]).toFixed(1)}" x2="${x(ch.marks[i]).toFixed(1)}" y1="${(y - 2).toFixed(1)}" y2="${(y + bh + 2).toFixed(1)}"/>`;
    // value label at the end of the bar; if it would sit on the target line, it steps past the line
    const txt = fmt(v), tw = txt.length * 3.5;
    // label at the bar's end; if a marker sits just past the bar, the label goes before it when it fits, else after it
    let lx = x(v) + 3;
    if (ch.marks) { const mx = x(ch.marks[i]); if (mx >= x(v) - 1 && mx < lx + tw + 2) lx = mx + 3; }
    if (ch.target != null && lx - 2 < x(ch.target) && x(ch.target) < lx + tw + 2) lx = x(ch.target) + 3;
    g += `<text class="dash-value" x="${lx.toFixed(1)}" y="${(y + bh - 1.5).toFixed(1)}">${txt}</text></g>`;
  });
  if (ch.target != null) {   // drawn after the bars, so the target sits on top
    const tx = x(ch.target).toFixed(1);
    g += `<line class="dash-target" x1="${tx}" x2="${tx}" y1="${top - 3}" y2="${top + plotH + 1}"/>`;
    g += `<text class="dash-target-label" x="${tx}" y="${top + plotH + 10}" text-anchor="middle">Target ${fmt(ch.target)}</text>`;
  }
  if (anyBelow && !ch.marks) g += `<rect class="dash-bar--below" x="${left}" y="${H - 9}" width="7" height="7" rx="1"/><text class="dash-key" x="${left + 10}" y="${H - 3}">Below target</text>`;
  if (ch.marks) g += `<line class="dash-mark" x1="${left + 3}" x2="${left + 3}" y1="${H - 10}" y2="${H - 2}"/><text class="dash-key" x="${left + 9}" y="${H - 3}">${esc(ch.mark_label || '')}</text>`;
  const label = `${ch.title}: ${ch.labels.map((l, i) => `${l} ${fmt(ch.values[i])}`).join(', ')}${ch.target != null ? `; target ${fmt(ch.target)}` : ''}.`;
  return `<svg class="dash-svg" viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(label)}">${g}</svg>`;
}

// A time series (spend by month): columns, with the budget as a dotted step line
function renderSeries(se) {
  const fmt = CHART_FORMATS[se.format] || String;
  const W = 300, H = 120, top = 8, base = 96, left = 6, right = 294, n = se.values.length;
  const max = Math.max(...se.values, ...(se.budget || [0])) * 1.12;
  const slot = (right - left) / n, bw = slot * 0.62, y = (v) => base - (v / max) * (base - top);
  let g = `<line class="dash-grid" x1="${left}" x2="${right}" y1="${base}" y2="${base}"/>`;
  se.values.forEach((v, i) => {
    const x0 = left + i * slot + (slot - bw) / 2;
    g += `<rect class="dash-bar" x="${x0.toFixed(1)}" y="${y(v).toFixed(1)}" width="${bw.toFixed(1)}" height="${(base - y(v)).toFixed(1)}" rx="1.5"><title>${esc(se.labels[i])}: ${fmt(v)}</title></rect>`;
    if (n <= 14) g += `<text class="dash-axis" x="${(x0 + bw / 2).toFixed(1)}" y="${base + 9}" text-anchor="middle">${esc(se.labels[i])}</text>`;
    if (se.budget) g += `<line class="dash-target" x1="${(left + i * slot).toFixed(1)}" x2="${(left + (i + 1) * slot).toFixed(1)}" y1="${y(se.budget[i]).toFixed(1)}" y2="${y(se.budget[i]).toFixed(1)}"/>`;
  });
  if (n > 14) [0, n - 1].forEach((i) => { g += `<text class="dash-axis" x="${(left + i * slot + slot / 2).toFixed(1)}" y="${base + 9}" text-anchor="middle">${esc(se.labels[i])}</text>`; });
  if (se.budget) g += `<line class="dash-target" x1="${left}" x2="${left + 14}" y1="${H - 5}" y2="${H - 5}"/><text class="dash-key" x="${left + 18}" y="${H - 3}">Monthly budget</text>`;
  return `<p class="support-chart-title">${esc(se.title)}</p><svg class="dash-svg" viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(se.title)}: ${se.labels.map((l, i) => `${l} ${fmt(se.values[i])}`).join(', ')}">${g}</svg>`;
}

function openSupport(sp) {
  if (!sp) return;
  document.getElementById('support-title').textContent = sp.title;
  const rows = sp.rows.map((r) => `<tr><th scope="row">${esc(r[0])}</th>${r.slice(1).map((c) => `<td class="n">${esc(c)}</td>`).join('')}</tr>`).join('');
  const twoCol = sp.rows.every((r) => !r[2]);
  const head = twoCol ? '' : `<thead><tr>${sp.head.map((h, i) => `<th scope="col"${i ? ' class="n"' : ''}>${esc(h)}</th>`).join('')}</tr></thead>`;
  document.getElementById('support-body').innerHTML =
    `<p class="support-formula">${esc(sp.formula)}</p>`
    + `<table class="support-table${twoCol ? ' support-table--two' : ''}">${head}<tbody>${twoCol ? rows.replace(/<td class="n"><\/td>/g, '') : rows}</tbody></table>`
    + (sp.note ? `<p class="assumptions-intro">${esc(sp.note)}</p>` : '')
    + (sp.series ? renderSeries(sp.series) : '')
    + `<p class="support-foot">Sample data. Every figure is in the Excel download.</p>`;
  const dlg = document.getElementById('support-dialog');
  if (dlg.showModal) dlg.showModal(); else dlg.setAttribute('open', '');
}

function renderFourth(o) {
  // Kept deliberately simple: three headline numbers and one chart. Every
  // number opens its workings; the full lists are in the Excel and PDF.
  const f = o.fourth;
  const kpis = f.kpis.slice(0, 3).map((k, i) => `<button type="button" class="dash-kpi${k.spine ? ' dash-kpi--spine' : ''}" data-kpi="${i}"><span>${esc(k.label)}</span><strong>${esc(k.value)}</strong><em class="${k.cls}">${esc(k.sub)}</em><small class="dash-how">How it's worked out</small></button>`).join('');
  let ch = f.chart;
  let toggle = '';
  if (ch.views) {
    const v = ch.views.find((x) => x.id === dash.view) || ch.views[0];
    ch = { ...ch, values: v.values, format: v.format, target: v.target, marks: v.marks, mark_label: v.mark_label, below_marks: v.below_marks };
    toggle = `<div class="dash-toggle dash-toggle--small" role="group" aria-label="Show as">${ch.views.map((x) => `<button type="button" data-view="${x.id}" aria-pressed="${x.id === v.id}">${esc(x.label)}</button>`).join('')}</div>`;
  }
  return `<div class="dash-kpis">${kpis}</div>
    <div class="dash-chart"><div class="dash-chart-head"><p class="dash-chart-title">${esc(ch.title)}</p>${toggle}</div>${ch.subtitle ? `<p class="dash-chart-sub">${esc(ch.subtitle)}</p>` : ''}${renderChart(ch)}<p class="dash-hint">Tap a bar or a number to see how it's worked out.</p></div>`;
}

function renderAssumptions(o) {
  document.getElementById('assumptions-title').textContent = `Assumptions: ${o.name}`;
  document.getElementById('assumptions-body').innerHTML =
    `<p class="assumptions-intro">Sample data. Every figure on the dashboard is calculated from these assumptions by a driver-based model, then checked.</p>` +
    o.assumptions.map(([group, items]) => `<h3>${esc(group)}</h3><dl>${items.map(([k, v]) => `<div><dt>${esc(k)}</dt><dd>${esc(v)}</dd></div>`).join('')}</dl>`).join('') +
    `<h3>How final is this data?</h3><dl>${window.FOURTH_SHEET_DASHBOARD.status.map((m) => `<div><dt>${esc(m.label)} · ${esc(m.status)}</dt><dd>${esc(m.note)}</dd></div>`).join('')}</dl>` +
    `<h3>Checks</h3><ul class="assumptions-checks">${o.checks.map((c) => `<li>${esc(c)}</li>`).join('')}</ul>`;
}

function renderDash() {
  const data = window.FOURTH_SHEET_DASHBOARD;
  const o = data.orgs.find((x) => x.id === dash.org);
  const panel = document.getElementById('dash-panel');
  panel.innerHTML = dash.tab === 'fourth' ? renderFourth(o) : renderStatement(o, o.statements[dash.tab]);
  document.querySelectorAll('#hero-dash [role="tab"]').forEach((t) => {
    t.setAttribute('aria-selected', String(t.dataset.tab === dash.tab));
    t.tabIndex = t.dataset.tab === dash.tab ? 0 : -1;
    if (t.dataset.tab === 'pnl') t.textContent = o.id === 'nfp' ? 'Income & exp.' : 'P&L';
  });
  document.querySelectorAll('#dash-orgs button').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.org === dash.org)));
  const check = document.getElementById('dash-check');
  const ok = orgBalances(o);
  check.hidden = false;
  check.className = `dash-check ${ok ? 'is-ok' : 'is-bad'}`;
  check.textContent = ok ? '✓ Balances' : '✗ Does not balance';
  check.title = ok ? o.checks.join(' · ') : 'A check failed: re-run tools/sample_data.py';
  const rep = data.status[0];
  const chip = document.getElementById('dash-status');
  chip.hidden = false;
  chip.className = `dash-status is-${rep.status.toLowerCase()}`;
  chip.textContent = `${rep.label.split(' ')[0]} ${rep.status.toLowerCase()}`;
  chip.title = data.status.map((m) => m.note).join(' ');
  document.getElementById('dash-xlsx').href = o.exports.xlsx;
  document.getElementById('dash-pdf').href = o.exports.pdf;
  renderAssumptions(o);
}

/* ---------------------------------------------------------------------------
   DELIVERIES MAP (work.html) — deliveries in and out of an invented Brisbane
   distribution centre. Data: deliveries-data.js, GENERATED by
   tools/deliveries.py (don't type numbers in here). Map: Leaflet with
   OpenStreetMap tiles. Dot colour = share on time; red if anything overdue.
--------------------------------------------------------------------------- */
const DELIV_COL = { good: '#5e8b76', some: '#c8a77e', bad: '#8f4a3e', open: '#8e9cab' };
function delivBand(p) {
  const done = p.on_time + p.late + p.very_late;
  if (p.overdue) return 'bad';
  if (!done) return 'open';
  const r = p.on_time / done;
  return r >= 0.95 ? 'good' : r >= 0.8 ? 'some' : 'bad';
}
function setupDeliveries() {
  const box = document.getElementById('deliv');
  const D = window.FOURTH_SHEET_DELIVERIES;
  if (!box || !D) return;
  const st = { side: 'out', period: '30d' };
  let map = null, layer = null;
  if (window.L) {
    map = L.map('deliv-map', { scrollWheelZoom: false });
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 18, attribution: '&copy; OpenStreetMap contributors' }).addTo(map);
    L.marker([D.dc.lat, D.dc.lon], { icon: L.divIcon({ className: '', html: '<span class="deliv-dc">DC</span>', iconSize: null }) }).bindPopup(esc(D.dc.name)).addTo(map);
    layer = L.layerGroup().addTo(map);
  } else {
    document.getElementById('deliv-map').innerHTML = '<p style="padding:1rem">The map could not load. The Excel and PDF downloads have every delivery.</p>';
  }
  document.getElementById('deliv-periods').innerHTML = D.periods.map((p) => `<button type="button" data-period="${p.id}" aria-pressed="false">${esc(p.label)}</button>`).join('');
  const pct = (v) => (v == null ? '–' : `${Number(v).toFixed(1)}%`);
  function render() {
    const v = D[st.side][st.period], k = v.kpis, out = st.side === 'out';
    box.querySelectorAll('[data-side]').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.side === st.side)));
    box.querySelectorAll('[data-period]').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.period === st.period)));
    document.getElementById('deliv-status').innerHTML = `<span class="dash-status is-${v.status.toLowerCase()}">${esc(v.status)}</span>${esc(v.status_note)}`;
    document.getElementById('deliv-period-label').textContent = `${out ? 'Deliveries out to customers' : 'Deliveries in from suppliers'} · ${D.periods.find((p) => p.id === st.period).long}`;
    document.getElementById('deliv-kpis').innerHTML = [
      [out ? 'Deliveries' : 'Deliveries due', k.total.toLocaleString('en-AU'), ''],
      ['On time', pct(k.on_time_pct), k.on_time_pct != null && k.on_time_pct < 95 ? 'bad' : ''],
      ['Delivered late', k.late, ''],
      ['Overdue now', k.overdue, k.overdue ? 'bad' : ''],
      [out ? 'On the truck' : 'Due, not here yet', k.open, ''],
    ].map(([l, val, c]) => `<div class="${c}"><span>${l}</span><strong>${val}</strong></div>`).join('');
    document.getElementById('deliv-hot').innerHTML = v.hotspots.length
      ? v.hotspots.map((h) => `<li>${esc(h.label)}: <b>${Number(h.pct).toFixed(1)}% late</b> (${h.late} of ${h.of})</li>`).join('')
      : '<li>Nothing stands out for this period.</li>';
    if (!map) return;
    layer.clearLayers();
    const pts = [[D.dc.lat, D.dc.lon]];
    v.points.forEach((p) => {
      pts.push([p.lat, p.lon]);
      const done = p.on_time + p.late + p.very_late;
      const lines = [`<strong>${esc(p.name)}</strong>`, esc(p.sub), `${p.n} ${p.n === 1 ? 'delivery' : 'deliveries'}${done ? `, ${p.on_time} on time` : ''}`];
      if (p.late + p.very_late) lines.push(`${p.late + p.very_late} late${p.very_late ? ` (${p.very_late} by 2+ days)` : ''}`);
      if (p.overdue) lines.push(`<b style="color:#8f4a3e">${p.overdue} overdue now</b>`);
      if (p.open) lines.push(`${p.open} on the way`);
      L.circleMarker([p.lat, p.lon], { radius: 4 + Math.sqrt(p.n) * 1.4, color: '#ffffff', weight: 1.5, fillColor: DELIV_COL[delivBand(p)], fillOpacity: 0.9 })
        .bindPopup(lines.join('<br>')).addTo(layer);
    });
    map.fitBounds(pts, { padding: [20, 20], maxZoom: 11 });
  }
  box.addEventListener('click', (e) => {
    const b = e.target.closest('[data-side],[data-period]');
    if (!b) return;
    if (b.dataset.side) st.side = b.dataset.side; else st.period = b.dataset.period;
    render();
  });
  render();
}

/* ---------------------------------------------------------------------------
   REPORT PAGES (report-*.html) — one report per question on the SME and
   not-for-profit pages. Data: data/reports-data.js, GENERATED by
   tools/build_reports.py from tools/reports.py (don't type numbers in here).
   Sections: headline numbers, bar charts (categories, horizontal), column
   charts (months: incomplete months lighter, marked "to date"), tables,
   "what it shows / what you'd do". Every number opens its workings.
--------------------------------------------------------------------------- */
function renderColumns(labels, values, status, format, ids) {
  // Time series: columns, every one labelled (small, vertical), quarter ticks, incomplete months lighter.
  const fmt = CHART_FORMATS[format] || String;
  const n = values.length, W = Math.max(300, n * 22), H = 150, top = 34, base = 118, left = 4, right = W - 4;
  const vals = values.filter((v) => v != null);
  const max = Math.max(0, ...vals) * 1.08 || 1, min = Math.min(0, ...vals);
  const y = (v) => base - ((v - min) / (max - min)) * (base - top);
  const slot = (right - left) / n, bw = slot * 0.66, zero = y(0);
  let g = `<line class="dash-grid" x1="${left}" x2="${right}" y1="${zero.toFixed(1)}" y2="${zero.toFixed(1)}"/>`;
  values.forEach((v, i) => {
    const x0 = left + i * slot + (slot - bw) / 2, cx = (x0 + bw / 2).toFixed(1);
    const light = status && (status[i] === 'Incomplete' || status[i] === 'Provisional');
    g += `<g class="dash-row" data-point="${i}" tabindex="0" role="button" aria-label="${esc(labels[i])}: ${v == null ? 'no figure' : fmt(v)}${light ? ` (${status[i].toLowerCase()})` : ''}. Show the workings.">`
      + `<rect class="dash-hit" x="${(left + i * slot).toFixed(1)}" y="0" width="${slot.toFixed(1)}" height="${H}"/>`;
    if (v != null) {
      const yy = y(v), t = Math.min(yy, zero), h = Math.abs(zero - yy);
      g += `<rect class="dash-col${light ? ' dash-col--light' : ''}" x="${x0.toFixed(1)}" y="${t.toFixed(1)}" width="${bw.toFixed(1)}" height="${Math.max(h, 0.5).toFixed(1)}" rx="1.5"/>`;
      g += `<text class="dash-value dash-value--v" transform="translate(${(+cx + 2.5).toFixed(1)},${(t - 3).toFixed(1)}) rotate(-90)">${fmt(v)}</text>`;
    }
    if (i % 3 === 0 || i === n - 1) g += `<text class="dash-axis" x="${cx}" y="${base + 11}" text-anchor="middle">${esc(labels[i])}</text>`;
    if (status && status[i] === 'Incomplete') g += `<text class="dash-key dash-key--warn" x="${cx}" y="${base + 21}" text-anchor="middle">to date</text>`;
    g += '</g>';
  });
  return `<div class="report-scroll"><svg class="dash-svg report-cols" viewBox="0 0 ${W} ${H}" style="min-width:${Math.min(W, 640)}px" role="img">${g}</svg></div>`;
}

function setupReport() {
  const box = document.getElementById('report');
  const all = window.FOURTH_SHEET_REPORTS;
  if (!box || !all) return;
  const r = all[box.dataset.report];
  if (!r) return;
  const root = document.getElementById('report-root');
  const st = r.status[0];
  document.getElementById('report-meta').insertAdjacentHTML('beforeend',
    ` · <span class="dash-status is-${st.status.toLowerCase()}" title="${esc(r.status.map((x) => x.note).join(' '))}">${esc(st.label.split(' ')[0])} ${esc(st.status.toLowerCase())}</span> · October is still in progress`);
  const state = { block: 0, views: {} };
  const supports = [];                 // every clickable number on the page -> its workings
  const sup = (sp) => { supports.push(sp); return supports.length - 1; };

  function kpiHtml(sec) {
    return `<div class="dash-kpis report-kpis">${sec.items.map((k) => `<button type="button" class="dash-kpi" data-sup="${sup(k.support)}"><span>${esc(k.label)}</span><strong>${esc(k.value)}</strong><em class="${k.cls || ''}">${esc(k.sub || '')}</em><small class="dash-how">How it's worked out</small></button>`).join('')}</div>`;
  }
  function barsHtml(sec, key) {
    let ch = sec.chart, toggle = '';
    if (ch.views) {
      const cur = state.views[key] || ch.views[0].id;
      const v = ch.views.find((x) => x.id === cur) || ch.views[0];
      ch = { ...ch, values: v.values, format: v.format, target: v.target, marks: v.marks, mark_label: v.mark_label, below_marks: v.below_marks };
      toggle = `<div class="dash-toggle dash-toggle--small" role="group" aria-label="Show as">${sec.chart.views.map((x) => `<button type="button" data-view="${key}" data-id="${x.id}" aria-pressed="${x.id === v.id}">${esc(x.label)}</button>`).join('')}</div>`;
    }
    const det = (sec.chart.details || []).map((d) => sup(d));
    const one = sec.support ? sup(sec.support) : null;
    const svg = renderChart(ch).replace(/data-detail="(\d+)"/g, (m, i) => `data-sup="${det.length ? det[+i] : one}"`);
    return `<div class="report-card"><div class="dash-chart-head"><h2 class="report-h">${esc(ch.title)}</h2>${toggle}</div>${ch.subtitle ? `<p class="dash-chart-sub">${esc(ch.subtitle)}</p>` : ''}${svg}</div>`;
  }
  function seriesHtml(sec, key) {
    const dims = sec.dims || { line: ['All'], measure: [[Object.keys(sec.views)[0].split('|')[1], '']] };
    const cur = state.views[key] || { line: dims.line[0], measure: dims.measure[0][0] };
    state.views[key] = cur;
    const view = sec.views[`${cur.line}|${cur.measure}`];
    const grp = (name, items, val) => (items.length > 1 ? `<div class="dash-toggle dash-toggle--small" role="group" aria-label="${name}">${items.map(([id, lab]) => `<button type="button" data-series="${key}" data-dim="${name}" data-id="${esc(id)}" aria-pressed="${id === val}">${esc(lab)}</button>`).join('')}</div>` : '');
    const lineSup = (sec.supports || {})[cur.line] || [];
    const ids = lineSup.map((p) => sup(p));
    const cols = renderColumns(sec.labels, view.values, sec.status, view.format).replace(/data-point="(\d+)"/g, (m, i) => (ids.length ? `data-sup="${ids[+i]}"` : ''));
    return `<div class="report-card"><h2 class="report-h">${esc(sec.title)}</h2><div class="report-toggles">${grp('line', dims.line.map((l) => [l, l === 'All' ? 'All' : l]), cur.line)}${grp('measure', dims.measure, cur.measure)}</div>${cols}${sec.note ? `<p class="dash-chart-sub">${esc(sec.note)}</p>` : ''}</div>`;
  }
  function tableHtml(sec) {
    return `<div class="report-card"><h2 class="report-h">${esc(sec.title)}</h2><div class="st-scroll"><table class="st-table report-table"><thead><tr>${sec.head.map((h, i) => `<th scope="col"${i ? ' class="n"' : ''}>${esc(h)}</th>`).join('')}</tr></thead><tbody>${sec.rows.map((row) => `<tr${row[0] === 'Total' ? ' class="st-total"' : ''}>${row.map((c, i) => `<td${i ? ' class="n"' : ''}>${esc(c)}</td>`).join('')}</tr>`).join('')}</tbody></table></div></div>`;
  }
  function render() {
    supports.length = 0;
    const blocks = r.blocks;
    const b = blocks[state.block];
    let html = '';
    if (blocks.length > 1) html += `<div class="dash-toggle report-blocks" role="group" aria-label="Business">${blocks.map((x, i) => `<button type="button" data-block="${i}" aria-pressed="${i === state.block}">${esc(x.label)}</button>`).join('')}</div>`;
    b.sections.forEach((sec, i) => {
      const key = `${state.block}-${i}`;
      if (sec.type === 'kpis') html += kpiHtml(sec);
      else if (sec.type === 'bars') html += barsHtml(sec, key);
      else if (sec.type === 'series') html += seriesHtml(sec, key);
      else if (sec.type === 'table') html += tableHtml(sec);
      else if (sec.type === 'text') html += `<div class="report-text"><div><h2 class="report-h">What it shows</h2><p>${esc(sec.shows)}</p></div><div class="report-act"><h2 class="report-h">What you'd do about it</h2><p>${esc(sec.action)}</p></div></div>`;
      else if (sec.type === 'list') html += `<div class="report-card"><h2 class="report-h">${esc(sec.title)}</h2><ul class="report-list">${sec.items.map((x) => `<li>${esc(x)}</li>`).join('')}</ul></div>`;
    });
    html += '<p class="dash-hint">Tap any number, bar or month to see how it\'s worked out.</p>';
    root.innerHTML = html;
  }
  root.addEventListener('click', (e) => {
    const t = e.target.closest('[data-sup],[data-view],[data-series],[data-block]');
    if (!t) return;
    if (t.dataset.block) { state.block = +t.dataset.block; render(); }
    else if (t.dataset.view) { state.views[t.dataset.view] = t.dataset.id; render(); }
    else if (t.dataset.series) { const v = state.views[t.dataset.series]; v[t.dataset.dim] = t.dataset.id; render(); }
    else if (t.dataset.sup !== undefined && t.dataset.sup !== 'null') openSupport(supports[+t.dataset.sup]);
  });
  root.addEventListener('keydown', (e) => {
    const t = e.target.closest('[data-sup]');
    if (t && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); openSupport(supports[+t.dataset.sup]); }
  });
  const dlg = document.getElementById('support-dialog');
  document.getElementById('support-close').addEventListener('click', () => dlg.close());
  dlg.addEventListener('click', (e) => { if (e.target === dlg) dlg.close(); });
  render();
}

function setupHeroDash() {
  const box = document.getElementById('hero-dash');
  const data = window.FOURTH_SHEET_DASHBOARD;
  if (!box || !data) return;
  document.getElementById('dash-orgs').innerHTML = data.orgs.map((o) => `<button type="button" data-org="${o.id}" aria-pressed="false">${esc(o.toggle)}</button>`).join('');
  // switching organisation always opens on the fourth sheet
  box.querySelectorAll('[data-org]').forEach((b) => b.addEventListener('click', () => { dash.org = b.dataset.org; dash.tab = 'fourth'; renderDash(); }));
  const tabs = [...box.querySelectorAll('[role="tab"]')];
  tabs.forEach((t, i) => {
    t.addEventListener('click', () => { dash.tab = t.dataset.tab; renderDash(); });
    // arrow keys move between tabs (standard tab behaviour)
    t.addEventListener('keydown', (e) => {
      const d = e.key === 'ArrowRight' ? 1 : e.key === 'ArrowLeft' ? -1 : 0;
      if (!d) return;
      const next = tabs[(i + d + tabs.length) % tabs.length];
      dash.tab = next.dataset.tab; renderDash(); next.focus();
    });
  });
  const dlg = document.getElementById('assumptions-dialog');
  document.getElementById('dash-assumptions').addEventListener('click', () => (dlg.showModal ? dlg.showModal() : dlg.setAttribute('open', '')));
  document.getElementById('assumptions-close').addEventListener('click', () => dlg.close());
  // workings: headline numbers, chart bars and the %/$ toggle
  const sdlg = document.getElementById('support-dialog');
  document.getElementById('support-close').addEventListener('click', () => sdlg.close());
  sdlg.addEventListener('click', (e) => { if (e.target === sdlg) sdlg.close(); });
  const panel = document.getElementById('dash-panel');
  const org = () => window.FOURTH_SHEET_DASHBOARD.orgs.find((x) => x.id === dash.org);
  panel.addEventListener('click', (e) => {
    const k = e.target.closest('[data-kpi]'), r = e.target.closest('[data-detail]'), v = e.target.closest('[data-view]');
    if (k) openSupport(org().fourth.kpis[+k.dataset.kpi].support);
    else if (r) openSupport((org().fourth.chart.details || [])[+r.dataset.detail]);
    else if (v) { dash.view = v.dataset.view; renderDash(); }
  });
  panel.addEventListener('keydown', (e) => {
    const r = e.target.closest('[data-detail]');
    if (r && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); openSupport((org().fourth.chart.details || [])[+r.dataset.detail]); }
  });
  dlg.addEventListener('click', (e) => { if (e.target === dlg) dlg.close(); }); // click outside closes
  renderDash();
}

/* ---------------------------------------------------------------------------
   Page start-up
--------------------------------------------------------------------------- */
document.addEventListener('DOMContentLoaded', () => {
  const year = document.getElementById('year');
  if (year) year.textContent = new Date().getFullYear();

  // Mobile menu toggle (the ☰ button shown on narrow screens).
  const toggle = document.querySelector('.nav-toggle');
  const navLinks = document.querySelector('.nav-links');

  if (toggle && navLinks) {
    const setOpen = (open) => {
      toggle.setAttribute('aria-expanded', String(open));
      toggle.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
      navLinks.classList.toggle('open', open);
    };
    toggle.addEventListener('click', () => setOpen(toggle.getAttribute('aria-expanded') !== 'true'));
    // Close the menu after picking a section.
    navLinks.querySelectorAll('a').forEach((link) => link.addEventListener('click', () => setOpen(false)));
  }

  setupGameSlot();
  applyPrices();
  setupHeroDash(); setupDeliveries(); setupReport();
  renderReports(); // must run before watchEmbedLoad so live report cards get a loading state
  document.querySelectorAll('[data-embed]').forEach(watchEmbedLoad);
});
