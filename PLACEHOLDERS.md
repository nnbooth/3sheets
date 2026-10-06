# Project notes: decisions, placeholders and how things work

## Where the business is (current thinking)

- **The Fourth Sheet** (Nathan Booth, Brisbane). *"Your accountant gives you three sheets. I give you the fourth."* The fourth sheet is the numbers underneath the P&L, balance sheet and cash flow: what a customer costs to win, which jobs make money, what a dollar costs to raise.
- **Who for:** SMEs (never "small business") and not-for-profits. Management-accountant thinking *without the full-time hire*.
- **Offer ladder:** Set up and hand over → Bedding-in → Monthly. Where a client has no usable data, setup includes the processes and frameworks to start capturing it. Small fixed-scope automations ("quick wins") on the side.
- **What makes it different:** daily numbers with drill-downs (year > quarter > month > week > day) instead of waiting for the accountant to close the month; month-end reporting against the prior month; granular down to the job, engagement, grant or delivery.
- **Technology agnostic:** data comes from wherever it lives and goes into whatever the client already uses. Copy names sources and outcomes, not products.
- **Data design:** all supporting data is built to live in a cloud database (star schema, daily grain) so any dashboard can be rebuilt in Power BI or another tool.
- **Claims:** no client results claimed; every sample is labelled "Sample data" and adds up. AI is "built with AI, checked by hand", with no big-data or AI-query promises. No "CPA" anywhere until confirmed. Prices off until the CPA certificate application is in.
- **Every report or dashboard** gets an Excel (formatted) and a PDF download.

