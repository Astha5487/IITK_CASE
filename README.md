# FinMind OS

**Emotion-aware AI bridging personal finance and investment & trading**

IITK Global Case Competition 2025 — Technical Research Repository

---

## What this is

FinMind OS is a decision-support system that computes three scores simultaneously before any trade is confirmed Financial Readiness (FRS), Emotional Risk (ERS), and Goal Alignment (GAS). It then uses a language model to generate a personalised intervention message anchored to the user's actual numbers, not generic financial advice.

The core insight: a trade is not just a financial event. It is the intersection of your market knowledge, your current financial health, and your psychological state at that exact moment. No existing platform measures all three simultaneously.

---

## Repository structure

```
IITK_CASE
│
├── Project_Notebook.ipynb          # Main research notebook — run this
│
├── utils/
│   ├── __init__.py
│   ├── scorer.py                   # FRS + ERS + GAS computation engine
│   ├── agent.py                    # LLM reframe agent (Groq / Llama 3.1)
│   └── advisor.py                  # Personalised trade recommendation engine
│
├── IITK_Case_Comp__Responses_.xlsx # Survey data — 54 retail investors
├── requirements.txt
└── README.md
```

---

## Setup

```bash
git clone https://github.com/Astha5487/IITK_CASE
cd IITK_CASE
pip install -r requirements.txt
```

Set your Groq API key before running the notebook. Get a free key at https://console.groq.com

```bash
export GROQ_API_KEY=your_key_here
```

Then open the notebook:

```bash
jupyter notebook Project_Notebook.ipynb
```

The notebook will prompt you to enter your API key interactively if the environment variable is not set. The key is never written to the notebook file.

---

## What the notebook covers

**Part 1 — VIX backtest**
Downloads India VIX and Nifty 50 data from 2015 to 2024 via yfinance. Classifies every trading day as Calm, Anxious, or Panic using rolling percentile thresholds no lookahead bias. Computes average 10-day forward returns for each state and generates two charts for the presentation.

**Part 2 — 3-score engine**
Implements the FRS, ERS, and GAS formulas as a Python class. Runs two contrasting scenarios — Rahul (panic sell at 2am, low FRS, very high ERS) and Priya (calm deliberate investment, strong scores across all three). Generates gauge dashboard visuals.

**Part 3 — LLM reframe agent**
Calls Groq API with Llama 3.1-8b-instant. System prompt forces exactly 3 sentences, each anchored to the user's real numbers. Demonstrates two scenarios — panic sell and FOMO buy.

**Part 4 — Survey analysis**
Reads the Google Form response Excel file directly. Computes real bias percentages from 54 respondents. Generates bias chart and survey results chart with actual data no placeholder values.

**Part 5 — Trade recommendation engine**
Pulls live market data via yfinance for a curated universe of Indian stocks. Selects a risk tier based on the user's three scores. Recommends what to buy, how much to deploy, and why — with the same contrast between calm and stressed scenarios.

---

## The 3-score system

```
FRS = (EmergencyFund/6 × 30) + EMI_proximity × 25 + SizeVsSurplus × 25 + DTI × 20

ERS = VIX_risk × 30 + TimeOfDay × 20 + Telemetry × 25 + SizeAnomaly × 25

GAS = (ProjectedCorpus/Target × 60) + ImpactRatio × 40

Verdict = FRS × 0.35 + (100 − ERS) × 0.35 + GAS × 0.30
```

Scores are risk bands, not precise measurements. Emotions are noisy and proxies can misfire. The system informs it never blocks a trade.

---

## Using the utils independently

```python
from utils import FinMindScorer, FinMindReframeAgent

scorer = FinMindScorer()

frs = scorer.compute_frs(
    monthly_income=75000,
    total_emi=28000,
    emergency_fund_months=1.5,
    days_to_next_emi=6,
    trade_amount=80000,
    monthly_surplus=12000
)

ers = scorer.compute_ers(
    vix_level=38.5,
    hour_of_day=2,
    days_since_last_trade=3,
    hover_seconds_on_confirm=0.8,
    page_revisits=7,
    trade_size_vs_usual=4.2
)

gas = scorer.compute_gas(
    goal_name='Home down payment',
    goal_target_inr=2500000,
    goal_years_away=4,
    current_corpus_inr=450000,
    monthly_sip_inr=8000,
    trade_amount=80000,
    expected_return_pct=12,
    asset_type='sell'
)

rec, color, composite = scorer.verdict(frs, ers, gas)
print(f"FRS: {frs}  ERS: {ers}  GAS: {gas}  →  {rec} ({composite:.1f}/100)")
```

---

## Survey data

`IITK_Case_Comp__Responses_.xlsx` contains responses from 54 retail investors using Zerodha, Groww, and Upstox, collected April 2025.

Key findings used in the analysis:
- 41% sold or felt a strong urge to sell during a market crash
- 63% rarely or never think about their EMIs when making a trade
- 75.9% found the FinMind OS intervention concept helpful or somewhat helpful
- 56% had invested purely because of social media or friends buzzing about a stock

The notebook reads this file directly and computes all chart values from real responses nothing is hardcoded.

---

## Data sources

| Source | What it provides | Access |
|--------|-----------------|--------|
| yfinance | India VIX, Nifty 50 OHLCV (2015–2024) | Free, public |
| NSEPy | NSE market data | Free, public |
| Groq API | Llama 3.1-8b-instant inference | Free tier available |
| Google Forms | Primary survey responses | Our own data |


---

## License

Research repository for academic competition purposes.
