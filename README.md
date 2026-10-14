# Mamaearth Returns & Growth Intelligence Pipeline

## Project Overview

This project analyzes Mamaearth order data to understand how product returns affect revenue and margins.

The pipeline uses:

- SQLite and SQL for relational data storage and reporting
- Python and Pandas for data cleaning and exploratory analysis
- Matplotlib for visualizations
- Gemini GenAI for the Insight Narrator
- A deterministic offline fallback when no Gemini API key is available

---

## Project Structure

```text
mamaearth-returns-growth-intelligence/
├── data/
│   ├── customers.csv
│   ├── products.csv
│   └── orders.csv
├── sql/
│   ├── schema.sql
│   ├── seed_data.sql
│   └── reports.sql
├── analysis/
│   ├── clean_and_eda.py
│   └── visualize.py
├── visualizations/
│   ├── return_rate_by_payment.png
│   └── monthly_revenue_trend.png
├── narrator/
│   ├── findings.json
│   ├── generate_narrative.py
│   └── sample_output.txt
└── README.md

```



## Setup and Run Instructions

### Prerequisites

- Python 3.10 or later
- Required Python libraries: `pandas`, `matplotlib`, and `google-genai`

Install the libraries by running:

```bash
pip install pandas matplotlib google-genai
```

For Gemini-powered narrative generation, configure your Gemini API key as the `GEMINI_API_KEY` environment variable. If the key is unavailable or Gemini fails, the offline fallback can generate the narrative.

### 1. Clone the repository

Clone the GitHub repository and open the project folder.

### 2. Run the SQL layer

The SQL scripts use SQLite. Make sure the SQLite command-line tool is installed before running these commands.

From the project root, start a fresh database:

```bash
sqlite3 mamaearth.db
```

Inside the SQLite prompt, run these commands in order:

```sql
.read sql/schema.sql
.read sql/seed_data.sql
.read sql/reports.sql
```

`schema.sql` creates the tables, `seed_data.sql` loads the data, and `reports.sql` runs the required SQL reports.

Use a fresh database for each full run. Running `reports.sql` again on the same database may fail because the `loyalty_tier` column already exists.

### 3. Run the Python analysis layer

Run:

    python analysis/clean_and_eda.py

This cleans the order data, performs exploratory analysis, reconciles revenue, and creates `narrator/findings.json`.

### 4. Generate visualizations

Run:

    python analysis/visualize.py

This creates the charts in the `visualizations/` folder.

### 5. Run the Insight Narrator

Run:

    python narrator/generate_narrative.py

The narrator uses Gemini when an API key is available. If Gemini is unavailable, the project uses the deterministic offline fallback.

### 6. Output flow

CSV data → SQL layer → Python cleaning & EDA → `findings.json` → Insight Narrator → `sample_output.txt`
