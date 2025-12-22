# src/scraper.py
import requests
from bs4 import BeautifulSoup
import random
import datetime
from src.models import Company

class ReviewScraper:
    
    # Extensive list of User-Agents to rotate
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    ]

    def fetch_data(self, company: Company, mock: bool = False) -> Company:
        """
        Attempts to scrape Google News RSS.
        Falls back to 'Smart Mock' data if blocked or in simulation mode.
        """
        print(f"--- 📡 DEBUG: Starting Scrape for '{company.name}' ---")
        
        # 1. Check for Manual Simulation Mode
        if mock:
            return self._get_smart_mock_data(company)
        
        # 2. Clean name for URL
        clean_name = company.name.replace(" ", "%20")
        
        # 3. Construct URL (Google News RSS)
        url = f"https://news.google.com/rss/search?q={clean_name}+business&hl=en-US&gl=US&ceid=US:en"
        print(f"--- 🔗 Target URL: {url} ---")
        
        # 4. Headers (CRITICAL: Must look like a real browser)
        headers = {
            "User-Agent": random.choice(self.USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://www.google.com/",
            "Upgrade-Insecure-Requests": "1"
        }
        
        try:
            # 5. Make the Request
            response = requests.get(url, headers=headers, timeout=10)
            
            print(f"--- 📊 HTTP Status: {response.status_code} ---")
            
            # 6. Check for Success
            if response.status_code == 200:
                # Parse XML (Handle different parsers)
                try:
                    soup = BeautifulSoup(response.content, features="xml")
                except:
                    soup = BeautifulSoup(response.content, features="lxml")
                    
                items = soup.find_all("item")
                
                print(f"--- 📄 Items Found: {len(items)} ---")
                
                if len(items) == 0:
                    print("⚠️ WARNING: No items found. Google might be blocking. Switching to Mock.")
                    return self._get_smart_mock_data(company)
                
                # Get top 15 items for better momentum calculation
                for item in items[:15]: 
                    title = item.title.text
                    pub_date = item.pubDate.text
                    
                    # Store data
                    company.add_review("Google News", title, 0.0, pub_date)
            else:
                print("❌ ERROR: Blocked or Failed. Switching to Mock.")
                return self._get_smart_mock_data(company)
        
        except Exception as e:
            print(f"❌ EXCEPTION: {e}")
            print("-> Switching to Simulation Mode due to error.")
            return self._get_smart_mock_data(company)
            
        return company

    def _get_smart_mock_data(self, company: Company) -> Company:
        """
        Generates consistent simulation data with VARIED DATES.
        This allows testing Momentum (Trends over time).
        """
        print(f"-> 🎲 Generating Simulation for: {company.name}")
        
        # Seed random with company name so "Apple" always gives same results
        random.seed(len(company.name))
        
        is_good = len(company.name) % 2 == 0 
        
        if is_good:
            templates = [
                "Revenue beat expectations this quarter.",
                "New product launch is highly successful.",
                "Market share is growing rapidly.",
                "Strong leadership and solid balance sheet.",
                "Analyst rating upgraded to Buy."
            ]
        else:
            templates = [
                "Facing a massive class-action lawsuit regarding fraud.",
                "CEO stepped down amidst accounting scandal.",
                "Revenue is dropping year over year.",
                "Customers are complaining about quality issues.",
                "Analyst downgraded rating to Sell."
            ]
            
        # Generate 12 reviews spread over the last 12 days
        base_date = datetime.datetime.now()
        
        for i in range(12):
            text = random.choice(templates)
            
            # Create a fake date (Today minus 'i' days)
            # This creates a timeline: Today, Yesterday, 2 days ago...
            fake_date = (base_date - datetime.timedelta(days=i)).strftime("%a, %d %b %Y %H:%M:%S GMT")
            
            company.add_review("Simulated Intel", text, 0.0, fake_date)
            
        return company