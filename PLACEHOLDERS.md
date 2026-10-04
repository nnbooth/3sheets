# Placeholders: what's still to fill in

Every detail that isn't final yet is marked with a token like `[[EMAIL]]`.
Search the repo for `[[` to find them all. Most of them are in `index.html`.

## How placeholders look on the page

Each token appears in one of three ways, so the live page never shows raw `[[TOKEN]]` text:

1. **TBC chip in body text.** It shows as a small dashed "Name TBC" pill:

   ```html
   <span class="tbc" data-placeholder="[[EMAIL]]">Email TBC</span>
   ```

   **To fill in:** replace the whole `<span …>…</span>` with the real value (for email, a `mailto:` link).

2. **Fallback in a heading or button.** The page shows a sensible default and the token sits in `data-placeholder` with an HTML comment above it:

   ```html
   <!-- [[BOOKING_URL]]: replace href="#contact" with your booking link. -->
   <a class="button primary" href="#contact" data-placeholder="[[BOOKING_URL]]">Book a free 20-min data check</a>
   ```

   **To fill in:** change the default (here `href="#contact"`) to the real value, then delete the `data-placeholder="…"` attribute and the comment.

3. **In `<head>` tags** (not visible on the page). The token sits in the address, e.g. `https://[[DOMAIN]]/`.

   **To fill in:** find-and-replace `[[DOMAIN]]` with the real domain.

When you're done, searching the repo for `[[` and for `class="tbc"` should only find `PLACEHOLDERS.md`, plus the `.tbc` style in `styles.css`, which is harmless to keep.

## Tokens

| Token | Meaning | Where it appears (file → section) | Shown on the page as |
| --- | --- | --- | --- |
| `[[PHOTO]]` | Headshot image path | `index.html` → Hero card `<img class="headshot">` | Neutral silhouette, `Assets/headshot-placeholder.svg` |
| `[[LOCATION]]` | City/region | `index.html` → Hero eyebrow ("CPA-built reporting for … SMEs") | Fallback word **"Australian"** |
| | | `index.html` → Hero card ("20 years in sales and cost reporting · …") | "Location TBC" chip |
| | | `index.html` → Footer | "Location TBC" chip |
| `[[EMAIL]]` | Contact email | `index.html` → Contact ("Prefer email or LinkedIn?") | "Email TBC" chip |
| `[[LINKEDIN_URL]]` | LinkedIn profile | `index.html` → Contact ("Prefer email or LinkedIn?") | "LinkedIn TBC" chip |
| `[[BOOKING_URL]]` | Calendar booking link | `index.html` → Hero button "Book a free 20-min data check" | Button links to `#contact` for now |
| | | `index.html` → Contact button "Book a free 20-min data check" | Button links to `#contact` for now, so it currently goes nowhere |
| | | `game/game.js` → `CONFIG.bookingUrl` (end card button) | Game button opens the site's Contact section |
| `[[DOMAIN]]` | Final domain | `index.html` → `<head>`: `canonical`, `og:url`, `og:image`, `twitter:image` | Not visible. Only affects link previews |
| | | `game/game.js` → `CONFIG.domain` (end card text) | Game shows `nnbooth.github.io/3sheets` |
| `[[PRICE]]` | Starter bundle price (AUD) | `index.html` → Starter bundle, "Price" box | "Price TBC" chip, followed by "AUD" |
| `[[TIMEFRAME]]` | Starter bundle delivery time | `index.html` → Starter bundle, "Delivery" box | "Timeframe TBC" chip, followed by "from kickoff to go-live" |
| `[[MONTHLY_PRICE]]` | Monthly fee for "Stay on top" (part-time management accountant) | `index.html` → What I do, package 3 | "Monthly price TBC" chip |
| `[[DAYS]]` | Days to finish month-end with the reporting in place | `game/game.js` → `CONFIG.daysToClose` (summary: "October 2026 – month-end done in N days") | Game shows **3** (matches "by the 3rd") |

### Notes on specific tokens

- **`[[PHOTO]]`:** add your photo to `Assets/` (square, at least 256×256 px, JPG or WebP, e.g. `Assets/headshot.jpg`). Then in the hero `<img class="headshot">`:
  - set `src="Assets/headshot.jpg"`;
  - change `alt` to `"Nathan Booth, CPA"`;
  - remove `data-placeholder`.

  You can delete `Assets/headshot-placeholder.svg` afterwards.
