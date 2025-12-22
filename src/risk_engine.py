# src/risk_engine.py
from textblob import TextBlob
from src.models import Company
import pandas as pd
import numpy as np

class RiskEvaluator:
    """
    Tier 3 Upgrade: Adds Financial Verification Logic (Cash Flow).
    """

    def evaluate(self, company: Company) -> Company:
        if not company.reviews:
            company.risk_score = 50.0 
            return company

        # 1. Convert Reviews to Pandas
        data = []
        CRITICAL_RISK_TERMS = ["bankruptcy", "fraud", "investigation", "subpoena", "default", "scandal", "lawsuit"]
        
        print(f"--- 🧠 Analyzing Risk for {company.name} ---")

        for review in company.reviews:
            blob = TextBlob(review.text)
            polarity = blob.sentiment.polarity
            
            # Compliance Check
            text_lower = review.text.lower()
            if any(term in text_lower for term in CRITICAL_RISK_TERMS):
                print(f"⚠️ RED FLAG DETECTED: {review.text[:30]}...")
                polarity = -1.0 
                company.lawsuit_flag = True
            
            data.append({
                "date": pd.to_datetime(review.date, errors='coerce'), 
                "sentiment": polarity
            })
            
        df = pd.DataFrame(data).dropna(subset=['date']).sort_values(by="date")
        
        if df.empty:
            company.risk_score = 50.0
            return company

        # --- CALCULATE METRICS ---
        if len(df) >= 3:
            recent_avg = df['sentiment'].tail(3).mean()
            historical_avg = df['sentiment'].iloc[:-3].mean() if len(df) > 3 else 0.0
            company.sentiment_momentum = recent_avg - historical_avg
        
        volatility = df['sentiment'].std()
        if np.isnan(volatility): volatility = 0.0
        company.news_volume_volatility = volatility

        # --- SCORING MODEL v3.2 ---
        avg_sentiment = df['sentiment'].mean()
        score = 50 + (avg_sentiment * 80) 
        
        # 1. Momentum Penalty
        if company.sentiment_momentum < -0.15:
            print("📉 PENALTY: Negative Momentum")
            score -= 10
            
        # 2. Volatility Penalty
        if volatility > 0.4:
            print("🌊 PENALTY: High Volatility")
            score -= 5
            
        # --- TIER 2: STABILITY ADJUSTMENTS ---
        
        # A. Business Age Logic
        if company.business_age > 0:
            if company.business_age < 2:
                print("👶 RISK: Startup (<2 years)")
                score -= 15 # High failure risk
            elif company.business_age > 20:
                print("🏛️ BONUS: Legacy Business (>20 years)")
                score += 5 # Proven track record
                
        # B. Industry Risk (Simple Keyword Match)
        high_risk_sectors = ["Restaurant", "Retail", "Airlines", "Construction"]
        if any(x in company.industry for x in high_risk_sectors):
            print(f"🏭 RISK: High-Risk Sector ({company.industry})")
            score -= 5

        # --- TIER 3: FINANCIAL LIQUIDITY CHECK (New!) ---
        # If the user uploaded a PDF and we found a balance:
        if company.has_verified_financials:
            if company.cash_balance > 50000:
                print("💰 BONUS: Strong Cash Reserves (>$50k)")
                score += 15 # Huge confidence boost
            elif company.cash_balance > 10000:
                print("💵 BONUS: Healthy Cash Flow (>$10k)")
                score += 5
            elif company.cash_balance < 1000:
                print("📉 RISK: Low Cash Reserves (<$1k)")
                score -= 10

        # Final Cap
        final_score = max(0, min(100, score))
        
        if company.lawsuit_flag:
            print("⛔ HARD STOP: Legal Flag")
            final_score = min(final_score, 40.0)
            
        company.risk_score = round(final_score, 2)
        company.sentiment_score = avg_sentiment
        
        return company