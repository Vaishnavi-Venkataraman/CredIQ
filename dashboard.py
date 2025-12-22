# dashboard.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from textblob import TextBlob 
from src.models import Company
from src.scraper import ReviewScraper
from src.risk_engine import RiskEvaluator

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="AltScore: Risk Engine", layout="wide", page_icon="🏦")

# --- CSS ---
st.markdown("""
    <style>
    .metric-card { background-color: #f0f2f6; padding: 20px; border-radius: 10px; text-align: center; }
    </style>
""", unsafe_allow_html=True)

# --- HEADER ---
st.title("🏦 AltScore: AI-Powered Credit Risk Engine")
st.markdown("**Enterprise Edition:** `v2.3` | **Module:** `Corporate Credit Analysis`")
st.divider()

# --- SIDEBAR ---
st.sidebar.header("🔍 Due Diligence Controls")
business_name = st.sidebar.text_input("Target Ticker / Company", value="Apple")
use_mock = st.sidebar.checkbox("Offline / Simulation Mode", value=False)
analyze_btn = st.sidebar.button("🚀 Run Risk Analysis")

# --- MAIN LOGIC ---
if analyze_btn:
    with st.spinner(f"📡 Interfacing with Global News Feeds for '{business_name}'..."):
        
        # 1. SETUP & SCRAPE
        company = Company(name=business_name, url="") 
        scraper = ReviewScraper()
        company = scraper.fetch_data(company, mock=use_mock)
        
        # 2. COMPUTE RISK
        engine = RiskEvaluator()
        company = engine.evaluate(company)
        
        # --- TABBED INTERFACE (Simplified) ---
        tab1, tab2 = st.tabs(["📊 Risk Dashboard", "📝 Raw Intelligence"])

        # TAB 1: The Main Scores
        with tab1:
            st.subheader(f"Risk Assessment: {company.name}")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("AltCredit Score", f"{company.risk_score}/100")
            
            with col2:
                sentiment_label = "Positive" if company.sentiment_score > 0 else "Negative"
                st.metric("News Sentiment", sentiment_label, delta=f"{company.sentiment_score:.3f}")
                
            with col3:
                # Decision Thresholds
                if company.risk_score >= 60:
                    st.success("✅ DECISION: APPROVE LOAN")
                elif company.risk_score >= 40:
                    st.warning("⚠️ DECISION: MANUAL REVIEW")
                else:
                    st.error("❌ DECISION: REJECT LOAN")

            st.divider()
            
            # Sentiment Volatility Chart
            st.subheader("Market Volatility Analysis")
            if company.reviews:
                scores = [TextBlob(r.text).sentiment.polarity for r in company.reviews]
                
                # Charting
                fig, ax = plt.subplots(figsize=(10, 3))
                colors = ['#4CAF50' if x > 0 else '#F44336' for x in scores]
                ax.bar(range(len(scores)), scores, color=colors)
                ax.axhline(0, color='black', linewidth=0.8)
                ax.set_ylabel("Sentiment Polarity")
                ax.set_xlabel("News Event Sequence")
                st.pyplot(fig)
            else:
                st.info("No sufficient data for volatility plotting.")

        # TAB 2: The Data (Raw Evidence)
        with tab2:
            st.subheader("Extracted Intelligence Source")
            if company.reviews:
                # Convert to DataFrame for a nice searchable table
                data = [{"Date": r.date, "Headline": r.text, "Source": r.source} for r in company.reviews]
                st.dataframe(pd.DataFrame(data), use_container_width=True)
            else:
                st.warning("No data found.")