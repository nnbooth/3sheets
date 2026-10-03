# Placeholders: what's still to fill in

Every detail that isn't final yet is marked with a token like `[[NAME]]`.
Search the repo for `[[` to find them all. Most of them are in `index.html`.

## How placeholders look on the page

Each token appears in one of three ways, so the live page never shows raw `[[TOKEN]]` text:

1. **TBC chip in body text.** It shows as a small dashed "Name TBC" pill:

   ```html
   <span class="tbc" data-placeholder="[[NAME]]">Name TBC</span>
   ```

   **To fill in:** replace the whole `<span …>…</span>` with the real value, e.g. `Jane Citizen`.

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
| `[[NAME]]` | Your name | `index.html` → Hero card (beside the photo) | "Name TBC" chip, then ", CPA" |
| | | `index.html` → Footer | "Name TBC" chip |
| `[[PHOTO]]` | Headshot image path | `index.html` → Hero card `<img class="headshot">` | Neutral silhouette, `Assets/headshot-placeholder.svg` |
| `[[LOCATION]]` | City/region | `index.html` → Hero eyebrow ("CPA-built reporting for … SMEs") | Fallback word **"Australian"** |
| | | `index.html` → Hero card ("20 years in finance · …") | "Location TBC" chip |
| | | `index.html` → Footer | "Location TBC" chip |
| `[[EMAIL]]` | Contact email | `index.html` → Contact ("Prefer email or LinkedIn?") | "Email TBC" chip |
| `[[LINKEDIN_URL]]` | LinkedIn profile | `index.html` → Contact ("Prefer email or LinkedIn?") | "LinkedIn TBC" chip |
| `[[BOOKING_URL]]` | Calendar booking link | `index.html` → Hero button "Book a free 20-min data check" | Button links to `#contact` for now |
| | | `index.html` → Contact button "Book a free 20-min data check" | Button links to `#contact` for now, so it currently goes nowhere |
| `[[DOMAIN]]` | Final domain | `index.html` → `<head>`: `canonical`, `og:url`, `og:image`, `twitter:image` | Not visible. Only affects link previews |
| `[[PRICE]]` | Starter bundle price (AUD) | `index.html` → Starter bundle, "Price" box | "Price TBC" chip, followed by "AUD" |
| `[[TIMEFRAME]]` | Starter bundle delivery time | `index.html` → Starter bundle, "Delivery" box | "Timeframe TBC" chip, followed by "from kickoff to go-live" |

### Notes on specific tokens

- **`[[PHOTO]]`:** add your photo to `Assets/` (square, at least 256×256 px, JPG or WebP, e.g. `Assets/headshot.jpg`). Then in the hero `<img class="headshot">`:
  - set `src="Assets/headshot.jpg"`;
  - change `alt` to `"[Your name], CPA"`;
  - remove `data-placeholder`.

  You can delete `Assets/headshot-placeholder.svg` afterwards.
- **`[[EMAIL]]` and `[[LINKEDIN_URL]]`:** replace each chip with a real link, e.g.
  `<a href="mailto:you@yourdomain.com.au">you@yourdomain.com.au</a>` and
  `<a href="https://www.linkedin.com/in/you/" target="_blank" rel="noopener">LinkedIn</a>`.
- **`[[BOOKING_URL]]`:** for an external link, also add `target="_blank" rel="noopener"` to both buttons.
- **`[[LOCATION]]` in the hero eyebrow:** "Australian" reads naturally until you choose a city. Replace it with e.g. "Brisbane" or "Perth".
- **`[[DOMAIN]]`:** use the bare domain without `https://` or a trailing slash, e.g. `3sheets.com.au`. The `https://` and paths are already in the tags.

## Draft copy to confirm (not tokens, but please check)

These sentences are on the page now and make promises you should confirm or edit (`index.html`, Starter bundle section):

- **What's included:** the Sales dashboard, the Purchasing dashboard and the automated weekly update; a Payroll & overtime report can replace either dashboard.
- **Data sources:** Excel/Google Sheets, accounting exports (Xero or MYOB named as examples), CRM and supplier exports, and emailed reports.
- **Refresh:** weekly, and daily where the source allows.
- **After go-live:** 30 days of support for fixes and small changes, plus a short handover.
- **Price:** say whether `[[PRICE]]` includes or excludes GST.
- **How it works:** "About an hour of your time for a kickoff call and read-only access to the files and exports you already have."

## TODO outside this repo

- [ ] **Live sheet (Live example section).** The embedded Google Sheet tab is titled **"Testing : Team_Budget"**, and it's thin test data with a `stevo` row. The title shows at the top of the embed. Publish a finished, read-only sheet, rename the tab, and if the published address changes, update both addresses on the `live-sheet` panel in `index.html`:
  - the `<iframe src>`, which must be the `/pubhtml` address;
  - `data-csv-url`, the `/pub?…output=csv` address of the same tab.

  Never use the `/edit` address.
- [ ] **Power BI reports.** None are built yet. When one is ready, use **File → Embed report → Publish to web** in Power BI and paste the `https://app.powerbi.com/view?r=…` link into that report's `embedUrl` in the `REPORTS` list at the top of `script.js`. Set its `status` to e.g. `'Live demo'`. "Publish to web" makes the report public, so only publish demo data.
- [ ] **Game poster.** `Assets/game-poster-placeholder.svg` is a stand-in; the game task replaces it (Game slot section in `index.html`).

## Before going live: checklist

- [ ] **Undeploy or restrict the old Apps Script web app** behind the removed "Email Staff Individually" button. Removing the button doesn't stop anyone who has the URL, and the URL is still in git history.
- [ ] **Deal with the old copies in `versions/`.** Every `versions/*/index.html` + `script.js` (apple, nes, sms, snes, geocities, social, as400, modern, insta) still contains the email button and its Apps Script address, the Power BI test embed and the case study. They're publicly served under `/3sheets/versions/…`. Delete them, strip them, or stop serving them before launch.
- [ ] Every token above is replaced: searching the repo for `[[` finds only this file.
- [ ] No `class="tbc"` chips remain in `index.html`.
- [ ] Both "Book a free 20-min data check" buttons open your booking page.
- [ ] Email link opens a mail client addressed to a mailbox that exists and is monitored.
- [ ] Real photo in the hero, with alt text set to your name.
- [ ] Price and timeframe filled in; GST treatment stated; the starter bundle scope wording confirmed.
- [ ] Finished, read-only Google Sheet published; "Testing" tab renamed (see TODO above).
- [ ] Domain registered, pointed at GitHub Pages (custom domain in the repo's Pages settings, which adds a `CNAME` file) and HTTPS enforced.
- [ ] Mailbox on the new domain set up and tested before any traffic goes to the site.
- [ ] Paste the live URL into LinkedIn Post Inspector (linkedin.com/post-inspector) and check the preview title, description and image.
- [ ] Still no client results or case studies claimed anywhere until you have a real, approved one.
- [ ] Final check at phone, tablet and desktop widths.
