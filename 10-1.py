import yfinance as yf
import pandas as pd
from stock_engine import get_cashflow_analysis

def run_test():
    # Ticker saham yang ingin diuji (contoh: BBCA.JK untuk Bank Central Asia)
    ticker_code = "BBCA.JK"
    print(f"Mengambil data untuk {ticker_code} dari Yahoo Finance...")
    
    saham = yf.Ticker(ticker_code)
    # Mengambil data historis 60 hari terakhir
    data = saham.history(period="60d")
    
    if not data.empty:
        # Menjalankan analisis cashflow & market microstructure dari stock_engine
        result, _ = get_cashflow_analysis(data, saham, ticker_code)
        
        # Cetak hasil analisis
        print("\n" + "="*50)
        print(f" HASIL ANALISIS CASHFLOW & MICROSTRUCTURE: {ticker_code} ")
        print("="*50)
        print(f"Harga Terakhir    : Rp {result.get('harga_terakhir', 0):,.0f}")
        
        change_pct = result.get('change_pct')
        change_str = f"{change_pct:+.2f}%" if change_pct is not None else "N/A"
        print(f"Perubahan Harga   : {change_str}")
        print(f"Skor Aliran Dana  : {result.get('skor', 0)}")
        print(f"Regime Aliran     : {result.get('regime', 'UNKNOWN')}")
        
        print("\n--- DETAIL ALASAN / INDIKATOR ---")
        alasan = result.get('alasan', [])
        if alasan:
            for idx, item in enumerate(alasan, 1):
                print(f"{idx}. {item}")
        else:
            print("- Tidak ada indikator aliran dana yang signifikan terdeteksi.")
            
        print("\n--- RINGKASAN PER MODUL ---")
        modules = [
            ("1. ETF Mechanics", "etf_mechanics"),
            ("2. Index Rebalancing", "index_rebalancing"),
            ("3. Liquidity Analysis", "liquidity"),
            ("4. Order Flow Analysis", "order_flow"),
            ("5. Forced Flow Detection", "forced_flow"),
            ("6. Positioning Analysis", "positioning"),
            ("7. Crowded Trade Detection", "crowded_trade"),
            ("8. Market Microstructure", "microstructure"),
            ("9. Passive vs Active Flow", "passive_active_flow"),
            ("10. Risk-On Risk-Off (RORO)", "risk_on_risk_off"),
        ]
        
        for name, key in modules:
            mod = result.get(key, {})
            print(f"- {name:<30} | Skor: {mod.get('skor', 0):>2} | Sinyal: {mod.get('signal', 'N/A')}")
        print("="*50)
    else:
        print(f"Gagal mengambil data untuk {ticker_code}. Pastikan koneksi internet aktif dan ticker valid.")

if __name__ == "__main__":
    run_test()
