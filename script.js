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
   EXPORT MENU — one Export button and menu wherever there are downloads (report pages, the home hero, the
   deliveries map, and any future embedded report: Power BI or other iframe).

     const menu = mountExportMenu(container, { period, filterLabel, exports: {xlsx, pdf, pptx}, meta: {pdf_pages, pptx_slides} });
     menu.update({ period, filterLabel, exports, meta });     // when the period or the filter changes

   Static pages can declare one instead: <div data-export data-export-period="September 2026" data-export-filter="All"
   data-export-xlsx="…" data-export-pdf="…" data-export-pptx="…" data-export-pdf-pages="5" data-export-pptx-slides="9"></div>
   No exports for a period (exports null) shows the rows disabled: "Not available for a part month".
--------------------------------------------------------------------------- */
const EXPORT_FORMATS = [
  { fmt: 'xlsx', badge: 'XLSX', name: 'Excel workbook', what: 'Every figure as a live formula, the data behind it, and charts. Opens in Excel or Google Sheets.' },
  { fmt: 'pdf', badge: 'PDF', name: 'PDF report', what: 'Print-ready A4, the same pages as this screen. For the board pack or your accountant.' },
  { fmt: 'pptx', badge: 'PPTX', name: 'PowerPoint deck', what: 'Editable charts, one slide per finding. For the monthly meeting.' },
];
const ICON_DOWNLOAD = '<svg class="xm-ico" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M12 4v11m0 0-4.5-4.5M12 15l4.5-4.5M5 19h14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>';
const ICON_CHEVRON = '<svg class="xm-chev" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="m7 10 5 5 5-5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>';
let exportMenuCount = 0;
const fileSize = (n) => (n >= 1048576 ? `${(n / 1048576).toFixed(1)} MB` : `${Math.max(1, Math.round(n / 1024))} KB`);

function mountExportMenu(container, opts) {
  const id = `xm-${exportMenuCount += 1}`;
  let state = { ...opts };
  container.classList.add('xm');
  container.innerHTML = `<button type="button" class="xm-btn" aria-haspopup="true" aria-expanded="false" aria-controls="${id}">${ICON_DOWNLOAD}<span>Export</span>${ICON_CHEVRON}</button>`
    + `<div class="xm-menu" id="${id}" role="menu" aria-label="Export" hidden>`
    + `<p class="xm-head"></p>`
    + EXPORT_FORMATS.map((f) => `<a class="xm-item" role="menuitem" data-fmt="${f.fmt}" download><span class="xm-badge xm-badge--${f.fmt}">${f.badge}</span><span class="xm-text"><b>${f.name}</b><span>${f.what}</span><small class="xm-size"></small></span></a>`).join('')
    // (An "Include the workings" option would go here. Every export includes the workings for now.)
    + `<div class="xm-foot"><a class="xm-sub" role="menuitem" href="contact.html?topic=monthly">Send this to me on the 3rd business day each month &rarr;</a></div>`
    + `</div>`;
  const btn = container.querySelector('.xm-btn');
  const menu = container.querySelector('.xm-menu');
  const items = () => [...menu.querySelectorAll('[role="menuitem"]')].filter((x) => !x.hasAttribute('aria-disabled'));

  function paint() {
    const q = new URLSearchParams({ topic: 'monthly', report: state.report || document.title.split(' | ')[0], period: state.period || '', view: state.filterLabel || '' });
    menu.querySelector('.xm-sub').href = `contact.html?${q}`;
    const bits = [state.filterLabel, 'sample data'].filter(Boolean).map(esc).join(' · ');
    menu.querySelector('.xm-head').innerHTML = `Export <strong>${esc(state.period || '')}</strong>${bits ? ` · ${bits}` : ''}`;
    menu.querySelectorAll('.xm-item').forEach((a) => {
      const href = state.exports && state.exports[a.dataset.fmt];
      const size = a.querySelector('.xm-size');
      if (href) {
        a.href = href;
        a.removeAttribute('aria-disabled');
        a.removeAttribute('tabindex');
        const m = state.meta || {};
        size.textContent = a.dataset.fmt === 'pdf' && m.pdf_pages ? `${m.pdf_pages} page${m.pdf_pages === 1 ? '' : 's'}`
          : a.dataset.fmt === 'pptx' && m.pptx_slides ? `${m.pptx_slides} slide${m.pptx_slides === 1 ? '' : 's'}` : '';
      } else {
        a.removeAttribute('href');
        a.setAttribute('aria-disabled', 'true');
        a.tabIndex = -1;
        size.textContent = 'Not available for a part month';
      }
    });
  }
  function sizeExcel() {                         // the workbook's size, read when the menu opens (blank if that fails)
    const a = menu.querySelector('.xm-item[data-fmt="xlsx"]');
    if (!a.getAttribute('href')) return;
    fetch(a.getAttribute('href'), { method: 'HEAD' }).then((r) => {
      const n = Number(r.headers.get('content-length'));
      if (r.ok && n) a.querySelector('.xm-size').textContent = fileSize(n);
    }).catch(() => {});
  }
  function open() {
    paint();
    menu.hidden = false;
    btn.setAttribute('aria-expanded', 'true');
    container.classList.add('is-open');
    sizeExcel();
    (items()[0] || btn).focus();
  }
  function close(refocus = true) {
    if (menu.hidden) return;
    menu.hidden = true;
    btn.setAttribute('aria-expanded', 'false');
    container.classList.remove('is-open');
    if (refocus) btn.focus();
  }
  btn.addEventListener('click', () => (menu.hidden ? open() : close()));
  menu.addEventListener('keydown', (e) => {
    const list = items(), i = list.indexOf(document.activeElement);
    if (e.key === 'Escape') { e.preventDefault(); close(); }
    else if (e.key === 'ArrowDown' || e.key === 'ArrowUp') { e.preventDefault(); list[(i + (e.key === 'ArrowDown' ? 1 : -1) + list.length) % list.length].focus(); }
    else if (e.key === 'Home' || e.key === 'End') { e.preventDefault(); list[e.key === 'Home' ? 0 : list.length - 1].focus(); }
    else if (e.key === 'Tab') close(false);
  });
  menu.addEventListener('click', (e) => {
    const item = e.target.closest('.xm-item[aria-disabled]');
    if (item) { e.preventDefault(); return; }
    if (e.target.closest('.xm-item, .xm-sub')) setTimeout(() => close(), 0);   // a choice closes the menu
  });
  document.addEventListener('click', (e) => { if (!container.contains(e.target)) close(false); });
  paint();
  return { update(next) { state = { ...state, ...next }; paint(); }, close };
}

function mountStaticExportMenus() {
  document.querySelectorAll('[data-export]').forEach((el) => {
    const d = el.dataset;
    mountExportMenu(el, {
      period: d.exportPeriod, filterLabel: d.exportFilter,
      exports: d.exportXlsx || d.exportPdf || d.exportPptx ? { xlsx: d.exportXlsx, pdf: d.exportPdf, pptx: d.exportPptx } : null,
      meta: { pdf_pages: Number(d.exportPdfPages) || 0, pptx_slides: Number(d.exportPptxSlides) || 0 },
    });
  });
}

