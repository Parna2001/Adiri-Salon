# Salon Engagement Dashboard

Shows customer counts, missing data, birthday/anniversary charts, upcoming occasions and a searchable
customer table, built from a salon customer spreadsheet (`Salon Customers Database*.xlsx`).

> **Public code, private data.** This repo and the live page are public. The spreadsheet and the plain
> `dashboard_data.json` made from it are git-ignored and never committed. The live site carries only an
> encrypted copy (`dashboard_data.enc.json`) that opens with the dashboard password. Anyone without the
> password sees nothing unless they load their own `dashboard_data.json` with the **Choose File** button.

| File | Role |
|---|---|
| `dashboard_data.py` | Reads the Excel file, cleans it, and writes `dashboard_data.json` |
| `dashboard_data.json` | All numbers and customer rows the dashboard shows (generated, git-ignored) |
| `dashboard_data.js` | The same data as a script file, so the page opens from disk (generated, git-ignored) |
| `dashboard_data.enc.json` | The same data, encrypted with `DASHBOARD_PASSWORD`, for the live site (generated, committed) |
| `dashboard.html` | The dashboard (one file, no internet or extra libraries needed; contains no customer data) |

## Refresh the data

Whenever the Excel file changes (and ideally each morning, since "upcoming" is relative to today):

```bash
python dashboard_data.py
```

That rewrites `dashboard_data.json` and `dashboard_data.js`, and, if `DASHBOARD_PASSWORD` is set in `.env`,
`dashboard_data.enc.json`.
Options: `--input other.xlsx` for a different workbook, `--today 2026-10-01` to preview another date.

It needs `pandas` and `openpyxl`, plus `cryptography` for the encrypted copy. All are already installed here.

## Open the dashboard

Double-click `dashboard.html`. It works straight from disk, using `dashboard_data.js` from the last run of
`dashboard_data.py`.

To make it load `dashboard_data.json` fresh on every page load instead, serve the folder:

```bash
python -m http.server 8000
# then browse to http://localhost:8000/dashboard.html
```

If neither data file is present, for example in a fresh clone, the page shows a **Choose File** button
instead. Pick a `dashboard_data.json` to load it.

### Online (GitHub Pages)

Live page: **https://parna2001.github.io/Adiri-Salon/**

The live site holds the customer data **encrypted** (AES-256-GCM, key derived from your password with
PBKDF2-SHA256, 600,000 rounds). The page asks for the password, decrypts the data in your browser and shows
the full dashboard. The password never leaves your device, and reloading the page locks it again.

**One-time setup:** add a strong password (12+ characters; a few random words works well) to `.env`:

```
DASHBOARD_PASSWORD=your-long-password-here
```

`.env` is git-ignored, so the password is never committed. Share it only with people who may see customer data.

**To update the live data** after the spreadsheet changes:

```bash
python dashboard_data.py
git add dashboard_data.enc.json
git commit -m "Update dashboard data"
git push
```

The site redeploys within a minute or two (`.github/workflows/pages.yml`).

- **Changing the password:** change it in `.env`, re-run the script and push. The old password stops working
  for the new file, but anyone who downloaded an older encrypted file can still open that copy with the old password.
- **Security depends on the password.** The encrypted file is public, so a short or guessable password could
  be cracked offline. Use a long one.
- Without the password, you can still load a local `dashboard_data.json` with **Choose File** on the same page.

If the top of the page says **"Not today's data"**, the numbers were generated on an earlier day. Re-run
`dashboard_data.py` and reload.

## How the data is cleaned

- Month names are normalised (`june`, `Jun`, `JUNE` all become June).
- A birthday or anniversary counts only when both day and month are present and form a real date.
- Mobile numbers are reduced to digits; a `+91` or leading `0` is dropped. "Missing mobile" means neither
  Mobile 1 nor Mobile 2 is filled in.
- **Date of Entry:** real Excel dates in that column have day and month swapped (typed as month/day,
  read as day/month), so the script swaps them back. Row order in the sheet confirms this. If you fix
  the column in Excel, set `SWAP_EXCEL_DATE_DAY_MONTH = False` at the top of `dashboard_data.py`.
- Things that look wrong (a 9-digit mobile, a number shared by several customers, half-filled dates)
  are listed under "Data quality notes" at the bottom of the dashboard.

`dashboard_data.json`, `dashboard_data.js` and the Excel file hold customers' names and phone numbers.
They are listed in `.gitignore` and must never be committed (don't `git add -f` them) or shared publicly.
