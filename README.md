# Macro Center V2

Premium macroeconomic intelligence dashboard built with Streamlit and a clean services/components architecture.

## V2 Highlights

- Apple-like dark fintech presentation with glassmorphic panels
- Country intelligence views with KPI cards, trend panels, sentiment, and news flow
- Compare mode for side-by-side macro snapshots
- Cached World Bank and FRED integrations with fallback data and freshness timestamps
- Session-state driven country selection and UI persistence

## Architecture

```text
macro-command-center/
├── app.py
├── config.py
├── components/
├── services/
├── utils/
├── assets/
└── requirements.txt
```

- `app.py`: thin orchestrator and layout composition
- `components/`: all Streamlit UI rendering
- `services/`: APIs, caching, and data fallback strategy
- `utils/`: formatting, country metadata, sentiment logic

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export FRED_API_KEY=your_key_here
streamlit run app.py
```

## Data Freshness

Service-layer caching stores fetch timestamps so the UI can show "data as of" context. API calls are cached for 1 hour and hot-path compositions for 5 minutes.