**Site structure (hub and spoke):** `index.html` (home: hero, two audience doors, credibility strip, short ladder, contact) → `sme.html`, `not-for-profit.html`, `work.html` (who I've worked with, example dashboards, reports, templates, the deliveries map, tools, game), `how-we-work.html` (full ladder, steps, quick wins, Excel, AI) and `about.html`. The header, nav, contact block and footer are repeated in each page: change them in all six files.

Every detail that isn't final is marked with a token like `[[EMAIL]]`. Search the repo for `[[` to find them all. Most are in `index.html`.

## How placeholders look on the page

The live page never shows raw `[[TOKEN]]` text. Each token appears in one of three ways:

1. **TBC chip in body text:** a small dashed pill, e.g. `<span class="tbc" data-placeholder="[[EMAIL]]">Email TBC</span>`.
   **To fill in:** replace the whole `<span …>…</span>` with the real value.
2. **Fallback on a button or link:** e.g. `href="#contact" data-placeholder="[[BOOKING_URL]]"`.
   **To fill in:** change the `href`, then delete the `data-placeholder="…"` attribute.
3. **In `<head>` tags** (not visible): e.g. `https://[[DOMAIN]]/`.
   **To fill in:** find-and-replace `[[DOMAIN]]` with the real domain.

## Tokens

| Token | What it is | Where | Shown as now |
| --- | --- | --- | --- |
| `[[DOMAIN]]` | Final domain | `index.html` `<head>` (canonical, og:url, og:image, twitter:image); `game/game.js` `CONFIG.domain` | Not visible; game end card shows `nnbooth.github.io/thefourthsheet` |
| `[[BOOKING_URL]]` | Booking link (Calendly or similar) | Every "Book a free 20-minute numbers check" button in `index.html`; `game/game.js` `CONFIG.bookingUrl` | Buttons jump to Contact |
| `[[EMAIL]]` | Contact email | `index.html` → Contact | "Email TBC" chip |
| `[[LINKEDIN_URL]]` | LinkedIn profile | `index.html` → Contact | "LinkedIn TBC" chip |
| `[[ABN]]` | ABN | `index.html` → footer | "ABN TBC" chip |
| `[[PHOTO]]` | Headshot | `index.html` → hero card | Neutral silhouette |
| `[[NFP_EXAMPLE]]` | The not-for-profit proof example | `index.html` → Not-for-profit section and Track record | "TBC" chips + orange TO DO note |
| `[[PRICE_SETUP]]`, `[[PRICE_BEDDING]]`, `[[PRICE_MONTHLY]]` | The three ladder prices | `script.js` → `PRICES` | Hidden: every rung says "Talk to me about pricing" |
| `[[DAYS]]` | Days to close month-end (game summary) | `game/game.js` `CONFIG.daysToClose` | Game shows 3 |

**Photo:** save a square photo (256×256 px or larger) as e.g. `Assets/headshot.jpg`, set the hero `<img>` `src` to it, set `alt="Nathan Booth"`, and remove `data-placeholder`.

**Email and LinkedIn:** replace each chip with a link, e.g. `<a href="mailto:you@thefourthsheet.com.au">you@thefourthsheet.com.au</a>`.

## Prices (switched off)

Prices are off by default because you shouldn't advertise priced services until your CPA Australia certificate application is in. Every rung shows "Talk to me about pricing", and that text sits in `index.html`, so it shows even without JavaScript.

To switch prices on, open `script.js`, search for **PRICES**, fill in the three values (e.g. `'From $3,500'`), then set `SHOW_PRICES = true`. A value still written like `[[TOKEN]]` is never shown.

**Also check:** the game's summary shows an illustrative "setup" cost ($1,500) and running cost. Decide whether that counts as advertising a price (see Open decisions).

## Open decisions (the ❓ ASKs)

1. **Domain:** `thefourthsheet.com.au`, `.com`, or both, and which is primary? Then fill in `[[DOMAIN]]` and add a `CNAME` (steps below).
2. **ABN:** the number, or keep the placeholder.
3. **Headline:** now the brand line, *"Your accountant gives you three sheets. I give you the fourth."*, with the "what each customer costs to win / what each dollar costs to raise" line under it; the audience doors carry the questions. Alternatives:
   1. *Your P&L tells you what happened. The fourth sheet tells you why.*
   2. *Three sheets tell you where you've been. The fourth shows where you're going.*
   3. *The numbers underneath.*
   4. *See the numbers underneath your numbers.*

   To change it, edit the `<h1>` in the home hero (`index.html`).
4. **Audience order:** on the home page the SME door comes first (interim). To swap, reorder the two `<a class="door">` blocks in `index.html`. Each audience has its own page (`sme.html`, `not-for-profit.html`).
5. **Naming clients:** may Bradbury Group Australia and Pocket Rocket Sports be named? (Our work lists them as "A manufacturer" and "A sole-trader fitness business". Also confirm the corporate list there: it's every employer on your resume.) How should the not-for-profit work be referenced, and what was it? Everything is de-identified for now.
6. **CPA:** "CPA" is removed everywhere (site, game, meta) until you confirm what's allowed. The same rule applies to the business card.
7. **Prices:** the three values (see above).
8. **Power BI:** is there a new "Publish to web" link? Paste it into that report's `embedUrl` in `script.js`. The cards show sample previews with "live report coming soon".
9. **Quick wins:** keep all six, cut to 2–3 and move lower, or remove? Unchanged for now. Its "quoted up front" pricing wording also needs confirming.
10. **Tools:** keep Azure, Salesforce, TechnologyOne and Datawrapper? Unchanged for now.
11. **Contact:** email, LinkedIn, whether to publish your mobile ([removed]), and a booking link.
12. **"Why it matters"** (the old "answer these on the 3rd" section, now on `how-we-work.html`): keep or remove?
13. **Game summary costs:** keep the illustrative setup and running costs, or relabel or remove them while prices are off?

## Example questions (doors and audience pages)

The questions on the home doors and the two audience pages are **examples**, finishing with "…or bring your own". Confirm you're happy to answer each one:
- **SME:** What does it cost to win a customer? · Which jobs actually make money? · Will cash cover payroll next month? · Which products or services should we drop? · Is the overtime worth it?
- **Not-for-profit:** What does it cost to raise a dollar? · What does each program really cost? · How many months of runway do we have? · Which funding is worth chasing? · What does the board need to see?

To change them, edit the `<ul class="q-chips">` lists in `index.html`, `sme.html` and `not-for-profit.html`.

## Domain setup (once the domain is chosen)

1. Replace `[[DOMAIN]]` everywhere (`index.html`, `game/game.js`).
2. Add a file called `CNAME` at the repo root containing just the domain, e.g. `thefourthsheet.com.au`.
3. **DNS, at your domain registrar:**
   - Apex domain (`thefourthsheet.com.au`): four **A** records pointing to `185.199.108.153`, `185.199.109.153`, `185.199.110.153`, `185.199.111.153`. Optionally add **AAAA** records for `2606:50c0:8000::153`, `2606:50c0:8001::153`, `2606:50c0:8002::153` and `2606:50c0:8003::153`.
   - `www`: a **CNAME** record pointing to `nnbooth.github.io`.
4. **On GitHub:** repo **Settings → Pages → Custom domain**. Enter the domain, wait for the DNS check, then tick **Enforce HTTPS**. Optionally verify the domain under your account's **Settings → Pages** to protect it.
5. **Re-record the game media** (`python3 tools/record_demo.py`) so the end card shows the real domain.

## Home-page sample dashboard

The dashboard in the home hero uses **sample data** (captioned "Sample data"). It is **month-end reporting**: **September 2026** (the last closed month) against the **prior month, August 2026**, with a Change column, in whole dollars. It shows three invented organisations, built up from the transactions:

- **SME · trades:** every job (14 maintenance contracts, named installations, every call-out), each with its own revenue, materials, subcontractors, technician hours, invoice date and payment date.
- **SME · services:** every client engagement (projects billed on milestones, retainers, training), with hours, billing, work in progress and invoices.
- **Not-for-profit:** every grant (funder, program, period, instalments, spend against budget), plus donations, a September gala, program fees.

The **fourth sheet** tab is first and always opens by default (also when switching organisation): three headline numbers for September against August, and one chart drilling into jobs, engagements or grants. Every bar shows its value; amber bars are below target (that is the only meaning of the colour).

**Every figure is calculated** by `tools/financial_model.py` and checked: subtotals, balance sheet balances, cash ties, profit/surplus rolls into equity, jobs/engagements/grants add up to the statements, debtors equal unpaid invoices, unspent grants equal instalments received less income recognised. To change anything, edit the assumptions in that file and run `python3 tools/sample_data.py`; that rewrites `dashboard-data.js`, the Excel and PDF downloads in `media/exports/` and the CSVs in OneDrive, `The 4th Sheet/Data/Website sample data/` (`model_statements` plus the star-schema tables below). The Assumptions pop-up shows the same assumptions.

**Cloud database.** The same numbers are also generated as a daily star schema (`dim_*` and `fact_*` CSVs plus `schema.sql`, written to OneDrive: `The 4th Sheet/Data/Website sample data/`): a daily ledger, daily cash and debtor balances and daily timesheets, with a date dimension for drilling from financial year to quarter, month, week and day. It's checked to roll up to the statements to the dollar, and is ready for rebuilding the dashboards in Power BI or another tool. **To do:** the Azure SQL database is currently deleted. Recreate it, run `schema.sql`, load the CSVs (dim_ tables first).

## Deliveries map (`work.html`)

An interactive map of deliveries **out** to ~65 customers across south-east Queensland and **in** from 14 suppliers around Australia, for an invented distribution centre at Wacol, as at 2pm today (6 Oct 2026). Periods: today, last working day, 7 days, 30 days. Dots are coloured by on-time share (green 95%+, amber 80–95%, red under 80% or anything overdue, blue on its way); a "Where it's going wrong" list ranks carrier/region or supplier hotspots. Planted stories: Carrier A's Gold Coast run goes late from 7 Sep; Supplier C (Melbourne) runs late in September; an import container is held at the port in late September.

Generated by `tools/deliveries.py` (via `python3 tools/sample_data.py`): `deliveries-data.js`, `media/exports/deliveries-sample.xlsx` and `.pdf`, and CSVs `dim_customer`, `dim_supplier`, `fact_delivery_out`, `fact_delivery_in` (one row per delivery, joined to `dim_date`). The map uses Leaflet with OpenStreetMap tiles: fine for a low-traffic site with the attribution shown; move to a paid tile provider if traffic grows.

## Where the data lives

All data (CSV, Excel) lives in OneDrive, not git: `Projects/The 4th Sheet/Data/` (website sample data in `Website sample data/`, domain datasets in `Health/`, `Legal/`, `Purchasing/`, `Retail/`). Scripts find it on the Mac or a Windows PC. Only the website's own downloads (`media/exports/`) are in git. For Power BI on the PC: point a folder parameter at the OneDrive `Data` folder (set it to "Always keep on this device"), or load the CSVs into the cloud database and connect to that.

## Downloads (Excel and PDF)

Each sample organisation on the home dashboard (and the deliveries map) has a formatted Excel workbook and an A4 PDF in `media/exports/` (fourth sheet, P&L, balance sheet and cash flow with a Change column, the full job / engagement / grant list, assumptions, checks). They're regenerated by `python3 tools/sample_data.py`, so they always match the page. New reports and dashboards should get the same two downloads.

## Logo mark

The site uses a **superscript 4<sup>th</sup>** mark and the wordmark "The 4<sup>th</sup> Sheet" everywhere: favicon and app icon, header, wordmark SVG, share image, PDFs and the game (where the small "th" is drawn as a pixel sprite). Icon links carry `?v=4th` so browsers drop any cached 3S icon.

## Old versions (`versions/`)

The themed pages are now **generated** from the main home page by `python3 tools/build_versions.py` (same copy, sections and dashboard; each theme's own stylesheet layered on top). Re-run it after changing `index.html`. Their old copies of the 2026 script (with the email-macro code) were removed.

## Sample-data images

The dashboard, report and template images are mock-ups with invented "Sample Co" data, captioned "Sample data".
- **To swap in a real screenshot** (sample data only): save it over the same file in `media/` at 1600×900, or change the `src`.
- **To change a mock-up:** edit `tools/mockups/*.html`, then run `python3 tools/render_mockups.py`.
- **Real employer work:** don't use real screens, data or branding from a past employer without their permission.

## Before going live: checklist

- [ ] All open decisions above resolved.
- [ ] **Turn off the orange TO DO notes:** delete `class="dev-notes"` from `<body>` in `index.html` and the "DEV NOTES ARE ON" bar under it. The note still showing: the not-for-profit example.
- [ ] Searching for `[[` finds only this file (and the comments in `script.js` and `game/game.js` that explain the tokens).
- [ ] Real photo in the hero.
- [ ] Domain live with HTTPS (steps above); LinkedIn Post Inspector shows the right preview.
- [ ] **Undeploy or restrict the old Apps Script** behind the removed "Email Staff Individually" button. Its address is still in git history.
- [ ] **Recreate the Azure SQL database** (currently deleted), run `schema.sql`, load the CSVs from OneDrive (dim_ tables first).
- [ ] Game `CONFIG` confirmed (hours, rate, costs, days) and media re-recorded.
- [ ] Final check at phone and desktop widths.

## Ideas and next steps (not started)

- **Second game:** *"Why did the accountant cross the road?" "Because that's what we did last month."* About streamlining or dropping processes that no longer earn their keep.
- **Daily data for the other mock-ups:** the warehouse, reception, boardroom, sales, purchasing and payroll images still sit on small summary tables. Give them daily transaction data underneath (orders, purchase orders, timesheets), close enough rather than perfect.
- **"October so far":** show the current month to date next to the closed month, to make the daily point on the home dashboard.
- **Business card:** waiting on the CPA, email and domain answers.
