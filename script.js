/*
  script.js — 3Sheets Consulting

  KEY LOCATIONS:
  - Report cards (edit this to add reports) .. REPORTS list, just below
  - Report card builder ...................... renderReports() / buildReportCard()
  - Loading message + 8-second fallback ...... watchEmbedLoad()
  - Google Sheet auto-height ................. applyDynamicSheetHeight()
  - Game (load on Play) ...................... setupGameSlot()
  - Email test feature (password) ............ EMAIL_TEST_URL / setupEmailTest()
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
      img.alt = `${report.title} report preview: illustrative mock-up with invented data.`;
      img.loading = 'lazy';
      img.width = 1600;
      img.height = 900;
      link.appendChild(img);
      frame.appendChild(link);
    } else {
      frame.appendChild(buildReportMock(index));
    }
    // Reminder for the site owner; hidden unless <body class="dev-notes"> (see styles.css)
    const note = el('span', 'devnote devnote--big');
    note.setAttribute('role', 'note');
    note.append(
      el('strong', '', 'TO DO: BUILD THIS IN POWER BI'),
      el('small', '', `${report.title} report. Publish to web, then paste the link into this report's embedUrl in script.js.`)
    );
    frame.appendChild(note);
    frame.appendChild(el('p', 'report-pending-msg', report.preview ? 'Mock-up · report in build' : 'In build — preview coming soon'));
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
   Loading state for embedded iframes (Google Sheet and Power BI reports).

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
   Google Sheet auto-height.

   Reads the sheet's published CSV (the panel's data-csv-url) to count rows
   and columns, then sizes the frame so a short sheet doesn't leave a big
   empty box and a long one doesn't run off the page. Falls back to the
   defaults below if the CSV can't be read.
--------------------------------------------------------------------------- */
const MIN_VISIBLE_ROWS = 3;
const MAX_VISIBLE_ROWS = 30;
const DESKTOP_ROW_HEIGHT_PX = 30;
const MOBILE_ROW_HEIGHT_PX = 24;
const DESKTOP_BASE_HEIGHT_PX = 100;
const MOBILE_BASE_HEIGHT_PX = 90;
const MIN_DESKTOP_HEIGHT_PX = 230;
const MAX_DESKTOP_HEIGHT_PX = 500;
const MIN_MOBILE_HEIGHT_PX = 230;
const MAX_MOBILE_HEIGHT_PX = 380;
const DEFAULT_DESKTOP_HEIGHT_PX = 300;
const DEFAULT_MOBILE_HEIGHT_PX = 280;

const MIN_VISIBLE_COLS = 2;
const MAX_VISIBLE_COLS = 8;
const DESKTOP_COL_WIDTH_PX = 150;
const DESKTOP_FRAME_PADDING_PX = 150;
const MIN_DESKTOP_WIDTH_PX = 520;
const MAX_DESKTOP_WIDTH_PX = 980;
const DEFAULT_DESKTOP_WIDTH_PX = 860;

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function setSheetSize(panel, desktopHeight, mobileHeight, desktopWidth) {
  panel.style.setProperty('--sheet-height-desktop', `${desktopHeight}px`);
  panel.style.setProperty('--sheet-height-mobile', `${mobileHeight}px`);
  panel.style.setProperty('--sheet-width-desktop', `${desktopWidth}px`);
}

