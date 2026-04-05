"""
FinMind OS — Personalised Trade Recommendation Engine
------------------------------------------------------
Takes a user's full financial and emotional context — budget, 3-score
profile, goal, and trading pattern — and recommends what to trade,
in what size, and why.

Pulls live price and 3-month momentum from yfinance for a curated
universe of Indian stocks, then asks the LLM to synthesise everything
into a structured recommendation.
"""

import time
import pandas as pd
import yfinance as yf
from groq import Groq


class FinMindTradeAdvisor:
    """
    Personalised trade recommendation engine.
    """

    STOCK_UNIVERSE = {
        'conservative': [
            ('HDFCBANK.NS',    'HDFC Bank'),
            ('TCS.NS',         'TCS'),
            ('INFY.NS',        'Infosys'),
            ('HINDUNILVR.NS',  'Hindustan Unilever'),
            ('KOTAKBANK.NS',   'Kotak Mahindra Bank'),
        ],
        'moderate': [
            ('RELIANCE.NS',    'Reliance Industries'),
            ('ICICIBANK.NS',   'ICICI Bank'),
            ('BHARTIARTL.NS',  'Bharti Airtel'),
            ('WIPRO.NS',       'Wipro'),
            ('AXISBANK.NS',    'Axis Bank'),
        ],
        'aggressive': [
            ('ETERNAL.NS',     'Zomato (Eternal Ltd)'),   # Zomato rebranded
            ('PAYTM.NS',       'Paytm'),                  # correct symbol
            ('IRCTC.NS',       'IRCTC'),
            ('NAUKRI.NS',      'Info Edge (Naukri)'),
        ]
    }

    def __init__(self, api_key):
        self.client = Groq(api_key=api_key)

    def _determine_risk_tier(self, frs, ers, gas):
        if frs < 40 or ers > 65:
            return 'conservative', 'Financial buffer low or emotional risk high.'
        elif frs >= 70 and ers < 35 and gas >= 60:
            return 'aggressive', 'Strong profile for growth.'
        else:
            return 'moderate', 'Balanced profile.'

    def _fetch_market_data(self, tickers_with_names):
        """
        Downloads price and momentum data for each stock.
        Handles yfinance MultiIndex columns, empty results,
        and rate limit errors — never crashes the full run.
        """
        records = []

        for ticker, name in tickers_with_names:
            fetched = False

            for attempt in range(2):
                try:
                    time.sleep(0.4)

                    hist = yf.download(
                        ticker,
                        period='3mo',
                        progress=False,
                        auto_adjust=True,
                        actions=False
                    )

                    if isinstance(hist.columns, pd.MultiIndex):
                        hist.columns = [col[0] for col in hist.columns]

                    if 'Close' not in hist.columns or hist.empty:
                        break

                    close = hist['Close'].dropna()
                    if len(close) < 5:
                        break

                    price = float(close.iloc[-1])
                    price_3m = float(close.iloc[0])
                    mom_3m = round((price - price_3m) / max(price_3m, 1) * 100, 2)

                    hist_1y = yf.download(
                        ticker,
                        period='1y',
                        progress=False,
                        auto_adjust=True,
                        actions=False
                    )

                    if isinstance(hist_1y.columns, pd.MultiIndex):
                        hist_1y.columns = [col[0] for col in hist_1y.columns]

                    close_1y = hist_1y['Close'].dropna() if 'Close' in hist_1y.columns else close
                    wk52_lo = float(close_1y.min())
                    wk52_hi = float(close_1y.max())

                    pct_range = round(
                        (price - wk52_lo) / max(wk52_hi - wk52_lo, 1) * 100, 1
                    )

                    records.append({
                        'ticker': ticker,
                        'name': name,
                        'price': round(price, 2),
                        'week52_lo': round(wk52_lo, 2),
                        'week52_hi': round(wk52_hi, 2),
                        'pct_of_range': pct_range,
                        'momentum_3m': mom_3m,
                    })

                    fetched = True
                    break

                except Exception:
                    time.sleep(1)
                    continue

            if not fetched:
                print(f"  Skipped: {name} ({ticker})")

        if not records:
            print("\nNo stocks fetched.")
            return pd.DataFrame()

        df = pd.DataFrame(records)
        print(f"\nFetched: {len(df)}/{len(tickers_with_names)} stocks")
        return df

    def _position_size(self, budget, frs, ers):
        if ers > 65 or frs < 40:
            return round(budget * 0.3), 0.3, "Low deployment"
        elif ers > 40 or frs < 60:
            return round(budget * 0.6), 0.6, "Moderate deployment"
        else:
            return round(budget * 0.85), 0.85, "High deployment"

    def recommend(self,
                  user_name,
                  available_budget_inr,
                  frs, ers, gas,
                  goal_name,
                  goal_years,
                  trading_pattern,
                  risk_appetite,
                  vix_level,
                  current_holdings_summary="Not provided"):

        tier, reason = self._determine_risk_tier(frs, ers, gas)

        stocks = self.STOCK_UNIVERSE[tier]
        data = self._fetch_market_data(stocks)

        if data.empty:
            print("No data fetched.")
            return

        data['score'] = (
            data['momentum_3m'].clip(-20, 20) * 0.5 +
            (100 - data['pct_of_range']) * 0.5
        )

        data = data.sort_values('score', ascending=False)

        deploy, pct, _ = self._position_size(available_budget_inr, frs, ers)

        print("\nTop Picks:")
        print(data[['name', 'price', 'momentum_3m']].head(3))

        return data.head(3)
