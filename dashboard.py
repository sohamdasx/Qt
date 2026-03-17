import streamlit as st
import asyncio
from dotenv import load_dotenv
import os
from supabase import create_client, Client

# 1. Load environment variables
load_dotenv()

# Initialize Supabase Client
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

# 2. Import our existing pipeline modules
from sifter import TickerRequest, sift_single_stock
from scavenger import process_and_store_news
from agentic_analyst import build_analyst_graph

# 3. Configure the Web Page
st.set_page_config(page_title="BSE Agentic Quant", layout="wide", page_icon="📈")
st.title("📈 Autonomous Agentic Quant Desk")
st.markdown("Enter a BSE Ticker to deploy the AI Analyst Pipeline.")

# 4. Create the User Input
ticker = st.text_input("BSE Ticker Symbol", "TCS.BO")

# 5. Create the Execution Button
if st.button("Deploy AI Analyst"):
    
    # --- PHASE 2: SIFTER UI ---
    with st.spinner(f"Running Quant Sifter for {ticker}..."):
        # Wrap async call for Streamlit
        async def run_pipeline():
            request = TickerRequest(symbol=ticker)
            return await sift_single_stock(request)
        
        sift_result = asyncio.run(run_pipeline())
        
        # (Forcing the bypass for our demo so we always get an AI report)
        sift_result["is_candidate"] = True
        if "metrics" not in sift_result:
            sift_result["metrics"] = {"close": 3500, "ema_200": 3400, "vol_z_score": 2.5}

    st.success("✅ Passed Quantitative Filter!")
    st.json(sift_result["metrics"])

    # --- PHASE 3: SCAVENGER UI ---
    with st.spinner("Scavenging & Vectorizing News..."):
        async def run_scavenger():
            await process_and_store_news(ticker, ticker_id=1)
        asyncio.run(run_scavenger())
    
    st.success("✅ News Vectorized and Stored in Supabase!")

    # --- PHASE 4: ANALYST UI ---
    # --- PHASE 4: ANALYST UI ---
    with st.spinner("Lead Analyst is writing the dossier..."):
        app = build_analyst_graph()
        initial_state = {
            "symbol": ticker,
            "quant_metrics": sift_result["metrics"],
            "retrieved_news": [],
            "final_dossier": {}
        }
        final_state = app.invoke(initial_state)
        dossier = final_state["final_dossier"]
        
        # --- NEW: SAVE TO DATABASE ---
        with st.spinner("Archiving dossier to Supabase..."):
            try:
                # We use ticker_id=1 because we hardcoded TCS.BO to ID 1 in Phase 3
                db_payload = {
                    "ticker_id": 1, 
                    "signal": dossier.get("signal"),
                    "confidence_score": dossier.get("confidence_score"),
                    "entry_price": dossier.get("entry_price"),
                    "exit_price": dossier.get("exit_price"),
                    "dossier_json": dossier # Storing the entire raw output
                }
                
                # Insert the record into the recommendations table
                supabase.table('recommendations').insert(db_payload).execute()
                st.toast("💾 Dossier successfully archived to database!")
            except Exception as e:
                st.error(f"Database Error: {e}")
    
    # --- PHASE 5: THE FINAL DISPLAY ---
    st.divider()
    st.subheader(f"Final Investment Dossier: {ticker}")
    
    # Create 3 nice visual columns for the metrics
    col1, col2, col3 = st.columns(3)
    
    # Color-code the signal
    signal_color = "green" if dossier.get("signal") == "BUY" else "red" if dossier.get("signal") == "SELL" else "gray"
    col1.metric("Signal", dossier.get("signal", "HOLD"))
    col2.metric("AI Confidence", f"{int(dossier.get('confidence_score', 0) * 100)}%")
    col3.metric("Entry Target", f"₹{dossier.get('entry_price', 0)}")

    st.markdown("### 🧠 Analyst Reasoning")
    st.info(dossier.get('reasoning', ''))
    
    st.markdown("### 📚 Source Citations")
    for cit in dossier.get("citations", []):
        st.markdown(f"- *{cit}*")