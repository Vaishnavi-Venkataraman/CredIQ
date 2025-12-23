# src/excel_generator.py
import pandas as pd
import io
from src.models import Company
import datetime

def generate_excel(company: Company):
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        
        # --- SHEET 1: EXECUTIVE SUMMARY ---
        summary_data = {
            "Metric": [
                "Target Company", "Headquarters", "Industry", "Business Age", 
                "Risk Score", "Decision", "Sentiment Momentum", "News Volatility",
                "Geo-Economic Zone", "Verified Cash Balance", "Contagion Penalty", 
                "Key Person", "Report Date"
            ],
            "Value": [
                company.name, company.headquarters, company.industry, f"{company.business_age} Years",
                f"{company.risk_score}/100", 
                "APPROVE" if company.risk_score >= 60 else "MANUAL REVIEW" if company.risk_score >= 40 else "REJECT",
                f"{company.sentiment_momentum:.3f}", f"{company.news_volume_volatility:.3f}",
                company.geo_risk_label,
                f"${company.cash_balance:,.2f}" if company.has_verified_financials else "Unverified",
                f"-{company.contagion_penalty} pts",
                company.key_people[0]['Name'] if company.key_people else "Unknown",
                datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ]
        }
        pd.DataFrame(summary_data).to_excel(writer, sheet_name='Executive Summary', index=False)
        
        # --- SHEET 2: AI INTELLIGENCE (NEW!) ---
        # We create a small table for the AI data
        ai_data = {
            "Insight Type": ["AI Executive Summary", " identified Peers", "Data Source"],
            "Content": [
                company.ai_summary if company.ai_summary else "Not Generated",
                ", ".join(company.ai_peers) if company.ai_peers else "Default (SPY, QQQ)",
                "Google Gemini 1.5 Flash"
            ]
        }
        pd.DataFrame(ai_data).to_excel(writer, sheet_name='AI Intelligence', index=False)

        # --- SHEET 3: MARKET NEWS ---
        if company.reviews:
            news_data = []
            for r in company.reviews:
                news_data.append({
                    "Date": r.date,
                    "Source": r.source,
                    "Headline": r.text,
                    "Sentiment": r.rating
                })
            pd.DataFrame(news_data).to_excel(writer, sheet_name='Market News', index=False)
            
        # --- SHEET 4: NETWORK & RISKS ---
        if company.related_entities:
            pd.DataFrame(company.related_entities).to_excel(writer, sheet_name='Related Network', index=False)
            
        if company.decision_reasons:
            pd.DataFrame({"Risk Factors": company.decision_reasons}).to_excel(writer, sheet_name='Risk Factors', index=False)

    output.seek(0)
    return output