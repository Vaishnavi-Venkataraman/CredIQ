# src/pdf_analyzer.py
import pdfplumber
import re

class FinancialAnalyzer:
    """
    Tier 3: Document Analysis Module.
    Extracts verification data from uploaded Bank Statements.
    """
    
    def analyze_statement(self, uploaded_file):
        """
        Scans a PDF for financial keywords and ending balances.
        Returns: extracted_cash (float), confidence_score (float)
        """
        extracted_text = ""
        found_balance = 0.0
        
        try:
            # Open the uploaded file (Streamlit handles file-like objects)
            with pdfplumber.open(uploaded_file) as pdf:
                for page in pdf.pages:
                    extracted_text += page.extract_text() + "\n"
            
            # --- INTELLIGENT PARSING ---
            # We look for patterns like "Ending Balance: $12,500.00"
            # Regex Explanation:
            # (?:Ending|Closing|Total)  -> Match words Ending OR Closing OR Total
            # \s+Balance                -> Followed by space and "Balance"
            # [:\-\s\$]* -> Followed by optional symbols (: - $ space)
            # ([\d,]+\.\d{2})           -> CAPTURE the number (digits, commas, dot, 2 decimals)
            
            pattern = r'(?:Ending|Closing|Total|Current)\s+Balance[:\-\s\$]*([\d,]+\.\d{2})'
            match = re.search(pattern, extracted_text, re.IGNORECASE)
            
            if match:
                # Clean the string (remove commas) and convert to float
                amount_str = match.group(1).replace(",", "")
                found_balance = float(amount_str)
                print(f"💰 PDF SUCCESS: Found Ending Balance ${found_balance}")
                return found_balance
            else:
                print("⚠️ PDF WARNING: Could not find 'Ending Balance' keyword.")
                return 0.0

        except Exception as e:
            print(f"❌ PDF ERROR: {e}")
            return 0.0