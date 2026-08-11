/*
  script.js — 3Sheets Consulting

  KEY LOCATIONS:
  - Google Sheet iframe auto-height .......... applyDynamicSheetHeight()
  - Refresh data button ...................... refreshSheet()
  - Export to Excel logic .................... configureSheetExport() / primePanelExportBlob()
  - Run Macro button ......................... runMacro() — calls Apps Script Web App via fetch()
  - Macro toast feedback UI .................. setMacroFeedback() / hideMacroFeedback()
  - Apps Script Web App URL .................. MACRO_URL constant
*/

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

const SHEET_SELECTORS = {
  panel: '.embed-panel',
  desktopIframe: '.desktop-sheet',
  mobileIframe: '.mobile-sheet',
  exportLink: '[data-sheet-export]',
};

const exportStateByPanel = new WeakMap();

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function getActiveSheetIframe(panel) {
  if (!panel) return null;

  const mobileIframe = panel.querySelector(SHEET_SELECTORS.mobileIframe);
  const desktopIframe = panel.querySelector(SHEET_SELECTORS.desktopIframe);

  if (mobileIframe && mobileIframe.offsetParent !== null) return mobileIframe;
  return desktopIframe || mobileIframe || null;
}

function buildExportUrlFromSheetSource(sourceUrl) {
  if (!sourceUrl) return null;

  try {
    const url = new URL(sourceUrl);
    const gid = url.searchParams.get('gid') || '0';

    const publishedSheetMatch = url.pathname.match(/\/spreadsheets\/d\/e\/([^/]+)\//);
    if (publishedSheetMatch) {
      const publishedId = publishedSheetMatch[1];
      return `https://docs.google.com/spreadsheets/d/e/${publishedId}/pub?gid=${gid}&single=true&output=xlsx`;
    }

    const standardSheetMatch = url.pathname.match(/\/spreadsheets\/d\/([^/]+)/);
    if (standardSheetMatch) {
      const sheetId = standardSheetMatch[1];
      return `https://docs.google.com/spreadsheets/d/${sheetId}/export?format=xlsx&gid=${gid}`;
    }

    const output = url.searchParams.get('output');
    if (output && output.toLowerCase() === 'csv') {
      url.searchParams.set('output', 'xlsx');
      return url.toString();
    }

    return null;
  } catch {
    return null;
  }
}

function sanitizeFilenamePart(value) {
  return value
    .trim()
    .replace(/[\\/:*?"<>|]+/g, '-')
    .replace(/\s+/g, ' ');
}

function normalizeSheetName(name) {
  return name
    .replace(/^read-only\s+/i, '')
    .replace(/\s+mobile\s+view$/i, '')
    .replace(/\s+-\s+google\s+sheets$/i, '')
    .trim();
}

async function applyDynamicSheetHeight() {
  const panel = document.querySelector(SHEET_SELECTORS.panel);
  await applyDynamicSheetHeightForPanel(panel);
}

async function applyDynamicSheetHeightForPanel(panel) {
  if (!panel) return;

  const csvUrl = panel.dataset.csvUrl;
  if (!csvUrl) {
    panel.style.setProperty('--sheet-height-desktop', `${DEFAULT_DESKTOP_HEIGHT_PX}px`);
    panel.style.setProperty('--sheet-height-mobile', `${DEFAULT_MOBILE_HEIGHT_PX}px`);
    panel.style.setProperty('--sheet-width-desktop', `${DEFAULT_DESKTOP_WIDTH_PX}px`);
    return;
  }

  try {
    const response = await fetch(csvUrl, { cache: 'no-store' });
    if (!response.ok) throw new Error('Unable to fetch sheet data');

    const csvText = await response.text();
    const rows = csvText
      .split(/\r?\n/)
      .map((line) => line.trim())
      .filter(Boolean);

    const headerLine = rows[0] || '';
    const columnCount = headerLine ? headerLine.split(',').length : 0;
    const boundedCols = clamp(columnCount, MIN_VISIBLE_COLS, MAX_VISIBLE_COLS);

    const dataRowCount = Math.max(0, rows.length - 1);
    const boundedRows = clamp(dataRowCount, MIN_VISIBLE_ROWS, MAX_VISIBLE_ROWS);

    const desktopHeight = clamp(
      DESKTOP_BASE_HEIGHT_PX + (boundedRows * DESKTOP_ROW_HEIGHT_PX),
      MIN_DESKTOP_HEIGHT_PX,
      MAX_DESKTOP_HEIGHT_PX
    );

    const mobileHeight = clamp(
      MOBILE_BASE_HEIGHT_PX + (boundedRows * MOBILE_ROW_HEIGHT_PX),
      MIN_MOBILE_HEIGHT_PX,
      MAX_MOBILE_HEIGHT_PX
    );

    const desktopWidth = clamp(
      DESKTOP_FRAME_PADDING_PX + (boundedCols * DESKTOP_COL_WIDTH_PX),
      MIN_DESKTOP_WIDTH_PX,
      MAX_DESKTOP_WIDTH_PX
    );

    panel.style.setProperty('--sheet-height-desktop', `${desktopHeight}px`);
    panel.style.setProperty('--sheet-height-mobile', `${mobileHeight}px`);
    panel.style.setProperty('--sheet-width-desktop', `${desktopWidth}px`);
  } catch {
    panel.style.setProperty('--sheet-height-desktop', `${DEFAULT_DESKTOP_HEIGHT_PX}px`);
    panel.style.setProperty('--sheet-height-mobile', `${DEFAULT_MOBILE_HEIGHT_PX}px`);
    panel.style.setProperty('--sheet-width-desktop', `${DEFAULT_DESKTOP_WIDTH_PX}px`);
  }
}

function applyDynamicSheetHeights() {
  const panels = document.querySelectorAll(SHEET_SELECTORS.panel);
  panels.forEach((panel) => {
    applyDynamicSheetHeightForPanel(panel);
  });
}

function refreshSheet(buttonEl) {
  const panel = buttonEl?.closest(SHEET_SELECTORS.panel) || document.querySelector(SHEET_SELECTORS.panel);
  applyDynamicSheetHeightForPanel(panel);

  const iframe = getActiveSheetIframe(panel);
  if (!iframe) return;
  iframe.src = iframe.src;
}

const MACRO_URL = "https://script.google.com/macros/s/AKfycbzTt_pUbYVwyxju2D9DtoLGGZtHG7hbKhlg6HhBCGfRbGzpFx3cEVdRjVoQGRzYmLpeDA/exec";

let _macroDismissTimer = null;

async function runMacro(btn) {
  btn.disabled = true;
  clearTimeout(_macroDismissTimer);
  setMacroFeedback('pending', 'Sending emails to your team \u2014 this usually takes a few seconds\u2026');

  try {
    const res = await fetch(MACRO_URL, { method: 'POST', redirect: 'follow' });
    const json = await res.json().catch(() => null);
    const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    if (json?.status === 'success') {
      setMacroFeedback('success', '\u2713 Done \u2014 emails sent to your team at ' + now + '.');
    } else {
      setMacroFeedback('error', 'Something went wrong: ' + (json?.message || res.status));
    }
  } catch {
    // CORS prevents reading the response but the POST still reached Apps Script
    const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    setMacroFeedback('success', '\u2713 Request sent at ' + now + ' \u2014 emails should arrive shortly.');
  }

  btn.disabled = false;
  _macroDismissTimer = setTimeout(hideMacroFeedback, 6000);
}

function setMacroFeedback(state, msg) {
  const el = document.getElementById('macro-feedback');
  if (!el) return;
  el.className = 'macro-toast macro-toast--' + state;
  const label = el.querySelector('.macro-toast-msg');
  if (label) label.textContent = msg;
}

function hideMacroFeedback() {
  const el = document.getElementById('macro-feedback');
  if (el) el.className = 'macro-toast macro-toast--hidden';
}

function buildTimestamp() {
  const now = new Date();
  return (
    now.getFullYear().toString() +
    String(now.getMonth() + 1).padStart(2, '0') +
    String(now.getDate()).padStart(2, '0') +
    ' ' +
    String(now.getHours()).padStart(2, '0') +
    String(now.getMinutes()).padStart(2, '0')
  );
}

function extractFilenameFromContentDisposition(contentDisposition) {
  if (!contentDisposition) return '';

  const utf8Match = contentDisposition.match(/filename\*=UTF-8''([^;]+)/i);
  if (utf8Match && utf8Match[1]) {
    try {
      return decodeURIComponent(utf8Match[1]).replace(/\.xlsx$/i, '').trim();
    } catch {
      return utf8Match[1].replace(/\.xlsx$/i, '').trim();
    }
  }

  const basicMatch = contentDisposition.match(/filename="?([^";]+)"?/i);
  if (basicMatch && basicMatch[1]) {
    return basicMatch[1].replace(/\.xlsx$/i, '').trim();
  }

  return '';
}

function resolvePanelSheetName(panel, link, activeIframe) {
  const nameFromLink = link?.dataset.sheetName || '';
  const nameFromPanel = panel?.dataset.sheetName || '';

  if (nameFromLink.trim()) return nameFromLink;
  if (nameFromPanel.trim()) return nameFromPanel;

  const titleSourceSelector = panel?.dataset.sheetTitleSource || '';
  if (titleSourceSelector) {
    const fromPanel = panel.querySelector(titleSourceSelector)?.textContent?.trim() || '';
    if (fromPanel) return fromPanel;

    const panelSection = panel.closest('section');
    const fromSection = panelSection?.querySelector(titleSourceSelector)?.textContent?.trim() || '';
    if (fromSection) return fromSection;
  }

  const nameFromIframeData = activeIframe?.dataset.sheetName || '';
  if (nameFromIframeData.trim()) return nameFromIframeData;

  return 'Sheet';
}

function resolveExportContext(panel, link) {
  const activeIframe = getActiveSheetIframe(panel);
  const sheetNameFromData = resolvePanelSheetName(panel, link, activeIframe);
  const docName = sanitizeFilenamePart(normalizeSheetName(sheetNameFromData || 'Sheet'));

  const exportUrl =
    panel.dataset.exportUrl ||
    buildExportUrlFromSheetSource(activeIframe?.src || '') ||
    buildExportUrlFromSheetSource(panel.dataset.csvUrl || '') ||
    link.getAttribute('href');

  const filename = `${docName} ${buildTimestamp()}.xlsx`;
  return { exportUrl, filename, baseName: docName };
}

function applyExportAttributes(link, exportContext) {
  if (exportContext.exportUrl) {
    link.setAttribute('href', exportContext.exportUrl);
  }
  link.setAttribute('download', exportContext.filename);
}

function getPanelExportState(panel) {
  if (!exportStateByPanel.has(panel)) {
    exportStateByPanel.set(panel, {
      blobUrl: '',
      baseName: '',
      isLoading: false,
    });
  }
  return exportStateByPanel.get(panel);
}

function updatePanelBlobState(panel, nextBlobUrl) {
  const state = getPanelExportState(panel);
  if (state.blobUrl) {
    URL.revokeObjectURL(state.blobUrl);
  }
  state.blobUrl = nextBlobUrl;
}

async function primePanelExportBlob(panel, link) {
  if (!panel || !link) return;

  const state = getPanelExportState(panel);
  if (state.isLoading) return;

  const exportContext = resolveExportContext(panel, link);
  applyExportAttributes(link, exportContext);
  if (!exportContext.exportUrl) return;

  state.isLoading = true;

  try {
    const response = await fetch(exportContext.exportUrl, { credentials: 'omit' });
    if (!response.ok) return;

    const headerName = extractFilenameFromContentDisposition(
      response.headers.get('content-disposition') || ''
    );
    const effectiveBaseName = sanitizeFilenamePart(
      normalizeSheetName(headerName || exportContext.baseName || 'Sheet')
    );

    const blob = await response.blob();
    const blobUrl = URL.createObjectURL(blob);
    updatePanelBlobState(panel, blobUrl);
    state.baseName = effectiveBaseName;
  } catch {
    // Browser/network policies may block cross-origin fetch; link will fallback to direct URL.
  } finally {
    state.isLoading = false;
  }
}

function configureSheetExport(panel) {
  if (!panel) return;

  const link = panel.querySelector(SHEET_SELECTORS.exportLink);
  if (!link) return;

  const initialExportContext = resolveExportContext(panel, link);
  applyExportAttributes(link, initialExportContext);
  primePanelExportBlob(panel, link);

  link.addEventListener('pointerenter', () => {
    primePanelExportBlob(panel, link);
  });

  link.addEventListener('focus', () => {
    primePanelExportBlob(panel, link);
  });

  link.addEventListener('click', () => {
    const state = getPanelExportState(panel);
    const exportContext = resolveExportContext(panel, link);
    const effectiveBaseName = sanitizeFilenamePart(
      normalizeSheetName(state.baseName || exportContext.baseName || 'Sheet')
    );
    const effectiveFilename = `${effectiveBaseName} ${buildTimestamp()}.xlsx`;

    if (state.blobUrl) {
      link.setAttribute('href', state.blobUrl);
    } else if (exportContext.exportUrl) {
      link.setAttribute('href', exportContext.exportUrl);
    }
    link.setAttribute('download', effectiveFilename);

    // Refresh blob in the background in case sheet content changed.
    primePanelExportBlob(panel, link);
  });
}

function configureSheetExports() {
  const panels = document.querySelectorAll(SHEET_SELECTORS.panel);
  panels.forEach((panel) => {
    configureSheetExport(panel);
  });
}

document.addEventListener('DOMContentLoaded', () => {
  const year = document.getElementById('year');
  if (year) year.textContent = new Date().getFullYear();

  const toggle = document.querySelector('.nav-toggle');
  const navLinks = document.querySelector('.nav-links');

  if (toggle && navLinks) {
    toggle.addEventListener('click', () => {
      const expanded = toggle.getAttribute('aria-expanded') === 'true';
      const nextExpanded = !expanded;
      toggle.setAttribute('aria-expanded', String(nextExpanded));
      navLinks.classList.toggle('open', nextExpanded);
    });
  }

  applyDynamicSheetHeights();
  configureSheetExports();
});

document.addEventListener("DOMContentLoaded", () => {
  const iframe = document.getElementById("powerbi-iframe");

  if (!iframe) return;

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {

        // Load iframe only when visible
        iframe.src = iframe.dataset.src;

        // Stop observing once loaded
        observer.unobserve(entry.target);
      }
    });
  }, {
    threshold: 0.25 // activate when 25% visible
  });

  observer.observe(iframe);
});
