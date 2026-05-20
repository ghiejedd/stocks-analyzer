import yfinance as yf
import pandas as pd
import warnings

warnings.filterwarnings('ignore')

# ============================================================
#  BAGIAN 1: ANALISA FUNDAMENTAL
# ============================================================
def get_fundamental(saham, kode):
    """Menarik data Laporan Keuangan lengkap dan mendalam"""
    try:
        info = saham.info
        print("\n" + "=" * 60)
        print(f"  ANALISA FUNDAMENTAL MENDALAM - {kode}")
        print("=" * 60)

        # --- VALUASI ---
        per = info.get('trailingPE', None)
        fwd_pe = info.get('forwardPE', None)
        pbv = info.get('priceToBook', None)
        ps = info.get('priceToSalesTrailing12Months', None)
        ev_ebitda = info.get('enterpriseToEbitda', None)
        ev_rev = info.get('enterpriseToRevenue', None)
        peg = info.get('pegRatio', None)

        print("\n-- Valuasi --")
        print(f"  P/E Ratio (TTM)     : {f'{per:.2f}x' if per else 'N/A'}")
        print(f"  Forward P/E         : {f'{fwd_pe:.2f}x' if fwd_pe else 'N/A'}")
        print(f"  PEG Ratio           : {f'{peg:.2f}' if peg else 'N/A'}")
        print(f"  Price to Book (PBV) : {f'{pbv:.2f}x' if pbv else 'N/A'}")
        print(f"  Price to Sales      : {f'{ps:.2f}x' if ps else 'N/A'}")
        print(f"  EV/EBITDA           : {f'{ev_ebitda:.2f}x' if ev_ebitda else 'N/A'}")
        print(f"  EV/Revenue          : {f'{ev_rev:.2f}x' if ev_rev else 'N/A'}")

        # --- PROFITABILITAS ---
        roe = info.get('returnOnEquity', None)
        roa = info.get('returnOnAssets', None)
        npm = info.get('profitMargins', None)
        opm = info.get('operatingMargins', None)
        gpm = info.get('grossMargins', None)
        ebitda_margin = info.get('ebitdaMargins', None)

        print("\n-- Profitabilitas --")
        print(f"  ROE                 : {f'{roe*100:.2f}%' if roe else 'N/A'}")
        print(f"  ROA                 : {f'{roa*100:.2f}%' if roa else 'N/A'}")
        print(f"  Gross Margin        : {f'{gpm*100:.2f}%' if gpm else 'N/A'}")
        print(f"  EBITDA Margin       : {f'{ebitda_margin*100:.2f}%' if ebitda_margin else 'N/A'}")
        print(f"  Operating Margin    : {f'{opm*100:.2f}%' if opm else 'N/A'}")
        print(f"  Net Profit Margin   : {f'{npm*100:.2f}%' if npm else 'N/A'}")

        # --- LAPORAN KEUANGAN ---
        rev = info.get('totalRevenue', None)
        ni = info.get('netIncomeToCommon', None)
        ebitda = info.get('ebitda', None)
        eps = info.get('trailingEps', None)
        fwd_eps = info.get('forwardEps', None)
        der = info.get('debtToEquity', None)
        cr = info.get('currentRatio', None)
        qr = info.get('quickRatio', None)
        td = info.get('totalDebt', None)
        tc = info.get('totalCash', None)
        fcf = info.get('freeCashflow', None)
        ocf = info.get('operatingCashflow', None)
        bv = info.get('bookValue', None)

        print("\n-- Laporan Keuangan --")
        print(f"  Revenue             : {format_rupiah(rev)}")
        print(f"  EBITDA              : {format_rupiah(ebitda)}")
        print(f"  Net Income          : {format_rupiah(ni)}")
        print(f"  EPS (TTM)           : {f'Rp {eps:,.0f}' if eps else 'N/A'}")
        print(f"  EPS (Forward)       : {f'Rp {fwd_eps:,.0f}' if fwd_eps else 'N/A'}")
        print(f"  Book Value/Share    : {f'Rp {bv:,.0f}' if bv else 'N/A'}")

        print("\n-- Neraca & Arus Kas --")
        print(f"  Total Debt          : {format_rupiah(td)}")
        print(f"  Total Cash          : {format_rupiah(tc)}")
        print(f"  Operating Cash Flow : {format_rupiah(ocf)}")
        print(f"  Free Cash Flow      : {format_rupiah(fcf)}")
        print(f"  Debt to Equity (DER): {f'{der:.2f}%' if der else 'N/A'}")
        print(f"  Current Ratio       : {f'{cr:.2f}x' if cr else 'N/A'}")
        print(f"  Quick Ratio         : {f'{qr:.2f}x' if qr else 'N/A'}")

        # --- PERTUMBUHAN ---
        rev_growth = info.get('revenueGrowth', None)
        earn_growth = info.get('earningsGrowth', None)
        earn_qg = info.get('earningsQuarterlyGrowth', None)
        rev_qg = info.get('revenueQuarterlyGrowth', None)

        print("\n-- Pertumbuhan --")
        print(f"  Revenue Growth (YoY)    : {f'{rev_growth*100:.2f}%' if rev_growth else 'N/A'}")
        print(f"  Earnings Growth (YoY)   : {f'{earn_growth*100:.2f}%' if earn_growth else 'N/A'}")
        print(f"  Revenue Growth (QoQ)    : {f'{rev_qg*100:.2f}%' if rev_qg else 'N/A'}")
        print(f"  Earnings Growth (QoQ)   : {f'{earn_qg*100:.2f}%' if earn_qg else 'N/A'}")

        # --- DIVIDEN & MARKET ---
        dy = info.get('dividendYield', None)
        dps = info.get('dividendRate', None)
        payout = info.get('payoutRatio', None)
        mcap = info.get('marketCap', None)
        ev = info.get('enterpriseValue', None)
        beta = info.get('beta', None)
        avg_vol = info.get('averageVolume', None)
        hi52 = info.get('fiftyTwoWeekHigh', None)
        lo52 = info.get('fiftyTwoWeekLow', None)
        price = info.get('currentPrice', None) or info.get('regularMarketPrice', None)

        print("\n-- Dividen --")
        print(f"  Dividen/Share       : {f'Rp {dps:,.0f}' if dps else 'N/A'}")
        print(f"  Dividen Yield       : {f'{dy*100:.2f}%' if dy else 'N/A'}")
        print(f"  Payout Ratio        : {f'{payout*100:.2f}%' if payout else 'N/A'}")

        print("\n-- Market Info --")
        print(f"  Market Cap          : {format_rupiah(mcap)}")
        print(f"  Enterprise Value    : {format_rupiah(ev)}")
        print(f"  Beta                : {f'{beta:.2f}' if beta else 'N/A'}")
        print(f"  Avg Volume          : {f'{avg_vol:,.0f}' if avg_vol else 'N/A'}")
        if hi52 and lo52:
            print(f"  52-Week High        : Rp {hi52:,.0f}")
            print(f"  52-Week Low         : Rp {lo52:,.0f}")
            if price:
                pct_from_hi = ((price - hi52) / hi52) * 100
                pct_from_lo = ((price - lo52) / lo52) * 100
                print(f"  Dari 52W High       : {pct_from_hi:+.2f}%")
                print(f"  Dari 52W Low        : {pct_from_lo:+.2f}%")

        # --- SKOR FUNDAMENTAL (12 kriteria) ---
        skor = 0
        alasan = []
        # Valuasi
        if per and per < 15: skor += 1; alasan.append("PER murah (<15x)")
        elif per and per > 25: skor -= 1; alasan.append("PER mahal (>25x)")
        if fwd_pe and fwd_pe < per if per else False: skor += 1; alasan.append("Forward PE < TTM PE (earnings naik)")
        if pbv and pbv < 1.5: skor += 1; alasan.append("PBV murah (<1.5x)")
        elif pbv and pbv > 5: skor -= 1; alasan.append("PBV mahal (>5x)")
        if peg and peg < 1: skor += 1; alasan.append("PEG < 1 (undervalued vs growth)")
        elif peg and peg > 2: skor -= 1; alasan.append("PEG > 2 (overvalued vs growth)")
        # Profitabilitas
        if roe and roe > 0.15: skor += 1; alasan.append("ROE bagus (>15%)")
        elif roe and roe < 0.05: skor -= 1; alasan.append("ROE rendah (<5%)")
        if npm and npm > 0.10: skor += 1; alasan.append("NPM sehat (>10%)")
        # Kesehatan Neraca
        if der and der < 100: skor += 1; alasan.append("DER aman (<100%)")
        elif der and der > 200: skor -= 1; alasan.append("DER tinggi (>200%)")
        if cr and cr > 1.5: skor += 1; alasan.append("Current Ratio kuat (>1.5x)")
        elif cr and cr < 1: skor -= 1; alasan.append("Current Ratio lemah (<1x)")
        if fcf and fcf > 0: skor += 1; alasan.append("Free Cash Flow positif")
        elif fcf and fcf < 0: skor -= 1; alasan.append("Free Cash Flow negatif")
        # Pertumbuhan
        if rev_growth and rev_growth > 0.10: skor += 1; alasan.append(f"Revenue tumbuh {rev_growth*100:.1f}%")
        elif rev_growth and rev_growth < -0.05: skor -= 1; alasan.append(f"Revenue turun {rev_growth*100:.1f}%")
        if earn_growth and earn_growth > 0.10: skor += 1; alasan.append(f"Earnings tumbuh {earn_growth*100:.1f}%")
        elif earn_growth and earn_growth < -0.10: skor -= 1; alasan.append(f"Earnings turun {earn_growth*100:.1f}%")
        # Dividen
        if dy and dy > 0.03: skor += 1; alasan.append("Dividen menarik (>3%)")

        return skor, alasan, info
    except Exception:
        print("[!] Gagal mengambil data Fundamental.")
        return 0, [], {}