- **`[[EMAIL]]` and `[[LINKEDIN_URL]]`:** replace each chip with a real link, e.g.
  `<a href="mailto:you@yourdomain.com.au">you@yourdomain.com.au</a>` and
  `<a href="https://www.linkedin.com/in/you/" target="_blank" rel="noopener">LinkedIn</a>`.
- **`[[BOOKING_URL]]`:** for an external link, also add `target="_blank" rel="noopener"` to both buttons.
- **`[[LOCATION]]` in the hero eyebrow:** "Australian" reads naturally until you choose a city. Replace it with e.g. "Brisbane" or "Perth".
- **The game (`game/game.js`, `CONFIG` at the top):** the tokens there are written in quotes, e.g. `domain: '[[DOMAIN]]'`. Find-and-replace them like everywhere else, keeping the quotes: `domain: '3sheets.com.au'`, `daysToClose: 3`. Until a value is replaced, the game shows the fallback listed above, never the raw token.
  - **Re-record the videos after you change anything in `CONFIG`:** run `python3 tools/record_demo.py` from the repo root. The videos, GIF and poster in `media/` are pictures of the game, so they keep showing the fallbacks until you do.
  - `CONFIG.setupCostAUD` (currently 1500) is the setup cost on the game's summary. **Keep it the same as `[[PRICE]]`**, or the game and the site will disagree.
- **`[[DOMAIN]]`:** use the bare domain without `https://` or a trailing slash, e.g. `3sheets.com.au`. The `https://` and paths are already in the tags.

## Draft copy to confirm (not tokens, but please check)

These sentences are on the page now and make promises you should confirm or edit (`index.html`, Starter bundle section):

- **What's included:** the Sales dashboard, the Purchasing dashboard and the automated weekly update; a Payroll & overtime report can replace either dashboard.
- **Data sources:** Excel/Google Sheets, accounting exports (Xero or MYOB named as examples), CRM and supplier exports, and emailed reports.
- **Refresh:** on a set schedule, usually weekly, daily where the data allows, **and "You review the numbers before they go out."** That last sentence is a promise about how you work: keep it only if it's true.
- **After go-live:** 30 days of support for fixes and small changes, plus a short handover.
- **Price:** say whether `[[PRICE]]` includes or excludes GST.
- **How it works:** "About an hour of your time for a kickoff call and read-only access to the files and exports you already have."

- **About section facts (from your resume):** the industries list; NYSE- and ASX-listed employers; and the Power BI platform used across Australia, New Zealand and the Pacific Islands. These describe your employment, not client results, so they're fine to keep, but check you're comfortable naming them publicly.

- **The three packages (What I do):** 1 Set up (fixed price, the starter bundle), 2 Dig in (quoted per project), 3 Stay on top (monthly). Check what's listed in each, and that "quoted per project" and a monthly fee are how you want to sell them.

- **"How I build" (AI) section: claims to confirm.** It says you use Claude to write and test queries, code and report logic; that every report is reconciled to the client's accounts and tested against source data before it's delivered; and that this site and the game were built with Claude. Keep each only if it's true of how you work. No speed figures are claimed, which is deliberate: add one only when you can back it up. Clients may also ask whether their data goes into an AI tool, so decide your answer before they do and add it to this section.
- **Tools strip (grouped).** Reporting: Excel, Power BI, Power Query, Google Sheets, Datawrapper. Data and automation: Power Automate, Azure, SQL, Python, R. Business systems: QAD (ERP), TechnologyOne, Salesforce, Elite 3E (legal ERP), Employment Hero (from your resume). AI: Claude. Only Python, R, Google Sheets and Claude have real logos (open-licence Simple Icons files in `Assets/tools/`); the rest use plain letter marks because their logos aren't in that set, and **Microsoft's official icon licence only allows use in architecture diagrams, training material or documentation, not marketing pages** (learn.microsoft.com/power-platform/guidance/icons). Writing the product name is fine. If a brand gives you permission or its press kit allows this use, save the logo in `Assets/tools/` and swap the letter mark for an `<img>` in `index.html` (search "TOOLS I WORK IN"). Don't imply a partnership. "Elite 3E (legal ERP)" is the current name: Elite was Thomson Reuters software until 2023, then a standalone company (sold to Francisco Partners in 2025); 3E is its flagship product.

- **Live dashboards section: images and claim.** The three screens (warehouse, reception, boardroom) are *mock-ups with invented "Sample Co" data*, not your real work. The sentence "I've built live data displays for the warehouse floor, reception and the boardroom" is yours: keep it only if it's true and you're happy saying it. Don't use real screens, data or branding from a past employer without their permission. To change a screen, edit `tools/mockups/*.html` and run `python3 tools/render_mockups.py`.

