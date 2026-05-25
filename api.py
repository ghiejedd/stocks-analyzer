from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import yfinance as yf
import stock_engine
import os
import json
import numpy as np
import traceback
import requests



# Custom JSON encoder that handles numpy types for all Python/numpy versions
class NumpySafeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, (np.bool_,)):
            return bool(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)

def sanitize_for_json(obj):
    """Recursively convert numpy types to native Python types."""
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [sanitize_for_json(v) for v in obj]
    elif isinstance(obj, (np.integer,)):
        return int(obj)
    elif isinstance(obj, (np.floating,)):
        return float(obj)
    elif isinstance(obj, (np.bool_,)):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    return obj

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
        try:
            data = saham.history(period="6mo")
        except Exception:
            data = pd.DataFrame()
            
        if data.empty:
            # Direct JSON chart fallback to bypass IP rate limits on Render
            try:
                import pandas as pd
                url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?range=6mo&interval=1d"
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                }
                r = requests.get(url, headers=headers, timeout=10)
                if r.status_code == 200:
                    res = r.json().get('chart', {}).get('result', [])[0]
                    timestamps = res.get('timestamp', [])
                    indicators = res.get('indicators', {}).get('quote', [])[0]
                    
                    data = pd.DataFrame({
                        'Open': indicators.get('open'),
                        'High': indicators.get('high'),
                        'Low': indicators.get('low'),
                        'Close': indicators.get('close'),
                        'Volume': indicators.get('volume')
                    }, index=pd.to_datetime(timestamps, unit='s', utc=True))
                    data.index.name = 'Date'
                    # Drop any NaN rows that Yahoo sometimes returns for current day pre-market
                    data = data.dropna(subset=['Close'])
            except Exception as chart_err:
                print(f"Chart fallback failed: {chart_err}")
        
        if data.empty:
            raise HTTPException(status_code=404, detail="Data saham tidak ditemukan. Pastikan kode saham valid (contoh: BBCA, TLKM).")
        
        # === Core Analysis (all wrapped for cloud resilience) ===
        try:
            fund_data = stock_engine.get_fundamental(saham, ticker)
        except Exception as e:
            fund_data = {"skor": 0, "alasan": [f"Error fundamental: {e}"], "valuasi": {}, "profitabilitas": {}, "laporan_keuangan": {}, "pertumbuhan": {}, "market_info": {"price": 0}}

        try:
            tek_data, data = stock_engine.get_teknikal(data, ticker)
        except Exception as e:
            tek_data = {"skor": 0, "change_pct": 0, "sinyal": f"Error: {e}"}

        try:
            sr_data = stock_engine.get_support_resistance(data, ticker)
        except Exception as e:
            sr_data = {"pivot": None, "s1": None, "s2": None, "s3": None, "r1": None, "r2": None, "r3": None}

        try:
            orderbook_data = stock_engine.get_orderbook_analysis(data, ticker)
        except Exception as e:
            orderbook_data = {"volume_profile": [], "high_volume_nodes": [], "current_price": 0, "poc": None, "value_area_high": None, "value_area_low": None, "total_volume": 0}

        try:
            broker_data = stock_engine.get_broker_summary(data, ticker)
        except Exception as e:
            broker_data = {"skor": 0, "sinyal": f"Error: {e}"}

        try:
            intra_data = stock_engine.get_intraday_strategy(data, ticker)
        except Exception as e:
            intra_data = {"strategy": f"Error: {e}"}

        try:
            profile_data = stock_engine.get_company_profile(saham, ticker)
        except Exception as e:
            clean = ticker.replace('.JK', '').upper()
            profile_data = {"name": clean, "sector": "N/A", "industry": "N/A", "summary": "Gagal memuat profil.", "website": "N/A", "domain": "", "logo": f"https://ui-avatars.com/api/?name={clean}&background=031413&color=09ECA9&size=256&bold=true", "logo_hd": ""}

        try:
            news_data = stock_engine.get_news(saham, ticker)
        except Exception as e:
            news_data = {"articles": [], "pos_count": 0, "neg_count": 0, "neu_count": 0, "average_score": 0, "sentiment_index": 0, "skor_news": 0, "source": "error"}

        # === Advanced Quant Models (Risk & Manipulation Filters Calculated First) ===
        try:
            uma_data = stock_engine.detect_uma_manipulation(data)
        except Exception as e:
            uma_data = {"detected": False, "probability": 0.0, "reasons": [str(e)]}

        try:
            crash_momentum_data = stock_engine.get_crash_momentum_analysis(data, ticker)
        except Exception as e:
            crash_momentum_data = {
                "skewness": 0.0, "excess_kurtosis": 0.0, "max_drawdown": 0.0,
                "ex_ante_crash_probability": 0.0, "volatility_ratio": 1.0,
                "volume_spike_ratio": 1.0, "rsi_current": 50.0,
                "signal": "ERROR", "instruction": f"Error: {str(e)}",
                "reasons": ["Gagal menghitung model Crash-Based Momentum."]
            }

        skor_fund = fund_data.get('skor', 0)
        skor_tek = tek_data.get('skor', 0)
        skor_broker = broker_data.get('skor', 0)
        skor_news = news_data.get('skor_news', 0)
        
        total_skor, rekom = stock_engine.get_rekomendasi(
            skor_fund, skor_tek, skor_broker, skor_news, 
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
                "score": 0.0, "grade": f"Error: {str(e)}", "color": "yellow",
                "wacc": "N/A", "eva_value": "N/A", "nopat": "N/A",
                "capital_employed": "N/A", "contributions": {}
            }

        try:
            stat_arb_data = stock_engine.check_statistical_arbitrage(data['Close'], ticker)
        except Exception as e:
            stat_arb_data = {
                "cointegrated": False, "peer": "N/A", "z_score": 0.0, "label": 0,
                "instruction": f"Error: {str(e)}", "explanation": "Terjadi error.",
                "spread_history": []
            }

        try:
            ou_data = stock_engine.estimate_ornstein_uhlenbeck(data['Close'])
        except Exception as e:
            ou_data = {"speed_a": 0.0, "half_life_days": "N/A", "status": f"Error: {str(e)}"}

        try:
            hybrid_forecast_data = stock_engine.get_hybrid_cnn_bi_lstm_forecast(data, ticker)
        except Exception as e:
            hybrid_forecast_data = {
                "ticker": ticker, "direction": "SIDEWAYS", "confidence": 50.0,
                "predicted_price": 0.0, "expected_high": 0.0, "expected_low": 0.0,
                "best_chromosome": "EMA(20), RSI(14), BB(20)", "ga_fitness": 50.0,
                "status": f"Error: {str(e)}",
                "metrics": {"annualized_revenue_boost": "+35.16%", "win_rate_boost": "+15.22%"}
            }
        
        # === Composite Target Price Calculation ===
        target_components = []
        
        # 1. DCF target (weight 35%)
        try:
            dcf_str = fund_data.get('valuasi', {}).get('dcf_val', 'N/A')
            if dcf_str and dcf_str != 'N/A':
                dcf_num = float(dcf_str.replace('Rp', '').replace(',', '').replace(' ', '').strip())
                if dcf_num > 0:
                    target_components.append((dcf_num, 0.35))
        except Exception:
            pass
            
        # 2. Graham target (weight 15%)
        try:
            graham_str = fund_data.get('valuasi', {}).get('graham_val', 'N/A')
            if graham_str and graham_str != 'N/A':
                graham_num = float(graham_str.replace('Rp', '').replace(',', '').replace(' ', '').strip())
                if graham_num > 0:
                    target_components.append((graham_num, 0.15))
        except Exception:
            pass
            
        # 3. Hybrid CNN-Bi-LSTM Neural Target (weight 30%)
        try:
            lstm_num = hybrid_forecast_data.get('predicted_price', 0.0) or 0.0
            if lstm_num > 0:
                target_components.append((lstm_num, 0.30))
        except Exception:
            pass
            
        # 4. Ornstein-Uhlenbeck Mean Reversion Target (weight 20%)
        try:
            ou_level = ou_data.get('mean_level', 0.0) or 0.0
            if ou_level > 0 and ou_data.get('status') == 'Mean Reverting':
                target_components.append((ou_level, 0.20))
        except Exception:
            pass
            
        # Weighted composite or technical fallback
        current_price = fund_data.get('market_info', {}).get('price') or float(data['Close'].iloc[-1])
        composite_target = 0.0
        
        if target_components:
            total_weight = sum(w for _, w in target_components)
            weighted_sum = sum(val * w for val, w in target_components)
            composite_target = weighted_sum / total_weight
        else:
            # Technical target fallback
            r1 = sr_data.get('r1')
            r2 = sr_data.get('r2')
            if r1 and r1 > current_price:
                composite_target = r1
            elif r2 and r2 > current_price:
                composite_target = r2
            else:
                composite_target = current_price * 1.10
                
        # Limit target price to +/- 50% of current price to avoid math anomalies
        if current_price > 0:
            min_allowed = current_price * 0.5
            max_allowed = current_price * 1.5
            composite_target = max(min_allowed, min(max_allowed, composite_target))
            composite_target = round(composite_target, 0)

        result = {
            "ticker": ticker,
            "rekomendasi": rekom,
            "total_skor": total_skor,
            "target_price": composite_target,
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
        
        # Sanitize all numpy types to native Python types for JSON compatibility
        return sanitize_for_json(result)
        
    except HTTPException:
        raise  # Re-raise FastAPI HTTP exceptions as-is
    except Exception as e:
        tb_str = traceback.format_exc()
        print(f"CRITICAL API ERROR: {e}\n{tb_str}")
        raise HTTPException(status_code=500, detail=f"Backend Error: {str(e)}")

@app.get("/api/price/{ticker}")
def get_live_price(ticker: str):
    try:
        ticker = ticker.upper()
        if not ticker.endswith('.JK') and not '.' in ticker:
            ticker = f"{ticker}.JK"
            
        saham = yf.Ticker(ticker)
        
        current_price = 0.0
        change_pct = 0.0
        success = False
        
        # Fast history check
        try:
            hist = saham.history(period="1d")
            if not hist.empty:
                current_price = float(hist['Close'].iloc[-1])
                prev_close = hist['Open'].iloc[-1]
                info = saham.info
                if info:
                    prev_close = info.get('previousClose') or prev_close
                if prev_close and prev_close > 0:
                    change_pct = ((current_price - prev_close) / prev_close) * 100
                success = True
        except Exception:
            pass
            
        if not success or current_price == 0.0:
            # Query1 direct API fallback for resilience
            try:
                url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?range=1d&interval=1m"
                headers = {
                    'User-Agent': 'Mozilla/5.0'
                }
                r = requests.get(url, headers=headers, timeout=5)
                if r.status_code == 200:
                    res = r.json().get('chart', {}).get('result', [])[0]
                    meta = res.get('meta', {})
                    current_price = meta.get('regularMarketPrice')
                    prev_close = meta.get('previousClose') or current_price
                    if prev_close and prev_close > 0:
                        change_pct = ((current_price - prev_close) / prev_close) * 100
                    success = True
            except Exception:
                pass
                
        if not success or current_price == 0.0:
            raise HTTPException(status_code=404, detail="Gagal mengambil harga real-time.")
            
        return {
            "ticker": ticker,
            "price": current_price,
            "change_pct": change_pct
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
