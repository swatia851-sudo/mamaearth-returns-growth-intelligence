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

```
