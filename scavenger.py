import asyncio
import httpx
import os
from sentence_transformers import SentenceTransformer
from supabase import create_client, Client

# 1. Initialize Supabase Client and the local Embedding Model
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

model = SentenceTransformer('all-MiniLM-L6-v2')

async def fetch_news_for_ticker(symbol: str) -> list:
    # 2. Open an asynchronous HTTP session
    async with httpx.AsyncClient() as client:
        # Note: Replace this URL with a real financial news API (e.g., NewsAPI, AlphaVantage)
        url = f"https://mock-news-api.com/v1/search?q={symbol}&apikey=SECRET"
        
        # 3. Yield control back to the event loop while waiting for the network
        # response = await client.get(url)
        # articles = response.json().get('articles', [])
        
        # Mocking the response for the sake of the example
        articles = [
            {"headline": f"{symbol} secures major government contract", "snippet": "The new deal is expected to boost Q4 revenues significantly."},
            {"headline": f"Insider buying detected at {symbol}", "snippet": "CEO purchases 50,000 shares on the open market."}
        ]
        return articles

async def process_and_store_news(symbol: str, ticker_id: int):
    # 4. Fetch the articles
    articles = await fetch_news_for_ticker(symbol)
    
    for article in articles:
        # 5. Concatenate headline and snippet for maximum context
        text_to_embed = f"{article['headline']}. {article['snippet']}"
        
        # 6. Convert the text into a 384-dimensional vector and cast to a Python list
        embedding = model.encode(text_to_embed).tolist()
        
        # 7. Insert the structured data and the vector into Supabase
        supabase.table('news_vault').insert({
            "ticker_id": ticker_id,
            "headline": article['headline'],
            "snippet": article['snippet'],
            "embedding": embedding
        }).execute()
        
    print(f"Stored {len(articles)} vector records for {symbol}")

async def run_news_scavenger(candidates: list[dict]):
    # 8. Create a list of tasks to run concurrently
    tasks = [process_and_store_news(c['symbol'], c['ticker_id']) for c in candidates]
    
    # 9. Execute all tasks in parallel
    await asyncio.gather(*tasks)

# Example execution:
# asyncio.run(run_news_scavenger([{"symbol": "RELIANCE.BO", "ticker_id": 1}]))