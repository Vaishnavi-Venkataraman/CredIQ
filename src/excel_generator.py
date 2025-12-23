# src/excel_generator.py
import pandas as pd
import io
from src.models import Company
import datetime

def generate_excel(company: Company):
    # Create an in-memory byte stream
    output = io.BytesIO()
    
    # Create a Pandas Excel Writer
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
        df_summary = pd.DataFrame(summary_data)
        df_summary.to_excel(writer, sheet_name='Executive Summary', index=False)
        
        # --- SHEET 2: MARKET INTELLIGENCE (Raw News) ---
        if company.reviews:
            news_data = []
            for r in company.reviews:
                news_data.append({
                    "Date": r.date,
                    "Source": r.source,
                    "Headline": r.text,
                    "Sentiment": r.rating
                })
            df_news = pd.DataFrame(news_data)
            df_news.to_excel(writer, sheet_name='Market Intel', index=False)
            
        # --- SHEET 3: CONTAGION NETWORK ---
        if company.related_entities:
            network_data = company.related_entities
            df_network = pd.DataFrame(network_data)
            df_network.to_excel(writer, sheet_name='Related Entities', index=False)
            
        # --- SHEET 4: DECISION REASONS ---
        if company.decision_reasons:
            df_reasons = pd.DataFrame({"Risk Factors": company.decision_reasons})
            df_reasons.to_excel(writer, sheet_name='Risk Factors', index=False)

    # Rewind the buffer
    output.seek(0)
    return output