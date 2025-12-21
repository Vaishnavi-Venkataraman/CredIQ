# src/risk_engine.py
from textblob import TextBlob
from src.models import Company
import statistics

class RiskEvaluator:
    """
    The 'Brain' of the system.
    Converts unstructured text into a mathematical Risk Score (0-100).
    """

    def evaluate(self, company: Company) -> Company:
        if not company.reviews:
            company.risk_score = 50.0 # Neutral risk if no data
            return company

        sentiment_scores = []
        
        print(f"--- Analyzying Risk for {company.name} ---")

        for review in company.reviews:
            # 1. NLP Processing
            # TextBlob calculates polarity: -1.0 (Bad) to +1.0 (Good)
            blob = TextBlob(review.text)
            polarity = blob.sentiment.polarity
            
            # 2. Risk Weighting logic
            # If text contains "fraud" or "bankrupt", force score down (Keyword Flagging)
            if "fraud" in review.text.lower() or "bankrupt" in review.text.lower():
                polarity = -1.0
                print(f"ALERT: Red Flag keyword detected in: '{review.text[:30]}...'")

            sentiment_scores.append(polarity)

        # 3. Calculate Aggregate Metrics
        avg_sentiment = statistics.mean(sentiment_scores)
        company.sentiment_score = avg_sentiment
        
        # 4. Convert Sentiment (-1 to 1) to a Credit Score (0 to 100)
        # Formula: Map [-1, 1] -> [0, 100]
        # -1 (Bad) should be High Risk? Or Low Credit Score?
        # Let's say: 0 is High Risk (Bad), 100 is Low Risk (Good).
        normalized_score = ((avg_sentiment + 1) / 2) * 100
        
        company.risk_score = round(normalized_score, 2)
        
        return company