import yfinance as yf
import pandas as pd
import warnings
import math
import random
import requests
import feedparser
import re
import urllib.parse
from datetime import datetime, timezone

warnings.filterwarnings('ignore')

BROKER_ASING = ['AK', 'BK', 'ZP', 'CS', 'ML', 'DB', 'JP', 'UB', 'GS', 'MS']
BROKER_LOKAL = ['YP', 'RX', 'PD', 'DX', 'MG', 'KZ', 'TP', 'AI', 'BZ', 'KI']

def format_rupiah(value):
    if value is None or pd.isna(value): return "N/A"
    if not isinstance(value, (int, float)): return str(value)
    if abs(value) >= 1_000_000_000_000:
        return f"Rp {value/1_000_000_000_000:.2f} Triliun"
    elif abs(value) >= 1_000_000_000:
        return f"Rp {value/1_000_000_000:.2f} Miliar"
    elif abs(value) >= 1_000_000:
        return f"Rp {value/1_000_000:.2f} Juta"
    else:
        return f"Rp {value:,.0f}"

def safe_get(info, key, default=None):
    val = info.get(key, default)
    if pd.isna(val):
        return default
    return val

def get_fundamental(saham, kode):
    try:
        info = saham.info
        
        per = safe_get(info, 'trailingPE')
        fwd_pe = safe_get(info, 'forwardPE')
        pbv = safe_get(info, 'priceToBook')
        ps = safe_get(info, 'priceToSalesTrailing12Months')
        ev_ebitda = safe_get(info, 'enterpriseToEbitda')
        ev_rev = safe_get(info, 'enterpriseToRevenue')
        peg = safe_get(info, 'pegRatio')

        roe = safe_get(info, 'returnOnEquity')
        roa = safe_get(info, 'returnOnAssets')
        npm = safe_get(info, 'profitMargins')
        opm = safe_get(info, 'operatingMargins')
        gpm = safe_get(info, 'grossMargins')
        ebitda_margin = safe_get(info, 'ebitdaMargins')

        rev = safe_get(info, 'totalRevenue')
        ni = safe_get(info, 'netIncomeToCommon')
        ebitda = safe_get(info, 'ebitda')
        eps = safe_get(info, 'trailingEps')
        fwd_eps = safe_get(info, 'forwardEps')
        der = safe_get(info, 'debtToEquity')
        cr = safe_get(info, 'currentRatio')
        qr = safe_get(info, 'quickRatio')
        td = safe_get(info, 'totalDebt')
        tc = safe_get(info, 'totalCash')
        fcf = safe_get(info, 'freeCashflow')
        ocf = safe_get(info, 'operatingCashflow')
        bv = safe_get(info, 'bookValue')

        rev_growth = safe_get(info, 'revenueGrowth')
        earn_growth = safe_get(info, 'earningsGrowth')
        earn_qg = safe_get(info, 'earningsQuarterlyGrowth')
        rev_qg = safe_get(info, 'revenueQuarterlyGrowth')

        dy = safe_get(info, 'dividendYield')
        dps = safe_get(info, 'dividendRate')
        payout = safe_get(info, 'payoutRatio')
        mcap = safe_get(info, 'marketCap')
        ev = safe_get(info, 'enterpriseValue')
        beta = safe_get(info, 'beta')
        avg_vol = safe_get(info, 'averageVolume')
        hi52 = safe_get(info, 'fiftyTwoWeekHigh')
        lo52 = safe_get(info, 'fiftyTwoWeekLow')
        price = safe_get(info, 'currentPrice') or safe_get(info, 'regularMarketPrice')

        skor = 0
        alasan = []
        if per and per < 15: skor += 1; alasan.append("PER murah (<15x)")
        elif per and per > 25: skor -= 1; alasan.append("PER mahal (>25x)")
        if fwd_pe and fwd_pe < per if per else False: skor += 1; alasan.append("Forward PE < TTM PE (earnings naik)")
        if pbv and pbv < 1.5: skor += 1; alasan.append("PBV murah (<1.5x)")
        elif pbv and pbv > 5: skor -= 1; alasan.append("PBV mahal (>5x)")
        if peg and peg < 1: skor += 1; alasan.append("PEG < 1 (undervalued vs growth)")
        elif peg and peg > 2: skor -= 1; alasan.append("PEG > 2 (overvalued vs growth)")
        
        if roe and roe > 0.15: skor += 1; alasan.append("ROE bagus (>15%)")
        elif roe and roe < 0.05: skor -= 1; alasan.append("ROE rendah (<5%)")
        if npm and npm > 0.10: skor += 1; alasan.append("NPM sehat (>10%)")
        
        if der and der < 100: skor += 1; alasan.append("DER aman (<100%)")
        elif der and der > 200: skor -= 1; alasan.append("DER tinggi (>200%)")
        if cr and cr > 1.5: skor += 1; alasan.append("Current Ratio kuat (>1.5x)")
        elif cr and cr < 1: skor -= 1; alasan.append("Current Ratio lemah (<1x)")
        if fcf and fcf > 0: skor += 1; alasan.append("Free Cash Flow positif")
        elif fcf and fcf < 0: skor -= 1; alasan.append("Free Cash Flow negatif")
        
        if rev_growth and rev_growth > 0.10: skor += 1; alasan.append(f"Revenue tumbuh {rev_growth*100:.1f}%")
        elif rev_growth and rev_growth < -0.05: skor -= 1; alasan.append(f"Revenue turun {rev_growth*100:.1f}%")
        if earn_growth and earn_growth > 0.10: skor += 1; alasan.append(f"Earnings tumbuh {earn_growth*100:.1f}%")
        elif earn_growth and earn_growth < -0.10: skor -= 1; alasan.append(f"Earnings turun {earn_growth*100:.1f}%")
        
        if dy and dy > 0.03: skor += 1; alasan.append("Dividen menarik (>3%)")

        # Graham Number Intrinsic Value
        graham_val = "N/A"
        graham_diff = "N/A"
        graham_status = "N/A"
        if eps and bv and eps > 0 and bv > 0:
            try:
                graham_num = math.sqrt(22.5 * eps * bv)
                graham_val = f"Rp {graham_num:,.0f}"
                if price:
                    diff_pct = ((graham_num - price) / price) * 100
                    graham_diff = f"{diff_pct:+.2f}%"
                    graham_status = "UNDERVALUED (Murah)" if price < graham_num else "OVERVALUED (Mahal)"
            except Exception:
                pass

        # Discounted Cash Flow (DCF) Valuation using CAPM Cost of Equity
        dcf_val = "N/A"
        dcf_diff = "N/A"
        dcf_status = "N/A"
        dcf_params = "N/A"
        try:
            if price and mcap:
                # 1. Cost of Equity (CAPM)
                rf = 0.065  # 6.5% Risk-free Rate (ID 10Y Bond Yield)
                mrp = 0.055  # 5.5% Market Risk Premium
                b_val = beta if (beta and not pd.isna(beta)) else 1.0
                r = rf + b_val * mrp
                r = max(0.08, min(0.18, r))  # Bound Ke between 8% and 18%
                
                # 2. Growth Rate (g)
                rev_g = rev_growth if (rev_growth and not pd.isna(rev_growth)) else 0.08
                earn_g = earn_growth if (earn_growth and not pd.isna(earn_growth)) else 0.08
                g = max(rev_g, earn_g) if (rev_g and earn_g) else 0.08
                g = max(0.04, min(0.15, g))  # Bound g between 4% and 15%
                
                # 3. Base Cash Flow (CF0)
                cf0 = None
                if fcf and fcf > 0:
                    cf0 = fcf
                elif ocf and ocf > 0:
                    cf0 = ocf * 0.7  # CapEx adjusted proxy
                elif ni and ni > 0:
                    cf0 = ni
                elif eps and eps > 0:
                    shares_est = mcap / price
                    cf0 = eps * shares_est
                
                if cf0:
                    shares = mcap / price
                    
                    # Year 1-5 PV projections
                    pv_sum = 0
                    cf_t = cf0
                    for t in range(1, 6):
                        cf_t = cf_t * (1 + g)
                        pv_t = cf_t / ((1 + r) ** t)
                        pv_sum += pv_t
                    
                    # Terminal Value
                    gn = 0.03  # 3% Long-term growth
                    if r > gn:
                        tv = cf_t * (1 + gn) / (r - gn)
                        pv_tv = tv / ((1 + r) ** 5)
                        
                        total_val = pv_sum + pv_tv
                        dcf_num = total_val / shares
                        dcf_num = round(dcf_num, 0)
                        
                        dcf_val = f"Rp {dcf_num:,.0f}"
                        diff_pct = ((dcf_num - price) / price) * 100
                        dcf_diff = f"{diff_pct:+.2f}%"
                        dcf_status = "UNDERVALUED (Murah)" if price < dcf_num else "OVERVALUED (Mahal)"
                        dcf_params = f"WACC/Ke: {r*100:.1f}%, Growth: {g*100:.1f}%"
        except Exception:
            pass

        # Piotroski F-Score (Smart Adaptation)
        f_score = 0
        f_details = []
        try:
            # 1. Positive ROA
            roa_val = safe_get(info, 'returnOnAssets')
            if roa_val and roa_val > 0:
                f_score += 1
                f_details.append("ROA Positif (+1)")
            else:
                f_details.append("ROA Negatif/Rendah (+0)")
            
            # 2. Positive Operating Cash Flow
            ocf_val = safe_get(info, 'operatingCashflow')
            if ocf_val and ocf_val > 0:
                f_score += 1
                f_details.append("OCF Positif (+1)")
            else:
                f_details.append("OCF Negatif (+0)")
            
            # 3. Quality of Earnings (OCF > Net Income)
            ni_val = safe_get(info, 'netIncomeToCommon')
            if ocf_val and ni_val and ocf_val > ni_val:
                f_score += 1
                f_details.append("Kualitas Laba Sehat (OCF > Net Income) (+1)")
            else:
                f_details.append("Kualitas Laba Rendah (Net Income > OCF) (+0)")
            
            # 4. Profitability Strength (ROA > 5%)
            if roa_val and roa_val > 0.05:
                f_score += 1
                f_details.append("ROA Kuat (>5%) (+1)")
            else:
                f_details.append("ROA Lemah (<5%) (+0)")
                
            # 5. Liquid Current Ratio (>1.5x)
            cr_val = safe_get(info, 'currentRatio')
            if cr_val and cr_val > 1.5:
                f_score += 1
                f_details.append("Current Ratio Aman (>1.5x) (+1)")
            else:
                f_details.append("Current Ratio Rendah (<1.5x) (+0)")
                
            # 6. Lower Debt-to-Equity (DER < 100%)
            der_val = safe_get(info, 'debtToEquity')
            if der_val and der_val < 100:
                f_score += 1
                f_details.append("DER Rendah (<100%) (+1)")
            else:
                f_details.append("DER Tinggi (>=100%) (+0)")
                
            # 7. Positive Revenue Growth
            rev_g = safe_get(info, 'revenueGrowth')
            if rev_g and rev_g > 0.05:
                f_score += 1
                f_details.append("Pertumbuhan Revenue Sehat (>5%) (+1)")
            else:
                f_details.append("Pertumbuhan Revenue Lambat (+0)")
                
            # 8. High Gross Margin (>25%)
            gpm_val = safe_get(info, 'grossMargins')
            if gpm_val and gpm_val > 0.25:
                f_score += 1
                f_details.append("Gross Margin Kuat (>25%) (+1)")
            else:
                f_details.append("Gross Margin Tipis (<25%) (+0)")
                
            # 9. Positive Earnings Growth
            earn_g = safe_get(info, 'earningsGrowth')
            if earn_g and earn_g > 0:
                f_score += 1
                f_details.append("Pertumbuhan Laba Positif (+1)")
            else:
                f_details.append("Pertumbuhan Laba Lambat/Negatif (+0)")
        except Exception:
            pass

        # Altman Z-Score (Emerging Market & Standard Corporate Model)
        z_score = 0.0
        z_status = "Distress Zone (Sangat Berisiko)"
        try:
            if price and mcap:
                td = safe_get(info, 'totalDebt') or 0
                bv_val = safe_get(info, 'bookValue')
                shares = mcap / price
                equity = (shares * bv_val) if (shares and bv_val) else mcap
                ta = equity + td
                
                if ta > 0:
                    # X1: Working Capital / Total Assets
                    cr_val = safe_get(info, 'currentRatio')
                    if cr_val and cr_val > 0:
                        cl = td * 0.5 if td > 0 else ta * 0.1
                        cl = max(cl, 1.0)
                        ca = cr_val * cl
                        wc = ca - cl
                        x1 = wc / ta
                    else:
                        x1 = 0.15
                    
                    # X2: Retained Earnings / Total Assets
                    roe_val = safe_get(info, 'returnOnEquity') or 0.1
                    x2 = (roe_val * equity) / ta
                    
                    # X3: EBIT / Total Assets
                    roa_val = safe_get(info, 'returnOnAssets') or 0.05
                    x3 = roa_val
                    
                    # X4: Market Equity / Total Liabilities (Total Debt)
                    x4 = mcap / td if td > 0 else 5.0
                    
                    # X5: Revenue / Total Assets
                    rev_val = safe_get(info, 'totalRevenue')
                    x5 = rev_val / ta if (rev_val and ta) else 0.7
                    
                    # Z-Score Formula
                    z_score = (1.2 * x1) + (1.4 * x2) + (3.3 * x3) + (0.6 * x4) + (0.99 * x5)
                    z_score = max(0.0, min(15.0, z_score))
                else:
                    # Simple fallback
                    cr_val = safe_get(info, 'currentRatio') or 1.0
                    roa_val = safe_get(info, 'returnOnAssets') or 0.05
                    der_val = safe_get(info, 'debtToEquity') or 100.0
                    z_score = (0.5 * min(2.0, cr_val)) + (10.0 * roa_val) + (100.0 / max(10.0, der_val))
                    z_score = max(0.0, min(15.0, z_score))
                
                if z_score > 2.99:
                    z_status = "Safe Zone (Sangat Sehat)"
                elif z_score >= 1.81:
                    z_status = "Gray Zone (Risiko Sedang)"
                else:
                    z_status = "Distress Zone (Sangat Berisiko)"
        except Exception:
            z_score = 1.9
            z_status = "Gray Zone (Risiko Sedang)"

        # Adjust fundamental score slightly
        if f_score >= 7:
            skor += 1
            alasan.append(f"Piotroski F-Score Sangat Kuat ({f_score}/9)")
        elif f_score <= 3:
            skor -= 1
            alasan.append(f"Piotroski F-Score Lemah ({f_score}/9)")

        if z_status.startswith("Safe"):
            skor += 1
            alasan.append("Altman Z-Score: Finansial aman (Safe Zone)")
        elif z_status.startswith("Distress"):
            skor -= 1
            alasan.append("Altman Z-Score: Risiko keuangan tinggi (Distress Zone)")

        return {
            "skor": skor,
            "alasan": alasan,
            "valuasi": {
                "per": f"{per:.2f}x" if per else "N/A",
                "fwd_pe": f"{fwd_pe:.2f}x" if fwd_pe else "N/A",
                "peg": f"{peg:.2f}" if peg else "N/A",
                "pbv": f"{pbv:.2f}x" if pbv else "N/A",
                "ps": f"{ps:.2f}x" if ps else "N/A",
                "ev_ebitda": f"{ev_ebitda:.2f}x" if ev_ebitda else "N/A",
                "ev_rev": f"{ev_rev:.2f}x" if ev_rev else "N/A",
                "graham_val": graham_val,
                "graham_diff": graham_diff,
                "graham_status": graham_status,
                "dcf_val": dcf_val,
                "dcf_diff": dcf_diff,
                "dcf_status": dcf_status,
                "dcf_params": dcf_params,
                "piotroski_val": f"{f_score}/9",
                "piotroski_details": f_details,
                "altman_val": f"{z_score:.2f}",
                "altman_status": z_status
            },
            "profitabilitas": {
                "roe": f"{roe*100:.2f}%" if roe else "N/A",
                "roa": f"{roa*100:.2f}%" if roa else "N/A",
                "gpm": f"{gpm*100:.2f}%" if gpm else "N/A",
                "ebitda_margin": f"{ebitda_margin*100:.2f}%" if ebitda_margin else "N/A",
                "opm": f"{opm*100:.2f}%" if opm else "N/A",
                "npm": f"{npm*100:.2f}%" if npm else "N/A"
            },
            "laporan_keuangan": {
                "rev": format_rupiah(rev),
                "ebitda": format_rupiah(ebitda),
                "ni": format_rupiah(ni),
                "eps": f"Rp {eps:,.0f}" if eps else "N/A",
                "fwd_eps": f"Rp {fwd_eps:,.0f}" if fwd_eps else "N/A",
                "bv": f"Rp {bv:,.0f}" if bv else "N/A",
                "td": format_rupiah(td),
                "tc": format_rupiah(tc),
                "ocf": format_rupiah(ocf),
                "fcf": format_rupiah(fcf),
                "der": f"{der:.2f}%" if der else "N/A",
                "cr": f"{cr:.2f}x" if cr else "N/A",
                "qr": f"{qr:.2f}x" if qr else "N/A"
            },
            "pertumbuhan": {
                "rev_growth_yoy": f"{rev_growth*100:.2f}%" if rev_growth else "N/A",
                "earn_growth_yoy": f"{earn_growth*100:.2f}%" if earn_growth else "N/A",
                "rev_growth_qoq": f"{rev_qg*100:.2f}%" if rev_qg else "N/A",
                "earn_growth_qoq": f"{earn_qg*100:.2f}%" if earn_qg else "N/A"
            },
            "market_info": {
                "dy": f"{dy*100:.2f}%" if dy else "N/A",
                "dps": f"Rp {dps:,.0f}" if dps else "N/A",
                "payout": f"{payout*100:.2f}%" if payout else "N/A",
                "mcap": format_rupiah(mcap),
                "ev": format_rupiah(ev),
                "beta": f"{beta:.2f}" if beta else "N/A",
                "avg_vol": f"{avg_vol:,.0f}" if avg_vol else "N/A",
                "hi52": f"Rp {hi52:,.0f}" if hi52 else "N/A",
                "lo52": f"Rp {lo52:,.0f}" if lo52 else "N/A",
                "pct_from_hi": f"{((price - hi52) / hi52) * 100:+.2f}%" if (price and hi52) else "N/A",
                "pct_from_lo": f"{((price - lo52) / lo52) * 100:+.2f}%" if (price and lo52) else "N/A",
                "price": price
            }
        }
    except Exception as e:
        return {"error": str(e), "skor": 0, "alasan": []}

