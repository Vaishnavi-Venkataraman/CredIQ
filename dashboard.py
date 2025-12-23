# dashboard.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import graphviz
import requests
import numpy as np
import time
from textblob import TextBlob 
from src.excel_generator import generate_excel
from src.report_generator import generate_pdf  
from src.models import Company
from src.scraper import ReviewScraper
from src.risk_engine import RiskEvaluator
from src.pdf_analyzer import FinancialAnalyzer
from src.ai_analyst import AIAnalyst

# ---  API KEYS ------------------------------------------------------
GEMINI_API_KEY = "AIzaSyDyHrOJ135jySiXo3_wjjuAu70TlNaPcfA" 
ALPHA_VANTAGE_KEY = "DQII4IL567BTP0RZ" 
# ----------------------------------------------------------------------

# --- PAGE CONFIG ---
st.set_page_config(page_title="AltScore: Risk Engine", layout="wide", page_icon="🏦")
st.markdown("""<style>.metric-card { background-color: #f0f2f6; padding: 20px; border-radius: 10px; text-align: center; }</style>""", unsafe_allow_html=True)

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

def check_password():
    # PASSWORD IS SET TO: admin
    if st.session_state.password_input == "admin": 
        st.session_state.authenticated = True
        del st.session_state.password_input
    else:
        st.error("❌ Access Denied: Invalid Credentials")

if not st.session_state.authenticated:
    st.markdown("## 🔒 AltScore Enterprise Login")
    st.markdown("Please verify your credentials to access the Risk Engine.")
    st.text_input("Enter Password", type="password", key="password_input", on_change=check_password)
    st.stop() # <--- STOPS THE APP HERE UNTIL LOGGED IN

# --- 1. CACHING LAYER ---
@st.cache_data(show_spinner=False)
def get_fresh_data(name, use_mock):
    try:
        comp = Company(name=name, url="") 
        scraper = ReviewScraper()
        comp = scraper.fetch_data(comp, mock=use_mock)
        engine = RiskEvaluator()
        comp = engine.evaluate(comp)
        return comp
    except Exception as e:
        return Company(name=name, url="")

# --- 2. SESSION STATE INIT ---
if 'company' not in st.session_state: st.session_state.company = None
if 'ai_summary' not in st.session_state: st.session_state.ai_summary = None
if 'ai_peers' not in st.session_state: st.session_state.ai_peers = None

# --- HEADER ---
st.title("🏦 AltScore: AI-Powered Credit Risk Engine")
st.markdown("**Enterprise Edition:** `v11.0 (Secure)` | **User:** `Admin`")
st.divider()

# --- SIDEBAR ---
st.sidebar.header("Due Diligence Controls")

# Key Cleaner
if GEMINI_API_KEY: GEMINI_API_KEY = GEMINI_API_KEY.strip()

if "PASTE" in GEMINI_API_KEY or not GEMINI_API_KEY:
    st.sidebar.warning("⚠️ No AI Key detected. Edit dashboard.py line 19.")

business_name = st.sidebar.text_input("Company Name", value="Tesla")
ticker_symbol = st.sidebar.text_input("Stock Ticker", value="TSLA") 
use_mock = st.sidebar.checkbox("Offline / Simulation Mode", value=False)
st.sidebar.divider()
uploaded_file = st.sidebar.file_uploader("Upload Bank Statement (PDF)", type="pdf")

# --- PROCESS BUTTON LOGIC ---
if st.sidebar.button("🚀 Run Risk Analysis"):
    with st.spinner(f"📡 Hunting data for '{business_name}'..."):
        
        # A. Get Data
        comp = get_fresh_data(business_name, use_mock)
        
        # B. Process PDF
        if uploaded_file:
            try:
                pdf_engine = FinancialAnalyzer()
                balance = pdf_engine.analyze_statement(uploaded_file)
                if balance > 0:
                    comp.cash_balance = balance
                    comp.has_verified_financials = True
                    engine = RiskEvaluator()
                    comp = engine.evaluate(comp)
                    st.sidebar.success(f"Verified Balance: ${balance:,.2f}")
                else:
                    st.sidebar.warning("Could not extract 'Ending Balance'.")
            except Exception as e:
                st.sidebar.error(f"PDF Error: {e}")

        # C. RUN AI ANALYSIS (With Strict Fallback)
        # Default Fallback first
        st.session_state.ai_peers = ["SPY", "QQQ"] 
        
        if GEMINI_API_KEY and "PASTE" not in GEMINI_API_KEY:
            try:
                ai = AIAnalyst(GEMINI_API_KEY)
                
                # 1. Generate Summary
                summary_text = ai.generate_risk_summary(comp)
                st.session_state.ai_summary = summary_text
                
                # SAVE TO COMPANY OBJECT (For PDF/Excel)
                comp.ai_summary = summary_text 
                
                # 2. Try to get peers
                if ticker_symbol:
                    fetched_peers = ai.get_competitors(business_name)
                    # Only overwrite if we actually got a list
                    if fetched_peers and len(fetched_peers) > 0:
                         st.session_state.ai_peers = fetched_peers
                         
            except Exception as e:
                st.error(f"AI Connection Failed: {e}")
                # Fallback remains SPY/QQQ
        else:
            st.session_state.ai_summary = None

        # SAVE PEERS TO COMPANY OBJECT (For PDF/Excel)
        comp.ai_peers = st.session_state.ai_peers

        st.session_state.company = comp

