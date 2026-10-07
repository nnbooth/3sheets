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
