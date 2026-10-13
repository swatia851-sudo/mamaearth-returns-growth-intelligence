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

### 1. Clone the repository

Clone the GitHub repository and open the project folder.

### 2. Run the SQL layer

Execute `sql/schema.sql` to create the database tables and `sql/seed_data.sql` to load the data.

Then run `sql/reports.sql` to generate the required SQL reports.

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