def get_teknikal(data, kode):
    """Perhitungan teknikal mendalam: MA, EMA, MACD, RSI, StochRSI, BB, ADX, W%R, ATR, Ichimoku, Orderbook Flow"""
    print("\n" + "=" * 60)
    print(f"  ANALISA TEKNIKAL MENDALAM - {kode}")
    print("=" * 60)

    # --- Moving Average ---
    data['MA7'] = data['Close'].rolling(window=7).mean()
    data['MA20'] = data['Close'].rolling(window=20).mean()
    data['MA50'] = data['Close'].rolling(window=50).mean()
    data['EMA9'] = data['Close'].ewm(span=9, adjust=False).mean()
    data['EMA12'] = data['Close'].ewm(span=12, adjust=False).mean()
    data['EMA26'] = data['Close'].ewm(span=26, adjust=False).mean()

    # --- MACD ---
    data['MACD'] = data['EMA12'] - data['EMA26']
    data['Signal'] = data['MACD'].ewm(span=9, adjust=False).mean()
    data['MACD_Hist'] = data['MACD'] - data['Signal']

    # --- RSI ---
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    data['RSI'] = 100 - (100 / (1 + rs))

    # --- Stochastic RSI ---
    min_rsi = data['RSI'].rolling(window=14).min()
    max_rsi = data['RSI'].rolling(window=14).max()
    data['StochRSI'] = (data['RSI'] - min_rsi) / (max_rsi - min_rsi) * 100

    # --- Bollinger Bands ---
    data['BB_Mid'] = data['Close'].rolling(window=20).mean()
    bb_std = data['Close'].rolling(window=20).std()
    data['BB_Upper'] = data['BB_Mid'] + (bb_std * 2)
    data['BB_Lower'] = data['BB_Mid'] - (bb_std * 2)
    data['BB_Width'] = (data['BB_Upper'] - data['BB_Lower']) / data['BB_Mid'] * 100

    # --- ADX (Average Directional Index) - kekuatan tren ---
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

    # --- Williams %R ---
    high14 = data['High'].rolling(14).max()
    low14 = data['Low'].rolling(14).min()
    data['Williams_R'] = -100 * (high14 - data['Close']) / (high14 - low14)

    # --- ATR (Average True Range) - volatilitas ---
    data['ATR'] = atr14

    # --- Volume Analysis ---
    data['Vol_MA20'] = data['Volume'].rolling(window=20).mean()

    hari_ini = data.iloc[-1]
    kemarin = data.iloc[-2] if len(data) > 1 else hari_ini

    harga = hari_ini['Close']
    change = ((harga - kemarin['Close']) / kemarin['Close']) * 100

    print(f"\n-- Harga --")
    print(f"  Harga Terakhir : Rp {harga:,.0f} ({'+' if change >= 0 else ''}{change:.2f}%)")
    print(f"  Open           : Rp {hari_ini['Open']:,.0f}")
    print(f"  High           : Rp {hari_ini['High']:,.0f}")
    print(f"  Low            : Rp {hari_ini['Low']:,.0f}")

    print(f"\n-- Moving Average & Crossover --")
    for ma_name in ['MA7', 'MA20', 'MA50']:
        val = hari_ini[ma_name]
        if not pd.isna(val):
            pos = "DI ATAS" if harga > val else "DI BAWAH"
            print(f"  {ma_name:6s} : Rp {val:,.0f} (Harga {pos} {ma_name})")
    # Deteksi Golden Cross / Death Cross
    ma20_now = hari_ini['MA20']; ma50_now = hari_ini['MA50']
    ma20_prev = kemarin['MA20'] if 'MA20' in kemarin.index else None
    ma50_prev = kemarin['MA50'] if 'MA50' in kemarin.index else None
    if not pd.isna(ma20_now) and not pd.isna(ma50_now) and ma20_prev and not pd.isna(ma20_prev) and ma50_prev and not pd.isna(ma50_prev):
        if ma20_prev <= ma50_prev and ma20_now > ma50_now:
            print(f"  ** GOLDEN CROSS TERDETEKSI! (MA20 menembus MA50 ke atas - Sinyal Bullish Kuat) **")
        elif ma20_prev >= ma50_prev and ma20_now < ma50_now:
            print(f"  ** DEATH CROSS TERDETEKSI! (MA20 menembus MA50 ke bawah - Sinyal Bearish Kuat) **")

    print(f"\n-- MACD --")
    macd_val = hari_ini['MACD']; sig_val = hari_ini['Signal']; hist_val = hari_ini['MACD_Hist']
    macd_prev = kemarin['MACD_Hist'] if 'MACD_Hist' in kemarin.index else None
    if not pd.isna(macd_val):
        sinyal_macd = "BULLISH (Buy Signal)" if macd_val > sig_val else "BEARISH (Sell Signal)"
        print(f"  MACD Line   : {macd_val:.2f}")
        print(f"  Signal Line : {sig_val:.2f}")
        print(f"  Histogram   : {hist_val:.2f} -> {sinyal_macd}")
        if macd_prev and not pd.isna(macd_prev):
            if macd_prev < 0 and hist_val > 0:
                print(f"  ** MACD CROSSOVER BULLISH (Histogram baru saja berubah positif) **")
            elif macd_prev > 0 and hist_val < 0:
                print(f"  ** MACD CROSSOVER BEARISH (Histogram baru saja berubah negatif) **")

    print(f"\n-- RSI & Stochastic RSI --")
    rsi_val = hari_ini['RSI']; stoch_val = hari_ini['StochRSI']
    if not pd.isna(rsi_val):
        rsi_status = "OVERSOLD" if rsi_val < 30 else ("OVERBOUGHT" if rsi_val > 70 else "NETRAL")
        print(f"  RSI (14)     : {rsi_val:.2f} -> {rsi_status}")
    if not pd.isna(stoch_val):
        stoch_status = "OVERSOLD" if stoch_val < 20 else ("OVERBOUGHT" if stoch_val > 80 else "NETRAL")
        print(f"  StochRSI     : {stoch_val:.2f} -> {stoch_status}")

    # ADX
    adx_val = hari_ini['ADX']; pdi = hari_ini['Plus_DI']; mdi = hari_ini['Minus_DI']
    print(f"\n-- ADX (Kekuatan Tren) --")
    if not pd.isna(adx_val):
        if adx_val > 25:
            adx_str = "TREN KUAT" + (" NAIK (+DI > -DI)" if pdi > mdi else " TURUN (-DI > +DI)")
        else:
            adx_str = "TREN LEMAH / SIDEWAYS"
        print(f"  ADX          : {adx_val:.2f} -> {adx_str}")
        print(f"  +DI / -DI    : {pdi:.2f} / {mdi:.2f}")

    # Williams %R
    wr = hari_ini['Williams_R']
    print(f"\n-- Williams %R --")
    if not pd.isna(wr):
        if wr > -20: wr_status = "OVERBOUGHT (Jenuh beli)"
        elif wr < -80: wr_status = "OVERSOLD (Jenuh jual)"
        else: wr_status = "NETRAL"
        print(f"  Williams %R  : {wr:.2f} -> {wr_status}")

    # Bollinger Bands
    bb_u = hari_ini['BB_Upper']; bb_l = hari_ini['BB_Lower']; bb_m = hari_ini['BB_Mid']
    bb_w = hari_ini['BB_Width']
    print(f"\n-- Bollinger Bands --")
    if not pd.isna(bb_u):
        if harga >= bb_u: bb_pos = "DEKAT UPPER BAND (Rawan koreksi turun)"
        elif harga <= bb_l: bb_pos = "DEKAT LOWER BAND (Peluang mantul naik)"
        else: bb_pos = "DI TENGAH BAND (Normal)"
        print(f"  Upper Band : Rp {bb_u:,.0f}")
        print(f"  Middle     : Rp {bb_m:,.0f}")
        print(f"  Lower Band : Rp {bb_l:,.0f}")
        print(f"  Posisi     : {bb_pos}")
        if not pd.isna(bb_w):
            squeeze = "BB SQUEEZE (Volatilitas rendah - siap breakout!)" if bb_w < 5 else ("Volatilitas tinggi" if bb_w > 15 else "Normal")
            print(f"  BB Width   : {bb_w:.2f}% -> {squeeze}")

    # ATR
    atr_val = hari_ini['ATR']
    print(f"\n-- ATR (Volatilitas) --")
    if not pd.isna(atr_val):
        atr_pct = (atr_val / harga) * 100
        print(f"  ATR (14)     : Rp {atr_val:,.0f} ({atr_pct:.2f}% dari harga)")

    # Volume
    vol = hari_ini['Volume']; vol_ma = hari_ini['Vol_MA20']
    print(f"\n-- Volume --")
    if not pd.isna(vol_ma) and vol_ma > 0:
        vol_ratio = vol / vol_ma
        vol_status = "TINGGI (Minat besar)" if vol_ratio > 1.5 else ("RENDAH" if vol_ratio < 0.5 else "NORMAL")
        print(f"  Volume Hari Ini  : {vol:,.0f}")
        print(f"  Rata-rata 20 Hari: {vol_ma:,.0f}")
        print(f"  Rasio Volume     : {vol_ratio:.2f}x -> {vol_status}")

    # --- Candlestick Pattern Detection ---
    print(f"\n-- Deteksi Pola Candlestick --")
    o, h, l, c = hari_ini['Open'], hari_ini['High'], hari_ini['Low'], hari_ini['Close']
    body = abs(c - o)
    upper_shadow = h - max(o, c)
    lower_shadow = min(o, c) - l
    total_range = h - l if h != l else 1
    patterns = []
    if body < total_range * 0.1 and lower_shadow > body * 2:
        patterns.append("HAMMER / DRAGONFLY DOJI (Potensi reversal naik)")
    if body < total_range * 0.1 and upper_shadow > body * 2:
        patterns.append("SHOOTING STAR (Potensi reversal turun)")
    if body < total_range * 0.05:
        patterns.append("DOJI (Pasar ragu-ragu, potensi reversal)")
    if c > o and body > total_range * 0.6:
        patterns.append("BULLISH MARUBOZU (Tekanan beli kuat)")
    if c < o and body > total_range * 0.6:
        patterns.append("BEARISH MARUBOZU (Tekanan jual kuat)")
    if len(data) >= 3:
        d2 = data.iloc[-2]; d3 = data.iloc[-3]
        if d3['Close'] < d3['Open'] and d2['Close'] < d2['Open'] and c > o and c > d3['Open']:
            patterns.append("MORNING STAR (Sinyal reversal bullish kuat)")
        if d3['Close'] > d3['Open'] and d2['Close'] > d2['Open'] and c < o and c < d3['Open']:
            patterns.append("EVENING STAR (Sinyal reversal bearish kuat)")
    if patterns:
        for p in patterns: print(f"  -> {p}")
    else:
        print(f"  Tidak ada pola candlestick signifikan terdeteksi.")

    # --- Orderbook Flow Estimation ---
    print(f"\n-- Estimasi Orderbook Flow (Tekanan Jual/Beli Intraday) --")
    buy_pressure = (c - l) / total_range * 100 if total_range > 0 else 50
    sell_pressure = (h - c) / total_range * 100 if total_range > 0 else 50
    print(f"  Tekanan Beli  : {buy_pressure:.1f}%")
    print(f"  Tekanan Jual  : {sell_pressure:.1f}%")

    # Deteksi dump/pump besar dari data beberapa hari terakhir
    dump_alerts = []
    for i in range(-min(5, len(data)), 0):
        row = data.iloc[i]
        day_change = ((row['Close'] - row['Open']) / row['Open']) * 100 if row['Open'] > 0 else 0
        day_vol_ratio = row['Volume'] / vol_ma if not pd.isna(vol_ma) and vol_ma > 0 else 1
        if day_change < -3 and day_vol_ratio > 1.5:
            dump_alerts.append((data.index[i].strftime('%Y-%m-%d'), day_change, day_vol_ratio))
        elif day_change > 3 and day_vol_ratio > 1.5:
            dump_alerts.append((data.index[i].strftime('%Y-%m-%d'), day_change, day_vol_ratio))
    if dump_alerts:
        print(f"\n  [!] ALERT - Pergerakan Besar Terdeteksi:")
        for dt, chg, vr in dump_alerts:
            tipe = "SELL-OFF BESAR" if chg < 0 else "PUMP BESAR"
            print(f"      {dt}: {chg:+.2f}% dengan volume {vr:.1f}x rata-rata -> {tipe}")
    else:
        print(f"  Tidak ada sell-off/pump besar terdeteksi dalam 5 hari terakhir.")

    if buy_pressure > 65:
        print(f"  Kesimpulan   : BUYER DOMINAN (Tekanan beli besar)")
    elif sell_pressure > 65:
        print(f"  Kesimpulan   : SELLER DOMINAN (Tekanan jual besar)")
    else:
        print(f"  Kesimpulan   : SEIMBANG")

    # --- SKOR TEKNIKAL (12 kriteria) ---
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

    return skor, alasan, data

