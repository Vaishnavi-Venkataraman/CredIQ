# dashboard.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from textblob import TextBlob 
from src.models import Company
from src.scraper import ReviewScraper
from src.risk_engine import RiskEvaluator
from src.pdf_analyzer import FinancialAnalyzer

st.set_page_config(page_title="AltScore: Risk Engine", layout="wide", page_icon="🏦")
st.markdown("""<style>.metric-card { background-color: #f0f2f6; padding: 20px; border-radius: 10px; text-align: center; }</style>""", unsafe_allow_html=True)

st.title("🏦 AltScore: AI-Powered Credit Risk Engine")
st.markdown("**Enterprise Edition:** `v4.0 (Final)` | **Module:** `Explainable AI & Reason Codes`")
st.divider()

# --- SIDEBAR ---
st.sidebar.header("🔍 Due Diligence Controls")
business_name = st.sidebar.text_input("Target Ticker / Company", value="Apple Inc.")
use_mock = st.sidebar.checkbox("Offline / Simulation Mode", value=False)
st.sidebar.divider()
st.sidebar.subheader("📂 Financial Documents")
uploaded_file = st.sidebar.file_uploader("Upload Bank Statement (PDF)", type="pdf")
analyze_btn = st.sidebar.button("🚀 Run Risk Analysis")

if analyze_btn:
    with st.spinner(f"📡 Hunting data for '{business_name}'..."):
        
        # 1. SETUP & SCRAPE
        company = Company(name=business_name, url="") 
        scraper = ReviewScraper()
        company = scraper.fetch_data(company, mock=use_mock)
        
        # 2. PROCESS PDF
        if uploaded_file:
            pdf_engine = FinancialAnalyzer()
            balance = pdf_engine.analyze_statement(uploaded_file)
            if balance > 0:
                company.cash_balance = balance
                company.has_verified_financials = True
                st.sidebar.success(f"Verified Balance: ${balance:,.2f}")
            else:
                st.sidebar.warning("Could not extract 'Ending Balance'.")

        # 3. COMPUTE RISK
        engine = RiskEvaluator()
        company = engine.evaluate(company)
        
        # --- HEADER ---
        st.subheader(f"📂 Corporate Profile: {company.name}")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Business Age", f"{company.business_age} Years")
        c2.metric("Industry", company.industry if company.industry else "Unknown")
        cash_display = f"${company.cash_balance:,.0f}" if company.has_verified_financials else "Unverified"
        c3.metric("Verified Cash", cash_display, delta="Liquidity Verified" if company.has_verified_financials else None)
        c4.metric("Legal Status", "Clean" if not company.lawsuit_flag else "Flagged", delta_color="inverse" if company.lawsuit_flag else "off")
        st.divider()

        # --- TABS ---
        tab1, tab2 = st.tabs(["📊 Risk Dashboard", "📝 Raw Intelligence"])

        with tab1:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("AltCredit Score", f"{company.risk_score}/100", delta=f"{company.sentiment_momentum:.3f} Momentum")
            with col2:
                sentiment_label = "Positive" if company.sentiment_score > 0 else "Negative"
                st.metric("News Sentiment", sentiment_label, delta=f"Vol: {company.news_volume_volatility:.2f}")
            with col3:
                if company.lawsuit_flag:
                    st.error("⛔ DECISION: REJECT")
                elif company.risk_score >= 60:
                    st.success("✅ DECISION: APPROVE")
                elif company.risk_score >= 40:
                    st.warning("⚠️ DECISION: MANUAL REVIEW")
                else:
                    st.error("❌ DECISION: REJECT")

            # --- TIER 5: EXPLAINABILITY SECTION (NEW) ---
            st.divider()
            st.subheader("📋 Principal Reasons for Decision")
            
            if company.decision_reasons:
                for reason in company.decision_reasons:
                    st.warning(f"⚠️ {reason}")
            else:
                st.info("✅ No negative risk factors detected. Strong applicant profile.")

            st.divider()
            
            if company.reviews:
                st.subheader("Market Volatility Analysis")
                scores = [TextBlob(r.text).sentiment.polarity for r in company.reviews]
                fig, ax = plt.subplots(figsize=(10, 3))
                colors = ['#4CAF50' if x > 0 else '#F44336' for x in scores]
                ax.bar(range(len(scores)), scores, color=colors)
                ax.axhline(0, color='black', linewidth=0.8)
                st.pyplot(fig)

        with tab2:
            st.subheader("Extracted Intelligence")
            if company.reviews:
                data = [{"Date": r.date, "Headline": r.text, "Source": r.source} for r in company.reviews]
                st.dataframe(pd.DataFrame(data), use_container_width=True)