/* ---------------------------------------------------------------------------
   CONTACT PAGE (contact.html) — the form posts to a form service that emails Nathan (the form's action, still the
   placeholder [[FORM_ENDPOINT]]). Until that's set the form says so rather than pretending to send. A link from a
   report's Export menu (?topic=monthly&report=…&period=…&view=…) fills in what's being asked for.
--------------------------------------------------------------------------- */
function setupContactForm() {
  const form = document.getElementById('contact-form');
  if (!form) return;
  const q = new URLSearchParams(location.search);
  const status = document.getElementById('form-status');
  if (q.get('topic')) {
    const radio = form.querySelector(`input[name="topic"][value="${CSS.escape(q.get('topic'))}"]`);
    if (radio) radio.checked = true;
  }
  ['report', 'period', 'view'].forEach((k) => { form.elements[k].value = q.get(k) || ''; });
  if (q.get('topic') === 'monthly' && q.get('report')) {
    const req = document.getElementById('contact-request');
    req.innerHTML = `You're asking for <strong>${esc(q.get('report'))}</strong>${q.get('view') ? ` (${esc(q.get('view'))})` : ''}, sent to you on the 3rd business day of each month${q.get('period') ? `, starting from ${esc(q.get('period'))}` : ''}.`;
    req.hidden = false;
  }
  form.addEventListener('submit', (e) => {
    e.preventDefault();
    if (!form.reportValidity()) return;
    const action = form.getAttribute('action') || '';
    if (!/^https?:\/\//.test(action)) {                    // still the [[FORM_ENDPOINT]] placeholder
      status.textContent = "Thanks. This form goes live with the business email, so nothing has been sent yet. Please try again soon.";
      return;
    }
    status.textContent = 'Sending…';
    fetch(action, { method: 'POST', body: new FormData(form), headers: { Accept: 'application/json' } })
      .then((r) => { if (!r.ok) throw new Error(); form.reset(); status.textContent = "Thanks: that's with me. I'll be in touch within one business day."; })
      .catch(() => { status.textContent = "That didn't send. Please try again in a moment."; });
  });
  // the booking link is still a placeholder ([[BOOKING_URL]]): say so rather than jumping nowhere
  const book = document.querySelector('[data-booking]');
  if (book) book.addEventListener('click', (e) => {
    if (/^https?:\/\//.test(book.getAttribute('href'))) return;
    e.preventDefault();
    document.getElementById('book-status').textContent = 'Online booking opens soon.';
  });
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
  document.querySelectorAll('[data-price-note]').forEach((n) => { n.hidden = true; });   // "Talk to me about pricing" goes once prices show
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
  // over (+) / under (-) budget, said in words so an underspend isn't shown as a red negative
  pct_var: (v) => (Math.round(v * 10) === 0 ? 'on budget' : `${Math.abs(Number(v)).toFixed(1)}% ${v > 0 ? 'over' : 'under'}`),
  money_var: (v) => (Math.round(v) === 0 ? 'on budget' : `$${Math.abs(Math.round(v)).toLocaleString('en-AU')} ${v > 0 ? 'over' : 'under'}`),
  money0: (v) => (v < 0 ? `($${Math.round(-v).toLocaleString('en-AU')})` : `$${Math.round(v).toLocaleString('en-AU')}`),
  pct0: (v) => `${Math.round(v)}%`,
  pct1: (v) => (v < 0 ? `(${Math.abs(Number(v)).toFixed(1)}%)` : `${Number(v).toFixed(1)}%`),
  cents_int: (v) => `${v}¢`,
  int: (v) => Math.round(v).toLocaleString('en-AU'),
  money_k: (v) => (Math.abs(v) >= 1000 ? `$${Math.round(v / 1000).toLocaleString('en-AU')}k` : `$${v}`),
};

// EXPLANATIONS: the "gross margin, not profit" boxes on the report pages. Hide them for an audience that
// doesn't need them: set SHOW_EXPLANATIONS = false (whole site), or add ?explain=off to any link you send.
const SHOW_EXPLANATIONS = true;
if (!SHOW_EXPLANATIONS || new URLSearchParams(location.search).get('explain') === 'off') document.documentElement.classList.add('no-explain');

// Charts are drawn at their real pixel width (1 SVG unit = 1px), so chart text stays at a fixed, readable size
// (11px labels, 12px values) on every screen. chartWidth() measures the box a chart will sit in.
const chartWidth = (node, pad = 0) => Math.max(160, Math.round((node && node.clientWidth ? node.clientWidth : 320) - pad));
const textW = (t, px = 11) => String(t).length * px * 0.56;              // close enough for Roboto at chart sizes
const clip = (t, maxW, px = 11) => { const s = String(t); const n = Math.floor(maxW / (px * 0.56)); return s.length <= n ? s : `${s.slice(0, Math.max(1, n - 1))}…`; };

// Colour by meaning, not by sign: is this value good, close (warn) or bad? goodWhen 'higher' or 'lower';
// target is the line it's judged against; warnWithin (same units) counts as close. Returns a CSS class.
function tone(value, { goodWhen = 'higher', target = null, warnWithin = 0 } = {}) {
  if (value == null || target == null || Number.isNaN(Number(value))) return '';
  const gap = goodWhen === 'lower' ? target - value : value - target;     // positive = on the good side
  if (gap >= 0) return 'is-good';
  return -gap <= warnWithin ? 'is-warn' : 'is-bad';
}

// Negative numbers are always red (and in brackets)
const isNeg = (t) => /^\(?-?\$?\(|^-\d|^-\$|^\(\$?\d/.test(String(t).trim());
const negCls = (t) => (isNeg(t) ? ' neg' : '');

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
    return `<tr class="st-${r.level}${r.level === 'detail' ? ' detail' : ''}"><td>${esc(r.label)}</td>${r.values.map((v) => `<td class="n${v < 0 ? ' neg' : ''}">${acct(v)}</td>`).join('')}<td class="n st-change${change < 0 ? ' neg' : ''}">${acct(change)}</td></tr>`;
  }).join('');
  const sts = window.FOURTH_SHEET_DASHBOARD.status.slice(0, 2).map((m) => `${m.label}: ${m.status.toLowerCase()}`).join(' · ');
  return `<p class="dash-chart-title">${esc(st.title)} · ${esc(o.name)}</p><p class="dash-status-line">${esc(sts)}</p>
    <div class="st-scroll"><table class="st-table"><thead><tr><th scope="col">$</th>${o.columns.map((c) => `<th scope="col" class="n">${c}</th>`).join('')}<th scope="col" class="n st-change">Change</th></tr></thead><tbody>${rows}</tbody></table></div>
    <p class="dash-phone-note">Headline lines shown. Every line is on a larger screen, and in the Excel and PDF downloads.</p>`;
}

function renderChart(ch, width = 320) {
  // Categorical data -> horizontal bars (labels down the left), the default. Drawn at its real pixel width.
  // Every bar carries a value label and opens its workings when clicked. Grey = below target (unless the chart is
  // "plain"); red = losing money (below zero). "marks" = a small tick per bar (e.g. budget to date).
  const fmt = CHART_FORMATS[ch.format] || String;
  const W = Math.round(width), top = 8, row = 26, bh = 15;
  const valW = Math.max(...ch.values.map((v) => textW(fmt(v), 12))) + 10;
  const right = W - valW;
  const left = Math.min(Math.round(W * 0.42), 12 + Math.max(...ch.labels.map((l) => textW(l))));
  const n = ch.values.length, plotH = n * row;
  const below = (v, i) => !ch.plain && ((ch.target != null && v < ch.target) || (ch.below_marks && ch.marks && v < ch.marks[i]));
  const anyBelow = ch.values.some((v, i) => below(v, i));
  const H = top + plotH + (anyBelow || ch.marks || ch.variance ? 40 : ch.target != null ? 24 : 6);
  const lo = Math.min(0, ...ch.values);
  const max = Math.max(...ch.values, ch.target || 0, ...(ch.marks || [0])) * 1.05;
  const x = (v) => left + ((v - lo) / (max - lo || 1)) * (right - left);
  const x0 = x(0);
  let g = `<line class="dash-grid" x1="${x0.toFixed(1)}" x2="${x0.toFixed(1)}" y1="${top - 2}" y2="${top + plotH}"/>`;
  // bars sorted by value, largest first; the order is set once (by the first view) and doesn't move when the view changes
  const by = ch.orderBy || ch.values;
  const order = ch.values.map((v, i) => i).sort((p, q) => by[q] - by[p]);
  order.forEach((i, pos) => {
    const v = ch.values[i];
    const y = top + pos * row + (row - bh) / 2;
    const dim = ch.highlight && ch.labels[i] !== ch.highlight ? ' dash-row--dim' : '';
    // variance charts: off budget either way is red; within 1% amber; on budget neutral (judged on the % of budget)
    const vp = ch.variance ? Math.abs((ch.variancePct || ch.values)[i]) : 0;
    const cls = ch.variance ? (vp < 0.05 ? '' : vp < 1 ? ' dash-bar--warn' : ' dash-bar--bad') : v < 0 ? ' dash-bar--bad' : below(v, i) ? ' dash-bar--below' : '';
    const bx = Math.min(x(v), x0), bw = Math.abs(x(v) - x0);
    g += `<g class="dash-row${dim}" data-detail="${i}" tabindex="0" role="button" aria-label="${esc(ch.labels[i])}: ${fmt(v)}. Show the workings.">`
      + `<rect class="dash-hit" x="0" y="${(top + pos * row).toFixed(1)}" width="${W}" height="${row}"/>`
      + `<text class="dash-axis" x="${left - 8}" y="${(y + bh - 3).toFixed(1)}" text-anchor="end"><title>${esc(ch.labels[i])}</title>${esc(clip(ch.labels[i], left - 12))}</text>`
      + `<rect class="dash-bar dash-bar--h${cls}" x="${bx.toFixed(1)}" y="${y.toFixed(1)}" width="${bw.toFixed(1)}" height="${bh}" rx="2"/>`;
    if (ch.marks) g += `<line class="dash-mark" x1="${x(ch.marks[i]).toFixed(1)}" x2="${x(ch.marks[i]).toFixed(1)}" y1="${(y - 3).toFixed(1)}" y2="${(y + bh + 3).toFixed(1)}"/>`;
    // value label at the bar's end; it steps past a marker or the target line rather than sitting on it
    const txt = fmt(v), tw = textW(txt, 12);
    let lx = Math.max(x(v), x0) + 5;
    if (ch.marks) { const mx = x(ch.marks[i]); if (mx >= x(v) - 1 && mx < lx + tw + 3) lx = mx + 5; }
    if (ch.target != null && lx - 3 < x(ch.target) && x(ch.target) < lx + tw + 3) lx = x(ch.target) + 5;
    const bad = ch.variance ? vp >= 1 : v < 0;
    g += `<text class="dash-value${bad ? ' neg' : ''}" x="${lx.toFixed(1)}" y="${(y + bh - 3).toFixed(1)}">${txt}</text></g>`;
  });
  if (ch.target != null) {   // drawn after the bars, so the target sits on top
    const tx = x(ch.target).toFixed(1);
    g += `<line class="dash-target" x1="${tx}" x2="${tx}" y1="${top - 4}" y2="${top + plotH + 2}"/>`;
    g += `<text class="dash-target-label" x="${tx}" y="${top + plotH + 16}" text-anchor="middle">Target ${fmt(ch.target)}</text>`;
  }
  if (ch.variance) g += `<rect class="dash-bar--bad" x="${left}" y="${H - 13}" width="11" height="11" rx="2"/><text class="dash-key" x="${left + 16}" y="${H - 3}">Over or under budget</text>`
    + `<rect class="dash-bar--warn" x="${left + 168}" y="${H - 13}" width="11" height="11" rx="2"/><text class="dash-key" x="${left + 184}" y="${H - 3}">Within 1%</text>`;
  else if (anyBelow && !ch.marks) g += `<rect class="dash-bar--below" x="${left}" y="${H - 13}" width="11" height="11" rx="2"/><text class="dash-key" x="${left + 16}" y="${H - 3}">Below target</text>`;
  if (ch.marks) g += `<line class="dash-mark" x1="${left + 4}" x2="${left + 4}" y1="${H - 14}" y2="${H - 1}"/><text class="dash-key" x="${left + 12}" y="${H - 3}">${esc(ch.mark_label || '')}</text>`;
  const label = `${ch.title}: ${ch.labels.map((l, i) => `${l} ${fmt(ch.values[i])}`).join(', ')}${ch.target != null ? `; target ${fmt(ch.target)}` : ''}.`;
  return `<svg class="dash-svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(label)}">${g}</svg>`;
}

// A time series (spend by month): columns, with the budget as a dotted step line
function renderSeries(se, width = 560) {
  const fmt = CHART_FORMATS[se.format] || String;
  const W = Math.round(width), H = 190, top = 10, base = 150, left = 4, right = W - 4, n = se.values.length;
  const max = Math.max(...se.values, ...(se.budget || [0])) * 1.12;
  const slot = (right - left) / n, bw = slot * 0.62, y = (v) => base - (v / max) * (base - top);
  const every = Math.max(1, Math.ceil((n * 46) / (right - left)));          // month labels never overlap
  let g = `<line class="dash-grid" x1="${left}" x2="${right}" y1="${base}" y2="${base}"/>`;
  se.values.forEach((v, i) => {
    const bx = left + i * slot + (slot - bw) / 2;
    g += `<rect class="dash-bar" x="${bx.toFixed(1)}" y="${y(v).toFixed(1)}" width="${bw.toFixed(1)}" height="${(base - y(v)).toFixed(1)}" rx="2"><title>${esc(se.labels[i])}: ${fmt(v)}</title></rect>`;
    if (i % every === 0 || i === n - 1) g += `<text class="dash-axis" x="${(bx + bw / 2).toFixed(1)}" y="${base + 16}" text-anchor="middle">${esc(se.labels[i])}</text>`;
    if (se.budget) g += `<line class="dash-target" x1="${(left + i * slot).toFixed(1)}" x2="${(left + (i + 1) * slot).toFixed(1)}" y1="${y(se.budget[i]).toFixed(1)}" y2="${y(se.budget[i]).toFixed(1)}"/>`;
  });
  if (se.budget) g += `<line class="dash-target" x1="${left}" x2="${left + 18}" y1="${H - 8}" y2="${H - 8}"/><text class="dash-key" x="${left + 24}" y="${H - 4}">Monthly budget</text>`;
  return `<p class="support-chart-title">${esc(se.title)}</p><svg class="dash-svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(se.title)}: ${se.labels.map((l, i) => `${l} ${fmt(se.values[i])}`).join(', ')}">${g}</svg>`;
}

function openSupport(sp) {
  if (!sp) return;
  document.getElementById('support-title').textContent = sp.title;
  const rows = sp.rows.map((r) => `<tr><th scope="row">${esc(r[0])}</th>${r.slice(1).map((c) => `<td class="n${negCls(c)}">${esc(c)}</td>`).join('')}</tr>`).join('');
  const twoCol = sp.rows.every((r) => !r[2]);
  const head = twoCol ? '' : `<thead><tr>${sp.head.map((h, i) => `<th scope="col"${i ? ' class="n"' : ''}>${esc(h)}</th>`).join('')}</tr></thead>`;
  document.getElementById('support-body').innerHTML =
    `<p class="support-formula">${esc(sp.formula)}</p>`
    + `<table class="support-table${twoCol ? ' support-table--two' : ''}">${head}<tbody>${twoCol ? rows.replace(/<td class="n"><\/td>/g, '') : rows}</tbody></table>`
    + (sp.note ? `<p class="assumptions-intro">${esc(sp.note)}</p>` : '')
    + (sp.series ? renderSeries(sp.series, chartWidth(document.getElementById('support-body'), 40)) : '')
    + `<p class="support-foot">Sample data. Every figure is in the Excel download.${document.getElementById('assumptions-dialog') ? ' <button type="button" class="link-btn" data-open-assumptions>See all assumptions</button>' : ''}</p>`;
  const dlg = document.getElementById('support-dialog');
  if (dlg.showModal) dlg.showModal(); else dlg.setAttribute('open', '');
}

function renderFourth(o) {
  // Kept deliberately simple: three headline numbers and one chart. Every
  // number opens its workings; the full lists are in the Excel and PDF.
  const f = o.fourth;
  const kpis = f.kpis.slice(0, 3).map((k, i) => `<button type="button" class="dash-kpi${k.spine ? ' dash-kpi--spine' : ''}" data-kpi="${i}"><span>${esc(k.label)}</span><strong class="${(negCls(k.value) + (k.tone ? ` is-${k.tone}` : '')).trim()}">${esc(k.value)}</strong><em class="${k.cls}">${esc(k.sub)}</em><small class="dash-how">How it's worked out</small></button>`).join('');
  let ch = f.chart;
  let toggle = '';
  if (ch.views) {
    const v = ch.views.find((x) => x.id === dash.view) || ch.views[0];
    ch = { ...ch, values: v.values, format: v.format, target: v.target, marks: v.marks, mark_label: v.mark_label, below_marks: v.below_marks, variancePct: ch.views[0].values };
    toggle = `<div class="seg" role="group" aria-label="Show as">${ch.views.map((x) => `<button type="button" data-view="${x.id}" aria-pressed="${x.id === v.id}">${esc(x.label)}</button>`).join('')}</div>`;
  }
  const w = chartWidth(document.getElementById('dash-panel'), 32);
  return `<div class="dash-kpis">${kpis}</div>
    <div class="dash-chart"><div class="dash-chart-head"><p class="dash-chart-title">${esc(ch.title)}</p>${toggle}</div>${ch.subtitle ? `<p class="dash-chart-sub">${esc(ch.subtitle)}</p>` : ''}${renderChart(ch, w)}<p class="dash-hint">Click or tap any number for its workings.</p></div>`;
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
  if (!ok) console.warn('Sample statements do not balance: re-run tools/sample_data.py');
  if (check) {
  check.hidden = false;
  check.className = `dash-check ${ok ? 'is-ok' : 'is-bad'}`;
  check.textContent = ok ? '✓ Balances' : '✗ Does not balance';
  check.title = ok ? o.checks.join(' · ') : 'A check failed: re-run tools/sample_data.py';
  }
  const rep = data.status[0];
  const chip = document.getElementById('dash-status');
  if (chip) {
    chip.hidden = false;
    chip.className = `dash-status is-${rep.status.toLowerCase()}`;
    chip.textContent = `${rep.label.split(' ')[0]} ${rep.status.toLowerCase()}`;
    chip.title = data.status.map((m) => m.note).join(' ');
  }
  if (dash.menu) dash.menu.update({ period: rep.label, filterLabel: o.toggle, exports: o.exports, meta: o.exports_meta });
  const u = new URL(window.location.href);
  if (dash.org === data.orgs[0].id) u.searchParams.delete('business'); else u.searchParams.set('business', dash.org);
  if (u.href !== window.location.href) history.replaceState(null, '', u);
  renderAssumptions(o);
}

/* ---------------------------------------------------------------------------
   DELIVERIES MAP (examples.html) — deliveries in and out of an invented Brisbane
   distribution centre. Data: deliveries-data.js, GENERATED by
   tools/deliveries.py (don't type numbers in here). Map: Leaflet with
   OpenStreetMap tiles. Dot colour = share on time; red if anything overdue.
--------------------------------------------------------------------------- */
const DELIV_COL = { good: '#0E9F6E', some: '#b28a92', bad: '#8f4a3e', open: '#8e9cab' };
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
  const exportBox = document.getElementById('deliv-export');
  const menu = exportBox ? mountExportMenu(exportBox, { period: D.periods[0].long, exports: D.exports, meta: D.exports_meta }) : null;
  document.getElementById('deliv-periods').innerHTML = D.periods.map((p) => `<button type="button" data-period="${p.id}" aria-pressed="false">${esc(p.label)}</button>`).join('');
  const pct = (v) => (v == null ? '–' : `${Number(v).toFixed(1)}%`);
  function render() {
    const v = D[st.side][st.period], k = v.kpis, out = st.side === 'out';
    box.querySelectorAll('[data-side]').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.side === st.side)));
    box.querySelectorAll('[data-period]').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.period === st.period)));
    document.getElementById('deliv-status').innerHTML = `<span class="dash-status is-${v.status.toLowerCase()}">${esc(v.status)}</span>${esc(v.status_note)}`;
    document.getElementById('deliv-period-label').textContent = `${out ? 'Deliveries out to customers' : 'Deliveries in from suppliers'} · ${D.periods.find((p) => p.id === st.period).long}`;
    if (menu) menu.update({ period: D.periods.find((p) => p.id === st.period).long, filterLabel: 'In and out: every delivery' });
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
function niceTicks(min, max, n) {
  const span = max - min || Math.abs(max) || 1, step0 = span / n, mag = 10 ** Math.floor(Math.log10(step0));
  const step = [1, 2, 2.5, 5, 10].map((m) => m * mag).find((x) => x >= step0);
  const lo = Math.floor(min / step) * step, hi = Math.ceil(max / step) * step, out = [];
  for (let v = lo; v <= hi + step / 2; v += step) out.push(+v.toFixed(10));
  return out;
}

