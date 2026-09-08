# Cashflow Intelligence

Cashflow Intelligence is an India-focused banking and cybercrime analytics project. It combines bank financials, ATM and card infrastructure, individual transactions, socioeconomic indicators, and cybercrime records into analysis-ready datasets.

The project has three main entry points:

- `data_merge.py` cleans the raw files and creates the merged CSV outputs.
- `main.ipynb` contains the full exploratory analysis and visualizations, organized into notebook cells.
- `app.py` provides a Streamlit dashboard for exploring the merged data through a browser.

## Project Structure

```text
.
├── app.py
├── data_merge.py
├── main.ipynb
├── requirements.txt
├── README.md
├── data/
│   └── geo/india_states.geojson
├── DATASETS/
│   ├── Bank Records/
│   └── Crime Records/
└── MERGED DATASETS/
```

`DATASETS/` contains source files. `MERGED DATASETS/` contains generated outputs and is not a replacement for the raw sources.

## Setup

From the project root, create and activate a virtual environment.

### Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### macOS or Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Regenerate the Data

Run the merge pipeline whenever the raw source files change:

```bash
python data_merge.py
```

The script reads from `DATASETS/` and writes these four files to `MERGED DATASETS/`:

| File | Purpose |
| --- | --- |
| `merged_bank_financials.csv` | Bank balance-sheet measures joined with ATM, PoS, QR, and card statistics. |
| `bank_transactions_clean.csv` | Deduplicated transactions with parsed dates and positive amounts. |
| `merged_crime_data.csv` | State and district socioeconomic data joined with crime and cyber-fraud measures. |
| `cyber_national_trends.csv` | Year-wise national cyber and financial-fraud measures. |

The crime pipeline expects `DATASETS/Crime Records/datafile.xls`, which is included with the local source files.

## Run the Dashboard

```bash
python -m streamlit run app.py
```

Open the local URL shown by Streamlit. The dashboard includes:

- An overview of data coverage and headline indicators.
- National cybercrime trends.
- Bank assets, deposits, returns, NPAs, and ATM infrastructure.
- Transaction date, value, and location analysis.
- State-level crime and cyber-fraud comparisons.

The dashboard loads generated CSVs from a path relative to `app.py`, so it does not depend on the terminal’s current directory.

## Open the Notebook

Run the notebook in JupyterLab:

```bash
jupyter lab main.ipynb
```

Run the cells from top to bottom after generating the merged datasets. The notebook contains the detailed charts, interactive maps, and exploratory analysis behind the dashboard’s summary views.

## Data Notes

- The project uses public banking, transaction, socioeconomic, and cybercrime records collected from multiple sources.
- Field names and units are preserved in the generated CSV headers where practical.
- Financial amounts are generally reported in Indian rupees, lakh, or crore according to the source field name.
- The outputs are analytical datasets, not live banking or crime feeds.
- Treat relationships in the exploratory charts as associations, not proof of causation.

## Troubleshooting

If the app says that merged datasets are missing, run:

```bash
python data_merge.py
```

If an import is missing, activate the virtual environment and reinstall:

```bash
python -m pip install -r requirements.txt
```

If PowerShell blocks environment activation, run this once in the current terminal or use the environment’s Python directly:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```
