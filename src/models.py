# src/models.py
from dataclasses import dataclass, field
from typing import List, Dict

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
    
    # Tier 2 Metadata
    founding_year: int = 0
    business_age: int = 0
    industry: str = "Unknown"
    headquarters: str = "Unknown"
    
    # Tier 2.5: Geo-Economic Risk
    geo_risk_score: float = 0.0  
    geo_risk_label: str = "Neutral" # e.g. "High Cost Zone"
    
    # Tier 3 Financials
    cash_balance: float = 0.0
    has_verified_financials: bool = False
    
    # Tier 4: Ownership & Contagion
    key_people: List[Dict[str, str]] = field(default_factory=list) 
    related_entities: List[Dict[str, any]] = field(default_factory=list)
    contagion_penalty: float = 0.0
    
    # Tier 5 Explainability
    decision_reasons: List[str] = field(default_factory=list)
    
    # Scores
    sentiment_score: float = 0.0
    risk_score: float = 0.0

    # Tier 1 Metrics
    sentiment_momentum: float = 0.0
    news_volume_volatility: float = 0.0
    lawsuit_flag: bool = False
    
    # --- NEW: AI Fields for PDF Report ---
    ai_summary: str = ""
    ai_peers: List[str] = field(default_factory=list)
    
    def add_review(self, source, text, rating, date):
        self.reviews.append(Review(source, text, rating, date))

    def summary(self):
        return {
            "Name": self.name,
            "HQ": self.headquarters,
            "Geo Risk": self.geo_risk_label
        }