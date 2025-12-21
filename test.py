# test.py
from src.models import Company
from src.scraper import ReviewScraper
from src.risk_engine import RiskEvaluator

# 1. Setup
print("\n=== SYSTEM START ===")
company = Company(name="Joe's Pizza", url="http://fake-url.com")

# 2. Ingest Data (Using Mock Mode=True to ensure it works)
scraper = ReviewScraper()
company = scraper.fetch_yelp_data(company.url, company, mock=True)

# 3. Analyze Risk
engine = RiskEvaluator()
company = engine.evaluate(company)

# 4. Output Report
print("\n=== CREDIT RISK REPORT ===")
print(f"Applicant: {company.name}")
print(f"Data Points: {len(company.reviews)} reviews processed")
print(f"Sentiment Polarity: {company.sentiment_score:.4f} (-1.0 to +1.0)")
print(f"FINAL CREDIT SCORE: {company.risk_score} / 100")

if company.risk_score < 50:
    print("DECISION: REJECT LOAN (High Risk)")
else:
    print("DECISION: APPROVE LOAN")