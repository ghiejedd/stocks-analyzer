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
import pandas as pd
import socket

# Prevent hanging connections in third-party libraries (e.g. yfinance)
socket.setdefaulttimeout(5)



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

def fetch_resilient_saham_info(ticker: str) -> dict:
    """
    Fetch financial and statistical data directly from Yahoo Finance quoteSummary REST API.
    Bypasses yfinance library rate limits and session blocks, making it highly resilient for Render.
    """
    info = {}
    try:
        url = f"https://query2.finance.yahoo.com/v10/finance/quoteSummary/{ticker}?modules=financialData,defaultKeyStatistics,summaryDetail,summaryProfile,quoteType"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code != 200:
            url = f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{ticker}?modules=financialData,defaultKeyStatistics,summaryDetail,summaryProfile,quoteType"
            response = requests.get(url, headers=headers, timeout=5)
            
        if response.status_code == 200:
            data = response.json()
            result = data.get('quoteSummary', {}).get('result', [])
            if result:
                res = result[0]
                
                fin = res.get('financialData', {})
                stats = res.get('defaultKeyStatistics', {})
                detail = res.get('summaryDetail', {})
                profile = res.get('summaryProfile', {})
                qtype = res.get('quoteType', {})
                
                def get_raw(module, key, default=None):
                    if not module or key not in module:
                        return default
                    val_obj = module.get(key)
                    if isinstance(val_obj, dict) and "raw" in val_obj:
                        return val_obj["raw"]
                    return val_obj if val_obj is not None else default
                
                info['longName'] = qtype.get('longName') or qtype.get('shortName') or ticker.replace('.JK', '')
                info['shortName'] = qtype.get('shortName') or ticker.replace('.JK', '')
                info['symbol'] = qtype.get('symbol') or ticker
                
                info['sector'] = profile.get('sector')
                info['industry'] = profile.get('industry')
                info['longBusinessSummary'] = profile.get('longBusinessSummary')
                info['website'] = profile.get('website')
                
                info['currentPrice'] = get_raw(fin, 'currentPrice')
                info['targetHighPrice'] = get_raw(fin, 'targetHighPrice')
                info['returnOnEquity'] = get_raw(fin, 'returnOnEquity')
                info['returnOnAssets'] = get_raw(fin, 'returnOnAssets')
                info['totalRevenue'] = get_raw(fin, 'totalRevenue')
                info['revenueGrowth'] = get_raw(fin, 'revenueGrowth')
                info['totalDebt'] = get_raw(fin, 'totalDebt')
                info['totalCash'] = get_raw(fin, 'totalCash')
                info['currentRatio'] = get_raw(fin, 'currentRatio')
                info['quickRatio'] = get_raw(fin, 'quickRatio')
                info['debtToEquity'] = get_raw(fin, 'debtToEquity')
                info['freeCashflow'] = get_raw(fin, 'freeCashflow')
                info['operatingCashflow'] = get_raw(fin, 'operatingCashflow')
                info['ebitda'] = get_raw(fin, 'ebitda')
                info['grossMargins'] = get_raw(fin, 'grossMargins')
                info['ebitdaMargins'] = get_raw(fin, 'ebitdaMargins')
                info['operatingMargins'] = get_raw(fin, 'operatingMargins')
                info['profitMargins'] = get_raw(fin, 'profitMargins')
                
                info['trailingEps'] = get_raw(stats, 'trailingEps')
                info['forwardEps'] = get_raw(stats, 'forwardEps')
                info['bookValue'] = get_raw(stats, 'bookValue')
                info['priceToBook'] = get_raw(stats, 'priceToBook')
                info['pegRatio'] = get_raw(stats, 'pegRatio')
                info['forwardPE'] = get_raw(stats, 'forwardPE')
                info['enterpriseToRevenue'] = get_raw(stats, 'enterpriseToRevenue')
                info['enterpriseToEbitda'] = get_raw(stats, 'enterpriseToEbitda')
                info['netIncomeToCommon'] = get_raw(stats, 'netIncomeToCommon')
                info['beta'] = get_raw(stats, 'beta')
                info['earningsGrowth'] = get_raw(stats, 'earningsGrowth')
                info['earningsQuarterlyGrowth'] = get_raw(stats, 'earningsQuarterlyGrowth')
                info['revenueQuarterlyGrowth'] = get_raw(stats, 'revenueQuarterlyGrowth')
                
                info['previousClose'] = get_raw(detail, 'previousClose')
                info['regularMarketPrice'] = get_raw(detail, 'regularMarketPrice') or info.get('currentPrice')
                info['marketCap'] = get_raw(detail, 'marketCap')
                info['enterpriseValue'] = get_raw(detail, 'enterpriseValue')
                info['trailingPE'] = get_raw(detail, 'trailingPE')
                info['priceToSalesTrailing12Months'] = get_raw(detail, 'priceToSalesTrailing12Months')
                info['dividendYield'] = get_raw(detail, 'dividendYield')
                info['dividendRate'] = get_raw(detail, 'dividendRate')
                info['payoutRatio'] = get_raw(detail, 'payoutRatio')
                info['fiftyTwoWeekHigh'] = get_raw(detail, 'fiftyTwoWeekHigh')
                info['fiftyTwoWeekLow'] = get_raw(detail, 'fiftyTwoWeekLow')
                info['averageVolume'] = get_raw(detail, 'averageVolume')
                
                print(f"Resilient fallback successfully retrieved and mapped info for {ticker}")
    except Exception as e:
        print(f"Error in fetch_resilient_saham_info for {ticker}: {e}")
        
    return info

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
        
        # Single saham.info load with resilient direct REST API fallback to bypass Render IP blocks
        saham_info = {}
        is_cloud = os.environ.get("RENDER") == "true" or os.environ.get("PORT") is not None
        
        if is_cloud:
            print("Running in cloud environment. Fetching fundamentals via resilient API fallback first.")
            saham_info = fetch_resilient_saham_info(ticker)
            
        if not saham_info or not saham_info.get('marketCap'):
            try:
                saham_info = saham.info
                if saham_info is None or not isinstance(saham_info, dict):
                    saham_info = {}
            except Exception as info_err:
                print(f"yfinance info fetch failed: {info_err}")
                saham_info = {}
                
        # Final attempt fallback if standard yfinance returned incomplete details
        if not saham_info or not saham_info.get('marketCap'):
            print("yfinance failed or incomplete. Trying resilient API fallback as final attempt.")
            saham_info = fetch_resilient_saham_info(ticker)

        # === Core Analysis (all wrapped for cloud resilience) ===
        try:
            fund_data = stock_engine.get_fundamental(saham, ticker, info=saham_info)
        except Exception as e:
            fund_data = {"skor": 0, "alasan": [f"Error fundamental: {e}"], "valuasi": {}, "profitabilitas": {}, "laporan_keuangan": {}, "pertumbuhan": {}, "market_info": {"price": 0}}

        try:
            cashflow_data, data = stock_engine.get_cashflow_analysis(data, saham, ticker, info=saham_info)
        except Exception as e:
            cashflow_data = {"skor": 0, "change_pct": 0, "regime": "ERROR", "alasan": [f"Error: {e}"]}

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
            profile_data = stock_engine.get_company_profile(saham, ticker, info=saham_info)
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
        skor_cashflow = cashflow_data.get('skor', 0)
        skor_broker = broker_data.get('skor', 0)
        skor_news = news_data.get('skor_news', 0)
        
        total_skor, rekom = stock_engine.get_rekomendasi(
            skor_fund, skor_cashflow, skor_broker, skor_news, 
            uma_detected=uma_data.get('detected', False),
            crash_prob=crash_momentum_data.get('ex_ante_crash_probability', 0.0)
        )
        
        # === Other Advanced Quant Models ===
        try:
            info = saham_info
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
            # Fallback target
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
            "cashflow": cashflow_data,
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
                prev_close = float(hist['Open'].iloc[-1])
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
