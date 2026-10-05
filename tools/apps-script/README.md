# Email test feature: setup

The website's **Live example** section has a password-protected **"Email this pack"** test feature. The website only collects the password and an email address. All the checking and sending happens in a Google Apps Script that you deploy from your own Google account.

## 1. Retire the old script first

The old "Email Staff Individually" web app is still in git history, so anyone can find its address. In that old Apps Script project, go to **Deploy → Manage deployments**, and **archive** the deployment, or delete the project. Don't reuse it.

## 2. Create the new script

1. Go to <https://script.google.com> → **New project**. Name it "The Fourth Sheet email test".
2. Replace the code with everything in `email-test.gs` (this folder) and save.
3. **Project Settings (gear) → Script properties → Add**:
   - `TEST_PASSWORD`: a long random password (e.g. 4 random words). Share it only with people testing. It is never stored in the website.
   - `SHEET_ID`: the ID of the finished, read-only sheet you want to email. It's the part between `/d/` and `/edit` in the sheet's address.
   - `SHEET_NAME`: optional, the tab to send (default: first tab).
   - `DAILY_LIMIT`: optional, maximum test emails per day (default 20).

## 3. Deploy it

1. **Deploy → New deployment → Select type: Web app**.
2. **Execute as: Me**. **Who has access: Anyone**. This is needed so the website can reach it. The password, limits and fixed email content are what protect it.
3. **Deploy**, approve the permissions (send email as you, read the spreadsheet), and copy the **Web app URL** (ends in `/exec`).

## 4. Connect the website

In `script.js`, set `EMAIL_TEST_URL` to that address, e.g.

```js
const EMAIL_TEST_URL = 'https://script.google.com/macros/s/AKfy…/exec';
```

Commit and push. Until it's set, the website's test panel says "not set up yet".

## How it's protected

- **Password checked by Google, not the web page.** Anything in a public web page can be read, so the page can't hold or check the password.
- **Lockout:** 5 wrong passwords lock everyone out for 15 minutes.
- **Fixed content:** the website can only choose *who* gets the email, not what it says, so it can't be used to send spam or anything else.
- **Limits:** a daily cap (`DAILY_LIMIT`) and one email per address every 10 minutes. Google also limits a free Gmail account to about 100 recipients a day.
- **The email comes from your Google account**, so recipients see your address. Test with your own addresses.

To switch the feature off: archive the deployment (Deploy → Manage deployments), or clear `EMAIL_TEST_URL` in `script.js`.
