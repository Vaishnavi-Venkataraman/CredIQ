# src/models.py
from dataclasses import dataclass, field
from typing import List, Optional
import datetime

@dataclass
class Review:
    source: str
    text: str
    rating: float
    date: str

@dataclass
class Company:
    name: str
    url: str
    
    # Containers
    reviews: List[Review] = field(default_factory=list)
    competitors: List[str] = field(default_factory=list)
    
    # Tier 2 Metadata
    founding_year: int = 0
    business_age: int = 0
    industry: str = "Unknown"
    headquarters: str = "Unknown"
    
    # --- TIER 3: FINANCIAL DATA  ---
    cash_balance: float = 0.0  # From PDF
    has_verified_financials: bool = False
    
    # Scores
    sentiment_score: float = 0.0
    risk_score: float = 0.0

    # Tier 1 Metrics
    sentiment_momentum: float = 0.0
    news_volume_volatility: float = 0.0
    lawsuit_flag: bool = False
    
    def add_review(self, source, text, rating, date):
        self.reviews.append(Review(source, text, rating, date))

    def summary(self):
        return {
            "Name": self.name,
            "Age": f"{self.business_age} Years",
            "Cash Reserves": f"${self.cash_balance:,.2f}" if self.has_verified_financials else "Unverified",
            "Risk Score": self.risk_score
        }