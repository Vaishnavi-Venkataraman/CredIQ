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
st.markdown("**Enterprise Edition:** `v3.0 (Tier 1 Features)` | **Module:** `Momentum & Legal Risk Analysis`")
st.divider()

# --- SIDEBAR ---
st.sidebar.header("🔍 Due Diligence Controls")
business_name = st.sidebar.text_input("Target Ticker / Company", value="Apple")
use_mock = st.sidebar.checkbox("Offline / Simulation Mode", value=False)
analyze_btn = st.sidebar.button("🚀 Run Risk Analysis")

if analyze_btn:
    with st.spinner(f"📡 Interfacing with Global News Feeds for '{business_name}'..."):
        
        # 1. SETUP & SCRAPE
        company = Company(name=business_name, url="") 
        scraper = ReviewScraper()
        company = scraper.fetch_data(company, mock=use_mock)
        
        # 2. COMPUTE RISK (Now includes Time-Series Math)
        engine = RiskEvaluator()
        company = engine.evaluate(company)
        
        # --- TABBED INTERFACE ---
        tab1, tab2 = st.tabs(["📊 Risk Dashboard", "📝 Raw Intelligence"])

        # TAB 1: The Main Scores
        with tab1:
            st.subheader(f"Risk Assessment: {company.name}")
            col1, col2, col3 = st.columns(3)
            
            # COLUMN 1: Score + Momentum
            with col1:
                # The 'delta' parameter creates the Green/Red arrow showing trend
                st.metric(
                    "AltCredit Score", 
                    f"{company.risk_score}/100",
                    delta=f"{company.sentiment_momentum:.3f} Momentum",
                    delta_color="normal" # Green = Up, Red = Down
                )
            
            # COLUMN 2: Sentiment + Volatility
            with col2:
                sentiment_label = "Positive" if company.sentiment_score > 0 else "Negative"
                # We show Volatility in the help text or delta
                st.metric(
                    "News Sentiment", 
                    sentiment_label, 
                    delta=f"Vol: {company.news_volume_volatility:.2f}",
                    help="Volatility measures the chaos/uncertainty of the news cycle."
                )
                
            # COLUMN 3: Decision Logic (Tier 1: Legal Hard Stop)
            with col3:
                # Check for Lawsuit Flag FIRST (Priority 1)
                if company.lawsuit_flag:
                    st.error("⛔ DECISION: REJECT (LEGAL RISK)")
                    st.caption("Critical Flag: Lawsuit/Fraud detected.")
                elif company.risk_score >= 55:
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
                ax.set_xlabel("News Event Sequence (Oldest -> Newest)")
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