# ============================================================
#  BAGIAN 3: SUPPORT & RESISTANCE
# ============================================================
def get_support_resistance(data, kode):
    """Menghitung level Support dan Resistance multi-level"""
    print("\n" + "=" * 55)
    print(f"  SUPPORT & RESISTANCE - {kode}")
    print("=" * 55)

    hari_ini = data.iloc[-1]
    harga = hari_ini['Close']

    # Pivot Point klasik (dari data hari terakhir)
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

    # MA-based support/resistance
    ma20 = hari_ini.get('MA20', None)
    ma50 = hari_ini.get('MA50', None)

    print(f"\n-- Pivot Point Classic --")
    print(f"  Resistance 3 (R3) : Rp {r3:,.0f}")
    print(f"  Resistance 2 (R2) : Rp {r2:,.0f}")
    print(f"  Resistance 1 (R1) : Rp {r1:,.0f}")
    print(f"  --- Pivot ---      : Rp {pivot:,.0f}")
    print(f"  Support 1 (S1)    : Rp {s1:,.0f}")
    print(f"  Support 2 (S2)    : Rp {s2:,.0f}")
    print(f"  Support 3 (S3)    : Rp {s3:,.0f}")

    if ma20 and not pd.isna(ma20) and ma50 and not pd.isna(ma50):
        print(f"\n-- MA-Based Level --")
        if harga > ma20:
            print(f"  Support (MA20)    : Rp {ma20:,.0f}")
        else:
            print(f"  Resistance (MA20) : Rp {ma20:,.0f}")
        if harga > ma50:
            print(f"  Support (MA50)    : Rp {ma50:,.0f}")
        else:
            print(f"  Resistance (MA50) : Rp {ma50:,.0f}")

