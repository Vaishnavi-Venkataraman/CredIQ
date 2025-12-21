# src/models.py
from dataclasses import dataclass, field
from typing import List, Optional
import datetime

@dataclass
class Review:
    """Class to represent a single customer review."""
    source: str  # e.g., "Yelp", "Google"
    text: str
    rating: float
    date: str

@dataclass
class Company:
    """
    The Core Domain Model. 
    This represents the business applying for the loan.
    """
    name: str
    url: str
    
    # Financial/Risk Indicators (Defaults to None/Empty initially)
    reviews: List[Review] = field(default_factory=list)
    competitors: List[str] = field(default_factory=list)
    founding_year: Optional[int] = None
    
    # Calculated Scores (We will fill these later)
    sentiment_score: float = 0.0
    risk_score: float = 0.0
    
    def add_review(self, source, text, rating, date):
        """Helper method to add a review safely."""
        new_review = Review(source, text, rating, date)
        self.reviews.append(new_review)

    def summary(self):
        """Returns a quick summary of the company data."""
        return {
            "Name": self.name,
            "Total Reviews": len(self.reviews),
            "Risk Score": self.risk_score
        }