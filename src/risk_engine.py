# src/risk_engine.py
from textblob import TextBlob
from src.models import Company
import statistics
import math

class RiskEvaluator:

    def evaluate(self, company: Company) -> Company:
        if not company.reviews:
            company.risk_score = 50.0 
            return company

        sentiment_scores = []
        red_flags = 0
        
        # KEYWORDS that tank the score immediately
        CRITICAL_RISK_TERMS = ["bankruptcy", "fraud", "investigation", "subpoena", "default", "scandal"]

        print(f"--- 🧠 Analyzing Risk for {company.name} ---")

        for review in company.reviews:
            # 1. NLP Processing
            blob = TextBlob(review.text)
            polarity = blob.sentiment.polarity
            
            # 2. Keyword Penalty (The "Compliance" Check)
            text_lower = review.text.lower()
            for term in CRITICAL_RISK_TERMS:
                if term in text_lower:
                    print(f"⚠️ RED FLAG DETECTED: {term}")
                    polarity -= 0.5 # Massive penalty
                    red_flags += 1

            sentiment_scores.append(polarity)

        # 3. Statistical Aggregation
        if not sentiment_scores:
            avg_sentiment = 0
        else:
            avg_sentiment = statistics.mean(sentiment_scores)

        # 4. Standardized Scoring 
        score_raw = 50 + (avg_sentiment * 100)
        
        # Cap the limits
        score_clamped = max(0, min(100, score_raw))
        
        # 5. Apply Red Flag Penalties
        # Each red flag drops the score by 10 points flat
        final_score = score_clamped - (red_flags * 10)
        
        company.sentiment_score = avg_sentiment
        company.risk_score = round(max(0, final_score), 2)
        
        return company