# ============================================================
#  BAGIAN 4: BROKER SUMMARY & SMART MONEY DETECTION
# ============================================================

# Daftar kode broker besar Indonesia (untuk simulasi)
BROKER_ASING = ['AK', 'BK', 'ZP', 'CS', 'ML', 'DB', 'JP', 'UB', 'GS', 'MS']
BROKER_LOKAL = ['YP', 'RX', 'PD', 'DX', 'MG', 'KZ', 'TP', 'AI', 'BZ', 'KI']
import random

def _hitung_smart_money(data):
    """Hitung semua indikator Smart Money dari data harga & volume"""
    d = data.copy()

    # 1. OBV (On-Balance Volume) — deteksi aliran uang tersembunyi
    obv = [0]
    for i in range(1, len(d)):
        if d['Close'].iloc[i] > d['Close'].iloc[i-1]:
            obv.append(obv[-1] + d['Volume'].iloc[i])
        elif d['Close'].iloc[i] < d['Close'].iloc[i-1]:
            obv.append(obv[-1] - d['Volume'].iloc[i])
        else:
            obv.append(obv[-1])
    d['OBV'] = obv
    d['OBV_MA20'] = d['OBV'].rolling(window=20).mean()

    # 2. A/D Line (Accumulation/Distribution Line)
    clv = ((d['Close'] - d['Low']) - (d['High'] - d['Close'])) / (d['High'] - d['Low'])
    clv = clv.fillna(0)
    d['AD'] = (clv * d['Volume']).cumsum()
    d['AD_MA20'] = d['AD'].rolling(window=20).mean()

    # 3. MFI (Money Flow Index) — RSI versi volume-weighted
    tp = (d['High'] + d['Low'] + d['Close']) / 3
    mf = tp * d['Volume']
    pos_mf = mf.where(tp > tp.shift(1), 0).rolling(14).sum()
    neg_mf = mf.where(tp < tp.shift(1), 0).rolling(14).sum()
    mfi_ratio = pos_mf / neg_mf.replace(0, 1)
    d['MFI'] = 100 - (100 / (1 + mfi_ratio))

    # 4. CMF (Chaikin Money Flow) — tekanan beli/jual institusi 20 hari
    d['CMF'] = (clv * d['Volume']).rolling(window=20).sum() / d['Volume'].rolling(window=20).sum()

    # 5. VWAP (Volume Weighted Average Price) — benchmark institusi
    d['VWAP'] = (d['Volume'] * (d['High'] + d['Low'] + d['Close']) / 3).cumsum() / d['Volume'].cumsum()

    # 6. Volume Spike Detection (deteksi anomali volume = kemungkinan big player masuk)
    d['Vol_MA20'] = d['Volume'].rolling(window=20).mean()
    d['Vol_Ratio'] = d['Volume'] / d['Vol_MA20']

    return d

