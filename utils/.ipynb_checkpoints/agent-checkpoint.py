"""
FinMind OS — LLM Reframe Agent
--------------------------------
Generates a personalised 3-sentence intervention message using Groq's
Llama 3.1 model.  The prompt is structured so the model is forced to use
the user's actual numbers — EMI amount, emergency fund, goal name — rather
than producing generic financial advice.

Usage
-----
from utils.agent import FinMindReframeAgent
import os

agent = FinMindReframeAgent(os.environ['GROQ_API_KEY'])
message = agent.generate(user_name='Rahul', age=28, ...)
print(message)
"""

from groq import Groq


class FinMindReframeAgent:
    """
    LLM-powered intervention agent.
    Forces the LLM to use the user's specific numbers — not generic advice.
    """

    def __init__(self, api_key):
        self.client = Groq(api_key=api_key)

    def generate(self, user_name, age, trade_intent, trade_amount_inr,
                 frs, ers, gas, recommendation,
                 monthly_income, emergency_fund_months,
                 days_to_emi, emi_amount,
                 goal_name, goal_years,
                 vix_level, hour_of_day,
                 emotional_state,
                 position_return_pct=None):

        # FIX: strict system prompt forces specific, personal output
        system_prompt = """You are FinMind OS, an empathetic AI financial companion.
Generate EXACTLY 3 sentences. No more.
Sentence 1: Mention their EXACT EMI amount (₹) and exact days remaining — nothing generic.
Sentence 2: Mention their emergency fund (X months) and what the risk is in plain words.
Sentence 3: Mention their goal by its exact name and ask ONE gentle question.
Never give generic financial advice. Never use bullet points.
Sound like a trusted friend who knows their finances, not a financial textbook.
Use ₹ symbol for all amounts."""

        pos_str = f" (currently {position_return_pct:+.1f}% on this position)" if position_return_pct else ""
        time_str = f"{hour_of_day}:00 {'AM' if hour_of_day < 12 else 'PM'}"

        user_prompt = f"""User: {user_name}, age {age}
Wants to: {trade_intent} — ₹{trade_amount_inr:,}{pos_str}
Time of decision: {time_str}
Emotional state detected: {emotional_state}
Market fear index (VIX): {vix_level}

Financial situation:
- Monthly income: ₹{monthly_income:,}
- EMI due in {days_to_emi} days: ₹{emi_amount:,}
- Emergency fund: {emergency_fund_months} months of expenses

FinMind OS Scores:
- FRS (Financial Readiness): {frs}/100
- ERS (Emotional Risk): {ers}/100 — higher means more emotional
- GAS (Goal Alignment): {gas}/100
- System verdict: {recommendation}

Their stated goal: {goal_name} in {goal_years} years

Write your 3-sentence intervention now:"""

        resp = self.client.chat.completions.create(
            model='llama-3.1-8b-instant',
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user',   'content': user_prompt}
            ],
            max_tokens=200,
            temperature=0.7
        )
        return resp.choices[0].message.content