function renderArea(labels, values, status, format, mini, width) {
  // Time series as an area, drawn at its real pixel width: labelled y-axis with light gridlines, a dot per month
  // (tap for the workings), the highest and lowest values labelled (the latest on minis), incomplete or provisional
  // months dashed and lighter. Month labels thin out so they never overlap.
  const fmt = CHART_FORMATS[format] || String;
  const n = values.length, W = Math.round(width || (mini ? 280 : 720));
  const H = mini ? 96 : Math.round(Math.max(210, Math.min(320, W * 0.3)));
  const vals = values.filter((v) => v != null);
  const ticks = niceTicks(Math.min(0, ...vals), Math.max(0, ...vals), mini ? 2 : 4);
  const yMin = ticks[0], yMax = ticks[ticks.length - 1];
  const tickW = mini ? 0 : Math.max(...ticks.map((t) => textW(fmt(t)))) + 10;
  const left = mini ? 4 : tickW, right = W - (mini ? 6 : 12), top = mini ? 20 : 22, base = H - (mini ? 6 : 34);
  const x = (i) => left + (n === 1 ? (right - left) / 2 : (i * (right - left)) / (n - 1));
  const y = (v) => base - ((v - yMin) / (yMax - yMin || 1)) * (base - top);
  const done = (i) => !status || (status[i] !== 'Incomplete' && status[i] !== 'Provisional');
  const gid = `ag${renderArea.n = (renderArea.n || 0) + 1}`;          // Google Sheets style: colour under the line fading to nothing
  let g = `<defs><linearGradient id="${gid}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0E9F6E" stop-opacity="0.30"/><stop offset="1" stop-color="#0E9F6E" stop-opacity="0.03"/></linearGradient>`
    + `<linearGradient id="${gid}l" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0E9F6E" stop-opacity="0.16"/><stop offset="1" stop-color="#0E9F6E" stop-opacity="0.03"/></linearGradient></defs>`;
  if (!mini) ticks.forEach((t) => { g += `<line class="dash-gridline" x1="${left}" x2="${right}" y1="${y(t).toFixed(1)}" y2="${y(t).toFixed(1)}"/><text class="dash-ytick" x="${left - 8}" y="${(y(t) + 4).toFixed(1)}" text-anchor="end">${fmt(t)}</text>`; });
  const pts = values.map((v, i) => (v == null ? null : [x(i), y(v)]));
  const zeroY = y(Math.max(yMin, Math.min(0, yMax)));
  const firm = pts.map((p, i) => (p && done(i) ? p : null));
  const lastFirm = firm.reduce((a, p, i) => (p ? i : a), -1);
  const path = (arr) => arr.filter(Boolean).map((p, k) => `${k ? 'L' : 'M'}${p[0].toFixed(1)},${p[1].toFixed(1)}`).join('');   // straight segments, no rounding
  const firmPts = firm.filter(Boolean);
  if (firmPts.length) {
    g += `<path class="dash-area" fill="url(#${gid})" d="${path(firmPts)}L${firmPts[firmPts.length - 1][0].toFixed(1)},${zeroY.toFixed(1)}L${firmPts[0][0].toFixed(1)},${zeroY.toFixed(1)}Z"/>`;
    g += `<path class="dash-line" d="${path(firmPts)}"/>`;
  }
  const tail = pts.map((p, i) => (p && i >= lastFirm && lastFirm >= 0 ? p : null)).filter(Boolean);
  if (tail.length > 1) {
    g += `<path class="dash-area dash-area--light" fill="url(#${gid}l)" d="${path(tail)}L${tail[tail.length - 1][0].toFixed(1)},${zeroY.toFixed(1)}L${tail[0][0].toFixed(1)},${zeroY.toFixed(1)}Z"/>`;
    g += `<path class="dash-line dash-line--light" d="${path(tail)}"/>`;
  }
  if (yMin < 0) g += `<line class="dash-grid" x1="${left}" x2="${right}" y1="${zeroY.toFixed(1)}" y2="${zeroY.toFixed(1)}"/>`;
  const idx = values.map((v, i) => (v == null ? null : i)).filter((i) => i != null);
  const hi = idx.reduce((a, i) => (values[i] > values[a] ? i : a), idx[0]);
  const lo = idx.reduce((a, i) => (values[i] < values[a] ? i : a), idx[0]);
  const labelled = mini ? new Set([idx[idx.length - 1]]) : new Set([hi, lo]);   // the y-axis carries the rest: mark only the highest and lowest
  const slot = (right - left) / Math.max(1, n - 1);
  const every = Math.max(1, Math.ceil((n * 64) / Math.max(1, right - left)));   // a month label every ~64px, never crowded
  values.forEach((v, i) => {
    const cx = x(i);
    g += `<g class="dash-row" data-point="${i}" tabindex="0" role="button" aria-label="${esc(labels[i])}: ${v == null ? 'no figure' : fmt(v)}${done(i) ? '' : ` (${status[i].toLowerCase()})`}. Show the workings.">`
      + `<rect class="dash-hit" x="${(cx - slot / 2).toFixed(1)}" y="0" width="${slot.toFixed(1)}" height="${H}"/>`
      + `<line class="dash-guide" x1="${cx.toFixed(1)}" x2="${cx.toFixed(1)}" y1="${top}" y2="${base}"/>`;
    if (v != null) {
      g += `<circle class="dash-dot${done(i) ? '' : ' dash-dot--light'}" cx="${cx.toFixed(1)}" cy="${y(v).toFixed(1)}" r="${mini ? 2 : 3}"><title>${esc(labels[i])}: ${fmt(v)}</title></circle>`;
      if (labelled.has(i)) {
        const anchor = i === n - 1 ? 'end' : i === 0 ? 'start' : 'middle';
        const below = !mini && i === lo && i !== hi;               // the lowest point's value sits under its marker
        g += `<circle class="dash-marker" cx="${cx.toFixed(1)}" cy="${y(v).toFixed(1)}" r="${mini ? 3 : 4.5}"/>`
          + `<text class="dash-value dash-value--top${v < 0 ? ' neg' : ''}" x="${cx.toFixed(1)}" y="${(below ? y(v) + 19 : y(v) - 10).toFixed(1)}" text-anchor="${anchor}">${fmt(v)}</text>`;
      }
    }
    // month labels: first and last always; others every few so they never collide (minis show none: the value says it)
    const lastGap = (n - 1 - i) < every && i !== n - 1;
    if (!mini && ((i % every === 0 && !lastGap) || i === n - 1)) g += `<text class="dash-axis" x="${cx.toFixed(1)}" y="${(base + 17).toFixed(1)}" text-anchor="${i === 0 ? 'start' : i === n - 1 ? 'end' : 'middle'}">${esc(labels[i])}</text>`;
    if (!mini && status && status[i] === 'Incomplete') g += `<text class="dash-key dash-key--warn" x="${cx.toFixed(1)}" y="${base + 31}" text-anchor="end">to date</text>`;
    g += '</g>';
  });
  return `<svg class="dash-svg report-area${mini ? ' report-area--mini' : ''}" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" role="img">${g}</svg>`;
}

