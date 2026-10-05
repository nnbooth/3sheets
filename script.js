/*
  script.js — The Fourth Sheet

  KEY LOCATIONS:
  - Report cards (edit this to add reports) .. REPORTS list, just below
  - Report card builder ...................... renderReports() / buildReportCard()
  - Loading message + 8-second fallback ...... watchEmbedLoad()
  - Game (load on Play) ...................... setupGameSlot()
  - Prices (switched off by default) ......... SHOW_PRICES / PRICES
  - Home-page sample dashboard ............... DASH_DATA / setupHeroDash()
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
   HERO DASHBOARD — the sample "fourth sheet" on the home page.

   SAMPLE DATA ONLY. Two views, switched by the Small business /
   Not-for-profit buttons. To change a number, edit DASH_DATA. The first
   view is also written into index.html so it shows without JavaScript.
--------------------------------------------------------------------------- */
const money = (v) => `$${Math.round(v).toLocaleString('en-AU')}`;
const cents = (v) => `$${v.toFixed(2)}`;

const DASH_DATA = {
  sb: {
    k1l: 'Cost to win a customer', k1v: '$184', k1d: ['good', '▼ 20% on last quarter'],
    k2l: 'Profit per customer', k2v: '$1,240', k2d: ['good', '▲ 8% on last quarter'],
    k3l: 'Cash in 30 days', k3v: '$42.6k', k3d: ['', 'after payroll and BAS'],
    chartTitle: 'Cost to win a customer, by month',
    chart: { values: [310, 284, 259, 231, 206, 184], target: 200, fmt: money, what: 'cost to win a customer' },
    head: ['Channel', 'Leads', 'Won', 'Cost to win'],
    rows: [['Referrals', '42', '18', ['good', '$95']], ['Google ads', '61', '14', ['', '$210']], ['Social', '38', '7', ['bad', '$260']]],
  },
  nfp: {
    k1l: 'Cost to raise a dollar', k1v: '$0.18', k1d: ['good', '▼ 16c since April'],
    k2l: 'Cost per program hour', k2v: '$62', k2d: ['', '▲ $4 on last quarter'],
    k3l: 'Cash runway', k3v: '7.5 months', k3d: ['', 'at current spend'],
    chartTitle: 'Cost to raise a dollar, by month',
    chart: { values: [0.34, 0.31, 0.27, 0.24, 0.21, 0.18], target: 0.2, fmt: cents, what: 'cost to raise a dollar' },
    head: ['Funding source', 'Raised', 'Share', 'Cost per $1'],
    rows: [['Grants', '$120k', '59%', ['good', '$0.06']], ['Events', '$48k', '23%', ['bad', '$0.41']], ['Donations', '$36k', '18%', ['', '$0.12']]],
  },
};
const DASH_MONTHS = ['Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep'];

// Bar chart as SVG. Keep the maths in step with the copy in index.html.
function renderDashChart({ values, target, fmt, what }) {
  const W = 300, H = 120, top = 14, base = 92, left = 6, right = 294;
  const max = Math.max(...values, target) * 1.12;
  const slot = (right - left) / values.length, bw = slot * 0.56;
  const y = (v) => base - (v / max) * (base - top);
  let g = `<line class="dash-grid" x1="${left}" x2="${right}" y1="${base}" y2="${base}"/>`;
  values.forEach((v, i) => {
    const x = left + i * slot + (slot - bw) / 2, yy = y(v);
    g += `<rect class="dash-bar${i === values.length - 1 ? ' dash-bar--now' : ''}" x="${x.toFixed(1)}" y="${yy.toFixed(1)}" width="${bw.toFixed(1)}" height="${(base - yy).toFixed(1)}" rx="2"/>`;
    g += `<text class="dash-axis" x="${(x + bw / 2).toFixed(1)}" y="${base + 14}" text-anchor="middle">${DASH_MONTHS[i]}</text>`;
  });
  const ty = y(target);
  g += `<line class="dash-target" x1="${left}" x2="${right}" y1="${ty.toFixed(1)}" y2="${ty.toFixed(1)}"/>`;
  g += `<text class="dash-target-label" x="${right}" y="${(ty - 4).toFixed(1)}" text-anchor="end">Target ${fmt(target)}</text>`;
  const label = `Bar chart: ${what} by month, falling from ${fmt(values[0])} to ${fmt(values[values.length - 1])}, against a target of ${fmt(target)}.`;
  return `<svg class="dash-svg" viewBox="0 0 ${W} ${H}" role="img" aria-label="${label}">${g}</svg>`;
}

function showDash(key) {
  const d = DASH_DATA[key];
  const dash = document.getElementById('hero-dash');
  if (!d || !dash) return;
  const set = (k, val) => {
    const node = dash.querySelector(`[data-k="${k}"]`);
    if (!node) return;
    if (Array.isArray(val)) { node.className = val[0]; node.textContent = val[1]; } else node.textContent = val;
  };
  ['k1l', 'k1v', 'k1d', 'k2l', 'k2v', 'k2d', 'k3l', 'k3v', 'k3d', 'chartTitle'].forEach((k) => set(k, d[k]));
  d.head.forEach((h, i) => set(`t${i}`, h));
  document.getElementById('dash-chart').innerHTML = renderDashChart(d.chart);
  document.getElementById('dash-rows').innerHTML = d.rows.map((r) =>
    `<tr><td>${r[0]}</td><td class="n">${r[1]}</td><td class="n">${r[2]}</td><td class="n ${r[3][0]}">${r[3][1]}</td></tr>`).join('');
  dash.querySelectorAll('[data-dash]').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.dash === key)));
}

function setupHeroDash() {
  const dash = document.getElementById('hero-dash');
  if (!dash) return;
  dash.querySelectorAll('[data-dash]').forEach((btn) => btn.addEventListener('click', () => showDash(btn.dataset.dash)));
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
