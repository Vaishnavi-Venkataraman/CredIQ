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

# --- CSS FOR STYLING ---
st.markdown("""
    <style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# --- HEADER ---
st.title("🏦 AltScore: AI-Powered Credit Risk Engine")
st.markdown("""
**Automated Due Diligence System** *Enter a company name below. The system will auto-scrape financial news and sentiment to calculate a risk profile.*
""")
st.divider()

# --- SIDEBAR (CONTROLS) ---
st.sidebar.header("🔍 Investigation Parameters")
business_name = st.sidebar.text_input("Target Company Name", value="Tesla")
use_mock = st.sidebar.checkbox("Force Simulation Mode", value=False, help="Check this if you are offline or want to test specific scenarios.")

analyze_btn = st.sidebar.button("🚀 Analyze Risk Profile")

# --- MAIN LOGIC ---
if analyze_btn:
    with st.spinner(f"📡 Scanning global sources for '{business_name}'..."):
        
        # 1. SETUP
        # Note: We no longer ask for a URL. The system finds it.
        company = Company(name=business_name, url="") 
        scraper = ReviewScraper()
        
        # 2. AUTO-DISCOVERY (Fetch Data)
        company = scraper.fetch_data(company, mock=use_mock)
        
        # 3. INTELLIGENCE (Calculate Risk)
        engine = RiskEvaluator()
        company = engine.evaluate(company)
        
        # --- RESULTS DASHBOARD ---
        
        # A. High-Level Decision Block
        st.subheader(f"Risk Assessment: {company.name}")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Credit Worthiness", f"{company.risk_score}/100")
        
        with col2:
            sentiment_label = "Positive" if company.sentiment_score > 0 else "Negative"
            st.metric("Market Sentiment", sentiment_label, delta=f"{company.sentiment_score:.2f}")
            
        with col3:
            if company.risk_score >= 60:
                st.success("✅ DECISION: APPROVE LOAN")
            else:
                st.error("❌ DECISION: REJECT LOAN")

        st.divider()

        # B. Detailed Analysis
        col_left, col_right = st.columns([2, 1])
        
        with col_left:
            st.subheader("📝 Intelligence Gathered")
            if company.reviews:
                data = [{"Source": r.source, "Date": r.date, "Snippet": r.text} for r in company.reviews]
                st.table(pd.DataFrame(data))
            else:
                st.warning("No data found.")
            
        with col_right:
            st.subheader("📊 Sentiment Volatility")
            if company.reviews:
                # Calculate polarity for chart
                scores = [TextBlob(r.text).sentiment.polarity for r in company.reviews]
                
                # Plotting
                fig, ax = plt.subplots()
                colors = ['green' if x > 0 else 'red' for x in scores]
                ax.bar(range(len(scores)), scores, color=colors)
                ax.set_ylim(-1, 1)
                ax.set_ylabel("Sentiment Polarity")
                ax.set_title("News Sentiment Analysis")
                st.pyplot(fig)
            else:
                st.info("No data to visualize.")