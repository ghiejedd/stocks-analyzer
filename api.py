from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import yfinance as yf
import stock_engine
import os

app = FastAPI(title="Stock Analyzer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

frontend_path = os.path.join(os.path.dirname(__file__), "frontend")
os.makedirs(frontend_path, exist_ok=True)

@app.get("/api/analyze/{ticker}")
def analyze_stock(ticker: str):
    ticker = ticker.upper()
    if not ticker.endswith('.JK') and not '.' in ticker:
        ticker = f"{ticker}.JK"
        
    saham = yf.Ticker(ticker)
    data = saham.history(period="6mo")
    
    if data.empty:
        raise HTTPException(status_code=404, detail="Data saham tidak ditemukan.")
    
    fund_data = stock_engine.get_fundamental(saham, ticker)
    tek_data, data = stock_engine.get_teknikal(data, ticker)
    sr_data = stock_engine.get_support_resistance(data, ticker)
    orderbook_data = stock_engine.get_orderbook_analysis(data, ticker)
    broker_data = stock_engine.get_broker_summary(data, ticker)
    intra_data = stock_engine.get_intraday_strategy(data, ticker)
    profile_data = stock_engine.get_company_profile(saham, ticker)
    news_data = stock_engine.get_news(saham, ticker)
    
    skor_fund = fund_data.get('skor', 0)
    skor_tek = tek_data.get('skor', 0)
    skor_broker = broker_data.get('skor', 0)
    skor_news = news_data.get('skor_news', 0)
    
    total_skor, rekom = stock_engine.get_rekomendasi(skor_fund, skor_tek, skor_broker, skor_news)
    
    return {
        "ticker": ticker,
        "rekomendasi": rekom,
        "total_skor": total_skor,
        "profile": profile_data,
        "news": news_data,
        "fundamental": fund_data,
        "teknikal": tek_data,
        "support_resistance": sr_data,
        "orderbook": orderbook_data,
        "broker": broker_data,
        "intraday": intra_data
    }

app.mount("/static", StaticFiles(directory=frontend_path), name="static")

@app.get("/{full_path:path}")
def catch_all(full_path: str):
    file_path = os.path.join(frontend_path, full_path)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)
    return FileResponse(os.path.join(frontend_path, "index.html"))

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
