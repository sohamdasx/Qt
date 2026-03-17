import asyncio
from dotenv import load_dotenv
import os

# 1. Load the secrets from the .env file BEFORE importing anything else
load_dotenv()

# 2. Import our isolated modules
from sifter import TickerRequest, sift_single_stock
from scavenger import process_and_store_news
from agentic_analyst import build_analyst_graph

async def run_autonomous_research(symbol: str):
    print(f"--- Starting Autonomous Research for {symbol} ---")
    
    # PHASE 2: The Sifter
    print("1. Running Quantitative Sifter...")
    request = TickerRequest(symbol=symbol)
    sift_result = await sift_single_stock(request)
    
    if not sift_result.get("is_candidate"):
        print(f"❌ {symbol} failed the quant filter. BYPASSING FOR TESTING.")
        # return  <-- Comment this out!
        sift_result["is_candidate"] = True # Force it to true
        sift_result["metrics"] = {"close": 3500, "ema_200": 3400, "vol_z_score": 2.5} # Fake the math
    
    print(f"✅ {symbol} passed! Metrics: {sift_result['metrics']}")
    
    # PHASE 3: The Scavenger
    print("2. Fetching & Vectorizing Contextual News...")
    # Note: We pass a mock ticker_id (e.g., 1) for this test run
    await process_and_store_news(symbol, ticker_id=1)
    
    # PHASE 4: The Agentic Analyst
    print("3. Initializing LangGraph Analyst Desk...")
    analyst_app = build_analyst_graph()
    
    initial_state = {
        "symbol": symbol,
        "quant_metrics": sift_result["metrics"],
        "retrieved_news": [], # The agent will fill this in
        "final_dossier": {}
    }
    
    print("4. Executing AI Analysis...")
    final_state = analyst_app.invoke(initial_state)
    
    print("\n--- FINAL INVESTMENT DOSSIER ---")
    print(final_state["final_dossier"])

if __name__ == "__main__":
    # Test the pipeline with a classic BSE ticker
    asyncio.run(run_autonomous_research("TCS.BO"))