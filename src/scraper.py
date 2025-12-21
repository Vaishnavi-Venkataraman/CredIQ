# src/scraper.py
import requests
from bs4 import BeautifulSoup
import random
import hashlib
from src.models import Company

class ReviewScraper:
    """
    Auto-detects data sources. 
    Searches Google News RSS for the company name automatically.
    """
    
    # List of browser signatures to avoid blocking
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Gecko/20100101 Firefox/89.0"
    ]

    def fetch_data(self, company: Company, mock: bool = False) -> Company:
        """
        Main entry point.
        """
        print(f"--- 🔍 Starting Auto-Discovery for: {company.name} ---")

        if mock:
            return self._get_smart_mock_data(company)
        
        try:
            # 1. Try Real News
            company = self._fetch_google_news(company)
            
            # 2. Check if we actually got data
            if len(company.reviews) > 0:
                print(f"✅ Success: Found {len(company.reviews)} real articles.")
                return company
            else:
                print("⚠️ Google returned 0 results. Switching to Simulation.")
                return self._get_smart_mock_data(company)

        except Exception as e:
            print(f"❌ Error during scrape: {e}")
            return self._get_smart_mock_data(company)

    def _fetch_google_news(self, company: Company) -> Company:
        """
        Scrapes Google News RSS with proper Headers.
        """
        clean_name = company.name.replace(" ", "%20")
        # Simpler query to ensure results
        url = f"https://news.google.com/rss/search?q={clean_name}+finance&hl=en-US&gl=US&ceid=US:en"
        
        print(f"--- 📡 Pinging: {url} ---")
        
        # --- THE FIX IS HERE: ADDING HEADERS ---
        headers = {
            "User-Agent": random.choice(self.USER_AGENTS)
        }
        
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            # parsing xml content
            soup = BeautifulSoup(response.content, features="xml")
            items = soup.find_all("item")[:8]
            
            for item in items:
                title = item.title.text
                pub_date = item.pubDate.text
                company.add_review("Google News", title, 0.0, pub_date)
        else:
            print(f"Block detected: Status Code {response.status_code}")
                
        return company

    def _get_smart_mock_data(self, company: Company) -> Company:
        """
        Fallback generator.
        """
        print(f"-> 🎲 Generating Simulation for: {company.name}")
        
        seed_value = int(hashlib.sha256(company.name.encode('utf-8')).hexdigest(), 16) % 10**8
        random.seed(seed_value)
        
        is_good = seed_value % 2 == 0 
        
        if is_good:
            templates = [
                f"{company.name} reports strong quarterly earnings.",
                "Stock price jumps 5% on positive outlook.",
                "New strategic partnership announced.",
                "Analyst upgrades rating to Buy.",
                "Expansion into Asian markets is succeeding."
            ]
        else:
            templates = [
                f"{company.name} faces regulatory scrutiny.",
                "Shares tumble after missed earnings report.",
                "CEO warns of supply chain issues.",
                "Class action lawsuit filed against the company.",
                "Analyst downgrades rating to Sell."
            ]
            
        for _ in range(5):
            text = random.choice(templates)
            company.add_review("Simulated Intel", text, 0.0, "2025-12-21")
            
        return company