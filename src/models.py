# src/models.py
from dataclasses import dataclass, field
from typing import List, Optional

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
    
    # Tier 3 Financials
    cash_balance: float = 0.0
    has_verified_financials: bool = False
    
    # Tier 5: Explainability (New!)
    decision_reasons: List[str] = field(default_factory=list)
    
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
            "Risk Score": self.risk_score,
            "Top Reason": self.decision_reasons[0] if self.decision_reasons else "None"
        }