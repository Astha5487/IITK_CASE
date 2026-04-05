"""
FinMind OS — 3-Score Engine
----------------------------
Computes three scores for any trade decision:
  FRS  Financial Readiness Score  — can you afford this trade right now?
  ERS  Emotional Risk Score       — are you in the right state to decide?
  GAS  Goal Alignment Score       — does this serve your financial future?

All scores are 0–100.  Higher FRS / GAS is better.  Higher ERS is worse.
The composite verdict combines all three into a single recommendation.

Important: these scores are decision-support proxies, not precise measurements.
Emotions are noisy and behavioral signals can misfire.  The system informs —
it never blocks a trade.
"""


class FinMindScorer:
    """
    3-Score engine for FinMind OS.
    All scores 0-100. Higher FRS/GAS = better. Higher ERS = more emotional risk.

    IMPORTANT LIMITATION: These scores are decision-support proxies.
    Emotions are noisy. Behavioral signals can be misread.
    The system NEVER blocks a trade — it only informs.
    """

    def compute_frs(self, monthly_income, total_emi,
                    emergency_fund_months, days_to_next_emi,
                    trade_amount, monthly_surplus):
        """Financial Readiness Score — can you afford this trade?"""
        # Factor 1: Emergency fund (weight 30) — ideal = 6 months
        ef_score = min(emergency_fund_months / 6.0, 1.0) * 30

        # Factor 2: EMI proximity + trade size pressure (weight 25)
        emi_urgency    = max(0, 1 - (days_to_next_emi / 30))
        trade_pressure = min(trade_amount / max(monthly_surplus, 1), 2.0)
        emi_score      = max(0, (1 - emi_urgency * trade_pressure * 0.5) * 25)

        # Factor 3: Trade size vs monthly surplus (weight 25)
        size_ratio = trade_amount / max(monthly_surplus, 1)
        size_score = max(0, (1 - min(size_ratio / 2, 1))) * 25

        # Factor 4: Debt-to-income ratio (weight 20)
        dti       = total_emi / max(monthly_income, 1)
        dti_score = max(0, (1 - min(dti / 0.5, 1))) * 20

        return round(min(ef_score + emi_score + size_score + dti_score, 100), 1)

    def compute_ers(self, vix_level, hour_of_day,
                    days_since_last_trade,
                    hover_seconds_on_confirm,
                    page_revisits, trade_size_vs_usual):
        """
        Emotional Risk Score — how emotionally driven is this trade?
        Uses behavioral PROXIES. High score = elevated emotional risk signal.
        NOT a direct measurement of emotion — read as a risk band.
        """
        # Factor 1: Market fear (VIX) — weight 30
        vix_risk = min(max((vix_level - 12) / 28, 0), 1) * 30

        # Factor 2: Time of day — weight 20
        # Late night / early morning = cognitively impaired decision-making
        if 23 <= hour_of_day or hour_of_day <= 5:
            time_risk = 20
        elif 6 <= hour_of_day <= 8:
            time_risk = 10
        else:
            time_risk = 0

        # Factor 3: Behavioral telemetry — weight 25
        # Proxy: fast click = impulsive, many revisits = anxious
        hover_risk   = max(0, (5 - min(hover_seconds_on_confirm, 5)) / 5) * 12
        revisit_risk = min(page_revisits / 5, 1) * 13
        telem_risk   = hover_risk + revisit_risk

        # Factor 4: Unusual trade size — weight 25
        # 3x+ normal size = FOMO or panic signal
        size_risk = min(max(trade_size_vs_usual - 1, 0) / 2, 1) * 25

        return round(min(vix_risk + time_risk + telem_risk + size_risk, 100), 1)

    def compute_gas(self, goal_name, goal_target_inr, goal_years_away,
                    current_corpus_inr, monthly_sip_inr,
                    trade_amount, expected_return_pct,
                    asset_type='equity',
                    selling_to_fund_goal=False):
        """Goal Alignment Score — does this trade serve your financial future?"""
        # Project future corpus via SIP formula
        r = expected_return_pct / 100 / 12
        n = goal_years_away * 12
        future_corpus = current_corpus_inr * (1 + r) ** n
        future_sip    = (monthly_sip_inr * (((1+r)**n - 1) / r)
                         if r > 0 else monthly_sip_inr * n)
        projected     = future_corpus + future_sip
        coverage      = min(projected / max(goal_target_inr, 1), 1.5)

        # selling_to_fund_goal = True means sell is goal-aligned
        if selling_to_fund_goal:
            impact = trade_amount   # Selling for this goal is positive
        elif asset_type == 'sell':
            impact = -trade_amount  # Selling without goal purpose = hurts
        elif asset_type in ['equity', 'mutual_fund']:
            impact = trade_amount
        else:
            impact = 0

        impact_ratio = impact / max(goal_target_inr, 1)
        gas = (coverage * 60) + (impact_ratio * 40)
        return round(min(max(gas, 0), 100), 1)

    def label(self, score, invert=False):
        if invert:  # ERS: high = bad
            if score >= 70: return ('PANIC / FOMO', '#E24B4A')
            elif score >= 45: return ('ANXIOUS',    '#EF9F27')
            elif score >= 25: return ('CAUTIOUS',   '#FAC775')
            else: return ('CALM', '#1D9E75')
        else:
            if score >= 75: return ('STRONG',   '#1D9E75')
            elif score >= 50: return ('MODERATE','#EF9F27')
            elif score >= 25: return ('WEAK',    '#D85A30')
            else: return ('CRITICAL','#E24B4A')

    def verdict(self, frs, ers, gas):
        composite = (frs * 0.35) + ((100 - ers) * 0.35) + (gas * 0.30)
        if composite >= 70:   return 'PROCEED',         '#1D9E75', composite
        elif composite >= 50: return 'PAUSE & REVIEW',  '#EF9F27', composite
        elif composite >= 30: return 'STRONG CAUTION',  '#D85A30', composite
        else:                 return 'DO NOT TRADE NOW','#E24B4A', composite
