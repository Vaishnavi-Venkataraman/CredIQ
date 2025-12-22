# src/risk_engine.py
from textblob import TextBlob
from src.models import Company
import pandas as pd
import numpy as np

class RiskEvaluator:
    """
    Tier 1 Upgrade: Momentum & Velocity Risk Engine.
    Calculates trends (Momentum) and stability (Volatility) using Time-Series data.
    """

    def evaluate(self, company: Company) -> Company:
        if not company.reviews:
            company.risk_score = 50.0 
            return company

        # 1. Convert Reviews to Pandas DataFrame for Time-Series Math
        data = []
        
        # KEYWORDS that trigger a hard stop
        CRITICAL_RISK_TERMS = ["bankruptcy", "fraud", "investigation", "subpoena", "default", "scandal", "lawsuit"]

        print(f"--- 🧠 Analyzing Risk for {company.name} ---")

        for review in company.reviews:
            # NLP Processing
            blob = TextBlob(review.text)
            polarity = blob.sentiment.polarity
            
            # Compliance Check (Hard Stop Flag)
            text_lower = review.text.lower()
            if any(term in text_lower for term in CRITICAL_RISK_TERMS):
                print(f"⚠️ RED FLAG DETECTED: Found critical term in review.")
                polarity = -1.0 # Force max negative sentiment for this specific item
                company.lawsuit_flag = True # Set the binary flag
            
            # Collect data for DataFrame
            # We use 'errors=coerce' to handle potential date parsing issues gracefully
            data.append({
                "date": pd.to_datetime(review.date, errors='coerce'), 
                "sentiment": polarity
            })
            
        # Create DataFrame and drop invalid dates
        df = pd.DataFrame(data).dropna(subset=['date'])
        
        if df.empty:
            company.risk_score = 50.0
            return company

        # Sort by date (Oldest -> Newest) to calculate Momentum correctly
        df = df.sort_values(by="date")

        # --- 2. CALCULATE MOMENTUM (Tier 1 Feature) ---
        # Compare "Recent" (Last 3 items) vs "Historical" (The rest)
        # Logic: If recent news is worse than historical average, Momentum is negative.
        if len(df) >= 3:
            recent_avg = df['sentiment'].tail(3).mean()
            historical_avg = df['sentiment'].iloc[:-3].mean() if len(df) > 3 else 0.0
            
            # Momentum = Recent Performance - Historical Baseline
            company.sentiment_momentum = recent_avg - historical_avg
        else:
            company.sentiment_momentum = 0.0 # Not enough data for trend

        # --- 3. CALCULATE VOLATILITY (Tier 1 Feature) ---
        # Standard Deviation measures chaos. If news swings wildly (+1 to -1), volatility is high.
        volatility = df['sentiment'].std()
        if np.isnan(volatility): volatility = 0.0
        company.news_volume_volatility = volatility

        # --- 4. FINAL WEIGHTED SCORING MODEL ---
        
        # Base Score: Standardized average
        avg_sentiment = df['sentiment'].mean()
        company.sentiment_score = avg_sentiment
        
        # Scale: 0.0 sentiment -> 50 score. +0.5 sentiment -> 90 score.
        score_raw = 50 + (avg_sentiment * 80) 
        
        # Apply Penalties
        
        # Penalty A: Crashing Momentum
        if company.sentiment_momentum < -0.15:
            print(f"📉 MOMENTUM PENALTY: Trend is crashing ({company.sentiment_momentum:.2f})")
            score_raw -= 10
            
        # Penalty B: High Volatility (Uncertainty)
        if volatility > 0.4:
            print(f"🌊 VOLATILITY PENALTY: High uncertainty detected ({volatility:.2f})")
            score_raw -= 5
            
        # Clamp Score (0-100)
        final_score = max(0, min(100, score_raw))
        
        # --- 5. THE HARD STOP (Regulatory Gate) ---
        # If a lawsuit/fraud is detected, the score CANNOT exceed 40 (Auto-Reject).
        if company.lawsuit_flag:
            print("⛔ HARD STOP TRIGGERED: Legal flag active. Capping score at 40.")
            final_score = min(final_score, 40.0)
            
        company.risk_score = round(final_score, 2)
        
        return company