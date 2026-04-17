# Macro Command Center

A dark, finance-style Streamlit dashboard for tracking macroeconomic indicators across major economies.

## Features

- Country selector for 10 economies
- KPI cards for GDP growth, inflation, unemployment, and interest rates
- 20-year historical indicator chart
- GDP choropleth world map
- Mock macro news feed
- Two-country radar comparison
- FRED API integration for US data
- World Bank API integration for international data with sample-data fallback

## Project Structure

```text
macro-command-center/
├── app.py
├── requirements.txt
├── .env
├── .streamlit/
│   └── config.toml
├── data/
│   └── sample_data.py
└── README.md
```

## Setup

```bash
cd /Users/Dany/Projects/macro-command-center
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 -m streamlit run app.py
```

## Environment

Create a `.env` file with:

```env
FRED_API_KEY=your_fred_api_key
```

The app automatically loads `.env` and reads `os.environ['FRED_API_KEY']` for FRED requests.

## Data Sources

- FRED API for US macro data
- World Bank API for international macro data and GDP levels
- Built-in sample data fallback when an API is unavailable

## Streamlit Cloud

This repo is deployment-ready for Streamlit Cloud. Add `FRED_API_KEY` as a secret or keep it in local `.env` for development.
