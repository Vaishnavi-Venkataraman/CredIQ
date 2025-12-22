# dashboard.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import graphviz
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
st.markdown("**Enterprise Edition:** `v2.1` | **Module:** `Corporate Credit & Contagion Analysis`")
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
        
        # --- TABBED INTERFACE (Bringing back features) ---
        tab1, tab2, tab3 = st.tabs(["📊 Risk Dashboard", "🕸️ Contagion Graph", "📝 Raw Intelligence"])

        # TAB 1: The Main Scores
        with tab1:
            st.subheader(f"Risk Assessment: {company.name}")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("AltCredit Score", f"{company.risk_score}/100", delta_color="normal")
            
            with col2:
                sentiment_label = "Positive" if company.sentiment_score > 0 else "Negative"
                st.metric("News Sentiment", sentiment_label, delta=f"{company.sentiment_score:.3f}")
                
            with col3:
                # Adjusted Threshold: 60 is the pass mark
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
                fig, ax = plt.subplots(figsize=(10, 3))
                colors = ['#4CAF50' if x > 0 else '#F44336' for x in scores]
                ax.bar(range(len(scores)), scores, color=colors)
                ax.axhline(0, color='black', linewidth=0.8)
                ax.set_ylabel("Sentiment Impact")
                ax.set_title("News Cycle Polarity (Real-Time)")
                st.pyplot(fig)
            else:
                st.info("No sufficient data for volatility plotting.")

        # TAB 2: The Network Graph (The "Tier-1" Feature)
        with tab2:
            st.subheader("Corporate Knowledge Graph")
            st.markdown("Visualizing hidden connections and potential contagion risks.")
            
            # Create a GraphViz Digraph
            graph = graphviz.Digraph()
            graph.attr(rankdir='LR')
            
            # Central Node (The Company)
            if company.risk_score < 50:
                color = "red" 
            else: 
                color = "green"
            
            graph.node('A', company.name, shape='box', style='filled', fillcolor=color)
            
            # Dynamic Nodes based on News
            # We extract entities from the headlines to build the graph
            for i, review in enumerate(company.reviews[:5]):
                # Heuristic: If headline mentions "CEO", "Court", "Stock"
                label = "News Event"
                if "CEO" in review.text or "Musk" in review.text or "Cook" in review.text:
                    label = "Leadership"
                    graph.node(f'L{i}', "Key Person", shape='ellipse', style='filled', fillcolor='lightblue')
                    graph.edge('A', f'L{i}', label="Managed By")
                
                elif "Lawsuit" in review.text or "Court" in review.text:
                    label = "Legal"
                    graph.node(f'L{i}', "Legal Entity", shape='diamond', style='filled', fillcolor='orange')
                    graph.edge('A', f'L{i}', label="Sued By")
                    
                else:
                    graph.node(f'N{i}', "Market Signal", shape='circle')
                    graph.edge('A', f'N{i}', label="Impacted By")

            st.graphviz_chart(graph)

        # TAB 3: The Data
        with tab3:
            st.subheader("Extracted Intelligence Source")
            if company.reviews:
                data = [{"Date": r.date, "Headline": r.text, "Source": r.source} for r in company.reviews]
                st.dataframe(pd.DataFrame(data), use_container_width=True)
            else:
                st.warning("No data found.")