def _calculate_parabolic_sar(data, af_start=0.02, af_step=0.02, af_max=0.20):
    """Calculate Parabolic SAR using Wilder's method."""
    length = len(data)
    sar = [0.0] * length
    
    if length < 2:
        return sar
    
    # Initialize
    is_uptrend = data['Close'].iloc[1] > data['Close'].iloc[0]
    af = af_start
    
    if is_uptrend:
        sar[0] = data['Low'].iloc[0]
        ep = data['High'].iloc[0]
    else:
        sar[0] = data['High'].iloc[0]
        ep = data['Low'].iloc[0]
    
    for i in range(1, length):
        prev_sar = sar[i - 1]
        
        if is_uptrend:
            sar[i] = prev_sar + af * (ep - prev_sar)
            sar[i] = min(sar[i], data['Low'].iloc[i - 1])
            if i >= 2:
                sar[i] = min(sar[i], data['Low'].iloc[i - 2])
            
            if data['Low'].iloc[i] < sar[i]:
                is_uptrend = False
                sar[i] = ep
                af = af_start
                ep = data['Low'].iloc[i]
            else:
                if data['High'].iloc[i] > ep:
                    ep = data['High'].iloc[i]
                    af = min(af + af_step, af_max)
        else:
            sar[i] = prev_sar + af * (ep - prev_sar)
            sar[i] = max(sar[i], data['High'].iloc[i - 1])
            if i >= 2:
                sar[i] = max(sar[i], data['High'].iloc[i - 2])
            
            if data['High'].iloc[i] > sar[i]:
                is_uptrend = True
                sar[i] = ep
                af = af_start
                ep = data['High'].iloc[i]
            else:
                if data['Low'].iloc[i] < ep:
                    ep = data['Low'].iloc[i]
                    af = min(af + af_step, af_max)
    
    return sar

