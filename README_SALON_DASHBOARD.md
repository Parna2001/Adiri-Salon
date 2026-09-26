# Salon Engagement Dashboard

Shows customer counts, missing data, birthday/anniversary charts, upcoming occasions and a searchable
customer table, built from a salon customer spreadsheet (`Salon Customers Database*.xlsx`).

> **Public code, private data.** This repo and the live page are public. The spreadsheet and the
> `dashboard_data.json` made from it are git-ignored and never committed. Anyone who clones the repo or
> opens the live link must supply their own `dashboard_data.json` locally, using the **Choose File**
> button, to see real data.

| File | Role |
|---|---|
| `dashboard_data.py` | Reads the Excel file, cleans it, and writes `dashboard_data.json` |
| `dashboard_data.json` | All numbers and customer rows the dashboard shows (generated, git-ignored) |
| `dashboard_data.js` | The same data as a script file, so the page opens from disk (generated, git-ignored) |
| `dashboard.html` | The dashboard (one file, no internet or extra libraries needed; contains no customer data) |

## Refresh the data

Whenever the Excel file changes (and ideally each morning, since "upcoming" is relative to today):

```bash
python dashboard_data.py
```

That rewrites `dashboard_data.json` and `dashboard_data.js`.
Options: `--input other.xlsx` for a different workbook, `--today 2026-10-01` to preview another date.

It needs only `pandas` and `openpyxl`, which are already installed in this project.

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

Live page: **https://parna2001.github.io/Adiri-Salon/dashboard.html**

The live page contains the dashboard code only; no customer data is published. On the live site it
doesn't even request a data file. It opens straight to the **Choose File** button:

1. On your own computer, run `python dashboard_data.py` to create `dashboard_data.json`.
2. Open the live link and click **Choose File**.
3. Pick that `dashboard_data.json`. The dashboard appears.

The file is read by your browser only. It is never uploaded, and it is gone once you close or reload the tab.
If you pick the wrong file, the page tells you and waits for another.

`.github/workflows/pages.yml` republishes the page whenever `dashboard.html` changes on `main`. It applies
when Settings → Pages → Source is set to **GitHub Actions**, which also makes the dashboard the site's
front page.

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