function renderColumns(labels, values, status, format, width) { return renderArea(labels, values, status, format, true, width); }

function mountReport(root, r, only, simple, opts = {}) {
  // Draws a report into root. One filter per block drives every section ("vary" sections have a version
  // for each filter value; bars and tables highlight it; series follow it). Only sections whose content
  // changed are redrawn, so charts don't re-animate when nothing about them changed.
  const state = { block: 0, filter: {}, views: {} };
  if (opts.initial) {                                   // e.g. from ?business=services&filter=Installations
    const bi = r.blocks.findIndex((x) => x.label && x.label.toLowerCase() === String(opts.initial.business || '').toLowerCase());
    if (bi >= 0) state.block = bi;
    const fb = r.blocks[state.block].filter;
    if (fb && opts.initial.filter != null && fb.options.some(([v]) => v === opts.initial.filter)) state.filter[state.block] = opts.initial.filter;
  }
  const supports = [];
  const cw = () => chartWidth(root, 38);                    // a card's inner width (cards have ~18px padding a side)
  const sup = (sp) => { supports.push(sp); return supports.length - 1; };
  const fval = () => { const b = r.blocks[state.block]; return b.filter ? (state.filter[state.block] ?? b.filter.options[0][0]) : 'All'; };

  function kpiHtml(sec) {
    return `<div class="dash-kpis report-kpis">${sec.items.map((k) => `<button type="button" class="dash-kpi" data-sup="${sup(k.support)}"><span>${esc(k.label)}</span><strong class="${(negCls(k.value) + (k.tone ? ` is-${k.tone}` : '')).trim()}">${esc(k.value)}</strong><em class="${k.cls || ''}">${esc(k.sub || '')}</em><small class="dash-how">How it's worked out</small></button>`).join('')}</div>`;
  }
  function barsHtml(sec, key) {
    let ch = sec.chart, toggle = '';
    if (ch.views) {
      const cur = state.views[key] || ch.views[0].id;
      const v = ch.views.find((x) => x.id === cur) || ch.views[0];
      ch = { ...ch, values: v.values, format: v.format, target: v.target, marks: v.marks, mark_label: v.mark_label, below_marks: v.below_marks, orderBy: sec.chart.views[0].values, variancePct: sec.chart.views[0].values };
      toggle = `<div class="seg" role="group" aria-label="Show as">${sec.chart.views.map((x) => `<button type="button" data-view="${key}" data-id="${x.id}" aria-pressed="${x.id === v.id}">${esc(x.label)}</button>`).join('')}</div>`;
    }
    if (sec.highlight_filter && ch.labels.includes(fval())) ch = { ...ch, highlight: fval() };
    const det = (sec.chart.details || []).map((d) => sup(d));
    const one = sec.support ? sup(sec.support) : null;
    const svg = renderChart(ch, Math.min(cw(), 860)).replace(/data-detail="(\d+)"/g, (m, i) => `data-sup="${det.length ? det[+i] : one}"`);
    return `<div class="report-card"><div class="dash-chart-head"><h2 class="report-h">${esc(ch.title)}</h2>${toggle}</div>${ch.subtitle ? `<p class="dash-chart-sub">${esc(ch.subtitle)}</p>` : ''}${svg}${simple ? '<p class="dash-hint">Click or tap any bar for its workings.</p>' : ''}</div>`;
  }
  function seriesHtml(sec, key, hasFilter) {
    const dims = sec.dims || { line: ['All'], measure: [[Object.keys(sec.views)[0].split('|')[1], '']] };
    const cur = state.views[key] || { line: dims.line[0], measure: dims.measure[0][0] };
    state.views[key] = cur;
    const line = hasFilter && dims.line.includes(fval()) ? fval() : cur.line;
    const view = sec.views[`${line}|${cur.measure}`] || sec.views[`All|${cur.measure}`];
    const grp = (name, items, val) => (items.length > 1 ? `<div class="seg" role="group" aria-label="${name}">${items.map(([id, lab]) => `<button type="button" data-series="${key}" data-dim="${name}" data-id="${esc(id)}" aria-pressed="${id === val}">${esc(lab)}</button>`).join('')}</div>` : '');
    const ids = ((sec.supports || {})[line] || []).map((p) => sup(p));
    const s0 = Math.max(0, view.values.findIndex((v) => v != null));
    const chart = renderArea(sec.labels.slice(s0), view.values.slice(s0), sec.status.slice(s0), view.format, false, cw()).replace(/data-point="(\d+)"/g, (m, i) => (ids.length ? `data-sup="${ids[+i + s0]}"` : ''));
    const measures = simple ? dims.measure.filter(([id]) => id !== 'margin') : dims.measure;
    const lineToggle = hasFilter || simple ? '' : grp('line', dims.line.map((l) => [l, l]), cur.line);
    const title = simple ? sec.title.replace(' by line', '').replace(' by type of work', '') : sec.title;
    const gmNote = simple && cur.measure.startsWith('margin') ? '<p class="dash-chart-sub">Gross margin is before overheads, so it is not profit. <a href="numbers-explained.html#gross-margin">What that means</a>.</p>' : '';
    const hint = simple ? '<p class="dash-hint">Click or tap any point for its workings.</p>' : '';
    return `<div class="report-card"><div class="dash-chart-head"><h2 class="report-h">${esc(title)}${hasFilter && line !== 'All' ? ` · ${esc(line)}` : ''}</h2><div class="report-toggles">${lineToggle}${grp('measure', measures, cur.measure)}</div></div>${chart}${sec.note && !simple ? `<p class="dash-chart-sub">${esc(sec.note)}</p>` : ''}${gmNote}${hint}</div>`;
  }
  function tableHtml(sec) {
    const hl = sec.highlight_filter ? fval() : null;
    return `<div class="report-card"><h2 class="report-h">${esc(sec.title)}</h2><div class="st-scroll"><table class="st-table report-table"><thead><tr>${sec.head.map((h, i) => `<th scope="col"${i ? ' class="n"' : ''}>${esc(h)}</th>`).join('')}</tr></thead><tbody>${sec.rows.map((row) => `<tr class="${row[0] === 'Total' ? 'st-total' : ''}${hl && hl !== 'All' && row[0] === hl ? ' st-hl' : ''}">${row.map((c, i) => `<td${i ? ` class="n${negCls(c)}"` : ''}>${esc(c)}</td>`).join('')}</tr>`).join('')}</tbody></table></div></div>`;
  }
  function sectionHtml(sec, key, hasFilter) {
    if (sec.type === 'vary') sec = sec.by[fval()] || sec.by.All || Object.values(sec.by)[0];
    if (only && !only.includes(sec.type)) return '';
    if (sec.type === 'kpis') return kpiHtml(sec);
    if (sec.type === 'bars') return barsHtml(sec, key);
    if (sec.type === 'series') return seriesHtml(sec, key, hasFilter);
    if (sec.type === 'table') return tableHtml(sec);
    if (sec.type === 'text') return simple ? `<p class="report-feature-line">${esc(sec.shows)}</p>` : `<div class="report-text"><div><h2 class="report-h">What it shows</h2><p>${esc(sec.shows)}</p></div><div class="report-act"><h2 class="report-h">What you'd do about it</h2><p>${esc(sec.action)}</p></div></div>`;
    if (sec.type === 'list') return `<div class="report-card"><h2 class="report-h">${esc(sec.title)}</h2><ul class="report-list">${sec.items.map((x) => `<li>${esc(x)}</li>`).join('')}</ul></div>`;
    if (sec.type === 'definition') return `<aside class="report-def"><strong>${esc(sec.title)}</strong><p>${esc(sec.text)}</p>${sec.link ? `<a href="${esc(sec.link)}">The numbers, explained &rarr;</a>` : ''}</aside>`;
    if (sec.type === 'insight') return `<button type="button" class="report-insight" data-sup="${sup(sec.support)}"><strong>${esc(sec.title)}</strong><span>${esc(sec.text)}</span><small class="dash-how">How it's worked out</small></button>`;
    return '';
  }
  const slots = [];
  function render() {
    supports.length = 0;
    const b = r.blocks[state.block];
    const parts = [];
    if (r.blocks.length > 1 && !simple) parts.push(`<div class="seg-bar report-blocks"><span class="seg-label">Business</span><div class="seg" role="group" aria-label="Business">${r.blocks.map((x, i) => `<button type="button" data-block="${i}" aria-pressed="${i === state.block}">${esc(x.label)}</button>`).join('')}</div></div>`);
    if (b.filter && !simple) parts.push(`<div class="report-filter seg-bar"><span class="seg-label">${esc(b.filter.label)}</span><div class="seg" role="group" aria-label="${esc(b.filter.label)}">${b.filter.options.map(([v, l]) => `<button type="button" data-filter="${esc(v)}" aria-pressed="${v === fval()}">${esc(l)}</button>`).join('')}</div></div>`);
    b.sections.forEach((sec, i) => parts.push(sectionHtml(sec, `${state.block}-${i}`, !!b.filter)));
    if (!simple) parts.push('<p class="dash-hint">Click or tap any number, bar or month for its workings.</p>');
    // only redraw (and so re-animate) sections whose content changed; others just get fresh workings links
    const norm = (h) => h.replace(/data-sup="\d+"/g, '').replace(/ag\d+/g, '');
    parts.forEach((h, i) => {
      if (!slots[i]) { slots[i] = document.createElement('div'); slots[i].className = 'report-slot'; root.appendChild(slots[i]); }
      const el = slots[i];
      if (el.dataset.h === h) return;
      const same = el.dataset.h !== undefined && (el.dataset.h === '' || norm(el.dataset.h) === norm(h));
      el.classList.toggle('no-anim', same);
      el.innerHTML = h;
      el.dataset.h = h;
    });
    while (slots.length > parts.length) slots.pop().remove();
    if (opts.onState) {
      const opt = b.filter ? b.filter.options.find(([v]) => v === fval()) : null;
      opts.onState({ business: r.blocks.length > 1 ? b.label : null, filter: b.filter ? fval() : null, filterLabel: opt ? opt[1] : null, isDefaultFilter: !b.filter || fval() === b.filter.options[0][0] });
    }
  }
  root.innerHTML = '';
  // redraw at the new width when the box resizes (no re-animation)
  let lastW = root.clientWidth;
  if ('ResizeObserver' in window) new ResizeObserver((entries, ro) => {
    if (!root.isConnected) { ro.disconnect(); return; }          // this report was replaced (e.g. a new period): stop
    if (Math.abs(root.clientWidth - lastW) < 8) return;
    lastW = root.clientWidth;
    slots.forEach((el) => el.classList.add('no-anim'));
    slots.forEach((el) => { el.dataset.h = ''; });
    render();
  }).observe(root);
  root.addEventListener('click', (e) => {
    const t = e.target.closest('[data-sup],[data-view],[data-series],[data-block],[data-filter]');
    if (!t) return;
    if (t.dataset.block) { state.block = +t.dataset.block; render(); }
    else if (t.dataset.filter !== undefined) { state.filter[state.block] = t.dataset.filter; render(); }
    else if (t.dataset.view) { state.views[t.dataset.view] = t.dataset.id; render(); }
    else if (t.dataset.series) { state.views[t.dataset.series][t.dataset.dim] = t.dataset.id; render(); }
    else if (t.dataset.sup !== undefined && t.dataset.sup !== 'null') openSupport(supports[+t.dataset.sup]);
  });
  root.addEventListener('keydown', (e) => {
    const t = e.target.closest('[data-sup]');
    if (t && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); openSupport(supports[+t.dataset.sup]); }
  });
  render();
}