def _simulasi_broker(data, kode):
    """Simulasi estimasi broker berdasarkan pola volume & harga"""
    recent = data.tail(5)
    random.seed(hash(kode) + len(data))

    total_vol = recent['Volume'].sum()
    if total_vol == 0:
        return [], [], 0, 0

    # Simulasi distribusi volume ke broker-broker besar
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
    """Broker Summary + Smart Money Detection lengkap"""
    print("\n" + "=" * 55)
    print(f"  BROKER SUMMARY & SMART MONEY - {kode}")
    print("=" * 55)

    # --- Hitung Smart Money Indicators ---
    data = _hitung_smart_money(data)
    hari_ini = data.iloc[-1]

    # --- Flow Harian 5 Hari Terakhir ---
    recent = data.tail(5).copy()
    recent['Change'] = recent['Close'].diff()

    total_buy_vol = 0
    total_sell_vol = 0

    print(f"\n  -- Daily Flow (5 Hari Terakhir) --")
    print(f"  {'Tanggal':<12} {'Close':>10} {'Volume':>15} {'Flow':>10}")
    print(f"  {'-'*12} {'-'*10} {'-'*15} {'-'*10}")

    for idx, row in recent.iterrows():
        tanggal = idx.strftime('%Y-%m-%d')
        change = row['Change']
        vol = row['Volume']
        if pd.isna(change):
            flow = "N/A"
        elif change >= 0:
            total_buy_vol += vol
            flow = "NET BUY"
        else:
            total_sell_vol += vol
            flow = "NET SELL"
        print(f"  {tanggal:<12} {row['Close']:>10,.0f} {vol:>15,.0f} {flow:>10}")

    total_vol = total_buy_vol + total_sell_vol
    buy_pct = (total_buy_vol / total_vol * 100) if total_vol > 0 else 50
    sell_pct = (total_sell_vol / total_vol * 100) if total_vol > 0 else 50

    print(f"\n  Net Buy Volume  : {total_buy_vol:>15,.0f} ({buy_pct:.1f}%)")
    print(f"  Net Sell Volume : {total_sell_vol:>15,.0f} ({sell_pct:.1f}%)")

    # --- Simulasi Broker ---
    all_brokers, top_asing, foreign_buy, foreign_sell = _simulasi_broker(data, kode)

    if all_brokers:
        print(f"\n  -- Estimasi Top Broker (Simulasi) --")
        print(f"  {'Kode':<6} {'Tipe':<7} {'Buy Vol':>12} {'Sell Vol':>12} {'Net':>12}")
        print(f"  {'-'*6} {'-'*7} {'-'*12} {'-'*12} {'-'*12}")
        for br, vb, vs, net, tipe in all_brokers[:10]:
            net_str = f"{'+' if net >= 0 else ''}{net:,.0f}"
            print(f"  {br:<6} {tipe:<7} {vb:>12,.0f} {vs:>12,.0f} {net_str:>12}")

        print(f"\n  -- Foreign Flow (Asing) --")
        foreign_net = foreign_buy - foreign_sell
        print(f"  Total Buy Asing  : {foreign_buy:>12,.0f}")
        print(f"  Total Sell Asing : {foreign_sell:>12,.0f}")
        print(f"  Net Foreign      : {'+' if foreign_net >= 0 else ''}{foreign_net:,.0f}")
        if foreign_net > 0:
            print(f"  Status Asing     : NET BUY (Asing sedang MASUK)")
        else:
            print(f"  Status Asing     : NET SELL (Asing sedang KELUAR)")

        print(f"\n  Top 5 Broker Asing : {', '.join(top_asing[:5])}")

    # --- Smart Money Indicators ---
    print(f"\n  -- Smart Money Indicators --")

    # OBV
    obv_now = hari_ini['OBV']
    obv_ma = hari_ini['OBV_MA20']
    if not pd.isna(obv_ma):
        obv_status = "BULLISH (Uang mengalir MASUK)" if obv_now > obv_ma else "BEARISH (Uang mengalir KELUAR)"
        print(f"  OBV vs MA20      : {obv_status}")

    # A/D Line
    ad_now = hari_ini['AD']
    ad_ma = hari_ini['AD_MA20']
    if not pd.isna(ad_ma):
        ad_status = "AKUMULASI (Big player sedang BELI)" if ad_now > ad_ma else "DISTRIBUSI (Big player sedang JUAL)"
        print(f"  A/D Line vs MA20 : {ad_status}")

    # MFI
    mfi = hari_ini['MFI']
    if not pd.isna(mfi):
        if mfi > 80:
            mfi_status = "OVERBOUGHT (Uang terlalu banyak masuk)"
        elif mfi < 20:
            mfi_status = "OVERSOLD (Uang terlalu banyak keluar)"
        else:
            mfi_status = "NETRAL"
        print(f"  MFI (14)         : {mfi:.2f} -> {mfi_status}")

    # CMF
    cmf = hari_ini['CMF']
    if not pd.isna(cmf):
        if cmf > 0.1:
            cmf_status = "TEKANAN BELI KUAT (Institusi masuk)"
        elif cmf > 0:
            cmf_status = "TEKANAN BELI RINGAN"
        elif cmf > -0.1:
            cmf_status = "TEKANAN JUAL RINGAN"
        else:
            cmf_status = "TEKANAN JUAL KUAT (Institusi keluar)"
        print(f"  CMF (20)         : {cmf:.4f} -> {cmf_status}")

    # VWAP
    vwap = hari_ini['VWAP']
    harga = hari_ini['Close']
    if not pd.isna(vwap):
        vwap_status = "DI ATAS VWAP (Institusi untung)" if harga > vwap else "DI BAWAH VWAP (Institusi rugi)"
        print(f"  VWAP             : Rp {vwap:,.0f} -> Harga {vwap_status}")

    # Volume Spike
    vol_ratio = hari_ini['Vol_Ratio']
    if not pd.isna(vol_ratio):
        if vol_ratio > 2.0:
            spike_status = "VOLUME SPIKE! (Kemungkinan big player beraksi)"
        elif vol_ratio > 1.5:
            spike_status = "Volume di atas rata-rata (Ada minat besar)"
        elif vol_ratio < 0.5:
            spike_status = "Volume sangat rendah (Sepi)"
        else:
            spike_status = "Volume normal"
        print(f"  Vol Ratio        : {vol_ratio:.2f}x -> {spike_status}")

    # --- Kesimpulan Fase ---
    print(f"\n  -- Kesimpulan Fase Pasar --")

    skor_sm = 0
    alasan = []

    # Skor dari OBV
    if not pd.isna(obv_ma):
        if obv_now > obv_ma: skor_sm += 1; alasan.append("OBV Bullish (uang masuk)")
        else: skor_sm -= 1; alasan.append("OBV Bearish (uang keluar)")

    # Skor dari A/D Line
    if not pd.isna(ad_ma):
        if ad_now > ad_ma: skor_sm += 1; alasan.append("A/D Line: Akumulasi")
        else: skor_sm -= 1; alasan.append("A/D Line: Distribusi")

    # Skor dari CMF
    if not pd.isna(cmf):
        if cmf > 0.05: skor_sm += 1; alasan.append("CMF positif (tekanan beli)")
        elif cmf < -0.05: skor_sm -= 1; alasan.append("CMF negatif (tekanan jual)")

    # Skor dari MFI
    if not pd.isna(mfi):
        if mfi < 20: skor_sm += 1; alasan.append("MFI Oversold (peluang reversal)")
        elif mfi > 80: skor_sm -= 1; alasan.append("MFI Overbought (rawan koreksi)")

    # Skor dari flow
    if buy_pct > 60: skor_sm += 1; alasan.append("Net buy dominan 5 hari")
    elif sell_pct > 60: skor_sm -= 1; alasan.append("Net sell dominan 5 hari")

    if skor_sm >= 2:
        fase = "FASE AKUMULASI (Smart money sedang MASUK - Pertimbangkan BUY)"
    elif skor_sm <= -2:
        fase = "FASE DISTRIBUSI (Smart money sedang KELUAR - Pertimbangkan SELL)"
    elif skor_sm > 0:
        fase = "CENDERUNG AKUMULASI (Ada tanda-tanda smart money masuk)"
    elif skor_sm < 0:
        fase = "CENDERUNG DISTRIBUSI (Ada tanda-tanda smart money keluar)"
    else:
        fase = "NETRAL (Belum ada sinyal jelas dari smart money)"

    print(f"  {fase}")

    return skor_sm, alasan

