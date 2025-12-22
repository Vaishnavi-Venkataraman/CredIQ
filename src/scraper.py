# src/scraper.py
import requests
from bs4 import BeautifulSoup
import random
import datetime
import re
from src.models import Company

class ReviewScraper:
    
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Version/17.2 Safari/605.1.15"
    ]

    def fetch_data(self, company: Company, mock: bool = False) -> Company:
        """Main entry point."""
        print(f"--- 📡 DEBUG: Starting Scrape for '{company.name}' ---")
        
        if mock:
            return self._get_smart_mock_data(company)
        
        # 1. Fetch News (Tier 1)
        company = self._fetch_google_news(company)
        
        # 2. Fetch Metadata (Tier 2 - NEW)
        company = self._fetch_wikipedia_data(company)
        
        return company

    def _fetch_google_news(self, company: Company) -> Company:
        """Scrapes Google News RSS (Existing Logic)."""
        clean_name = company.name.replace(" ", "%20")
        url = f"https://news.google.com/rss/search?q={clean_name}+business&hl=en-US&gl=US&ceid=US:en"
        headers = {"User-Agent": random.choice(self.USER_AGENTS)}
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                try:
                    soup = BeautifulSoup(response.content, features="xml")
                except:
                    soup = BeautifulSoup(response.content, features="lxml")
                    
                items = soup.find_all("item")
                if not items:
                    print("⚠️ No news found. Switching to Mock.")
                    return self._get_smart_mock_data(company)
                    
                for item in items[:15]: 
                    company.add_review("Google News", item.title.text, 0.0, item.pubDate.text)
            else:
                return self._get_smart_mock_data(company)
        except Exception as e:
            print(f"❌ News Error: {e}")
            return self._get_smart_mock_data(company)
            
        return company

    def _fetch_wikipedia_data(self, company: Company) -> Company:
        """
        Tier 2: Scrapes 'Founded', 'Industry', and 'HQ' from Wikipedia Infobox.
        """
        print(f"--- 🏛️ Metadata: Hunting Wikipedia for '{company.name}' ---")
        
        # Try direct URL guessing (e.g., "Apple_Inc.")
        search_term = company.name.replace(" ", "_")
        urls_to_try = [
            f"https://en.wikipedia.org/wiki/{search_term}",
            f"https://en.wikipedia.org/wiki/{search_term}_(company)"
        ]
        
        headers = {"User-Agent": random.choice(self.USER_AGENTS)}
        
        for url in urls_to_try:
            try:
                response = requests.get(url, headers=headers, timeout=5)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    infobox = soup.find("table", {"class": "infobox"})
                    
                    if infobox:
                        # 1. Get Founded Year
                        # Look for a row with 'Founded' in header
                        for row in infobox.find_all("tr"):
                            header = row.find("th")
                            if header and "Founded" in header.text:
                                text = row.find("td").text
                                # Regex to find 4 digit year (e.g. 1976)
                                match = re.search(r'\d{4}', text)
                                if match:
                                    company.founding_year = int(match.group(0))
                                    current_year = datetime.datetime.now().year
                                    company.business_age = current_year - company.founding_year
                                    print(f"✅ FOUND AGE: {company.business_age} years old ({company.founding_year})")
                                    
                            # 2. Get Headquarters
                            if header and "Headquarters" in header.text:
                                company.headquarters = row.find("td").text.strip().split("\n")[0]
                                
                            # 3. Get Industry
                            if header and "Industry" in header.text:
                                company.industry = row.find("td").text.strip().split("\n")[0]
                        
                        return company # Success, stop trying URLs
            except Exception as e:
                print(f"Wiki Error: {e}")
                
        print("⚠️ Metadata not found on Wikipedia. Using defaults.")
        return company

    def _get_smart_mock_data(self, company: Company) -> Company:
        """Fallback Simulation."""
        print(f"-> 🎲 Generating Simulation for: {company.name}")
        random.seed(len(company.name))
        
        # Simulate Metadata
        company.founding_year = 2010
        company.business_age = 15
        company.industry = "Technology (Simulated)"
        company.headquarters = "San Francisco, CA"
        
        templates = [
            "Revenue beat expectations this quarter.",
            "New product launch is highly successful.",
            "Market share is growing rapidly.",
            "Strong leadership and solid balance sheet.",
            "Analyst rating upgraded to Buy."
        ]
        
        base_date = datetime.datetime.now()
        for i in range(12):
            text = random.choice(templates)
            fake_date = (base_date - datetime.timedelta(days=i)).strftime("%a, %d %b %Y %H:%M:%S GMT")
            company.add_review("Simulated Intel", text, 0.0, fake_date)
            
        return company