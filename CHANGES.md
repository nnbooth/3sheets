# Changes

## Site review (branch `review-fixes`)

### Phase 1: design tokens and components
- `styles.css` uses tokens for colour (one data green `--good`, one red `--bad`, one amber `--warn`, a darker below-target grey `--neutral-bar`), type (six steps, no 800 weight), spacing (4 px base), radius (three) and shadow (two). No `!important` left. Dev notes and TBC chips untouched.
- One segmented toggle, `.seg`, for statement tabs, sample business, %/$ views and report filters: 36 px (44 px on touch), arrow keys, and a sideways scroll strip on narrow screens.
- Dashed borders only mean "not built yet".
- `tone()` (script.js and exportkit.py) colours by meaning (higher or lower is good), not by sign.
- Container 1360 px; 18 px root font from 1700 px wide.
- Charts are drawn at their real pixel width, so chart text is 11–12 px at every width; month labels thin out instead of colliding.
- **Decisions:** `--good` is the existing chart green `#0E9F6E` for bars and lines. "Good" *text* uses the brand green `--accent`, because `#0E9F6E` is under 4.5:1 on white for small text.

### Phase 2: home page
- Hero top-aligned with the dashboard at about 55%; "Sample business" bar above the statement tabs.
- Not-for-profit grant chart shows over/under budget around zero (overspend red), in the site, PDF, Excel and PowerPoint; KPI 3 is the dollar figure.
- Question rows: four per card, full width, › on the right; "Coming soon" row for the cash question; "Bring your own →" line.
- Plain employer names; ladder card 1 labelled "Start here"; pricing said once; "No data" cut to one line.

## Export menu (branch `export-menu`, on top of review phase 2)
- One **Export** button and menu replaces every row of download pills: report pages (beside the Period picker), the home hero (Assumptions moved into the workings dialog as "See all assumptions"), and the deliveries map's top bar.
- Menu header names the period and the current business and filter, live. Rows for Excel, PDF and PowerPoint show the Excel file size (read when the menu opens) and the PDF page and PowerPoint slide counts. The build writes the counts into the data (`exports_meta`); nothing is typed in.
- Linkable views: report links carry `?period=`, `&business=` and `&filter=`, and the home page `?business=`; all are restored on load, so a link copied from the address bar opens the same view. (The menu's "Copy a link" row was removed at Nathan's request; the menu is narrower for it.)
- "Send this to me on the 3rd business day each month →" links to `#contact` with `data-placeholder="[[SUBSCRIBE_URL]]"`, ready for a subscription form.
- Keyboard: Enter or Space opens it with focus on the first item; arrows, Home and End move; Esc and outside clicks close it, returning focus. On phones it's a bottom sheet with 44 px rows.
- Reusable: `mountExportMenu(container, {period, filterLabel, exports, meta})`, plus `data-export-*` attributes for static or embedded pages. A period with no exports shows the rows disabled ("Not available for a part month").
- Fixed along the way: a replaced report's resize watcher could re-send the old period to the menu.
- `tools/tests/site_check.py` now opens the menu on every report at every period, checks the header and the three files, round-trips the view's link (period and filter), and runs a keyboard-only pass.
- No new tokens were needed: the review's Phase 1 tokens were already in place.

## Sample data and colour (7 Oct, on `export-menu`)
- SME services: three September engagements now sit below the 40% target, each for a stated reason in `financial_model.py`. The Hospitality payroll retainer has scope creep (52 hours in September and 48 in August on the same fee: 25.7%). The Logistics systems rollout leans on contractors (35.2%). Excel for managers carries a venue and co-trainer (27.7%). Every CSV, `schema.sql`, the table guide, the Power BI prompts and all downloads are rebuilt from the model.
- Grant budget chart: under budget is red, the same as over budget; within 1% is amber; on budget is neutral. Same on the site, in the PDF and in PowerPoint.
- Export menu: "Copy a link to this exact view" removed sitewide; the menu is narrower. The hero's menu opens upwards and is no longer clipped by the card.