# ============================================================
#  BAGIAN 5: REKOMENDASI AKHIR
# ============================================================
def get_rekomendasi(skor_fund, alasan_fund, skor_tek, alasan_tek, skor_broker, alasan_broker, kode, data):
    """Gabungkan semua skor dan berikan rekomendasi akhir + strategi intraday"""

    # ============================================================
    #  BAGIAN 6: STRATEGI INTRADAY (Beli Pagi Jual Sore / Sebaliknya)
    # ============================================================
    print("\n" + "=" * 60)
    print(f"  STRATEGI INTRADAY (SCALPING) - {kode}")
    print("=" * 60)

    hari_ini = data.iloc[-1]
    harga = hari_ini['Close']

    # --- Analisa pola Open vs Close beberapa hari terakhir ---
    recent = data.tail(10).copy()
    pagi_naik = 0    # Hari dimana Close > Open (beli pagi, jual sore untung)
    pagi_turun = 0   # Hari dimana Close < Open (beli sore, jual pagi untung)
    total_hari = 0
    avg_intraday_gain = 0
    avg_intraday_loss = 0

    for _, row in recent.iterrows():
        if row['Open'] > 0:
            total_hari += 1
            intraday_pct = ((row['Close'] - row['Open']) / row['Open']) * 100
            if row['Close'] > row['Open']:
                pagi_naik += 1
                avg_intraday_gain += intraday_pct
            elif row['Close'] < row['Open']:
                pagi_turun += 1
                avg_intraday_loss += intraday_pct

    if pagi_naik > 0: avg_intraday_gain /= pagi_naik
    if pagi_turun > 0: avg_intraday_loss /= pagi_turun

    pct_pagi_naik = (pagi_naik / total_hari * 100) if total_hari > 0 else 50
    pct_pagi_turun = (pagi_turun / total_hari * 100) if total_hari > 0 else 50

    print(f"\n  -- Pola Open vs Close (10 Hari Terakhir) --")
    print(f"  Hari Close > Open (Naik)  : {pagi_naik}/{total_hari} ({pct_pagi_naik:.0f}%)")
    print(f"  Hari Close < Open (Turun) : {pagi_turun}/{total_hari} ({pct_pagi_turun:.0f}%)")
    print(f"  Rata-rata gain intraday   : {avg_intraday_gain:+.2f}%")
    print(f"  Rata-rata loss intraday   : {avg_intraday_loss:+.2f}%")

    # --- Analisa gap (selisih Open hari ini vs Close kemarin) ---
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

    print(f"\n  -- Analisa Gap (Open vs Close Sebelumnya) --")
    print(f"  Rata-rata gap           : {avg_gap:+.2f}%")
    print(f"  Gap Up (naik saat buka) : {gap_up_count}/{len(gap_data)} hari")
    print(f"  Gap Down (turun buka)   : {gap_down_count}/{len(gap_data)} hari")

    # --- Orderbook intraday pressure hari ini ---
    o, h, l, c = hari_ini['Open'], hari_ini['High'], hari_ini['Low'], hari_ini['Close']
    total_range = h - l if h != l else 1
    buy_pressure = (c - l) / total_range * 100
    sell_pressure = (h - c) / total_range * 100

    # Harga mendekati High atau Low?
    pct_from_high = ((h - c) / total_range * 100) if total_range > 0 else 50
    pct_from_low = ((c - l) / total_range * 100) if total_range > 0 else 50

    print(f"\n  -- Tekanan Intraday Hari Ini --")
    print(f"  Buyer Pressure  : {buy_pressure:.1f}%")
    print(f"  Seller Pressure : {sell_pressure:.1f}%")
    print(f"  Posisi Close    : {pct_from_low:.0f}% dari Low, {pct_from_high:.0f}% dari High")

    # --- Volume Session Estimation ---
    vol_today = hari_ini['Volume']
    vol_ma = hari_ini.get('Vol_MA20', 0)
    vol_ratio = vol_today / vol_ma if not pd.isna(vol_ma) and vol_ma > 0 else 1

    # --- Skor Intraday ---
    skor_intraday = 0
    alasan_intraday = []

    # 1. Pola historis beli pagi jual sore
    if pct_pagi_naik >= 70:
        skor_intraday += 2
        alasan_intraday.append(f"Dominan naik intraday ({pct_pagi_naik:.0f}% hari)")
    elif pct_pagi_naik >= 60:
        skor_intraday += 1
        alasan_intraday.append(f"Cenderung naik intraday ({pct_pagi_naik:.0f}% hari)")
    elif pct_pagi_turun >= 70:
        skor_intraday -= 2
        alasan_intraday.append(f"Dominan turun intraday ({pct_pagi_turun:.0f}% hari)")
    elif pct_pagi_turun >= 60:
        skor_intraday -= 1
        alasan_intraday.append(f"Cenderung turun intraday ({pct_pagi_turun:.0f}% hari)")

    # 2. Gap analysis
    if avg_gap > 0.3:
        skor_intraday -= 1  # Gap up = beli sore kemarin lebih untung
        alasan_intraday.append(f"Sering gap up (avg {avg_gap:+.2f}%) -> beli sore lebih baik")
    elif avg_gap < -0.3:
        skor_intraday += 1  # Gap down = beli pagi lebih murah
        alasan_intraday.append(f"Sering gap down (avg {avg_gap:+.2f}%) -> beli pagi lebih murah")

    # 3. Tekanan hari ini
    if buy_pressure > 65:
        skor_intraday += 1
        alasan_intraday.append("Buyer dominan hari ini")
    elif sell_pressure > 65:
        skor_intraday -= 1
        alasan_intraday.append("Seller dominan hari ini")

    # 4. Volume
    if vol_ratio > 1.5:
        alasan_intraday.append(f"Volume tinggi ({vol_ratio:.1f}x) - likuiditas bagus utk scalping")
    elif vol_ratio < 0.5:
        skor_intraday = 0  # Reset - tidak disarankan scalping
        alasan_intraday.append("Volume terlalu rendah - TIDAK DISARANKAN scalping")

    # --- Kesimpulan Intraday ---
    print(f"\n  -- Rekomendasi Intraday --")

    if vol_ratio < 0.5:
        print(f"  [X] TIDAK DISARANKAN SCALPING (Volume terlalu sepi)")
    elif skor_intraday >= 2:
        print(f"  [>>] BELI PAGI, JUAL SORE (Pola harga cenderung naik dalam hari)")
        print(f"       Strategi: Beli di awal sesi (09:00-10:00), jual mendekati penutupan")
    elif skor_intraday >= 1:
        print(f"  [>]  CENDERUNG Beli Pagi Jual Sore (Tapi tidak terlalu kuat)")
    elif skor_intraday <= -2:
        print(f"  [<<] BELI SORE, JUAL PAGI (Pola harga cenderung gap up keesokan hari)")
        print(f"       Strategi: Beli mendekati penutupan, jual saat pembukaan besok")
    elif skor_intraday <= -1:
        print(f"  [<]  CENDERUNG Beli Sore Jual Pagi (Tapi tidak terlalu kuat)")
    else:
        print(f"  [=]  NETRAL - Tidak ada pola intraday yang jelas")

    for a in alasan_intraday:
        print(f"       - {a}")

    # ============================================================
    #  REKOMENDASI UTAMA (JANGKA PANJANG)
    # ============================================================
    print("\n" + "=" * 60)
    print(f"  REKOMENDASI AKHIR - {kode}")
    print("=" * 60)

    total_skor = skor_fund + skor_tek + skor_broker

    print(f"\n  Skor Fundamental : {skor_fund:+d}")
    for a in alasan_fund:
        print(f"    - {a}")

    print(f"\n  Skor Teknikal    : {skor_tek:+d}")
    for a in alasan_tek:
        print(f"    - {a}")

    print(f"\n  Skor Broker Flow : {skor_broker:+d}")
    for a in alasan_broker:
        print(f"    - {a}")

    print(f"\n  {'='*50}")
    print(f"  TOTAL SKOR       : {total_skor:+d}")

    if total_skor >= 4:
        rekom = ">>> STRONG BUY <<<"
    elif total_skor >= 2:
        rekom = ">>> BUY <<<"
    elif total_skor >= -1:
        rekom = ">>> HOLD / WAIT <<<"
    elif total_skor >= -3:
        rekom = ">>> SELL <<<"
    else:
        rekom = ">>> STRONG SELL <<<"

    print(f"  REKOMENDASI (Jangka Panjang) : {rekom}")
    print(f"  {'='*50}")
    print(f"\n  [!] Disclaimer: Ini hanya alat bantu analisa.")
    print(f"      Keputusan investasi tetap tanggung jawab Anda.")

