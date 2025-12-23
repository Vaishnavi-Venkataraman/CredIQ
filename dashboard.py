# dashboard.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import graphviz
from textblob import TextBlob 
from src.report_generator import generate_pdf  
from src.models import Company
from src.scraper import ReviewScraper
from src.risk_engine import RiskEvaluator
from src.pdf_analyzer import FinancialAnalyzer

st.set_page_config(page_title="AltScore: Risk Engine", layout="wide", page_icon="🏦")
st.markdown("""<style>.metric-card { background-color: #f0f2f6; padding: 20px; border-radius: 10px; text-align: center; }</style>""", unsafe_allow_html=True)

st.title("🏦 AltScore: AI-Powered Credit Risk Engine")
st.markdown("**Enterprise Edition:** `v5.0 (Full Suite)` | **Module:** `Contagion & Systemic Risk`")
st.divider()

# --- SIDEBAR ---
st.sidebar.header("🔍 Due Diligence Controls")
business_name = st.sidebar.text_input("Target Ticker / Company", value="Tesla") # Default changed to Tesla to show off graph
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
        # NEW: Show Key Person (e.g. Elon Musk)
        key_person = company.key_people[0]['Name'] if company.key_people else "Unknown"
        c2.metric("Key Person", key_person)
        # NEW: Show Contagion Penalty
        c3.metric("Contagion Risk", f"-{company.contagion_penalty} pts", delta_color="inverse" if company.contagion_penalty > 0 else "off")
        c4.metric("Legal Status", "Clean" if not company.lawsuit_flag else "Flagged", delta_color="inverse" if company.lawsuit_flag else "off")
        st.divider()

        # --- TABS (Updated to include Graph) ---
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

        # TAB 2: Ownership Graph (NEW)
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
    st.sidebar.subheader("📄 Export")

    # Generate the PDF
    report_pdf = generate_pdf(company)

    st.sidebar.download_button(
        label="Download Credit Memo (PDF)",
        data=report_pdf,
        file_name=f"{company.name}_Credit_Memo.pdf",
        mime="application/pdf"
    )