function wireSupportDialog() {
  const dlg = document.getElementById('support-dialog');
  if (!dlg || dlg.dataset.wired) return;
  dlg.dataset.wired = '1';
  document.getElementById('support-close').addEventListener('click', () => dlg.close());
  dlg.addEventListener('click', (e) => { if (e.target === dlg) dlg.close(); });
}

function setupReport() {
  const all = window.FOURTH_SHEET_REPORTS;
  if (!all) return;
  wireSupportDialog();
  // a report page: the Period dropdown runs the report for another month (each period is built from the
  // data by tools/fourthsheet; its file is loaded when picked). ?period=YYYY-MM links straight to one.
  const box = document.getElementById('report');
  if (box && all[box.dataset.report]) {
    const slug = box.dataset.report;
    const base = all[slug];
    const sel = document.getElementById('report-period');
    const meta = document.getElementById('report-meta');
    const metaStart = meta.innerHTML;
    const ver = ((document.querySelector('script[src*="reports-data.js"]') || {}).src || '').split('?v=')[1] || '';
    const cache = window.FOURTH_SHEET_PERIODS = window.FOURTH_SHEET_PERIODS || {};
    cache[`${slug}|${base.period}`] = base;
    const load = (p) => new Promise((ok, fail) => {
      if (cache[`${slug}|${p}`]) { ok(cache[`${slug}|${p}`]); return; }
      const s_ = document.createElement('script');
      s_.src = `data/reports/${slug}/${p}.js${ver ? `?v=${ver}` : ''}`;
      s_.onload = () => (cache[`${slug}|${p}`] ? ok(cache[`${slug}|${p}`]) : fail());
      s_.onerror = fail;
      document.head.appendChild(s_);
    });
    const params = new URLSearchParams(window.location.search);
    let view = { business: params.get('business'), filter: params.get('filter') };     // restored from a copied link
    let current = base;
    const exportBox = document.getElementById('report-export');
    const menu = exportBox ? mountExportMenu(exportBox, { period: base.period_label, exports: base.exports, meta: base.exports_meta }) : null;
    const syncUrl = () => {
      const u = new URL(window.location.href);
      const set = (k, v) => (v ? u.searchParams.set(k, v) : u.searchParams.delete(k));
      set('period', current.period === base.default_period ? null : current.period);
      set('business', view.business && current.blocks.length > 1 && view.business !== current.blocks[0].label ? view.business.toLowerCase() : null);
      set('filter', view.isDefaultFilter ? null : view.filter);
      history.replaceState(null, '', u);
    };
    const show = (r) => {
      current = r;
      const st = r.status[0];
      const later = r.status.slice(1).map((x) => `${x.label} is still in progress`);
      meta.innerHTML = `${metaStart} · <span class="dash-status is-${st.status.toLowerCase()}" title="${esc(r.status.map((x) => x.note).join(' '))}">${esc(r.period_label)}: ${esc(st.status.toLowerCase())}</span>${later.length ? ` · ${esc(later.join(' · '))}` : ''}`;
      document.getElementById('report-period-note').textContent = r.part_note || '';
      const root = document.getElementById('report-root');
      root.innerHTML = '';
      const inner = document.createElement('div');
      root.appendChild(inner);
      mountReport(inner, r, null, false, {
        initial: view,
        onState: (v) => {
          view = v;
          if (menu) menu.update({ period: r.period_label, filterLabel: [v.business, v.filterLabel].filter(Boolean).join(' · '), exports: r.exports, meta: r.exports_meta });
          syncUrl();
        },
      });
    };
    const go = (p, push) => {
      sel.disabled = true;
      load(p).then((r) => {
        show(r);
        sel.value = p;
      }).catch(() => {
        document.getElementById('report-period-note').textContent = 'That period could not load. Try again, or pick another.';
        sel.value = base.period;
      }).finally(() => { sel.disabled = false; });
    };
    const want = params.get('period');
    const valid = (p) => base.periods.some((o) => o.value === p);
    if (want && valid(want) && want !== base.period) go(want, false); else show(base);
    if (sel) sel.addEventListener('change', () => go(sel.value, true));
  }
  // the featured chart on the SME and not-for-profit pages
  document.querySelectorAll('[data-report-feature]').forEach((el) => {
    const r = all[el.dataset.reportFeature];
    if (r) mountReport(el, r, el.dataset.only ? el.dataset.only.split(',') : null, true);
  });
  // a small live chart on every example report card
  const drawCard = (el) => {
    const r = all[el.dataset.reportCard];
    if (!r) return;
    const secs = r.blocks[0].sections.map((x) => (x.type === 'vary' ? (x.by.All || Object.values(x.by)[0]) : x));
    const k = secs.find((x) => x.type === 'kpis');
    const first = secs.find((x) => x.type === 'bars' || x.type === 'series');   // the report's main chart
    const bars = first && first.type === 'bars' ? first : null;
    const ser = first && first.type === 'series' ? first : null;
    let html = '';
    if (k) { const k0 = k.items[0]; html += `<p class="card-kpi"><strong class="${k0.tone ? `is-${k0.tone}` : ''}">${esc(k0.value)}</strong> <span>${esc(k0.label)}${k0.tone ? ` · ${esc(k0.sub)}` : ''}</span></p>`; }
    if (ser) {
      const dims = ser.dims || { line: ['All'], measure: [[Object.keys(ser.views)[0].split('|')[1], '']] };
      const v = ser.views[`${dims.line[0]}|${dims.measure[0][0]}`];
      const n = 12;
      html += renderColumns(ser.labels.slice(-n), v.values.slice(-n), ser.status.slice(-n), v.format, chartWidth(el)).replace(/ data-point="\d+" tabindex="0" role="button"/g, '');
    } else if (bars) {
      // a readable mini bar list (label, bar, value) for the biggest few, largest first
      const ch = bars.chart, v0 = ch.views ? ch.views[0] : ch;
      const fmt = CHART_FORMATS[v0.format] || String;
      const items = ch.labels.map((l, i) => [l, v0.values[i]]).sort((p, q) => q[1] - p[1]).slice(0, 5);
      const max = Math.max(...items.map((x) => x[1]), v0.target || 0) || 1;
      const below = (v) => !ch.plain && v0.target != null && v < v0.target;
      html += `<ul class="mini-bars">${items.map(([l, v]) => `<li><span class="mb-l">${esc(l)}</span><span class="mb-t"><i class="${below(v) ? 'below' : ''}" style="width:${(100 * v / max).toFixed(1)}%"></i></span><span class="mb-v${v < 0 ? ' neg' : ''}">${fmt(v)}</span></li>`).join('')}</ul>`;
    }
    el.innerHTML = html;
  };
  document.querySelectorAll('[data-report-card]').forEach((el) => {
    drawCard(el);
    if ('ResizeObserver' in window) { let w = el.clientWidth; new ResizeObserver(() => { if (Math.abs(el.clientWidth - w) >= 8) { w = el.clientWidth; drawCard(el); } }).observe(el); }
  });
}

function setupHeroDash() {
  const box = document.getElementById('hero-dash');
  const data = window.FOURTH_SHEET_DASHBOARD;
  if (!box || !data) return;
  const askedFor = new URLSearchParams(window.location.search).get('business');
  if (data.orgs.some((o) => o.id === askedFor)) dash.org = askedFor;
  const exportBox = document.getElementById('dash-export');
  if (exportBox) dash.menu = mountExportMenu(exportBox, { period: data.status[0].label });
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
  // "See all assumptions" sits in the workings dialog
  document.addEventListener('click', (e) => {
    if (!e.target.closest('[data-open-assumptions]')) return;
    const sd = document.getElementById('support-dialog');
    if (sd && sd.open) sd.close();
    if (dlg.showModal) dlg.showModal(); else dlg.setAttribute('open', '');
  });
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
  if ('ResizeObserver' in window) {
    let w = panel.clientWidth;
    new ResizeObserver(() => { if (Math.abs(panel.clientWidth - w) >= 8) { w = panel.clientWidth; panel.classList.add('no-anim'); renderDash(); } }).observe(panel);
  }
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

  // .seg groups: Left/Right (and Home/End) move to the next option and choose it
  document.addEventListener('keydown', (e) => {
    const btn = e.target.closest && e.target.closest('.seg[role="group"] > button');
    if (!btn || !['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(e.key)) return;
    const all = [...btn.parentElement.children];
    const i = all.indexOf(btn);
    const next = all[e.key === 'Home' ? 0 : e.key === 'End' ? all.length - 1 : (i + (e.key === 'ArrowRight' ? 1 : -1) + all.length) % all.length];
    e.preventDefault();
    next.click();
    const sel = next.dataset.org ? `[data-org="${next.dataset.org}"]` : next.dataset.view ? `[data-view="${next.dataset.view}"]${next.dataset.id ? `[data-id="${next.dataset.id}"]` : ''}`
      : next.dataset.filter !== undefined ? `[data-filter="${next.dataset.filter}"]` : next.dataset.block ? `[data-block="${next.dataset.block}"]`
      : next.dataset.series ? `[data-series="${next.dataset.series}"][data-id="${next.dataset.id}"]` : next.dataset.side ? `[data-side="${next.dataset.side}"]` : next.dataset.period ? `[data-period="${next.dataset.period}"]` : null;
    requestAnimationFrame(() => { const again = sel && document.querySelector(`.seg ${sel}`); (again || next).focus(); });   // the group may have been redrawn
  });

  setupGameSlot();
  applyPrices();
  setupHeroDash(); setupDeliveries(); setupReport(); mountStaticExportMenus(); setupContactForm();
  renderReports(); // must run before watchEmbedLoad so live report cards get a loading state
  document.querySelectorAll('[data-embed]').forEach(watchEmbedLoad);
});