# ============================================================
#  UTILITAS
# ============================================================
def format_rupiah(value):
    """Format angka besar ke Triliun/Miliar Rupiah"""
    if value is None: return "N/A"
    if not isinstance(value, (int, float)): return str(value)
    if abs(value) >= 1_000_000_000_000:
        return f"Rp {value/1_000_000_000_000:.2f} Triliun"
    elif abs(value) >= 1_000_000_000:
        return f"Rp {value/1_000_000_000:.2f} Miliar"
    elif abs(value) >= 1_000_000:
        return f"Rp {value/1_000_000:.2f} Juta"
    else:
        return f"Rp {value:,.0f}"

# ============================================================
#  MAIN BOT
# ============================================================
def mulai_bot():
    print("=" * 55)
    print("  [ BOT SCREENING SAHAM INDONESIA - FULL ANALYSIS ]")
    print("=" * 55)
    print("  Fitur: Fundamental | Teknikal | Support/Resistance")
    print("         Broker Summary | Rekomendasi Buy/Sell")
    print("=" * 55)
    print("Ketik 'exit' atau 'keluar' untuk mematikan bot.\n")

    while True:
        kode_saham = input("Masukkan kode saham (contoh: BBCA): ").strip().upper()

        if kode_saham in ['EXIT', 'KELUAR', 'QUIT']:
            print("Mematikan bot. Sampai jumpa!")
            break

        if not kode_saham:
            continue

        print(f"\n[*] Mengambil data saham {kode_saham} dari server...")

        ticker = f"{kode_saham}.JK"
        saham = yf.Ticker(ticker)

        # Ambil data 6 bulan agar semua indikator terhitung
        data = saham.history(period="6mo")

        if data.empty:
            print(f"[!] Data saham {kode_saham} tidak ditemukan. Pastikan kodenya benar.")
            print("-" * 55)
            continue

        # Jalankan semua analisa
        skor_fund, alasan_fund, info = get_fundamental(saham, kode_saham)
        skor_tek, alasan_tek, data = get_teknikal(data, kode_saham)
        get_support_resistance(data, kode_saham)
        skor_broker, alasan_broker = get_broker_summary(data, kode_saham)
        get_rekomendasi(skor_fund, alasan_fund, skor_tek, alasan_tek, skor_broker, alasan_broker, kode_saham, data)

        print("\n" + "=" * 55 + "\n")

if __name__ == "__main__":
    mulai_bot()
