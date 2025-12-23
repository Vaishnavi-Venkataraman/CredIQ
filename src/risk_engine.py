# src/risk_engine.py
from textblob import TextBlob
from src.models import Company
import pandas as pd
import numpy as np

class RiskEvaluator:
    """
    Tier 6 Upgrade: Includes Geo-Economic & Location Risk.
    """

    def evaluate(self, company: Company) -> Company:
        # Clear previous reasons to avoid duplicates
        company.decision_reasons = []
        company.contagion_penalty = 0.0
        
        if not company.reviews:
            company.risk_score = 50.0
            company.decision_reasons.append("Insufficient data to generate full risk profile.")
            return company

        # 1. Convert Reviews to Pandas
        data = []
        CRITICAL_RISK_TERMS = ["bankruptcy", "fraud", "investigation", "subpoena", "default", "scandal", "lawsuit"]
        
        print(f"--- 🧠 Analyzing Risk for {company.name} ---")

        # --- CRITICAL FIX: Iterate with ENUMERATE to force update in place ---
        for i, review in enumerate(company.reviews):
            blob = TextBlob(review.text)
            polarity = blob.sentiment.polarity
            
            # FORCE UPDATE THE OBJECT IN THE LIST
            company.reviews[i].rating = polarity 
            
            # Compliance Check
            text_lower = review.text.lower()
            if any(term in text_lower for term in CRITICAL_RISK_TERMS):
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

        # --- METRICS ---
        if len(df) >= 3:
            recent_avg = df['sentiment'].tail(3).mean()
            historical_avg = df['sentiment'].iloc[:-3].mean() if len(df) > 3 else 0.0
            company.sentiment_momentum = recent_avg - historical_avg
        
        volatility = df['sentiment'].std()
        if np.isnan(volatility): volatility = 0.0
        company.news_volume_volatility = volatility

        # --- SCORING & EXPLAINABILITY ---
        avg_sentiment = df['sentiment'].mean()
        score = 50 + (avg_sentiment * 80) 
        
        # 1. Momentum Penalty
        if company.sentiment_momentum < -0.15:
            score -= 10
            company.decision_reasons.append(f"Negative market sentiment trend detected ({company.sentiment_momentum:.2f} momentum).")
            
        # 2. Volatility Penalty
        if volatility > 0.4:
            score -= 5
            company.decision_reasons.append("High volatility in market news signals instability.")
            
        # 3. Age Logic
        if company.business_age > 0:
            if company.business_age < 2:
                score -= 15 
                company.decision_reasons.append("High Risk: Early-stage startup (< 2 years operating history).")
            elif company.business_age > 20:
                score += 5
                
        # 4. Industry Risk
        high_risk_sectors = ["Restaurant", "Retail", "Airlines", "Construction"]
        if any(x in company.industry for x in high_risk_sectors):
            score -= 5
            company.decision_reasons.append(f"High-risk industry sector identified: {company.industry}.")

        # 5. Financial Liquidity
        if company.has_verified_financials:
            if company.cash_balance > 50000:
                score += 15 
            elif company.cash_balance < 1000:
                score -= 10
                company.decision_reasons.append("CRITICAL: Insufficient cash reserves verified (< $1,000).")

        # 6. Contagion Risk
        for entity in company.related_entities:
            if entity["Risk_Score"] < 50:
                penalty = 10.0
                company.contagion_penalty += penalty
                score -= penalty
                company.decision_reasons.append(f"Contagion Risk: Sister company '{entity['Name']}' is distressed.")

        # --- 7. GEO-ECONOMIC RISK ---
        hq = company.headquarters.lower()
        company.geo_risk_label = "Neutral Zone"
        
        # A. High Cost Zones
        high_cost_zones = ["california", " ca", "new york", " ny", "san francisco", "manhattan", "massachusetts"]
        if any(z in hq for z in high_cost_zones):
            company.geo_risk_score = 70.0
            company.geo_risk_label = "High Operational Cost Zone"
            if company.business_age < 5:
                score -= 5
                company.decision_reasons.append(f"Geo-Risk: High burn-rate location ({company.headquarters}) for early-stage co.")

        # B. Climate/Disaster Zones
        disaster_zones = ["florida", " fl", "louisiana", " la", "miami", "houston"]
        if any(z in hq for z in disaster_zones):
            company.geo_risk_score = 60.0
            company.geo_risk_label = "Climate/Insurance Risk Zone"
            company.decision_reasons.append(f"Geo-Risk: Location flags high insurance premiums ({company.headquarters}).")

        # Final Cap
        final_score = max(0, min(100, score))
        
        # 8. Hard Stop Logic
        if company.lawsuit_flag:
            final_score = min(final_score, 40.0)
            company.decision_reasons.insert(0, "HARD STOP: Active legal/regulatory risk detected in background check.")
            
        # Generic Reason
        if final_score < 50 and not company.decision_reasons:
            company.decision_reasons.append("Overall negative market sentiment.")

        company.risk_score = round(final_score, 2)
        company.sentiment_score = avg_sentiment
        
        return company