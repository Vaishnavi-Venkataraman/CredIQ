# src/ai_analyst.py
import google.generativeai as genai
import os

class AIAnalyst:
    def __init__(self, api_key):
        self.api_key = api_key
        self.model = None
        
        if api_key:
            try:
                genai.configure(api_key=api_key)
                
                # --- AUTO-DISCOVERY MODE ---
                # Instead of guessing 'gemini-1.5-flash', we ask the API what you have access to.
                available_models = []
                for m in genai.list_models():
                    if 'generateContent' in m.supported_generation_methods:
                        available_models.append(m.name)
                
                # Priority: Try Flash -> Pro -> 1.0 -> Any
                target_model = None
                for m in available_models:
                    if 'flash' in m and '1.5' in m: target_model = m; break
                
                if not target_model:
                    for m in available_models:
                        if 'pro' in m and '1.5' in m: target_model = m; break
                
                if not target_model and available_models:
                    target_model = available_models[0] # Fallback to first available
                
                if target_model:
                    print(f"✅ AI Connected to: {target_model}")
                    self.model = genai.GenerativeModel(target_model)
                else:
                    print("⚠️ No valid generative models found for this API key.")
                    
            except Exception as e:
                print(f"AI Setup Error: {e}")

    def get_competitors(self, company_name):
        """Asks AI for 2 competitor tickers."""
        if not self.model: return ["SPY", "QQQ"]
        try:
            resp = self.model.generate_content(f"Identify top 2 stock competitors for {company_name}. Return only tickers comma separated. Example: F, GM")
            return [t.strip().upper() for t in resp.text.split(',')] [:2]
        except Exception as e:
            print(f"AI Peer Error: {e}")
            return ["SPY", "QQQ"]

    def generate_risk_summary(self, company):
        """Generates a risk summary."""
        if not self.model: return "⚠️ AI Summary Unavailable (Check API Key or Region)."
        try:
            prompt = f"Write a 2-sentence risk summary for {company.name} (Score: {company.risk_score}/100). Focus on: {', '.join(company.decision_reasons[:2])}."
            return self.model.generate_content(prompt).text.strip()
        except: return "AI Connection Failed."