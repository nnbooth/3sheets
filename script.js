/*
  script.js — 3Sheets Consulting

  KEY LOCATIONS:
  - Google Sheet iframe auto-height .......... applyDynamicSheetHeight()
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
};

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
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
});