## Contact page (7 Oct, on `export-menu`)
- New `contact.html`. A form (what you'd like: a monthly report on the 3rd business day, a numbers check, or something else; name, email, organisation, phone, message, consent) posts to a form service that emails Nathan. Its address is a new placeholder, `[[FORM_ENDPOINT]]` (e.g. Formspree), and until it's set the form says nothing has been sent. Beside it is "Or book a time" (`[[BOOKING_URL]]`, which also says it isn't live yet). A hidden trap field catches spam bots.
- The Export menu's "Send this to me on the 3rd business day each month →" now opens the contact page with the report, period and view filled in. This replaces the `[[SUBSCRIBE_URL]]` placeholder added earlier today.
- "Contact" in the menu now opens the contact page on every page, and each page's contact block gains "Or send me your details →".

### Phase 3: SME and not-for-profit pages
- Each report card leads with its headline number and answers its question in one sentence (`answer` in each report, from the data).
- The cash question is a slim "Coming soon" strip under the SME cards; the dashed card is gone.
- Featured charts: the "gross margin is not profit" note only shows on the gross margin views; the hint sits inside the chart card. Mini charts show no axis labels, just the latest value at 11 px or more, and mini bars get a wider label column.
- Cards sit 3 across, so the five not-for-profit cards are 3 + 2.
- Runway's headline is coloured against the reserves target (red at 2.0 months), with "target 3.0 months" beside it. Funding has headline numbers: cheapest and dearest to raise, and the amount raised year to date.
- Both pages use the question rows from the home page. Downloads read "Excel, PDF and PowerPoint". Both pages end on the booking button and a line on what the 20 minutes covers. The SME fitness example line is deleted (Nathan's call); the not-for-profit example placeholder is untouched.

### Phase 4: report pages
- **Bug fixed:** in a month still in progress, the "From gross margin to profit" box is now titled "latest closed month: September" and says why: a part month can't be bridged because wages are paid fortnightly.
- "Gross margin is not profit" is said once, in a collapsible box ("What's the difference?"). The repeats in the job-margins intro, the installation chart subtitle and the Growth note are gone. On phones the box follows the first chart.
- Job margins has three headline numbers: this month and last month (each coloured against the 35% target) and the break-even gross margin (31.1%, from the bridge).
- Margin charts draw both thresholds: the target (dashed) and break-even (dotted red, labelled on its own row), with one line on why they differ. Same in the PDF charts. PowerPoint follows in Phase 6.
- "What you'd do about it" lines are quantified flags, not instructions. For example, "Installations: 27.0% gross margin, 8.0 points under the 35.0% target: about $10,413 on $130,700 of revenue in September." The shortfall is (target − gross margin) × revenue. Growth flags use the year to date.
- Runway: the Gap is red when short of the target. The cash chart has a reserves target line ($644,800 for September = 3 months of spending + unspent grant money). Day labels no longer collide at either end.
- Board: bigger headline numbers, numbered decisions and correct plurals ("2 grants end"). The grants table colours "Against budget": red more than 1% over or under, amber within 1% (Youth outreach 102.1%, Housing support 95.4%, Mental health first aid 95.3% red; Digital literacy 99.3% amber).
- The workings hint names only what can be tapped on that report ("any number for its workings" on the board, "number or day" on runway).
- Sentence-case breadcrumb; fixed-width Period picker; a single headline number is capped in width. Cost to win explains its missing October: "No October yet: new customers are counted at month end."
- Embed-ready: `EMBEDS` in `tools/build_reports.py` maps a report to a live report link (`{period}` filled in). When it's set, the charts give way to a lazy-loaded frame with the loading spinner and the slow message, inside the same shell (Period, Export, headline numbers, notes). It's empty for now.

### Phase 5: Examples, Services, About, Numbers explained, phone menu, footer
- **Examples:** four working reports as cards (job margins, growth, program cost, runway), built by the same card builder as the SME and not-for-profit pages (`EXAMPLE_CARDS` in `tools/build_reports.py`), with links to all of them. The "In build" cards' code (script.js `REPORTS`, with the Power BI embeds) is kept: put `#report-grid` back and they render. "Designs for live data displays…". Mock-ups open in an on-page lightbox (`<dialog>`, Esc or × to close; Ctrl/Cmd-click still opens a new tab). Tools are all plain-text chips. The deliveries map's "some late" colour is `--warn` (#8a6d3b) on the site and in the deliveries downloads.
- **Services:** the home page's one-line ladder is replaced by three cards in depth: what's included, how long, and what you keep. "The first 30 days" (week 1 kick-off, week 2 first numbers, week 4 handover) replaces Connect / Shape / Publish. "Can I have it in Excel?" moves up to second. The "This site is the proof" card is removed; the AI paragraph stays. The three questions are now working reports (job margins, cost to win, runway), each linking to its report.
- **Needs you:** the "How long" lines and the 30-day steps are drafts, in italics, with an orange TO DO note.
- **About:** headshot slot (the existing `[[PHOTO]]` placeholder) and a one-line intro under the opening line. Three career moments are marked placeholders (`[[CAREER_1]]`–`[[CAREER_3]]`, for you to write, each with a result in numbers). "How an engagement runs" follows, with Services, booking (`[[BOOKING_URL]]`) and LinkedIn (`[[LINKEDIN_URL]]`).
- **Numbers explained:** a two-column jump list of every term; eyebrow "Plain English"; in the footer.
- **Phone menu:** opaque, 44 px rows, and the booking button as the last item (`data-placeholder="[[BOOKING_URL]]"`).
- **Footer:** a link row (SME, Not-for-profit, Examples, Services, About, Numbers explained, Contact) on every page, report pages included.
- **Touch:** on touch screens, Export rows, the Period picker, the definition box, footer links and "How it's worked out" are 44 px. On phones the whole KPI card is the tap target and its small link is hidden.

## New report: Will cash cover payroll next month? (7–8 Oct)
- `report-cash-payroll.html`, built like the others (Period picker, Export menu, workings on every number and every day; Excel, PDF and PowerPoint for August, September and October to date). It replaces the "Coming soon" row and strip on the home and SME pages.
- A 13-week daily cash forecast for the trades business, from the end of the period (or 2pm today for October to date), using only what was known that day:
  - Each unpaid invoice is expected on its customer's usual payment date: contract terms for contracts, and the median for installations and call-outs over the last 90 days. Invoices already past that date are assumed a week out, and flagged.
  - Contract fees are invoiced on the 1st. Installations and call-outs come in at the last three months' rate.
  - Pay runs are fortnightly at the last run's amount. Supplier bills (last month's creditors plus overheads) are paid on the 15th and at month end. Interest and equipment finance are paid monthly, and the PAYG instalment on 28 October. Weekend due dates roll to Monday.
- It reconciles or stops: opening cash equals the opening balance plus every day's money in and out; unpaid invoices equal the debtors balance; the month's purchases equal trade creditors on the balance sheet.
- Shows: cash now, wages due next month (October has three pay runs), cash after the tightest pay run, the lowest point in 13 weeks (amber below one pay run, red below zero), the daily line (actual, then a lighter forecast, with a one-pay-run buffer line), next month's money in and out, 13 weeks week by week, and the invoices past their usual date.
- "How this forecast has done so far": earlier forecasts are checked against the bank, and the box names the invoices that were expected but haven't arrived. For example, September's forecast was $62,883 high for 5 October, $64,300 of it seven invoices led by the Wacol switchboard ($46,800).
- New database table `report_cash_forecast_daily` (Data/Reports, in `schema.sql`), plus a Power BI prompt and a "Cash forecast" entry in Numbers explained.
- GST and BAS are left out of the sample (said under the chart).

## Every chart point shows its number (8 Oct)
- One shared tooltip shows the label and value of any chart point, bar or mini-bar row on hover, keyboard focus or tap: card mini charts (which have no y-axis), report charts, the workings dialog's monthly columns, and the home page.
- `site_check.py` now fails a page if any chart point lacks a value label, and hovers the first and last on each page.
- The growth card now shows what it asks: year-to-date growth by line, with **trades and services as separate groups**, each with its own headline. They're never added together or ranked against each other.
- The cash card shows forecast cash after each pay run.

### Phase 6: downloads (Excel, PowerPoint, PDF)
- **Font:** Roboto is set explicitly on every Excel cell (headings included), every PowerPoint run and chart, and the PDFs. Arial is the fallback where Roboto isn't installed.
- **Excel:**
  - **Charts:** native bar charts beside each report's charted table and each job, engagement or grant list (green, grey below target, red losing money or off budget), with the target and break-even drawn as vertical lines: the standard Excel combo, an XY scatter series from (x, 0) to (x, 1) on hidden secondary axes scaled like the bars, labelled at the top (points on a hidden "Chart lines" sheet). Checked in Excel itself. LibreOffice rotates the whole diagram for horizontal bars, so it shows these lines across the top; Excel is right, and a native line chart beside each monthly or daily Data sheet.
  - **Tables and names:** Excel Tables on the Data sheets and the job, engagement and grant lists, and named ranges for every headline number.
  - **Changes:** changes in rates are in points (`+0.0" pts"`). Changes are coloured by direction (good when it moved the right way, e.g. cost to win falling is green), not by sign; each headline number carries `good_when`.
  - **Layout:** the Report sheet reads headline numbers, then the chart, then tables, then notes.
  - **Printing:** print areas cover the cells, so charts beside a table don't shrink the printout.
- **PowerPoint (`tools/pptkit.py`, rebuilt):**
  - **Layouts:** real layouts (Title Slide, Title Only), with the theme's fonts set to Roboto and its colours to the brand, so a client can restyle a whole deck from the master.
  - **Titles:** they wrap and push the subtitle down, never over it.
  - **Charts:** no automatic "Value" titles, and series are properly named. Target and break-even lines are drawn on the bars (the plot area is laid out exactly), and the reserves or buffer line on area charts. Area axes use round steps.
  - **One slide per topic:** headline numbers across the top, the chart, then "What it shows" and "What you'd do about it". Growth is 11 slides (was 27); the board is one slide plus the title (the grants table joins it when it fits); job margins is 8.
  - **Tables:** no empty header rows (assumptions are now one slide per group), text columns left-aligned, numbers right-aligned.
  - **Sizing:** text boxes are sized to their content, and every slide has speaker notes.
- **PDF:**
  - On the "Gross margin $" chart, each bar under target says how far it's short in dollars (e.g. "$10,080 short of 35.0%"), replacing the per-job ticks. Same on the statements PDF.
  - Long tables flow across pages with their header repeated; short ones stay whole. The statements PDF's workings flow on from page 1, so the blank fifth of the page is gone.
  - The growth PDF is 5 pages per business set (was 7).
- **Checked:** every workbook recalculated in LibreOffice with no formula errors (13 workbooks scanned after recalculation), and samples of each format rendered to images and reviewed (trades statements, job margins, growth, board, cash).
- **Note:** LibreOffice was installed (Homebrew) for these renders, and Roboto copied into its own font folder; neither affects the site.

## Trades and services never mixed (8 Oct)
- **Rule:** trades, services and the not-for-profit are separate, unrelated businesses. New test `tools/tests/org_separation.py` proves it end to end:
  - every data row (36,150 rows in 24 tables) sits in its own business's files;
  - every fact row's account, job, engagement or grant belongs to the same business;
  - ids and line names never repeat across businesses;
  - in every report run (86), each block is one business, and growth's year-to-date revenue ties to each business alone, never the combined figure;
  - every working names its business;
  - every Power BI prompt carries the rule.
- **Growth downloads:** one set per business (`growth-trades.*`, `growth-services.*`), each holding that business only. The Export menu hands out the files of the business on screen, which `site_check` checks. The old combined `growth.*` files are removed.
- **Labels:** every growth working names its business ("Trades, all lines: …", "Services, Projects, Sep 26"). The report's header names both businesses and says they're separate.
- **Power BI prompts:** one page per business, each with a locked `dim_org[org_id]` page filter. Every base measure is wrapped in `IF(HASONEVALUE(dim_org[org_id]), …)`, so no visual can show a total across businesses, plus a temporary "Org check" card that must read 1.
- **Database:** account ids are already distinct (trades 1–54, services 55–106, not-for-profit 107–162), so a join can't cross businesses.

## Download names and generated stamps (8 Oct)
- **Inside every download** (reports, statements, deliveries; Excel, PDF and PowerPoint): the business, the period and "Generated 8 Oct 2026, 9:46am" (Excel title block and footer, PDF footer, PowerPoint footer).
- **Saved name:** e.g. `Sample Electrical & Air Pty Ltd - Job margins - September 2026 - generated 2026-10-08 0935.xlsx`. The month in progress is named by month only ("October"); a closed month in full. The repo keeps stable file names; the site's `download` attribute supplies the full name.
- **Stamps only change with the content:** `media/exports/generated.json` records each file's content fingerprint (stamp and pictures left out) and when that content was generated. A rebuild that changes nothing keeps the files and their stamps; proven by two builds in a row with no change. Unchanged PDFs aren't even re-printed.
- **Time zone:** stamps are Brisbane time whatever the build machine's clock (`tzdata` added for Windows).

## Made-with notes (8 Oct)
- Every hand-built chart or report says what made it, in a quiet credit line: report pages, card grids, the home dashboard, the deliveries map (Leaflet, © OpenStreetMap contributors), the mock-up images, and every download ("Made with Python (openpyxl)", "(python-pptx)", "laid out in HTML and CSS, printed to PDF in Chromium").
- Embedded Power BI or Datawrapper won't need it: they say so themselves.

## Also
- OneDrive sometimes stalls reading a file it's still syncing; the data reader now waits and retries rather than stopping the build.
- Home dashboard: the three headline tiles look alike (the left tile's green "lead" style is gone; on phones the third tile takes its own row). A change that rounds to nothing reads "■ same as Aug ($173)" in neutral, not a red arrow beside two equal numbers.

## Final checks (8 Oct)
- `site_check.py`: 17 pages × 3 widths, 9 reports at every period, Export menus, links, keyboard, chart tooltips, per-business growth files, download names. `check_exports.py`: 86 workbooks, 13,686 formulas and headline numbers. `org_separation.py`: data, 86 report runs, 9 Power BI prompts. All pass.
- Playwright at 390, 1440 and 2560 px: no sideways scrolling and no chart text under 11 px on any page. Drill-downs open on every report at September and at October to date.
- Every local `href` resolves and every download exists (site_check). No line with `data-placeholder`, `.devnote` or `dev-notes` was removed or changed in any commit (checked with git diff each phase).

### Couldn't do, or needs you
- **Drafts to confirm:** the Services "How long" lines and the first-30-days steps (italic, with a TO DO note), and the About career moments (`[[CAREER_1]]`–`[[CAREER_3]]`).
- **PowerPoint extra views:** decks show the first view of each chart (gross margin %). The $ view is in Excel and the PDF.
- **Growth card:** shows trades and services as two separate groups on one card (never combined or ranked). If you'd rather the card show one business only, say which.

## ABN and contact form (8 Oct)
- ABN 31 839 620 153 in every page's footer (replaces the `[[ABN]]` placeholder, as the project notes describe).
- Contact form: asks for job title. Phone isn't required, and the form doesn't call it optional. The first option reads "Standardised reporting, given on your schedule" (was "a report each month, on the 3rd business day").
- Same wording where it was a delivery promise: the Export menu's "Get this report on your schedule →" and the request line it fills in on the contact page, and the Services "Monthly" card ("on the schedule we agree").
- The Services heading now reads "Three questions you should be able to answer as soon as the month closes." No "3rd business day" is left on the site. ("Within one business day" in the form's thank-you is a reply time, so it stays.)

## Budget colours (8 Oct)
- Grant budget charts and the board's grants table: over budget red, under budget green (the standard green), within 1% amber, on budget neutral, judged on % of budget. Site, PDF, Excel and PowerPoint alike, with a three-way key ("Over budget · Under budget · Within 1%"). This replaces the 7 Oct rule that showed under budget red like over.
