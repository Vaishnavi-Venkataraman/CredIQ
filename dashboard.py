# dashboard.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import graphviz
import requests
import yfinance as yf
from textblob import TextBlob 
from src.excel_generator import generate_excel
from src.report_generator import generate_pdf  
from src.models import Company
from src.scraper import ReviewScraper
from src.risk_engine import RiskEvaluator
from src.pdf_analyzer import FinancialAnalyzer

st.set_page_config(page_title="AltScore: Risk Engine", layout="wide", page_icon="🏦")
st.markdown("""<style>.metric-card { background-color: #f0f2f6; padding: 20px; border-radius: 10px; text-align: center; }</style>""", unsafe_allow_html=True)

st.title("🏦 AltScore: AI-Powered Credit Risk Engine")
st.markdown("**Enterprise Edition:** `v6.0 (Geo-Economic)` | **Module:** `Full Suite`")
st.divider()

# --- SIDEBAR ---
st.sidebar.header("🔍 Due Diligence Controls")
business_name = st.sidebar.text_input("Company Name", value="Tesla")
ticker_symbol = st.sidebar.text_input("Stock Ticker", value="TSLA") 
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
        
        # --- HEADER (UPDATED TO 5 COLUMNS FOR GEO RISK) ---
        st.subheader(f"📂 Corporate Profile: {company.name}")
        c1, c2, c3, c4, c5 = st.columns(5) # <--- Changed to 5
        
        c1.metric("Business Age", f"{company.business_age} Years")
        
        key_person = company.key_people[0]['Name'] if company.key_people else "Unknown"
        c2.metric("Key Person", key_person)
        
        c3.metric("Contagion Risk", f"-{company.contagion_penalty} pts", delta_color="inverse" if company.contagion_penalty > 0 else "off")
        
        # NEW: Geo Risk Metric
        geo_color = "inverse" if "High" in company.geo_risk_label or "Risk" in company.geo_risk_label else "normal"
        c4.metric("Geo Profile", company.geo_risk_label, help=f"HQ: {company.headquarters}", delta_color=geo_color)
        
        c5.metric("Legal Status", "Clean" if not company.lawsuit_flag else "Flagged", delta_color="inverse" if company.lawsuit_flag else "off")
        
        st.divider()

        # --- TABS ---
        tab1, tab2, tab3 = st.tabs(["📊 Risk Dashboard", "🕸️ Ownership Graph", "📝 Raw Intelligence"])

        # TAB 1: Main Dashboard
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
                elif company.risk_score >= 55:
                    st.success("✅ DECISION: APPROVE")
                elif company.risk_score >= 40:
                    st.warning("⚠️ DECISION: MANUAL REVIEW")
                else:
                    st.error("❌ DECISION: REJECT")

            # Tier 5: Explainability
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
            

            # --- TIER 6: LIVE STOCK MARKET ---
            st.divider()
            
            # CHECK: Only run if user actually typed a ticker
            if ticker_symbol and ticker_symbol.strip() != "":
                st.subheader(f"📈 Market Signals: {ticker_symbol.upper()}")
                
                # PASTE YOUR KEY HERE
                ALPHA_VANTAGE_KEY = "DQII4IL567BTP0RZ" 
            
                if ALPHA_VANTAGE_KEY == "PASTE_YOUR_KEY_HERE":
                    st.markdown("[Get Free Key Here](https://www.alphavantage.co/support/#api-key)")
                else:
                    try:
                        # 2. REAL API CALL
                        url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={ticker_symbol}&apikey={ALPHA_VANTAGE_KEY}&datatype=json"
                        response = requests.get(url, timeout=10)
                        data = response.json()
                        
                        # 3. PARSE JSON DATA
                        if "Time Series (Daily)" in data:
                            ts = data["Time Series (Daily)"]
                            df_stock = pd.DataFrame.from_dict(ts, orient='index')
                            
                            # Clean Data
                            df_stock = df_stock.rename(columns={"4. close": "Close"})
                            df_stock["Close"] = df_stock["Close"].astype(float)
                            df_stock.index = pd.to_datetime(df_stock.index)
                            df_stock = df_stock.sort_index() # Sort strictly by date
                            
                            # Limit to last 6 months (~126 trading days)
                            df_recent = df_stock.tail(126)
                            
                            # 4. CALCULATE METRICS
                            current_price = df_recent['Close'].iloc[-1]
                            start_price = df_recent['Close'].iloc[0]
                            delta = ((current_price - start_price) / start_price) * 100
                            
                            # Volatility (Standard Deviation of Returns)
                            returns = df_stock['Close'].pct_change()
                            volatility = returns.std() * (252 ** 0.5) * 100
                            
                            # Drawdown (Crash risk)
                            rolling_max = df_stock['Close'].cummax()
                            drawdown = (df_stock['Close'] - rolling_max) / rolling_max
                            max_drawdown = drawdown.min() * 100

                            # 5. DISPLAY
                            m1, m2, m3 = st.columns(3)
                            m1.metric("Current Price", f"${current_price:.2f}", f"{delta:.2f}% (6mo)")
                            
                            vol_color = "inverse" if volatility > 40 else "normal"
                            m2.metric("Annualized Volatility", f"{volatility:.1f}%", delta="High Risk" if volatility > 40 else "Stable", delta_color=vol_color)
                            
                            dd_color = "inverse" if max_drawdown < -20 else "normal"
                            m3.metric("Max Drawdown (1Y)", f"{max_drawdown:.1f}%", delta="Crash Detected" if max_drawdown < -20 else "Resilient", delta_color=dd_color)
                            
                            st.area_chart(df_recent['Close'], color="#0068c9")
                            
                        elif "Note" in data:
                            st.info("⚠️ API Limit Reached. Alpha Vantage (Free) allows 5 calls per minute. Wait a moment.")
                        else:
                            st.error("Error fetching data. Check Ticker Symbol.")
                            
                    except Exception as e:
                        st.error(f"API Connection Failed: {e}")

            else:
                st.info("ℹ️ Stock analysis skipped (No ticker symbol provided).")
            
            
        # TAB 2: Ownership Graph
        with tab2:
            st.subheader("Systemic Risk & Ownership Map")
            st.markdown("Visualizing shared ownership and potential contagion vectors.")
            
            if company.key_people:
                graph = graphviz.Digraph()
                graph.attr(rankdir='LR')
                
                # Main Company Node
                graph.node('MAIN', company.name, shape='doubleoctagon', style='filled', fillcolor='#ccffcc')
                
                # Owner Node
                owner_name = company.key_people[0]['Name']
                graph.node('OWNER', owner_name, shape='box', style='filled', fillcolor='#e0e0e0')
                graph.edge('OWNER', 'MAIN', label="Owns/Runs")
                
                # Related Entities
                for entity in company.related_entities:
                    # Color code red if score is low (<50)
                    is_risky = entity['Risk_Score'] < 50
                    node_color = '#ffcccc' if is_risky else '#ccffcc'
                    
                    graph.node(entity['Name'], f"{entity['Name']}\n(Score: {entity['Risk_Score']})", style='filled', fillcolor=node_color)
                    graph.edge('OWNER', entity['Name'], label=entity['Relation'])
                    
                    # Draw a red dashed line if contagion is happening
                    if is_risky:
                        graph.edge(entity['Name'], 'MAIN', color='red', style='dashed', label="Contagion Risk")

                st.graphviz_chart(graph)
            else:
                st.info("No ownership data available for graph generation.")

        # TAB 3: Raw Data
        with tab3:
            st.subheader("Extracted Intelligence")
            if company.reviews:
                data = [{"Date": r.date, "Headline": r.text, "Source": r.source} for r in company.reviews]
                st.dataframe(pd.DataFrame(data), use_container_width=True)

    # --- SIDEBAR: DOWNLOAD REPORT ---
    st.sidebar.divider()
    st.sidebar.subheader("Export")

    # Generate the PDF
    report_pdf = generate_pdf(company)
    excel_data = generate_excel(company)
    
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        st.download_button(
            label="📄 PDF Report",
            data=report_pdf,
            file_name=f"{company.name}_Credit_Memo.pdf",
            mime="application/pdf"
        )
        
    with col2:
        st.download_button(
            label="📊 Excel Data",
            data=excel_data,
            file_name=f"{company.name}_Financials.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )