import os
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

plt.rcParams['font.family'] = 'Apple SD Gothic Neo'
plt.rcParams['axes.unicode_minus'] = False

OUTPUT_DIRS = [
    "/Users/harris/.gemini/antigravity-ide/brain/bacdcaeb-aa0b-40df-a9ae-09d2efd11c08/charts",
    "/Users/harris/project/toss_bot/toss/backtest/charts"
]

for d in OUTPUT_DIRS:
    os.makedirs(d, exist_ok=True)

SYMBOLS_CONFIG = [
    {"symbol": "QQQM", "tp": 0.033, "title": "QQQM (나스닥 100 1배수) - 3.3% 익절 전략", "color": "#0ea5e9"},
    {"symbol": "QLD", "tp": 0.066, "title": "QLD (나스닥 100 2배수) - 6.6% 비례 익절 전략", "color": "#8b5cf6"},
    {"symbol": "TQQQ", "tp": 0.100, "title": "TQQQ (나스닥 100 3배수) - 10.0% 익절 전략", "color": "#ec4899"},
    {"symbol": "SOXL", "tp": 0.100, "title": "SOXL (반도체 3배수) - 10.0% 익절 전략", "color": "#f59e0b"},
]

def generate_chart(cfg):
    symbol = cfg["symbol"]
    tp = cfg["tp"]
    title = cfg["title"]
    line_color = cfg["color"]
    
    print(f"Generating chart for {symbol} (TP: {tp*100:.1f}%)...")
    
    # Download data
    df = yf.download(symbol, start="2021-12-15", auto_adjust=True, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [col[0] for col in df.columns]
    df = df.sort_index()
    dates = [d.strftime("%Y-%m-%d") for d in df.index]
    start_idx = [i for i, d in enumerate(dates) if d >= "2022-01-01"][0]
    
    qty = 0
    avg_price = 0.0
    total_profit = 0.0
    
    dates_list = []
    close_list = []
    avg_price_list = []
    qty_list = []
    val_list = []
    
    exits = []  # (date, sell_price, sold_qty, profit, avg_p)
    
    for i in range(start_idx, len(df)):
        cur_date = df.index[i]
        date_str = dates[i]
        prev_close = float(df["Close"].iloc[i-1])
        high_p = float(df["High"].iloc[i])
        close_p = float(df["Close"].iloc[i])
        
        base_p = avg_price if qty > 0 else round(prev_close * 0.95, 2)
        sell_p = round(base_p * (1 + tp), 2) if qty > 0 else 0.0
        
        # Check exit
        if qty > 0 and high_p >= sell_p:
            profit = (sell_p - avg_price) * qty
            total_profit += profit
            exits.append({
                "date": cur_date,
                "price": sell_p,
                "qty": qty,
                "profit": profit,
                "avg_price": avg_price
            })
            qty = 0
            avg_price = 0.0
            
        b1 = round(base_p, 2)
        b2 = round(prev_close * 1.10, 2)
        b_qty = (1 if close_p <= b1 else 0) + (1 if close_p <= b2 else 0)
        
        if b_qty > 0:
            avg_price = (qty * avg_price + b_qty * close_p) / (qty + b_qty)
            qty += b_qty
            
        dates_list.append(cur_date)
        close_list.append(close_p)
        avg_price_list.append(avg_price if qty > 0 else np.nan)
        qty_list.append(qty)
        val_list.append(qty * avg_price)
        
    # Plotting
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 9), gridspec_kw={'height_ratios': [2.2, 1]}, sharex=True)
    fig.patch.set_facecolor('#0f172a')
    ax1.set_facecolor('#1e293b')
    ax2.set_facecolor('#1e293b')
    
    # 1. Price Chart
    ax1.plot(dates_list, close_list, label=f"{symbol} 종가 (Close)", color=line_color, linewidth=1.5, alpha=0.9)
    ax1.plot(dates_list, avg_price_list, label="보유 평단가 (Avg Cost)", color='#f59e0b', linestyle='--', linewidth=1.2, alpha=0.85)
    
    # Exits scatter
    if exits:
        exit_dates = [e["date"] for e in exits]
        exit_prices = [e["price"] for e in exits]
        exit_qtys = [e["qty"] for e in exits]
        exit_profits = [e["profit"] for e in exits]
        
        # Plot exit points
        ax1.scatter(exit_dates, exit_prices, color='#10b981', s=70, edgecolors='#ffffff', linewidths=1.2, zorder=5, label=f"익절 매도 ({len(exits)}회)", marker='^')
        
        # Highlight top 3 largest exits with text annotations
        sorted_by_profit = sorted(exits, key=lambda x: x["profit"], reverse=True)
        for top_e in sorted_by_profit[:3]:
            txt = f"{top_e['qty']}주 매도\n+${top_e['profit']:,.0f}"
            ax1.annotate(
                txt,
                xy=(top_e["date"], top_e["price"]),
                xytext=(0, 20),
                textcoords="offset points",
                ha='center',
                fontsize=8,
                fontweight='bold',
                color='#10b981',
                bbox=dict(boxstyle="round,pad=0.3", fc="#064e3b", ec="#10b981", alpha=0.85),
                arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0", color="#10b981", lw=1)
            )
            
    ax1.set_title(f"{title} (2022 ~ 2026)", fontsize=15, fontweight='bold', color='#f8fafc', pad=12)
    ax1.set_ylabel("주가 (USD)", fontsize=11, color='#94a3b8')
    ax1.tick_params(colors='#94a3b8', labelsize=10)
    ax1.grid(True, linestyle=':', alpha=0.3, color='#64748b')
    ax1.legend(loc='upper left', facecolor='#0f172a', edgecolor='#334155', labelcolor='#e2e8f0', fontsize=10)
    
    # 2. Position & Capital Chart
    ax2.bar(dates_list, qty_list, width=2, color='#38bdf8', alpha=0.45, label="보유 수량 (주)")
    ax2.set_ylabel("보유 수량 (주)", fontsize=11, color='#38bdf8')
    ax2.tick_params(axis='y', labelcolor='#38bdf8', labelsize=10)
    
    ax2_twin = ax2.twinx()
    ax2_twin.plot(dates_list, val_list, color='#f43f5e', linewidth=1.2, alpha=0.85, label="투입 시드 ($)")
    ax2_twin.set_ylabel("투입 자본 ($)", fontsize=11, color='#f43f5e')
    ax2_twin.tick_params(axis='y', labelcolor='#f43f5e', labelsize=10)
    
    max_seed = max(val_list) if val_list else 0
    max_q = max(qty_list) if qty_list else 0
    
    # Subplot 2 styling
    ax2.set_title(f"누적 매집 수량 (최대 {max_q}주) & 투입 시드 금액 (최대 ${max_seed:,.0f})", fontsize=11, color='#cbd5e1', pad=8)

    ax2.tick_params(colors='#94a3b8', labelsize=10)
    ax2.grid(True, linestyle=':', alpha=0.3, color='#64748b')
    ax2.xaxis.set_major_locator(mdates.YearLocator())
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    
    # Combined legend for ax2
    lines_1, labels_1 = ax2.get_legend_handles_labels()
    lines_2, labels_2 = ax2_twin.get_legend_handles_labels()
    ax2.legend(lines_1 + lines_2, labels_1 + labels_2, loc='upper left', facecolor='#0f172a', edgecolor='#334155', labelcolor='#e2e8f0', fontsize=9)
    
    plt.tight_layout()
    
    # Save to all target paths
    filename = f"{symbol.lower()}_backtest_chart.png"
    for d in OUTPUT_DIRS:
        out_path = os.path.join(d, filename)
        fig.savefig(out_path, dpi=180, facecolor=fig.get_facecolor(), edgecolor='none')
        print(f"Saved: {out_path}")
        
    plt.close(fig)

for cfg in SYMBOLS_CONFIG:
    generate_chart(cfg)

print("All charts generated successfully!")
