# src/scraper.py
import requests
from bs4 import BeautifulSoup
import random
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
        """
        print(f"--- 📡 DEBUG: Starting Scrape for '{company.name}' ---")
        
        # 1. Clean name for URL
        clean_name = company.name.replace(" ", "%20")
        
        # 2. Construct URL (Google News RSS)
        url = f"https://news.google.com/rss/search?q={clean_name}+business&hl=en-US&gl=US&ceid=US:en"
        print(f"--- 🔗 Target URL: {url} ---")
        
        # 3. Headers (CRITICAL: Must look like a real browser)
        headers = {
            "User-Agent": random.choice(self.USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://www.google.com/",
            "Upgrade-Insecure-Requests": "1"
        }
        
        try:
            # 4. Make the Request
            response = requests.get(url, headers=headers, timeout=10)
            
            print(f"--- 📊 HTTP Status: {response.status_code} ---")
            
            # 5. Check for Success
            if response.status_code == 200:
                # Parse XML
                soup = BeautifulSoup(response.content, features="xml")
                items = soup.find_all("item")
                
                print(f"--- 📄 Items Found: {len(items)} ---")
                
                if len(items) == 0:
                    print("⚠️ WARNING: Status 200 OK, but no <item> tags found. Google might have returned a CAPTCHA page.")
                    # Debug: print first 200 chars to see what we actually got
                    print(f"Response Snippet: {response.text[:200]}")
                
                for item in items[:10]: # Get top 10
                    title = item.title.text
                    pub_date = item.pubDate.text
                    link = item.link.text
                    
                    # Store data
                    company.add_review("Google News", title, 0.0, pub_date)
            else:
                print("❌ ERROR: Blocked or Failed.")
        
        except Exception as e:
            print(f"❌ EXCEPTION: {e}")
            
        return company