- **Reports section images.** The three report previews (`media/report-*.png`) are mock-ups with invented data, made from `tools/mockups/report-*.html` by `python3 tools/render_mockups.py`. Replace each with a real Power BI build (sample data) or its "Publish to web" link (`embedUrl` in `script.js`).
- **"Can I have it in Excel?" section.** Says you're technology agnostic, build on the client's existing tools, and only recommend new tools that earn their keep. Confirm that's how you want to work.

## TODO outside this repo

- [ ] **Live sheet (Live example section).** The embedded Google Sheet tab is titled **"Testing : Team_Budget"**, and it's thin test data with a `stevo` row. The title shows at the top of the embed. Publish a finished, read-only sheet, rename the tab, and if the published address changes, update both addresses on the `live-sheet` panel in `index.html`:
  - the `<iframe src>`, which must be the `/pubhtml` address;
  - `data-csv-url`, the `/pub?…output=csv` address of the same tab.

  Never use the `/edit` address.
- [ ] **Power BI reports.** None are built yet. When one is ready, use **File → Embed report → Publish to web** in Power BI and paste the `https://app.powerbi.com/view?r=…` link into that report's `embedUrl` in the `REPORTS` list at the top of `script.js`. Set its `status` to e.g. `'Live demo'`. "Publish to web" makes the report public, so only publish demo data.
- [ ] **Game numbers.** The game's summary uses illustrative assumptions in `game/game.js` `CONFIG`: 32 hours saved, $85/hour, $1,500 setup, $120/month running cost and a 40-hour manual month-end. Confirm or change them, then re-record (`python3 tools/record_demo.py`).

- [ ] **Email test feature (Live example section).** Password-protected "email this pack". Until set up, it says "not set up yet". To switch it on: follow `tools/apps-script/README.md` (new Apps Script, `TEST_PASSWORD` and `SHEET_ID` in Script Properties, deploy as a web app), then paste the `/exec` address into `EMAIL_TEST_URL` in `script.js`. The password lives only in the Apps Script, never in the website or git.

## Before going live: checklist

- [ ] Decide whether the password-protected email test panel stays on the live site (it's visible to visitors, locked). To hide it, delete the `<div class="email-test">` block in `index.html` or leave `EMAIL_TEST_URL` empty.

- [ ] **Turn off the orange TO DO notes:** in `index.html`, delete `class="dev-notes"` from the `<body>` tag (and the "DEV NOTES ARE ON" bar under it). While that class is there, the notes show over the three dashboard images, the three "In build" report cards and the test Google Sheet.

- [ ] **Undeploy or restrict the old Apps Script web app** behind the removed "Email Staff Individually" button. Removing the button doesn't stop anyone who has the URL, and the URL is still in git history.
- [ ] **Deal with the old copies in `versions/`.** Every `versions/*/index.html` + `script.js` (apple, nes, sms, snes, geocities, social, as400, modern, insta) still contains the email button and its Apps Script address, the Power BI test embed and the case study. They're publicly served under `/3sheets/versions/…`. Delete them, strip them, or stop serving them before launch.
- [ ] Every token above is replaced: searching the repo for `[[` finds only this file.
- [ ] No `class="tbc"` chips remain in `index.html`.
- [ ] Both "Book a free 20-min data check" buttons open your booking page.
- [ ] Email link opens a mail client addressed to a mailbox that exists and is monitored.
- [ ] Real photo in the hero, with alt text "Nathan Booth, CPA".
- [ ] Price and timeframe filled in; GST treatment stated; the starter bundle scope wording confirmed.
- [ ] Finished, read-only Google Sheet published; "Testing" tab renamed (see TODO above).
- [ ] Domain registered, pointed at GitHub Pages (custom domain in the repo's Pages settings, which adds a `CNAME` file) and HTTPS enforced.
- [ ] Mailbox on the new domain set up and tested before any traffic goes to the site.
- [ ] Paste the live URL into LinkedIn Post Inspector (linkedin.com/post-inspector) and check the preview title, description and image.
- [ ] Still no client results or case studies claimed anywhere until you have a real, approved one.
- [ ] Game `CONFIG` filled in (booking link, domain, days, numbers) and the media re-recorded with `python3 tools/record_demo.py`.
- [ ] Final check at phone, tablet and desktop widths.
