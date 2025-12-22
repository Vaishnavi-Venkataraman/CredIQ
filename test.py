# test_scraper.py
from src.models import Company
from src.scraper import ReviewScraper

# 1. Define Target
target_name = "Tesla"  # Try different names here (Tesla, Apple, Domino's)
print(f"\n🧪 TEST STARTING FOR: {target_name}")

# 2. Initialize
company = Company(name=target_name, url="")
scraper = ReviewScraper()

# 3. Run Scrape (Mock=False to force real connection)
company = scraper.fetch_data(company, mock=False)

# 4. Report Results
print("\n--- 🏁 TEST RESULTS ---")
if len(company.reviews) > 0:
    print(f"✅ SUCCESS! Scraped {len(company.reviews)} articles.")
    print("Top 3 Headlines:")
    for i, review in enumerate(company.reviews[:3]):
        print(f"  {i+1}. [{review.date}] {review.text}")
else:
    print("❌ FAILURE: No data retrieved.")