import asyncio
import httpx
import os
from sentence_transformers import SentenceTransformer
from supabase import create_client, Client
import yfinance as yf
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET

# 1. Initialize Supabase Client and the local Embedding Model
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

model = SentenceTransformer('all-MiniLM-L6-v2')

async def fetch_news_for_ticker(symbol: str) -> list:
    print(f"📡 Fetching LIVE Bing News for {symbol}...")
    
    clean_name = symbol.replace(".BO", "").replace(".NS", "")
    
    # 1. Switch to Bing News RSS (Bypasses Google's tracking and 400 errors)
    query = urllib.parse.quote(f"{clean_name} stock market news India")
    url = f"https://www.bing.com/news/search?q={query}&format=rss"
    
    articles = []
    
    try:
        # Disguise our Python script as a browser
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req) as response:
            xml_data = response.read()
            
        root = ET.fromstring(xml_data)
        
        # 2. Extract Top 5 articles
        for item in root.findall('./channel/item')[:5]:
            title = item.find('title').text
            link = item.find('link').text
            pub_date = item.find('pubDate').text
            
            # The link is now a clean, direct, tracking-free URL!
            articles.append({
                "headline": title,
                "snippet": f"Published on {pub_date}. Source URL: {link}"
            })
            
    except Exception as e:
        print(f"⚠️ Error fetching news for {symbol}: {e}")
        
    if not articles:
        articles.append({
            "headline": f"No recent news found for {symbol}.",
            "snippet": "Market is currently quiet regarding this ticker. Source URL: #"
        })
        
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