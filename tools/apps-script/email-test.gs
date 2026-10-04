/**
 * email-test.gs — Google Apps Script behind the website's password-protected
 * "Email this pack" TEST feature (Live example section).
 *
 * WHAT IT DOES
 *   The website sends {action, password, to}. This script:
 *     1. checks the password against TEST_PASSWORD (a Script Property, so it
 *        is never in the website or in git);
 *     2. locks everyone out for 15 minutes after 5 wrong passwords;
 *     3. re-checks the email address (never trust the browser alone);
 *     4. sends ONE fixed email (the published sheet as a table) to that
 *        address. The website can't change the subject or body, so this
 *        can't be used to send anything else;
 *     5. caps sends per day (DAILY_LIMIT, default 20) and allows one email
 *        per address every 10 minutes.
 *
 * SETUP: see tools/apps-script/README.md. Deploy this as a NEW web app.
 * Do not reuse the old "Email Staff Individually" deployment.
 *
 * Script Properties (Project Settings > Script properties):
 *   TEST_PASSWORD  required. Long and random; share it only with testers.
 *   SHEET_ID       required. The spreadsheet ID (from its /d/<ID>/ address).
 *   SHEET_NAME     optional. Tab to send; defaults to the first tab.
 *   DAILY_LIMIT    optional. Max test emails per day; default 20.
 */

const MAX_FAILS = 5;                 // wrong passwords before lockout
const LOCKOUT_SECONDS = 15 * 60;     // lockout length
const PER_ADDRESS_SECONDS = 10 * 60; // one email per address per 10 minutes
const MAX_ROWS = 60, MAX_COLS = 12;  // keep the email a sensible size
const TIMEZONE = 'Australia/Brisbane';

function doPost(e) {
  let req;
  try {
    req = JSON.parse(e.postData.contents);
  } catch (err) {
    return reply({ ok: false, error: 'Bad request.' });
  }

  const props = PropertiesService.getScriptProperties();
  const cache = CacheService.getScriptCache();

  // 1-2. Password, with lockout after repeated failures
  const fails = Number(cache.get('fails') || 0);
  if (fails >= MAX_FAILS) return reply({ ok: false, error: 'Too many wrong passwords. Try again in 15 minutes.' });
  const expected = props.getProperty('TEST_PASSWORD');
  if (!expected) return reply({ ok: false, error: 'Not set up: TEST_PASSWORD is missing in Script Properties.' });
  if (typeof req.password !== 'string' || req.password !== expected) {
    cache.put('fails', String(fails + 1), LOCKOUT_SECONDS);
    return reply({ ok: false, error: 'Wrong password.' });
  }

  if (req.action === 'verify') return reply({ ok: true });
  if (req.action !== 'send') return reply({ ok: false, error: 'Unknown action.' });

  // 3. Email address, checked again here
  const to = String(req.to || '').trim();
  if (!isValidEmail(to)) return reply({ ok: false, error: "That email address doesn't look right." });

  // 4-5. Limits, then send (the lock stops two requests racing past a limit)
  const lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    const addressKey = 'to:' + to.toLowerCase();
    if (cache.get(addressKey)) return reply({ ok: false, error: 'Already sent to that address in the last 10 minutes.' });

    const dayKey = 'sent:' + Utilities.formatDate(new Date(), TIMEZONE, 'yyyy-MM-dd');
    const sentToday = Number(props.getProperty(dayKey) || 0);
    const limit = Number(props.getProperty('DAILY_LIMIT') || 20);
    if (sentToday >= limit) return reply({ ok: false, error: "Today's test limit has been reached." });
    if (MailApp.getRemainingDailyQuota() < 1) return reply({ ok: false, error: "Google's daily email quota has been reached." });

    MailApp.sendEmail({
      to: to,
      subject: 'Sample weekly reporting pack (test)',
      htmlBody: buildEmail(props),
      name: '3Sheets Consulting',
    });

    // Tidy old day counters, record this one
    props.getKeys().filter(k => k.indexOf('sent:') === 0 && k !== dayKey).forEach(k => props.deleteProperty(k));
    props.setProperty(dayKey, String(sentToday + 1));
    cache.put(addressKey, '1', PER_ADDRESS_SECONDS);
    return reply({ ok: true });
  } catch (err) {
    return reply({ ok: false, error: 'Sending failed. Check the script logs.' });
  } finally {
    lock.releaseLock();
  }
}

// Visiting the web app address in a browser just says what it is.
function doGet() {
  return ContentService.createTextOutput('3Sheets email test endpoint. Use the website.');
}

function isValidEmail(s) {
  return s.length <= 254 && /^[^\s@<>()[\]\\,;:"]+@[^\s@<>()[\]\\,;:"]+\.[A-Za-z]{2,}$/.test(s);
}

// The fixed email: the chosen sheet tab as a simple HTML table
function buildEmail(props) {
  const book = SpreadsheetApp.openById(props.getProperty('SHEET_ID'));
  const name = props.getProperty('SHEET_NAME');
  const sheet = (name && book.getSheetByName(name)) || book.getSheets()[0];
  const values = sheet.getDataRange().getDisplayValues().slice(0, MAX_ROWS).map(r => r.slice(0, MAX_COLS));

  const cell = (v, head) => `<${head ? 'th' : 'td'} style="border:1px solid #dce8dc;padding:6px 10px;text-align:left;${head ? 'background:#eaf6ee;' : ''}">${escapeHtml(v)}</${head ? 'th' : 'td'}>`;
  const rows = values.map((r, i) => '<tr>' + r.map(v => cell(v, i === 0)).join('') + '</tr>').join('');

  return '<div style="font-family:Arial,sans-serif;color:#25342a">' +
    '<h2 style="color:#2f7a5d">Sample weekly reporting pack</h2>' +
    '<p>This is a test email from the 3Sheets Consulting website. The figures are sample data.</p>' +
    '<table style="border-collapse:collapse;font-size:14px">' + rows + '</table>' +
    '<p style="color:#5f6f63;font-size:12px;margin-top:16px">You received this because your address was entered in the ' +
    "website's password-protected test feature. If that wasn't expected, you can ignore this email.</p></div>";
}

function escapeHtml(v) {
  return String(v).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

function reply(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj)).setMimeType(ContentService.MimeType.JSON);
}