async function applyDynamicSheetHeight(panel) {
  const csvUrl = panel.dataset.csvUrl;
  if (!csvUrl) return; // CSS defaults apply

  try {
    const response = await fetch(csvUrl, { cache: 'no-store' });
    if (!response.ok) throw new Error('Unable to fetch sheet data');

    const rows = (await response.text())
      .split(/\r?\n/)
      .map((line) => line.trim())
      .filter(Boolean);

    const columnCount = rows[0] ? rows[0].split(',').length : 0;
    const cols = clamp(columnCount, MIN_VISIBLE_COLS, MAX_VISIBLE_COLS);
    const dataRows = clamp(Math.max(0, rows.length - 1), MIN_VISIBLE_ROWS, MAX_VISIBLE_ROWS);

    setSheetSize(
      panel,
      clamp(DESKTOP_BASE_HEIGHT_PX + dataRows * DESKTOP_ROW_HEIGHT_PX, MIN_DESKTOP_HEIGHT_PX, MAX_DESKTOP_HEIGHT_PX),
      clamp(MOBILE_BASE_HEIGHT_PX + dataRows * MOBILE_ROW_HEIGHT_PX, MIN_MOBILE_HEIGHT_PX, MAX_MOBILE_HEIGHT_PX),
      clamp(DESKTOP_FRAME_PADDING_PX + cols * DESKTOP_COL_WIDTH_PX, MIN_DESKTOP_WIDTH_PX, MAX_DESKTOP_WIDTH_PX)
    );
  } catch {
    setSheetSize(panel, DEFAULT_DESKTOP_HEIGHT_PX, DEFAULT_MOBILE_HEIGHT_PX, DEFAULT_DESKTOP_WIDTH_PX);
  }
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
   EMAIL TEST — password-protected "email this pack" test feature.

   EMAIL_TEST_URL is the address of YOUR Google Apps Script web app (from
   tools/apps-script/email-test.gs; setup steps in tools/apps-script/README.md).
   Leave it '' and the panel just says it isn't set up yet.

   Security: this page never knows the password. It sends what you type to
   the Apps Script, which checks it (with a lockout), re-checks the email
   address, applies limits and sends one fixed email. Anything checked only
   here could be read or bypassed by anyone viewing the page source.
   The password is kept in memory only, never saved.
--------------------------------------------------------------------------- */
const EMAIL_TEST_URL = '';

// Same rule as the Apps Script: a sensible length, one @, a real-looking domain
function isValidEmail(value) {
  return value.length <= 254 && /^[^\s@<>()[\]\\,;:"]+@[^\s@<>()[\]\\,;:"]+\.[A-Za-z]{2,}$/.test(value);
}

// Post to the Apps Script. Plain-text JSON keeps it a "simple" request,
// which Apps Script web apps accept from other websites.
async function callEmailService(payload) {
  const res = await fetch(EMAIL_TEST_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'text/plain;charset=utf-8' },
    body: JSON.stringify(payload),
    redirect: 'follow',
  });
  return res.json();
}

function setupEmailTest() {
  const box = document.getElementById('email-test');
  if (!box) return;
  const toggle = box.querySelector('.email-test-toggle');
  const body = document.getElementById('email-test-body');
  const unlockForm = document.getElementById('email-test-unlock');
  const sendForm = document.getElementById('email-test-send');
  const passwordInput = document.getElementById('email-test-password');
  const toInput = document.getElementById('email-test-to');
  const status = document.getElementById('email-test-status');
  let password = ''; // in memory only

  const say = (text, kind = '') => { status.textContent = text; status.dataset.kind = kind; };
  const busy = (form, on) => form.querySelectorAll('button, input').forEach((el) => { el.disabled = on; });

  toggle.addEventListener('click', () => {
    const open = toggle.getAttribute('aria-expanded') !== 'true';
    toggle.setAttribute('aria-expanded', String(open));
    body.hidden = !open;
    if (open) {
      if (!EMAIL_TEST_URL) say('Not set up yet: deploy the Apps Script and set EMAIL_TEST_URL in script.js.', 'error');
      (password ? toInput : passwordInput).focus();
    }
  });

  unlockForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    if (!EMAIL_TEST_URL) { say('Not set up yet: deploy the Apps Script and set EMAIL_TEST_URL in script.js.', 'error'); return; }
    const attempt = passwordInput.value;
    if (!attempt) { say('Enter the password.', 'error'); passwordInput.focus(); return; }
    busy(unlockForm, true); say('Checking…');
    try {
      const result = await callEmailService({ action: 'verify', password: attempt });
      if (result.ok) {
        password = attempt;
        passwordInput.value = '';
        unlockForm.hidden = true;
        sendForm.hidden = false;
        say('Unlocked.', 'ok');
        toInput.focus();
      } else {
        say(result.error || 'Wrong password.', 'error');
        passwordInput.select();
      }
    } catch {
      say("Couldn't reach the email service. Try again shortly.", 'error');
    } finally {
      busy(unlockForm, false);
    }
  });

  sendForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    const to = toInput.value.trim();
    if (!isValidEmail(to)) {
      toInput.setAttribute('aria-invalid', 'true');
      say('Enter a valid email address, like name@company.com.au.', 'error');
      toInput.focus();
      return;
    }
    toInput.removeAttribute('aria-invalid');
    busy(sendForm, true); say('Sending…');
    try {
      const result = await callEmailService({ action: 'send', password, to });
      if (result.ok) say(`Sent to ${to}. It can take a minute to arrive.`, 'ok');
      else say(result.error || 'Sending failed.', 'error');
    } catch {
      say("Couldn't reach the email service. Try again shortly.", 'error');
    } finally {
      busy(sendForm, false);
    }
  });
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
  setupEmailTest();
  renderReports(); // must run before watchEmbedLoad so live report cards get a loading state
  document.querySelectorAll('[data-embed]').forEach(watchEmbedLoad);
  document.querySelectorAll('.embed-panel[data-csv-url]').forEach(applyDynamicSheetHeight);
});
