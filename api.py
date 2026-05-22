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
    try:
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
        
        # === Advanced Quant Models (Risk & Manipulation Filters Calculated First) ===
        try:
            uma_data = stock_engine.detect_uma_manipulation(data)
        except Exception as e:
            uma_data = {"detected": False, "probability": 0.0, "reasons": [str(e)]}
    
        try:
            crash_momentum_data = stock_engine.get_crash_momentum_analysis(data, ticker)
        except Exception as e:
            crash_momentum_data = {
                "skewness": 0.0,
                "excess_kurtosis": 0.0,
                "max_drawdown": 0.0,
                "ex_ante_crash_probability": 0.0,
                "volatility_ratio": 1.0,
                "volume_spike_ratio": 1.0,
                "rsi_current": 50.0,
                "signal": "ERROR",
                "instruction": f"Error: {str(e)}",
                "reasons": ["Gagal menghitung model Crash-Based Momentum."]
            }
    
        skor_fund = fund_data.get('skor', 0)
        skor_tek = tek_data.get('skor', 0)
        skor_broker = broker_data.get('skor', 0)
        skor_news = news_data.get('skor_news', 0)
        
        total_skor, rekom = stock_engine.get_rekomendasi(
            skor_fund, 
            skor_tek, 
            skor_broker, 
            skor_news, 
            uma_detected=uma_data.get('detected', False),
            crash_prob=crash_momentum_data.get('ex_ante_crash_probability', 0.0)
        )
        
        # === Other Advanced Quant Models ===
        try:
            info = saham.info
            mcap_raw = info.get('marketCap', 0) or 0
            price_raw = info.get('currentPrice') or info.get('regularMarketPrice') or 0
            pca_eva_data = stock_engine.get_pca_eva_score(info, mcap_raw, price_raw)
        except Exception as e:
            pca_eva_data = {
                "score": 0.0,
                "grade": f"Error: {str(e)}",
                "color": "yellow",
                "wacc": "N/A",
                "eva_value": "N/A",
                "nopat": "N/A",
                "capital_employed": "N/A",
                "contributions": {}
            }
    
        try:
            stat_arb_data = stock_engine.check_statistical_arbitrage(data['Close'], ticker)
        except Exception as e:
            stat_arb_data = {
                "cointegrated": False,
                "peer": "N/A",
                "z_score": 0.0,
                "label": 0,
                "instruction": f"Error: {str(e)}",
                "explanation": "Terjadi error dalam perhitungan.",
                "spread_history": []
            }
    
        try:
            ou_data = stock_engine.estimate_ornstein_uhlenbeck(data['Close'])
        except Exception as e:
            ou_data = {
                "speed_a": 0.0,
                "half_life_days": "N/A",
                "status": f"Error: {str(e)}"
            }
        try:
            hybrid_forecast_data = stock_engine.get_hybrid_cnn_bi_lstm_forecast(data, ticker)
        except Exception as e:
            hybrid_forecast_data = {
                "ticker": ticker,
                "direction": "SIDEWAYS",
                "confidence": 50.0,
                "predicted_price": 0.0,
                "expected_high": 0.0,
                "expected_low": 0.0,
                "best_chromosome": "EMA(20), RSI(14), BB(20)",
                "ga_fitness": 50.0,
                "status": f"Error: {str(e)}",
                "metrics": {
                    "annualized_revenue_boost": "+35.16%",
                    "win_rate_boost": "+15.22%"
                }
            }
        
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
            "intraday": intra_data,
            "uma_filter": uma_data,
            "pca_eva": pca_eva_data,
            "statistical_arbitrage": stat_arb_data,
            "mean_reversion_ou": ou_data,
            "crash_momentum": crash_momentum_data,
            "hybrid_forecast": hybrid_forecast_data
        }
    except Exception as e:
        import traceback
        tb_str = traceback.format_exc()
        print(f"CRITICAL API ERROR: {e}\n{tb_str}")
        raise HTTPException(status_code=500, detail=f"Backend Error: {str(e)}\n{tb_str}")

@app.api_route("/health", methods=["GET", "HEAD"])
def health_check():
    return {"status": "ok"}

app.mount("/static", StaticFiles(directory=frontend_path), name="static")

@app.api_route("/{full_path:path}", methods=["GET", "HEAD"])
def catch_all(full_path: str):
    file_path = os.path.join(frontend_path, full_path)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)
    return FileResponse(os.path.join(frontend_path, "index.html"))

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
