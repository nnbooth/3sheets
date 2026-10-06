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
    preview: 'media/report-sales.png',
    question: "What's selling, what's cancelling and what's in the pipeline",
    embedUrl: '',
    status: 'In build',
  },
  {
    title: 'Purchasing',
    preview: 'media/report-purchasing.png',
    question: 'Which suppliers are late, and where costs are moving',
    embedUrl: '',
    status: 'In build',
  },
  {
    title: 'Payroll & overtime',
    preview: 'media/report-payroll.png',
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

   Tabs: P&L, Balance sheet, Cash flow, The fourth sheet.
   Toggle: SME · trades, SME · services, Not-for-profit.
   Phones show headline lines; larger screens show every line (CSS hides
   .detail rows under 720px). The page re-checks that everything adds up
   before showing the "Balances" tick.
--------------------------------------------------------------------------- */
const dash = { org: 'trades', tab: 'fourth' };

// Accounting format in $'000: 1,234 / (1,234) for negatives / - for zero
const acct = (n) => (n < 0 ? `(${Math.abs(n).toLocaleString('en-AU')})` : n === 0 ? '-' : n.toLocaleString('en-AU'));
const esc = (v) => String(v).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const CHART_FORMATS = {
  money0: (v) => `$${Math.round(v).toLocaleString('en-AU')}`,
  pct0: (v) => `${Math.round(v)}%`,
  cents_int: (v) => `${v}c`,
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
  return ok && [0, 1].every((i) => val(bs, 'Net assets')[i] === equity[i] && val(cf, 'Cash at 30 June')[i] === val(bs, 'Cash at bank')[i]);
}

function renderStatement(o, st) {
  const rows = st.rows.map((r) => {
    if (r.level === 'heading') return `<tr class="st-heading"><th colspan="3" scope="rowgroup">${esc(r.label)}</th></tr>`;
    return `<tr class="st-${r.level}${r.level === 'detail' ? ' detail' : ''}"><td>${esc(r.label)}</td>${r.values.map((v) => `<td class="n">${acct(v)}</td>`).join('')}</tr>`;
  }).join('');
  return `<p class="dash-chart-title">${esc(st.title)} · ${esc(o.name)} · $'000</p>
    <div class="st-scroll"><table class="st-table"><thead><tr><th scope="col">$'000</th>${o.columns.map((c) => `<th scope="col" class="n">${c}</th>`).join('')}</tr></thead><tbody>${rows}</tbody></table></div>
    <p class="dash-phone-note">Headline lines shown. Every line is on a larger screen, and in the Excel and PDF downloads.</p>`;
}

function renderChart(ch) {
  const W = 300, H = 120, top = 14, base = 92, left = 6, right = 294;
  const fmt = CHART_FORMATS[ch.format] || String;
  const max = Math.max(...ch.values, ch.target || 0) * 1.12;
  const slot = (right - left) / ch.values.length, bw = slot * 0.6;
  const y = (v) => base - (v / max) * (base - top);
  let g = `<line class="dash-grid" x1="${left}" x2="${right}" y1="${base}" y2="${base}"/>`;
  ch.values.forEach((v, i) => {
    const x = left + i * slot + (slot - bw) / 2, yy = y(v);
    g += `<rect class="dash-bar${i === ch.values.length - 1 ? ' dash-bar--now' : ''}" x="${x.toFixed(1)}" y="${yy.toFixed(1)}" width="${bw.toFixed(1)}" height="${(base - yy).toFixed(1)}" rx="2"><title>${ch.labels[i]}: ${fmt(v)}</title></rect>`;
    g += `<text class="dash-axis" x="${(x + bw / 2).toFixed(1)}" y="${base + 13}" text-anchor="middle">${ch.labels[i]}</text>`;
  });
  if (ch.target) {
    const ty = y(ch.target);
    g += `<line class="dash-target" x1="${left}" x2="${right}" y1="${ty.toFixed(1)}" y2="${ty.toFixed(1)}"/><text class="dash-target-label" x="${right}" y="${(ty - 4).toFixed(1)}" text-anchor="end">Target ${fmt(ch.target)}</text>`;
  }
  const label = `${ch.title}: ${ch.labels.map((l, i) => `${l} ${fmt(ch.values[i])}`).join(', ')}${ch.target ? `; target ${fmt(ch.target)}` : ''}.`;
  return `<svg class="dash-svg" viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(label)}">${g}</svg>`;
}

function renderFourth(o) {
  // Kept deliberately simple: three headline numbers and one chart.
  // The fuller fourth sheet (tables etc.) is in the Excel and PDF downloads.
  const f = o.fourth;
  const kpis = f.kpis.slice(0, 3).map((k) => `<div class="dash-kpi${k.spine ? ' dash-kpi--spine' : ''}"><span>${esc(k.label)}</span><strong>${esc(k.value)}</strong><em class="${k.cls}">${esc(k.sub)}</em></div>`).join('');
  return `<div class="dash-kpis">${kpis}</div>
    <div class="dash-chart"><p class="dash-chart-title">${esc(f.chart.title)}</p>${renderChart(f.chart)}</div>`;
}

function renderAssumptions(o) {
  document.getElementById('assumptions-title').textContent = `Assumptions: ${o.name}`;
  document.getElementById('assumptions-body').innerHTML =
    `<p class="assumptions-intro">Sample data. Every figure on the dashboard is calculated from these assumptions by a driver-based model, then checked.</p>` +
    o.assumptions.map(([group, items]) => `<h3>${esc(group)}</h3><dl>${items.map(([k, v]) => `<div><dt>${esc(k)}</dt><dd>${esc(v)}</dd></div>`).join('')}</dl>`).join('') +
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
  document.getElementById('dash-xlsx').href = o.exports.xlsx;
  document.getElementById('dash-pdf').href = o.exports.pdf;
  renderAssumptions(o);
}

function setupHeroDash() {
  const box = document.getElementById('hero-dash');
  const data = window.FOURTH_SHEET_DASHBOARD;
  if (!box || !data) return;
  document.getElementById('dash-orgs').innerHTML = data.orgs.map((o) => `<button type="button" data-org="${o.id}" aria-pressed="false">${esc(o.toggle)}</button>`).join('');
  box.querySelectorAll('[data-org]').forEach((b) => b.addEventListener('click', () => { dash.org = b.dataset.org; renderDash(); }));
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
  setupHeroDash();
  renderReports(); // must run before watchEmbedLoad so live report cards get a loading state
  document.querySelectorAll('[data-embed]').forEach(watchEmbedLoad);
});
