# RAG experiments and salon customer dashboard

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
pip install chromadb langchain-huggingface sentence-transformers pypdf pandas openpyxl
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

- `.env` (API keys) is git-ignored; `.env.example` lists the variable names.
- Excel/CSV files and the generated `dashboard_data.json` / `dashboard_data.js` contain real customer
  names and phone numbers and are git-ignored.
