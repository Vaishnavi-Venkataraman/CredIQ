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
        
        # 2. Fetch Metadata (Tier 2)
        company = self._fetch_wikipedia_data(company)

        # 3. Fetch Contagion Data (Tier 4 - NEW)
        # This maps owners and related companies for the graph
        company = self._fetch_contagion_links(company)
        
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
                        for row in infobox.find_all("tr"):
                            header = row.find("th")
                            if header and "Founded" in header.text:
                                text = row.find("td").text
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

    def _fetch_contagion_links(self, company: Company) -> Company:
        """
        Tier 4: Simulates ownership graphs for famous entities to demonstrate Systemic Risk.
        In a real app, this would query a Neo4j database or Crunchbase API.
        """
        print(f"--- 🕸️ Contagion: Mapping network for '{company.name}' ---")
        name_lower = company.name.lower()
        
        # DEMO DATASET: Map Companies to Owners & Sister Companies
        if "tesla" in name_lower or "spacex" in name_lower or "twitter" in name_lower or "x corp" in name_lower:
            company.key_people.append({"Name": "Elon Musk", "Role": "CEO"})
            # Simulating that 'X' is high risk to show contagion effect
            company.related_entities.append({"Name": "SpaceX", "Risk_Score": 85, "Relation": "Sister Co."})
            company.related_entities.append({"Name": "X (Twitter)", "Risk_Score": 35, "Relation": "Sister Co."}) # High Risk!
            
        elif "meta" in name_lower or "facebook" in name_lower:
            company.key_people.append({"Name": "Mark Zuckerberg", "Role": "CEO"})
            company.related_entities.append({"Name": "Instagram", "Risk_Score": 90, "Relation": "Subsidiary"})
            company.related_entities.append({"Name": "Reality Labs", "Risk_Score": 45, "Relation": "Cash Burn Unit"})
            
        elif "amazon" in name_lower:
            company.key_people.append({"Name": "Jeff Bezos", "Role": "Founder"})
            company.related_entities.append({"Name": "Blue Origin", "Risk_Score": 60, "Relation": "Ventures"})
            
        else:
            # Generic fallback for unknown companies
            company.key_people.append({"Name": "Board of Directors", "Role": "Governance"})
            
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
        
        # Tier 4 Mock Data
        company.key_people.append({"Name": "John Doe", "Role": "CEO"})
        
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