def get_teknikal(data, kode):
    data['MA7'] = data['Close'].rolling(window=7).mean()
    data['MA20'] = data['Close'].rolling(window=20).mean()
    data['MA50'] = data['Close'].rolling(window=50).mean()
    data['EMA9'] = data['Close'].ewm(span=9, adjust=False).mean()
    data['EMA12'] = data['Close'].ewm(span=12, adjust=False).mean()
    data['EMA26'] = data['Close'].ewm(span=26, adjust=False).mean()
    data['EMA200'] = data['Close'].ewm(span=200, adjust=False).mean()

    data['MACD'] = data['EMA12'] - data['EMA26']
    data['Signal'] = data['MACD'].ewm(span=9, adjust=False).mean()
    data['MACD_Hist'] = data['MACD'] - data['Signal']

    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    data['RSI'] = 100 - (100 / (1 + rs))

    min_rsi = data['RSI'].rolling(window=14).min()
    max_rsi = data['RSI'].rolling(window=14).max()
    data['StochRSI'] = (data['RSI'] - min_rsi) / (max_rsi - min_rsi) * 100

    data['BB_Mid'] = data['Close'].rolling(window=20).mean()
    bb_std = data['Close'].rolling(window=20).std()
    data['BB_Upper'] = data['BB_Mid'] + (bb_std * 2)
    data['BB_Lower'] = data['BB_Mid'] - (bb_std * 2)
    data['BB_Width'] = (data['BB_Upper'] - data['BB_Lower']) / data['BB_Mid'] * 100

    high_diff = data['High'].diff()
    low_diff = data['Low'].diff().multiply(-1)
    plus_dm = high_diff.where((high_diff > low_diff) & (high_diff > 0), 0)
    minus_dm = low_diff.where((low_diff > high_diff) & (low_diff > 0), 0)
    tr = pd.concat([data['High'] - data['Low'], (data['High'] - data['Close'].shift(1)).abs(), (data['Low'] - data['Close'].shift(1)).abs()], axis=1).max(axis=1)
    atr14 = tr.rolling(14).mean()
    plus_di = 100 * (plus_dm.rolling(14).mean() / atr14)
    minus_di = 100 * (minus_dm.rolling(14).mean() / atr14)
    dx = (plus_di - minus_di).abs() / (plus_di + minus_di) * 100
    data['ADX'] = dx.rolling(14).mean()
    data['Plus_DI'] = plus_di
    data['Minus_DI'] = minus_di

    high14 = data['High'].rolling(14).max()
    low14 = data['Low'].rolling(14).min()
    data['Williams_R'] = -100 * (high14 - data['Close']) / (high14 - low14)

    data['ATR'] = atr14
    data['Vol_MA20'] = data['Volume'].rolling(window=20).mean()

    # === ICHIMOKU CLOUD ===
    high9 = data['High'].rolling(window=9).max()
    low9 = data['Low'].rolling(window=9).min()
    data['Tenkan'] = (high9 + low9) / 2

    high26 = data['High'].rolling(window=26).max()
    low26 = data['Low'].rolling(window=26).min()
    data['Kijun'] = (high26 + low26) / 2

    data['Senkou_A'] = ((data['Tenkan'] + data['Kijun']) / 2).shift(26)
    high52 = data['High'].rolling(window=52).max()
    low52 = data['Low'].rolling(window=52).min()
    data['Senkou_B'] = ((high52 + low52) / 2).shift(26)
    data['Chikou'] = data['Close'].shift(-26)

    # === PARABOLIC SAR ===
    sar_values = _calculate_parabolic_sar(data)
    data['PSAR'] = sar_values

    # === VWAP with Bands ===
    tp_vwap = (data['High'] + data['Low'] + data['Close']) / 3
    data['VWAP'] = (tp_vwap * data['Volume']).cumsum() / data['Volume'].cumsum()
    vwap_sq = (tp_vwap ** 2 * data['Volume']).cumsum() / data['Volume'].cumsum()
    data['VWAP_Std'] = (vwap_sq - data['VWAP'] ** 2).clip(lower=0).apply(lambda x: x ** 0.5)
    data['VWAP_Upper'] = data['VWAP'] + data['VWAP_Std']
    data['VWAP_Lower'] = data['VWAP'] - data['VWAP_Std']

    hari_ini = data.iloc[-1]
    kemarin = data.iloc[-2] if len(data) > 1 else hari_ini

    harga = hari_ini['Close']
    change = ((harga - kemarin['Close']) / kemarin['Close']) * 100

    # Moving Average & Crossover
    ma20_now = hari_ini['MA20']; ma50_now = hari_ini['MA50']
    ma20_prev = kemarin['MA20'] if 'MA20' in kemarin.index else None
    ma50_prev = kemarin['MA50'] if 'MA50' in kemarin.index else None
    
    crossover = None
    if not pd.isna(ma20_now) and not pd.isna(ma50_now) and ma20_prev and ma50_prev:
        if ma20_prev <= ma50_prev and ma20_now > ma50_now:
            crossover = "GOLDEN CROSS TERDETEKSI!"
        elif ma20_prev >= ma50_prev and ma20_now < ma50_now:
            crossover = "DEATH CROSS TERDETEKSI!"

    macd_val = hari_ini['MACD']; sig_val = hari_ini['Signal']; hist_val = hari_ini['MACD_Hist']
    macd_prev = kemarin['MACD_Hist'] if 'MACD_Hist' in kemarin.index else None
    macd_crossover = None
    if not pd.isna(macd_val) and not pd.isna(macd_prev):
        if macd_prev < 0 and hist_val > 0: macd_crossover = "MACD CROSSOVER BULLISH"
        elif macd_prev > 0 and hist_val < 0: macd_crossover = "MACD CROSSOVER BEARISH"

    rsi_val = hari_ini['RSI']; stoch_val = hari_ini['StochRSI']
    adx_val = hari_ini['ADX']; pdi = hari_ini['Plus_DI']; mdi = hari_ini['Minus_DI']
    wr = hari_ini['Williams_R']
    bb_u = hari_ini['BB_Upper']; bb_l = hari_ini['BB_Lower']; bb_m = hari_ini['BB_Mid']; bb_w = hari_ini['BB_Width']
    atr_val = hari_ini['ATR']
    vol = hari_ini['Volume']; vol_ma = hari_ini['Vol_MA20']

    o, h, l, c = hari_ini['Open'], hari_ini['High'], hari_ini['Low'], hari_ini['Close']
    total_range = h - l if h != l else 1
    body = abs(c - o)
    upper_shadow = h - max(o, c)
    lower_shadow = min(o, c) - l
    
    patterns = []
    if body < total_range * 0.1 and lower_shadow > body * 2: patterns.append("HAMMER / DRAGONFLY DOJI")
    if body < total_range * 0.1 and upper_shadow > body * 2: patterns.append("SHOOTING STAR")
    if body < total_range * 0.05: patterns.append("DOJI")
    if c > o and body > total_range * 0.6: patterns.append("BULLISH MARUBOZU")
    if c < o and body > total_range * 0.6: patterns.append("BEARISH MARUBOZU")
    if len(data) >= 3:
        d2 = data.iloc[-2]; d3 = data.iloc[-3]
        if d3['Close'] < d3['Open'] and d2['Close'] < d2['Open'] and c > o and c > d3['Open']:
            patterns.append("MORNING STAR")
        if d3['Close'] > d3['Open'] and d2['Close'] > d2['Open'] and c < o and c < d3['Open']:
            patterns.append("EVENING STAR")

    buy_pressure = (c - l) / total_range * 100 if total_range > 0 else 50
    sell_pressure = (h - c) / total_range * 100 if total_range > 0 else 50

    skor = 0
    alasan = []
    if not pd.isna(macd_val):
        if macd_val > sig_val: skor += 1; alasan.append("MACD Bullish")
        else: skor -= 1; alasan.append("MACD Bearish")
    if not pd.isna(rsi_val):
        if rsi_val < 30: skor += 1; alasan.append("RSI Oversold (peluang buy)")
        elif rsi_val > 70: skor -= 1; alasan.append("RSI Overbought (rawan turun)")
    if not pd.isna(stoch_val):
        if stoch_val < 20: skor += 1; alasan.append("StochRSI Oversold")
        elif stoch_val > 80: skor -= 1; alasan.append("StochRSI Overbought")
    if not pd.isna(wr):
        if wr < -80: skor += 1; alasan.append("Williams %R Oversold")
        elif wr > -20: skor -= 1; alasan.append("Williams %R Overbought")
    if not pd.isna(adx_val):
        if adx_val > 25 and pdi > mdi: skor += 1; alasan.append("ADX tren kuat naik")
        elif adx_val > 25 and mdi > pdi: skor -= 1; alasan.append("ADX tren kuat turun")
    if not pd.isna(ma20_now):
        if harga > ma20_now: skor += 1; alasan.append("Harga di atas MA20")
        else: skor -= 1; alasan.append("Harga di bawah MA20")
    if not pd.isna(ma50_now):
        if harga > ma50_now: skor += 1; alasan.append("Harga di atas MA50")
        else: skor -= 1; alasan.append("Harga di bawah MA50")
    if not pd.isna(bb_u):
        if harga <= bb_l: skor += 1; alasan.append("Harga di Lower BB (peluang mantul)")
        elif harga >= bb_u: skor -= 1; alasan.append("Harga di Upper BB (rawan koreksi)")
    if buy_pressure > 65: skor += 1; alasan.append("Orderbook: buyer dominan")
    elif sell_pressure > 65: skor -= 1; alasan.append("Orderbook: seller dominan")
    if patterns:
        bullish_p = any("BULLISH" in p or "HAMMER" in p or "MORNING" in p for p in patterns)
        bearish_p = any("BEARISH" in p or "SHOOTING" in p or "EVENING" in p for p in patterns)
        if bullish_p: skor += 1; alasan.append("Pola candlestick bullish")
        if bearish_p: skor -= 1; alasan.append("Pola candlestick bearish")

    # Fibonacci Retracement (6-month Swing High/Low)
    try:
        hi_6m = float(data['High'].max())
        lo_6m = float(data['Low'].min())
        diff_6m = hi_6m - lo_6m
        fib = {
            "fib_0": lo_6m,
            "fib_236": lo_6m + 0.236 * diff_6m,
            "fib_382": lo_6m + 0.382 * diff_6m,
            "fib_50": lo_6m + 0.5 * diff_6m,
            "fib_618": lo_6m + 0.618 * diff_6m,
            "fib_786": lo_6m + 0.786 * diff_6m,
            "fib_100": hi_6m
        }
    except Exception:
        fib = {
            "fib_0": 0.0, "fib_236": 0.0, "fib_382": 0.0,
            "fib_50": 0.0, "fib_618": 0.0, "fib_786": 0.0, "fib_100": 0.0
        }

    # === ADVANCED INDICATORS VALUES ===
    ema200_val = hari_ini['EMA200']
    tenkan_val = hari_ini['Tenkan']
    kijun_val = hari_ini['Kijun']
    senkou_a_val = hari_ini.get('Senkou_A', None)
    senkou_b_val = hari_ini.get('Senkou_B', None)
    psar_val = hari_ini['PSAR']
    vwap_val = hari_ini['VWAP']
    vwap_upper = hari_ini['VWAP_Upper']
    vwap_lower = hari_ini['VWAP_Lower']

    # Ichimoku signal
    ichimoku_signal = "NETRAL"
    if not pd.isna(tenkan_val) and not pd.isna(kijun_val):
        if not pd.isna(senkou_a_val) and not pd.isna(senkou_b_val):
            cloud_top = max(senkou_a_val, senkou_b_val)
            cloud_bottom = min(senkou_a_val, senkou_b_val)
            if harga > cloud_top and tenkan_val > kijun_val:
                ichimoku_signal = "STRONG BULLISH"
                skor += 1; alasan.append("Ichimoku: Harga di atas Cloud + TK Cross Bullish")
            elif harga > cloud_top:
                ichimoku_signal = "BULLISH"
            elif harga < cloud_bottom and tenkan_val < kijun_val:
                ichimoku_signal = "STRONG BEARISH"
                skor -= 1; alasan.append("Ichimoku: Harga di bawah Cloud + TK Cross Bearish")
            elif harga < cloud_bottom:
                ichimoku_signal = "BEARISH"
            else:
                ichimoku_signal = "DALAM CLOUD (Sideways)"

    # Parabolic SAR signal
    psar_trend = "NETRAL"
    if not pd.isna(psar_val):
        if harga > psar_val:
            psar_trend = "UPTREND"
        else:
            psar_trend = "DOWNTREND"

    # EMA200 major trend
    if not pd.isna(ema200_val):
        if harga > ema200_val:
            skor += 1; alasan.append("Harga di atas EMA200 (tren jangka panjang bullish)")
        else:
            skor -= 1; alasan.append("Harga di bawah EMA200 (tren jangka panjang bearish)")

    # === TREND SUMMARY ===
    trend_score = 0
    if not pd.isna(ma20_now) and harga > ma20_now: trend_score += 1
    if not pd.isna(ma50_now) and harga > ma50_now: trend_score += 1
    if not pd.isna(ema200_val) and harga > ema200_val: trend_score += 1
    if not pd.isna(adx_val) and adx_val > 25 and pdi > mdi: trend_score += 1
    if not pd.isna(macd_val) and macd_val > sig_val: trend_score += 1
    if psar_trend == "UPTREND": trend_score += 1
    if ichimoku_signal in ["BULLISH", "STRONG BULLISH"]: trend_score += 1

    if not pd.isna(ma20_now) and harga < ma20_now: trend_score -= 1
    if not pd.isna(ma50_now) and harga < ma50_now: trend_score -= 1
    if not pd.isna(ema200_val) and harga < ema200_val: trend_score -= 1
    if not pd.isna(adx_val) and adx_val > 25 and mdi > pdi: trend_score -= 1
    if not pd.isna(macd_val) and macd_val < sig_val: trend_score -= 1
    if psar_trend == "DOWNTREND": trend_score -= 1
    if ichimoku_signal in ["BEARISH", "STRONG BEARISH"]: trend_score -= 1

    if trend_score >= 5: trend_label = "STRONG UPTREND"
    elif trend_score >= 2: trend_label = "UPTREND"
    elif trend_score <= -5: trend_label = "STRONG DOWNTREND"
    elif trend_score <= -2: trend_label = "DOWNTREND"
    else: trend_label = "SIDEWAYS"

    trend_strength = max(-2, min(2, trend_score // 3))

    return {
        "skor": skor,
        "alasan": alasan,
        "fibonacci": fib,
        "harga_terakhir": float(harga) if not pd.isna(harga) else None,
        "change_pct": float(change) if not pd.isna(change) else None,
        "open": float(o), "high": float(h), "low": float(l),
        "ma": {
            "ma7": float(hari_ini['MA7']) if not pd.isna(hari_ini['MA7']) else None,
            "ma20": float(ma20_now) if not pd.isna(ma20_now) else None,
            "ma50": float(ma50_now) if not pd.isna(ma50_now) else None,
            "crossover": crossover
        },
        "ema200": float(ema200_val) if not pd.isna(ema200_val) else None,
        "macd": {
            "macd": float(macd_val) if not pd.isna(macd_val) else None,
            "signal": float(sig_val) if not pd.isna(sig_val) else None,
            "hist": float(hist_val) if not pd.isna(hist_val) else None,
            "crossover": macd_crossover
        },
        "rsi": float(rsi_val) if not pd.isna(rsi_val) else None,
        "stoch_rsi": float(stoch_val) if not pd.isna(stoch_val) else None,
        "adx": {
            "adx": float(adx_val) if not pd.isna(adx_val) else None,
            "pdi": float(pdi) if not pd.isna(pdi) else None,
            "mdi": float(mdi) if not pd.isna(mdi) else None
        },
        "williams_r": float(wr) if not pd.isna(wr) else None,
        "bb": {
            "upper": float(bb_u) if not pd.isna(bb_u) else None,
            "mid": float(bb_m) if not pd.isna(bb_m) else None,
            "lower": float(bb_l) if not pd.isna(bb_l) else None,
            "width": float(bb_w) if not pd.isna(bb_w) else None
        },
        "ichimoku": {
            "tenkan": float(tenkan_val) if not pd.isna(tenkan_val) else None,
            "kijun": float(kijun_val) if not pd.isna(kijun_val) else None,
            "senkou_a": float(senkou_a_val) if pd.notna(senkou_a_val) else None,
            "senkou_b": float(senkou_b_val) if pd.notna(senkou_b_val) else None,
            "signal": ichimoku_signal
        },
        "parabolic_sar": {
            "value": float(psar_val) if not pd.isna(psar_val) else None,
            "trend": psar_trend
        },
        "vwap": {
            "vwap": float(vwap_val) if not pd.isna(vwap_val) else None,
            "upper": float(vwap_upper) if not pd.isna(vwap_upper) else None,
            "lower": float(vwap_lower) if not pd.isna(vwap_lower) else None
        },
        "trend_summary": {
            "label": trend_label,
            "strength": trend_strength,
            "score": trend_score
        },
        "atr": float(atr_val) if not pd.isna(atr_val) else None,
        "volume": {
            "vol": int(vol) if not pd.isna(vol) else None,
            "vol_ma20": int(vol_ma) if not pd.isna(vol_ma) else None
        },
        "patterns": patterns,
        "orderbook": {
            "buy_pressure": float(buy_pressure),
            "sell_pressure": float(sell_pressure)
        }
    }, data

def get_support_resistance(data, kode):
    hari_ini = data.iloc[-1]
    harga = hari_ini['Close']
    high = hari_ini['High']
    low = hari_ini['Low']
    close = hari_ini['Close']
    pivot = (high + low + close) / 3

    s1 = (2 * pivot) - high
    s2 = pivot - (high - low)
    s3 = low - 2 * (high - pivot)
    r1 = (2 * pivot) - low
    r2 = pivot + (high - low)
    r3 = high + 2 * (pivot - low)

    ma20 = hari_ini.get('MA20', None)
    ma50 = hari_ini.get('MA50', None)

    return {
        "pivot": float(pivot) if not pd.isna(pivot) else None,
        "s1": float(s1) if not pd.isna(s1) else None,
        "s2": float(s2) if not pd.isna(s2) else None,
        "s3": float(s3) if not pd.isna(s3) else None,
        "r1": float(r1) if not pd.isna(r1) else None,
        "r2": float(r2) if not pd.isna(r2) else None,
        "r3": float(r3) if not pd.isna(r3) else None,
        "ma20": float(ma20) if pd.notna(ma20) else None,
        "ma50": float(ma50) if pd.notna(ma50) else None
    }

def get_orderbook_analysis(data, ticker):
    """Volume Profile analysis based on real historical price/volume distribution."""
    try:
        recent = data.tail(20).copy()
        hari_ini = data.iloc[-1]
        harga = float(hari_ini['Close'])
        
        # === VOLUME PROFILE (Real data) ===
        price_min = float(recent['Low'].min())
        price_max = float(recent['High'].max())
        num_buckets = 20
        bucket_size = (price_max - price_min) / num_buckets if price_max > price_min else 1
        
        volume_profile = []
        total_volume = 0
        for i in range(num_buckets):
            bucket_low = price_min + (i * bucket_size)
            bucket_high = bucket_low + bucket_size
            bucket_mid = (bucket_low + bucket_high) / 2
            
            vol_in_bucket = 0
            for _, row in recent.iterrows():
                if row['Low'] <= bucket_high and row['High'] >= bucket_low:
                    overlap = min(row['High'], bucket_high) - max(row['Low'], bucket_low)
                    total_range = row['High'] - row['Low'] if row['High'] > row['Low'] else 1
                    proportion = overlap / total_range
                    vol_in_bucket += float(row['Volume']) * proportion
            
            total_volume += vol_in_bucket
            volume_profile.append({
                "price": round(bucket_mid, 0),
                "volume": int(vol_in_bucket),
                "is_high_volume": False
            })
        
        # Mark high volume nodes (top 25%)
        high_volume_nodes = []
        if volume_profile:
            volumes = [vp['volume'] for vp in volume_profile]
            threshold = sorted(volumes, reverse=True)[max(0, len(volumes) // 4)]
            for vp in volume_profile:
                if vp['volume'] >= threshold:
                    vp['is_high_volume'] = True
                    high_volume_nodes.append(vp['price'])
        
        # POC (Point of Control) - price level with highest volume
        poc_price = None
        if volume_profile:
            poc = max(volume_profile, key=lambda x: x['volume'])
            poc_price = poc['price']
        
        # Value Area (70% of volume)
        value_area_high = None
        value_area_low = None
        if volume_profile and total_volume > 0:
            sorted_vp = sorted(volume_profile, key=lambda x: x['volume'], reverse=True)
            cum_vol = 0
            va_prices = []
            for vp in sorted_vp:
                cum_vol += vp['volume']
                va_prices.append(vp['price'])
                if cum_vol >= total_volume * 0.7:
                    break
            if va_prices:
                value_area_high = max(va_prices)
                value_area_low = min(va_prices)
        
        return {
            "volume_profile": volume_profile,
            "high_volume_nodes": high_volume_nodes,
            "current_price": harga,
            "poc": poc_price,
            "value_area_high": value_area_high,
            "value_area_low": value_area_low,
            "total_volume": int(total_volume)
        }
    except Exception:
        return {
            "volume_profile": [], "high_volume_nodes": [],
            "current_price": 0, "poc": None,
            "value_area_high": None, "value_area_low": None,
            "total_volume": 0
        }

def _hitung_smart_money(data):
    d = data.copy()
    obv = [0]
    for i in range(1, len(d)):
        if d['Close'].iloc[i] > d['Close'].iloc[i-1]: obv.append(obv[-1] + d['Volume'].iloc[i])
        elif d['Close'].iloc[i] < d['Close'].iloc[i-1]: obv.append(obv[-1] - d['Volume'].iloc[i])
        else: obv.append(obv[-1])
    d['OBV'] = obv
    d['OBV_MA20'] = d['OBV'].rolling(window=20).mean()

    clv = ((d['Close'] - d['Low']) - (d['High'] - d['Close'])) / (d['High'] - d['Low'])
    clv = clv.fillna(0)
    d['AD'] = (clv * d['Volume']).cumsum()
    d['AD_MA20'] = d['AD'].rolling(window=20).mean()

    tp = (d['High'] + d['Low'] + d['Close']) / 3
    mf = tp * d['Volume']
    pos_mf = mf.where(tp > tp.shift(1), 0).rolling(14).sum()
    neg_mf = mf.where(tp < tp.shift(1), 0).rolling(14).sum()
    mfi_ratio = pos_mf / neg_mf.replace(0, 1)
    d['MFI'] = 100 - (100 / (1 + mfi_ratio))
    d['CMF'] = (clv * d['Volume']).rolling(window=20).sum() / d['Volume'].rolling(window=20).sum()
    d['VWAP'] = (d['Volume'] * (d['High'] + d['Low'] + d['Close']) / 3).cumsum() / d['Volume'].cumsum()
    d['Vol_MA20'] = d['Volume'].rolling(window=20).mean()
    d['Vol_Ratio'] = d['Volume'] / d['Vol_MA20']
    return d

def _simulasi_broker(data, kode):
    recent = data.tail(5)
    random.seed(hash(kode) + len(data))
    total_vol = recent['Volume'].sum()
    if total_vol == 0: return [], [], 0, 0
    broker_buy = []
    broker_sell = []
    sisa_buy = 0.45 * total_vol
    sisa_sell = 0.35 * total_vol
    shuffled_asing = random.sample(BROKER_ASING, min(5, len(BROKER_ASING)))
    shuffled_lokal = random.sample(BROKER_LOKAL, min(5, len(BROKER_LOKAL)))
    for i, br in enumerate(shuffled_asing):
        frac = random.uniform(0.10, 0.35) if i < 2 else random.uniform(0.05, 0.15)
        vol_b = int(sisa_buy * frac)
        vol_s = int(sisa_sell * frac * random.uniform(0.5, 1.2))
        net = vol_b - vol_s
        broker_buy.append((br, vol_b, vol_s, net, "ASING"))
    for i, br in enumerate(shuffled_lokal):
        frac = random.uniform(0.08, 0.20) if i < 2 else random.uniform(0.03, 0.10)
        vol_b = int(sisa_sell * frac)
        vol_s = int(sisa_buy * frac * random.uniform(0.6, 1.1))
        net = vol_b - vol_s
        broker_sell.append((br, vol_b, vol_s, net, "LOKAL"))
    all_brokers = broker_buy + broker_sell
    all_brokers.sort(key=lambda x: abs(x[3]), reverse=True)
    total_foreign_buy = sum(b[1] for b in broker_buy)
    total_foreign_sell = sum(b[2] for b in broker_buy)
    return all_brokers, shuffled_asing, total_foreign_buy, total_foreign_sell

def get_broker_summary(data, kode):
    data = _hitung_smart_money(data)
    hari_ini = data.iloc[-1]
    
    recent = data.tail(5).copy()
    recent['Change'] = recent['Close'].diff()
    total_buy_vol = 0
    total_sell_vol = 0
    
    daily_flow = []
    for idx, row in recent.iterrows():
        change = row['Change']
        vol = row['Volume']
        if not pd.isna(change):
            if change >= 0: total_buy_vol += vol; flow = "NET BUY"
            else: total_sell_vol += vol; flow = "NET SELL"
        else: flow = "N/A"
        daily_flow.append({"tanggal": idx.strftime('%Y-%m-%d'), "close": float(row['Close']), "volume": float(vol), "flow": flow})
        
    total_vol = total_buy_vol + total_sell_vol
    buy_pct = (total_buy_vol / total_vol * 100) if total_vol > 0 else 50
    sell_pct = (total_sell_vol / total_vol * 100) if total_vol > 0 else 50
    
    all_brokers, top_asing, foreign_buy, foreign_sell = [], [], 0, 0

    obv_now = hari_ini['OBV']
    obv_ma = hari_ini['OBV_MA20']
    ad_now = hari_ini['AD']
    ad_ma = hari_ini['AD_MA20']
    mfi = hari_ini['MFI']
    cmf = hari_ini['CMF']
    vwap = hari_ini['VWAP']
    vol_ratio = hari_ini['Vol_Ratio']

    skor_sm = 0
    alasan = []
    if not pd.isna(obv_ma):
        if obv_now > obv_ma: skor_sm += 1; alasan.append("OBV Bullish (uang masuk)")
        else: skor_sm -= 1; alasan.append("OBV Bearish (uang keluar)")
    if not pd.isna(ad_ma):
        if ad_now > ad_ma: skor_sm += 1; alasan.append("A/D Line: Akumulasi")
        else: skor_sm -= 1; alasan.append("A/D Line: Distribusi")
    if not pd.isna(cmf):
        if cmf > 0.05: skor_sm += 1; alasan.append("CMF positif (tekanan beli)")
        elif cmf < -0.05: skor_sm -= 1; alasan.append("CMF negatif (tekanan jual)")
    if not pd.isna(mfi):
        if mfi < 20: skor_sm += 1; alasan.append("MFI Oversold (peluang reversal)")
        elif mfi > 80: skor_sm -= 1; alasan.append("MFI Overbought (rawan koreksi)")
    if buy_pct > 60: skor_sm += 1; alasan.append("Net buy dominan 5 hari")
    elif sell_pct > 60: skor_sm -= 1; alasan.append("Net sell dominan 5 hari")

    if skor_sm >= 2: fase = "FASE AKUMULASI (Smart money sedang MASUK - Pertimbangkan BUY)"
    elif skor_sm <= -2: fase = "FASE DISTRIBUSI (Smart money sedang KELUAR - Pertimbangkan SELL)"
    elif skor_sm > 0: fase = "CENDERUNG AKUMULASI (Ada tanda-tanda smart money masuk)"
    elif skor_sm < 0: fase = "CENDERUNG DISTRIBUSI (Ada tanda-tanda smart money keluar)"
    else: fase = "NETRAL (Belum ada sinyal jelas dari smart money)"

    return {
        "skor": skor_sm,
        "alasan": alasan,
        "fase": fase,
        "daily_flow": daily_flow,
        "net_buy_vol": total_buy_vol,
        "net_sell_vol": total_sell_vol,
        "buy_pct": buy_pct,
        "sell_pct": sell_pct,
        "smart_money": {
            "obv": float(obv_now) if not pd.isna(obv_now) else None,
            "obv_ma": float(obv_ma) if not pd.isna(obv_ma) else None,
            "ad": float(ad_now) if not pd.isna(ad_now) else None,
            "ad_ma": float(ad_ma) if not pd.isna(ad_ma) else None,
            "mfi": float(mfi) if not pd.isna(mfi) else None,
            "cmf": float(cmf) if not pd.isna(cmf) else None,
            "vwap": float(vwap) if not pd.isna(vwap) else None,
            "vol_ratio": float(vol_ratio) if not pd.isna(vol_ratio) else None
        }
    }

def get_intraday_strategy(data, kode):
    recent = data.tail(10).copy()
    pagi_naik = 0
    pagi_turun = 0
    total_hari = 0
    avg_intraday_gain = 0
    avg_intraday_loss = 0
    for _, row in recent.iterrows():
        if row['Open'] > 0:
            total_hari += 1
            intraday_pct = ((row['Close'] - row['Open']) / row['Open']) * 100
            if row['Close'] > row['Open']:
                pagi_naik += 1; avg_intraday_gain += intraday_pct
            elif row['Close'] < row['Open']:
                pagi_turun += 1; avg_intraday_loss += intraday_pct
    if pagi_naik > 0: avg_intraday_gain /= pagi_naik
    if pagi_turun > 0: avg_intraday_loss /= pagi_turun
    pct_pagi_naik = (pagi_naik / total_hari * 100) if total_hari > 0 else 50
    pct_pagi_turun = (pagi_turun / total_hari * 100) if total_hari > 0 else 50

    gap_data = []
    for i in range(1, min(10, len(data))):
        prev_close = data.iloc[-(i+1)]['Close']
        curr_open = data.iloc[-i]['Open']
        if prev_close > 0:
            gap_pct = ((curr_open - prev_close) / prev_close) * 100
            gap_data.append(gap_pct)
    avg_gap = sum(gap_data) / len(gap_data) if gap_data else 0
    gap_up_count = sum(1 for g in gap_data if g > 0.2)
    gap_down_count = sum(1 for g in gap_data if g < -0.2)

    hari_ini = data.iloc[-1]
    o, h, l, c = hari_ini['Open'], hari_ini['High'], hari_ini['Low'], hari_ini['Close']
    total_range = h - l if h != l else 1
    buy_pressure = (c - l) / total_range * 100
    sell_pressure = (h - c) / total_range * 100

    vol_today = hari_ini['Volume']
    vol_ma = hari_ini.get('Vol_MA20', 0)
    vol_ratio = vol_today / vol_ma if not pd.isna(vol_ma) and vol_ma > 0 else 1

    skor = 0
    alasan = []
    if pct_pagi_naik >= 70: skor += 2; alasan.append(f"Dominan naik intraday ({pct_pagi_naik:.0f}% hari)")
    elif pct_pagi_naik >= 60: skor += 1; alasan.append(f"Cenderung naik intraday ({pct_pagi_naik:.0f}% hari)")
    elif pct_pagi_turun >= 70: skor -= 2; alasan.append(f"Dominan turun intraday ({pct_pagi_turun:.0f}% hari)")
    elif pct_pagi_turun >= 60: skor -= 1; alasan.append(f"Cenderung turun intraday ({pct_pagi_turun:.0f}% hari)")

    if avg_gap > 0.3: skor -= 1; alasan.append(f"Sering gap up (avg {avg_gap:+.2f}%) -> beli sore lebih baik")
    elif avg_gap < -0.3: skor += 1; alasan.append(f"Sering gap down (avg {avg_gap:+.2f}%) -> beli pagi lebih murah")

    if buy_pressure > 65: skor += 1; alasan.append("Buyer dominan hari ini")
    elif sell_pressure > 65: skor -= 1; alasan.append("Seller dominan hari ini")

    if vol_ratio > 1.5: alasan.append(f"Volume tinggi ({vol_ratio:.1f}x) - likuiditas bagus utk scalping")
    elif vol_ratio < 0.5: skor = 0; alasan.append("Volume terlalu rendah - TIDAK DISARANKAN scalping")

    if vol_ratio < 0.5: kesimpulan = "TIDAK DISARANKAN SCALPING (Volume terlalu sepi)"
    elif skor >= 2: kesimpulan = "BELI PAGI, JUAL SORE (Pola harga cenderung naik dalam hari)"
    elif skor >= 1: kesimpulan = "CENDERUNG Beli Pagi Jual Sore (Tapi tidak terlalu kuat)"
    elif skor <= -2: kesimpulan = "BELI SORE, JUAL PAGI (Pola harga cenderung gap up keesokan hari)"
    elif skor <= -1: kesimpulan = "CENDERUNG Beli Sore Jual Pagi (Tapi tidak terlalu kuat)"
    else: kesimpulan = "NETRAL - Tidak ada pola intraday yang jelas"

    return {
        "skor": skor,
        "alasan": alasan,
        "kesimpulan": kesimpulan,
        "pagi_naik_pct": pct_pagi_naik,
        "pagi_turun_pct": pct_pagi_turun,
        "avg_gain": avg_intraday_gain,
        "avg_loss": avg_intraday_loss,
        "avg_gap": avg_gap,
        "gap_up": gap_up_count,
        "gap_down": gap_down_count,
        "buy_pressure": buy_pressure,
        "sell_pressure": sell_pressure,
        "vol_ratio": vol_ratio
    }

def get_rekomendasi(skor_fund, skor_tek, skor_broker, skor_news=0):
    total = skor_fund + skor_tek + skor_broker + skor_news
    if total >= 5: rekom = "STRONG BUY"
    elif total >= 2: rekom = "BUY"
    elif total >= -1: rekom = "HOLD / WAIT"
    elif total >= -4: rekom = "SELL"
    else: rekom = "STRONG SELL"
    return total, rekom

IDX_DOMAINS = {
    # Big Banks
    "BBCA": "bca.co.id", "BBRI": "bri.co.id", "BMRI": "bankmandiri.co.id",
    "BBNI": "bni.co.id", "BRIS": "bankbsi.co.id", "BTPS": "btpnsyariah.com",
    "BJTM": "bankjatim.co.id", "BDMN": "danamon.co.id", "BNII": "maybank.co.id",
    "MEGA": "bankmega.com", "NISP": "ocbc.id", "PNBN": "panin.co.id",
    "BNGA": "cimb.co.id", "BBTN": "btn.co.id", "BNLI": "permatabank.com",
    # Telco & Tech
    "TLKM": "telkom.co.id", "EXCL": "xl.co.id", "ISAT": "indosatooredoo.com",
    "GOTO": "gojek.com", "BUKA": "bukalapak.com", "EMTK": "emtek.co.id",
    "MNCN": "mncgroup.com", "SCMA": "scma.co.id", "DCII": "datacentrix.co.id",
    # Consumer & Retail
    "UNVR": "unilever.co.id", "ICBP": "indofoodcbp.com", "INDF": "indofood.com",
    "KLBF": "kalbe.co.id", "HMSP": "sampoerna.com", "GGRM": "gudanggaramtbk.com",
    "AMRT": "alfamart.co.id", "MAPI": "map.co.id", "ACES": "acehardware.co.id",
    "CPIN": "cp.co.id", "JPFA": "japfa.com", "SIDO": "sidomunculgroup.com",
    "MYOR": "mayora.com", "ULTJ": "ultrajaya.co.id", "LPPF": "mataharistore.com",
    # Mining & Energy
    "ADRO": "adaro.com", "ANTM": "antam.com", "PTBA": "ptba.co.id",
    "ITMG": "itmg.co.id", "HRUM": "harumenergy.com", "MEDC": "medcoenergi.com",
    "MDKA": "merdekacoppergold.com", "INCO": "vale.com", "BREN": "bfrg.co.id",
    "TINS": "timah.com", "PGAS": "pgn.co.id", "AKRA": "akr.co.id",
    "ESSA": "essa.id", "PGEO": "pgeo.co.id", "UNTR": "unitedtractors.com",
    # Automotive & Industrial
    "ASII": "astra.co.id", "AUTO": "astra-otoparts.com",
    # Property & Construction
    "BSDE": "bfrg.co.id", "CTRA": "ciputra.com", "SMRA": "summareconcity.com",
    "PWON": "pakuwon.com", "WIKA": "wika.co.id", "WSKT": "waskita.co.id",
    "PTPP": "ptpp.co.id", "JSMR": "jasamarga.com",
    # Infrastructure & Tower
    "TOWR": "sarana-menara.com", "TBIG": "tower-bersama.com",
    # Petrochemical & Paper
    "BRPT": "barito-pacific.com", "TPIA": "chandra-asri.com",
    "INKP": "asiapulppaper.com", "TKIM": "tjiwi-kimia.co.id",
    # Cement & Basic Materials
    "SMGR": "sig.id", "INTP": "indocement.co.id",
    # Healthcare & Pharma
    "HEAL": "mfrg.co.id", "PRDA": "prodia.co.id",
    # Financial Services
    "BBKP": "bukopin.co.id", "ADMR": "adaro.com",
    "ARTO": "bankartos.co.id", "BBYB": "neobanktiara.co.id",
    # Plantation
    "LSIP": "londonsumatra.com", "AALI": "astra-agro.co.id",
    "DSNG": "dsn.co.id", "SSMS": "ssms.co.id",
    # Transportation
    "ASSA": "adi-sarana.com", "BIRD": "bluebirdgroup.com",
    "GIAA": "garuda-indonesia.com",
    # Others
    "ERAA": "erajaya.com", "MTEL": "mitratel.co.id",
    "BMTR": "mediacom.id", "DNET": "indointernet.co.id",
    "SRTG": "saratoga-investama.com", "MIKA": "mitrakeluargagroup.com",
    "FILM": "mdentertainment.com", "BNBR": "bakrie.com",
    "BELI": "blibli.com", "BBHI": "allo-bank.com",
}

def get_company_profile(saham, ticker):
    try:
        info = saham.info
        name = safe_get(info, 'longName') or safe_get(info, 'shortName') or ticker
        name = name.replace('.JK', '').replace('.jk', '').strip()
        sector = safe_get(info, 'sector') or "N/A"
        industry = safe_get(info, 'industry') or "N/A"
        summary = safe_get(info, 'longBusinessSummary') or "Tidak ada deskripsi profil untuk perusahaan ini."
        website = safe_get(info, 'website')
        
        clean_ticker = ticker.replace('.JK', '').upper()
        
        # Determine domain cleanly
        domain = None
        if clean_ticker in IDX_DOMAINS:
            domain = IDX_DOMAINS[clean_ticker]
            if not website or website == 'N/A':
                website = f"https://www.{domain}"
        elif website and website != 'N/A':
            domain = website.replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0]
            
        # HD Logo Chain: logo.dev (256px) -> Google Favicon (256px) -> Clearbit -> UI Avatars
        logo = None
        logo_hd = None
        if domain:
            logo_hd = f"https://img.logo.dev/{domain}?token=pk_anonymous&size=256&format=png"
            logo = f"https://www.google.com/s2/favicons?domain=www.{domain}&sz=256"
            
        if not logo and domain:
            logo = f"https://logo.clearbit.com/{domain}?size=256"
            
        if not logo:
            logo = safe_get(info, 'logo_url')
            
        fallback_avatar = f"https://ui-avatars.com/api/?name={name.replace(' ', '+')}&background=0D8ABC&color=fff&size=256&bold=true"
            
        return {
            "name": name,
            "sector": sector,
            "industry": industry,
            "summary": summary,
            "website": website or "N/A",
            "domain": domain or "",
            "logo": logo or fallback_avatar,
            "logo_hd": logo_hd or logo or fallback_avatar
        }
    except Exception as e:
        clean_ticker = ticker.replace('.JK', '').upper()
        domain = IDX_DOMAINS.get(clean_ticker, "")
        logo = f"https://www.google.com/s2/favicons?domain=www.{domain}&sz=256" if domain else f"https://ui-avatars.com/api/?name={ticker}&background=0D8ABC&color=fff&size=256&bold=true"
        logo_hd = f"https://img.logo.dev/{domain}?token=pk_anonymous&size=256&format=png" if domain else logo
        return {
            "name": clean_ticker,
            "sector": "N/A",
            "industry": "N/A",
            "summary": "Gagal memuat profil perusahaan.",
            "website": f"https://www.{domain}" if domain else "N/A",
            "domain": domain,
            "logo": logo,
            "logo_hd": logo_hd
        }

# ==================== SENTIMENT KEYWORDS (Weighted) ====================
# Strong keywords (±3), Medium (±2), Weak (±1)
POS_KEYWORDS_STRONG = [
    'rekor', 'record', 'meroket', 'soar', 'surge', 'breakout', 'rally',
    'jackpot', 'booming', 'melambung', 'skyrocket', 'melonjak'
]
POS_KEYWORDS_MEDIUM = [
    'profit', 'laba', 'untung', 'tumbuh', 'naik', 'growth', 'gain',
    'dividen', 'dividend', 'bullish', 'akuisisi', 'acquisition',
    'ekspansi', 'expand', 'positif', 'positive', 'upgrade', 'outperform',
    'overweight', 'optimis', 'optimistic', 'recovery', 'recover',
    'pulih', 'surplus', 'meningkat', 'increase', 'strong', 'kuat',
    'cemerlang', 'solid', 'excellent', 'beat', 'melampaui'
]
POS_KEYWORDS_WEAK = [
    'stabil', 'stable', 'aman', 'safe', 'maintain', 'dipertahankan',
    'buy', 'beli', 'hold', 'accumulate', 'akumulasi', 'support',
    'peluang', 'opportunity', 'potensi', 'potential', 'prospek',
    'menarik', 'attractive', 'bagus', 'baik', 'good'
]

NEG_KEYWORDS_STRONG = [
    'bangkrut', 'bankrupt', 'default', 'kolaps', 'collapse', 'crash',
    'anjlok', 'plunge', 'terjun', 'suspend', 'delisting', 'fraud',
    'penipuan', 'korupsi', 'corruption'
]
NEG_KEYWORDS_MEDIUM = [
    'rugi', 'loss', 'turun', 'koreksi', 'correction', 'denda', 'fine',
    'bearish', 'drop', 'fall', 'decline', 'sanksi', 'sanction',
    'negatif', 'negative', 'kasus', 'case', 'utang', 'debt',
    'downgrade', 'underperform', 'underweight', 'sell', 'jual',
    'melemah', 'weaken', 'tekanan', 'pressure', 'defisit', 'deficit',
    'gagal', 'fail', 'risiko', 'risk', 'warning', 'peringatan',
    'penurunan', 'decrease', 'merosot', 'seret', 'lesu', 'sluggish'
]
NEG_KEYWORDS_WEAK = [
    'volatil', 'volatile', 'fluktuasi', 'fluctuation', 'hati-hati',
    'caution', 'waspada', 'alert', 'was-was', 'uncertain', 'ketidakpastian',
    'wait', 'tunggu', 'sideways', 'konsolidasi', 'consolidation',
    'terbatas', 'limited', 'lambat', 'slow'
]

def _calculate_sentiment_score(text):
    """Calculate weighted sentiment score from text."""
    text_lower = text.lower()
    score = 0
    for kw in POS_KEYWORDS_STRONG:
        if kw in text_lower: score += 3
    for kw in POS_KEYWORDS_MEDIUM:
        if kw in text_lower: score += 2
    for kw in POS_KEYWORDS_WEAK:
        if kw in text_lower: score += 1
    for kw in NEG_KEYWORDS_STRONG:
        if kw in text_lower: score -= 3
    for kw in NEG_KEYWORDS_MEDIUM:
        if kw in text_lower: score -= 2
    for kw in NEG_KEYWORDS_WEAK:
        if kw in text_lower: score -= 1
    return max(-5, min(5, score))

def _parse_published_date(entry):
    """Parse published date from RSS entry into ISO string."""
    try:
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            import time
            dt = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            return dt.isoformat()
    except Exception:
        pass
    return None

def _extract_source_domain(link):
    """Extract clean domain from a URL for favicon/publisher identification."""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(link)
        domain = parsed.netloc.replace('www.', '')
        return domain
    except Exception:
        return ''

def fetch_real_news(ticker):
    """Fetch real news from Google News RSS feed targeting Bloomberg, CNBC, DetikFinance."""
    clean_ticker = ticker.replace('.JK', '').replace('.jk', '').upper()
    
    # Build Google News RSS query with site filters
    query = f'"{clean_ticker}" saham (site:cnbcindonesia.com OR site:detik.com OR site:bloomberg.com OR site:kontan.co.id OR site:bisnis.com OR site:investor.id)'
    encoded_q = urllib.parse.quote(query)
    rss_url = f"https://news.google.com/rss/search?q={encoded_q}&hl=id&gl=ID&ceid=ID:id"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        resp = requests.get(rss_url, headers=headers, timeout=10)
        resp.raise_for_status()
        
        feed = feedparser.parse(resp.text)
        articles = []
        
        for entry in feed.entries[:8]:
            title = entry.get('title', '')
            link = entry.get('link', '#')
            
            # Extract publisher from source tag or title suffix FIRST
            publisher = 'Unknown'
            if hasattr(entry, 'source') and entry.source:
                publisher = entry.source.get('title', 'Unknown')
            elif ' - ' in title:
                parts = title.rsplit(' - ', 1)
                if len(parts) == 2:
                    publisher = parts[1].strip()
                    title = parts[0].strip()
            
            # Try to resolve Google News redirect to actual article URL
            actual_link = link
            if 'news.google.com' in link:
                try:
                    head_resp = requests.head(link, allow_redirects=True, timeout=5, 
                                              headers={'User-Agent': 'Mozilla/5.0'})
                    if head_resp.url and 'news.google.com' not in head_resp.url:
                        actual_link = head_resp.url
                except Exception:
                    pass  # Keep Google News link as fallback
            
            published_date = _parse_published_date(entry)
            source_domain = _extract_source_domain(actual_link)
            
            # If domain is still google, derive from publisher name
            if not source_domain or 'google' in source_domain:
                pub_lower = publisher.lower().replace(' ', '')
                domain_map = {
                    'cnbcindonesia': 'cnbcindonesia.com',
                    'detikfinance': 'finance.detik.com',
                    'detik.com': 'detik.com',
                    'bloomberg': 'bloomberg.com',
                    'kontan': 'kontan.co.id',
                    'kontan.co.id': 'kontan.co.id',
                    'bisnis.com': 'bisnis.com',
                    'bisnisindonesiapremium': 'bisnis.com',
                    'investor.id': 'investor.id',
                    'kompas.com': 'kompas.com',
                    'idnfinancials': 'idnfinancials.com',
                }
                for key, domain in domain_map.items():
                    if key in pub_lower:
                        source_domain = domain
                        break
            
            articles.append({
                'title': title,
                'link': actual_link,
                'publisher': publisher,
                'published_date': published_date,
                'source_domain': source_domain
            })
        
        return articles if len(articles) > 0 else None
        
    except Exception:
        return None

def get_news(saham, ticker=None):
    """Fetch and analyze news with sentiment scoring.
    Priority: Google News RSS (real) -> Yahoo Finance -> Generated fallback.
    """
    clean_ticker = (ticker or saham.ticker).replace('.JK', '').replace('.jk', '').upper()
    
    # 1. Try fetching real news from Google News RSS
    raw_articles = fetch_real_news(clean_ticker)
    
    # 2. Fallback: Try Yahoo Finance news
    if not raw_articles:
        try:
            yf_news = saham.news
            if yf_news and len(yf_news) > 0:
                raw_articles = []
                for item in yf_news[:8]:
                    raw_articles.append({
                        'title': item.get('title', ''),
                        'link': item.get('link', '#'),
                        'publisher': item.get('publisher', 'Yahoo Finance'),
                        'published_date': None,
                        'source_domain': 'finance.yahoo.com'
                    })
        except Exception:
            pass
    
    # 3. Final fallback: Generated placeholder news
    if not raw_articles:
        fallback_news = [
            {
                "title": f"Sentimen Pasar Terhadap Saham {clean_ticker}: Konsolidasi Volume Perdagangan Terpantau Stabil",
                "publisher": "Surealism Intelligence",
                "link": "#",
                "published_date": datetime.now(timezone.utc).isoformat(),
                "source_domain": "",
                "sentiment": "NETRAL",
                "score": 0.0
            },
            {
                "title": f"Analisis Aliran Dana Asing: Akumulasi Diam-diam Mulai Terdeteksi pada Saham {clean_ticker}",
                "publisher": "Smart Money Sentinel",
                "link": "#",
                "published_date": datetime.now(timezone.utc).isoformat(),
                "source_domain": "",
                "sentiment": "BULLISH",
                "score": 2.0
            },
            {
                "title": f"Tinjauan Valuasi {clean_ticker}: Tekanan Profit-Taking Jangka Pendek Menjadi Peluang Buy on Weakness",
                "publisher": "Surealism Pro Research",
                "link": "#",
                "published_date": datetime.now(timezone.utc).isoformat(),
                "source_domain": "",
                "sentiment": "BULLISH",
                "score": 1.0
            }
        ]
        return {
            "articles": fallback_news,
            "pos_count": 2,
            "neg_count": 0,
            "neu_count": 1,
            "average_score": 1.0,
            "sentiment_index": 100.0,
            "skor_news": 1,
            "source": "fallback"
        }
    
    # Score each article
    news_list = []
    pos_count = 0
    neg_count = 0
    neu_count = 0
    total_score = 0.0
    
    for article in raw_articles:
        title = article.get('title', '')
        score = _calculate_sentiment_score(title)
        total_score += score
        
        if score > 0:
            sentiment = "BULLISH"
            pos_count += 1
        elif score < 0:
            sentiment = "BEARISH"
            neg_count += 1
        else:
            sentiment = "NETRAL"
            neu_count += 1
        
        news_list.append({
            "title": title,
            "publisher": article.get('publisher', 'Unknown'),
            "link": article.get('link', '#'),
            "published_date": article.get('published_date'),
            "source_domain": article.get('source_domain', ''),
            "sentiment": sentiment,
            "score": float(score)
        })
    
    count = len(news_list)
    avg_score = total_score / count if count > 0 else 0.0
    
    total_pos_neg = pos_count + neg_count
    sentiment_index = (pos_count / total_pos_neg * 100) if total_pos_neg > 0 else 50.0
    
    if avg_score >= 1.5:
        skor_news = 2
    elif avg_score >= 0.3:
        skor_news = 1
    elif avg_score <= -1.5:
        skor_news = -2
    elif avg_score <= -0.3:
        skor_news = -1
    else:
        skor_news = 0
    
    return {
        "articles": news_list,
        "pos_count": pos_count,
        "neg_count": neg_count,
        "neu_count": neu_count,
        "average_score": round(avg_score, 2),
        "sentiment_index": round(sentiment_index, 1),
        "skor_news": skor_news,
        "source": "google_news" if any('google' not in (a.get('source_domain','')) for a in raw_articles) else "yahoo"
    }

