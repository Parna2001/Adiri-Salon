# RAG experiments and salon customer dashboard

> **This repository is public. Real customer data is never committed in readable form.**
> The dashboard's code and page are public (live at https://parna2001.github.io/Adiri-Salon/). The customer
> spreadsheet and the plain `dashboard_data.json` generated from it are never committed. The only copy of
> the data in the repo is `dashboard_data.enc.json`, which is encrypted and useless without the dashboard
> password. To see real data you need either that password or your own `dashboard_data.json`, loaded
> through the page's **Choose File** button. Either way it is decrypted or read in your browser only.

Two small projects in one repo:

1. **RAG pipeline** (`1.0_RAG_WITH_OWN_TEXT.ipynb`): ask Claude questions about your own documents.
2. **Salon engagement dashboard** (`dashboard_data.py` + `dashboard.html`): turns a customer spreadsheet into a
   birthday/anniversary and data-quality dashboard.

## 1. RAG pipeline

The notebook walks through the steps one cell at a time:

| Step | What happens | Tools |
|---|---|---|
| Load | Read a scanned PDF (with OCR) or, in the second half, an Excel customer list (one document per row) | `PyPDFLoader`, `rapidocr`, pandas |
| Split | Cut the PDF text into overlapping chunks (customer rows are already short, so they aren't split) | `RecursiveCharacterTextSplitter` |
| Embed | Turn text into vectors | `sentence-transformers/all-MiniLM-L6-v2` |
| Store | Keep the vectors for similarity search | Chroma |
| Answer | Retrieve the closest chunks and pass them to Claude as context | `langchain-anthropic` (Claude Haiku 4.5) |

Similarity search returns only the closest few records, so it is weak for counting or filtering questions
("who has a birthday in September?"). Use pandas or metadata filters for those.

### Setup

```bash
python -m venv .venv && .venv\Scripts\activate      # Python 3.14 per pyproject.toml
pip install -r requirements.txt
pip install chromadb langchain-huggingface sentence-transformers pypdf pandas openpyxl cryptography
copy .env.example .env                              # then put your ANTHROPIC_API_KEY in .env
```

Open the notebook in VS Code or Jupyter and run the cells in order. The PDF path and Excel path inside it
point at files on the author's machine; change them to your own.

## 2. Salon dashboard

`dashboard_data.py` reads the Excel file, cleans it, and writes the data `dashboard.html` displays:
KPI cards, birthdays and anniversaries by month, the next 30 days of occasions, data completeness,
new customers by month, and a searchable customer table.

```bash
python dashboard_data.py     # regenerate whenever the spreadsheet changes
# then double-click dashboard.html
```

Full instructions are in [README_SALON_DASHBOARD.md](README_SALON_DASHBOARD.md).

### Bring your own data

The real customer file is deliberately **not** in this repository. Put your own workbook next to the script,
named `Salon Customers Database*.xlsx` (or pass `--input`), with these columns:

`Date of Entry`, `First_Name`, `Middle_Name`, `Last_Name`, `Mobile_1`, `Mobile_2`, `Birth_Day`,
`Birth_Month`, `Anniversary_Day`, `Anniversary_Month`, `Notes`

Month columns accept full or short names in any case (`June`, `jun`). Extra columns such as `Index` are ignored.

## Privacy and secrets

| Public (in this repo) | Never committed (git-ignored, stays on your machine) |
|---|---|
| Dashboard code and page (`dashboard.html`, `dashboard_data.py`) | Customer spreadsheets (`*.xlsx`, `*.xls`, `*.csv`) |
| `dashboard_data.enc.json` (encrypted, needs the password) | Plain generated data (`dashboard_data.json`, `dashboard_data.js`) |
| Notebook, READMEs, dependency files | `.env` (API keys and the dashboard password) |
| `.env.example` (variable names only) | |

- **Cloned the repo?** You get the code without any data. Add your own spreadsheet, run
  `python dashboard_data.py`, then open `dashboard.html`, or use **Choose File** to load the JSON.
- **Visiting the live page?** It asks for the dashboard password and decrypts the data in your browser.
  The password is never sent anywhere, and reloading the page locks it again. Without the password you can
  still load your own `dashboard_data.json` with **Choose File**.
- **Contributing?** Run `git status` before every commit and make sure none of the right-hand files appear.
  Never use `git add -f` on them.