# Logout Button
if st.sidebar.button("🚪 Logout"):
    st.session_state.authenticated = False
    st.rerun()

# --- MAIN DASHBOARD RENDERER ---
if st.session_state.company:
    company = st.session_state.company

    # 1. AI EXECUTIVE SUMMARY
    if st.session_state.ai_summary:
        st.info(f"🤖 **AI Executive Summary:** {st.session_state.ai_summary}")
    elif "PASTE" in GEMINI_API_KEY:
        st.warning("ℹ️ AI Summary skipped. Add Key to enable.")

    # Metrics
    st.subheader(f"📂 Corporate Profile: {company.name}")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Business Age", f"{company.business_age} Years")
    key_p = company.key_people[0]['Name'] if company.key_people else "Unknown"
    c2.metric("Key Person", key_p)
    c3.metric("Contagion Risk", f"-{company.contagion_penalty} pts", delta_color="inverse" if company.contagion_penalty > 0 else "off")
    geo_color = "inverse" if "High" in company.geo_risk_label or "Risk" in company.geo_risk_label else "normal"
    c4.metric("Geo Profile", company.geo_risk_label, help=f"HQ: {company.headquarters}", delta_color=geo_color)
    c5.metric("Legal Status", "Clean" if not company.lawsuit_flag else "Flagged", delta_color="inverse" if company.lawsuit_flag else "off")
    st.divider()

    # Tabs
    tab1, tab2, tab3 = st.tabs(["📊 Risk Dashboard", "🕸️ Ownership Graph", "📝 Raw Intelligence"])

    with tab1:
        col1, col2, col3 = st.columns(3)
        col1.metric("AltCredit Score", f"{company.risk_score}/100", delta=f"{company.sentiment_momentum:.3f} Momentum")
        col2.metric("News Sentiment", "Positive" if company.sentiment_score > 0 else "Negative", delta=f"Vol: {company.news_volume_volatility:.2f}")
        
        if company.lawsuit_flag:
            col3.error("⛔ DECISION: REJECT")
        elif company.risk_score >= 55:
            col3.success("✅ DECISION: APPROVE")
        elif company.risk_score >= 40:
            col3.warning("⚠️ DECISION: MANUAL REVIEW")
        else:
            col3.error("❌ DECISION: REJECT")

        st.divider()
        st.subheader("📋 Principal Reasons for Decision")
        if company.decision_reasons:
            for reason in company.decision_reasons:
                st.warning(f"⚠️ {reason}")
        else:
            st.info("✅ No negative risk factors detected.")

        st.divider()
        if company.reviews:
            st.subheader("Market Volatility Analysis")
            scores = [r.rating for r in company.reviews] 
            if scores:
                fig, ax = plt.subplots(figsize=(10, 3))
                colors = ['#4CAF50' if x > 0 else '#F44336' for x in scores]
                ax.bar(range(len(scores)), scores, color=colors)
                ax.axhline(0, color='black', linewidth=0.8)
                st.pyplot(fig)
        
        # --- TIER 7: ALPHA VANTAGE + METRICS ---
        st.divider()
        if ticker_symbol and ticker_symbol.strip() != "":
            st.subheader(f"📈 Competitive Benchmarking")
            
            # Use Fallback if AI didn't return anything
            peers = st.session_state.ai_peers if st.session_state.ai_peers else ["SPY", "QQQ"]
            
            # Fetch target + max 2 peers (Total 3 calls < 5 call limit)
            tickers_to_fetch = [ticker_symbol.upper()] + peers[:2]
            
            st.caption(f"Fetching: {', '.join(tickers_to_fetch)}")

            data_frames = {}
            main_metrics = None
            
            for t in tickers_to_fetch:
                try:
                    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={t}&apikey={ALPHA_VANTAGE_KEY}&datatype=json"
                    response = requests.get(url, timeout=10)
                    data = response.json()
                    
                    if "Time Series (Daily)" in data:
                        ts = data["Time Series (Daily)"]
                        df_stock = pd.DataFrame.from_dict(ts, orient='index')
                        df_stock = df_stock.rename(columns={"4. close": "Close"})
                        df_stock["Close"] = df_stock["Close"].astype(float)
                        df_stock.index = pd.to_datetime(df_stock.index)
                        df_stock = df_stock.sort_index()
                        
                        # FIX: Use .copy() to avoid SettingWithCopyWarning
                        df_recent = df_stock.tail(126).copy() 
                        
                        # METRICS CALCULATION (Only for Main Ticker)
                        if t == ticker_symbol.upper():
                            current_price = df_recent['Close'].iloc[-1]
                            start_price = df_recent['Close'].iloc[0]
                            delta = ((current_price - start_price) / start_price) * 100
                            
                            returns = df_recent['Close'].pct_change()
                            volatility = returns.std() * (252 ** 0.5) * 100
                            
                            rolling_max = df_recent['Close'].cummax()
                            drawdown = (df_recent['Close'] - rolling_max) / rolling_max
                            max_drawdown = drawdown.min() * 100
                            
                            main_metrics = {
                                "price": current_price,
                                "delta": delta,
                                "vol": volatility,
                                "dd": max_drawdown
                            }

                        start_price_chart = df_recent['Close'].iloc[0]
                        df_recent['Normalized'] = ((df_recent['Close'] - start_price_chart) / start_price_chart) * 100
                        data_frames[t] = df_recent['Normalized']
                        
                    elif "Note" in data:
                        st.warning(f"⚠️ API Rate Limit Hit fetching {t}. Stopping.")
                        break 
                        
                except Exception as e:
                    st.error(f"Error fetching {t}: {e}")
            
            # DISPLAY METRICS
            if main_metrics:
                m1, m2, m3 = st.columns(3)
                m1.metric("Current Price", f"${main_metrics['price']:.2f}", f"{main_metrics['delta']:.2f}% (6mo)")
                
                vol_color = "inverse" if main_metrics['vol'] > 40 else "normal"
                m2.metric("Annualized Volatility", f"{main_metrics['vol']:.1f}%", delta="High Risk" if main_metrics['vol'] > 40 else "Stable", delta_color=vol_color)
                
                dd_color = "inverse" if main_metrics['dd'] < -20 else "normal"
                m3.metric("Max Drawdown (1Y)", f"{main_metrics['dd']:.1f}%", delta="Crash Detected" if main_metrics['dd'] < -20 else "Resilient", delta_color=dd_color)

            # DISPLAY CHART
            if data_frames:
                st.line_chart(pd.DataFrame(data_frames))
            else:
                st.info("ℹ️ No market data available (Check API Key or Network).")
        else:
            st.info("ℹ️ Stock analysis skipped.")
        
    with tab2:
        st.subheader("Systemic Risk & Ownership Map")
        if company.key_people:
            graph = graphviz.Digraph()
            graph.attr(rankdir='LR')
            graph.node('MAIN', company.name, shape='doubleoctagon', style='filled', fillcolor='#ccffcc')
            owner_name = company.key_people[0]['Name']
            graph.node('OWNER', owner_name, shape='box', style='filled', fillcolor='#e0e0e0')
            graph.edge('OWNER', 'MAIN', label="Owns/Runs")
            
            for entity in company.related_entities:
                is_risky = entity['Risk_Score'] < 50
                node_color = '#ffcccc' if is_risky else '#ccffcc'
                graph.node(entity['Name'], f"{entity['Name']}\n(Score: {entity['Risk_Score']})", style='filled', fillcolor=node_color)
                graph.edge('OWNER', entity['Name'], label=entity['Relation'])
                if is_risky:
                    graph.edge(entity['Name'], 'MAIN', color='red', style='dashed', label="Contagion Risk")
            st.graphviz_chart(graph)
        else:
            st.info("No ownership data.")

    with tab3:
        st.subheader("Extracted Intelligence")
        if company.reviews:
            display_data = [{"Date": r.date, "Headline": r.text, "Source": r.source, "Sentiment": r.rating} for r in company.reviews]
            st.dataframe(pd.DataFrame(display_data), width="stretch") 

    st.sidebar.divider()
    st.sidebar.subheader("Export")
    report_pdf = generate_pdf(company)
    excel_data = generate_excel(company)
    col1, col2 = st.sidebar.columns(2)
    with col1:
        st.download_button("📄 PDF Report", report_pdf, f"{company.name}_Credit_Memo.pdf", "application/pdf")
    with col2:
        st.download_button("📊 Excel Data", excel_data, f"{company.name}_Financials.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
else:
    st.info("👋 Welcome to AltScore. Enter a company name in the sidebar and click 'Run Risk Analysis' to begin.")