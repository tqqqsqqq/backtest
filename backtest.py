#!/usr/bin/env python3
"""
Toss Trading Bot - Strategy Backtester
전략: LOC 2분할 매수 + 평단가 대비 10% 지정가 익절 매도
"""

import argparse
import json
import pandas as pd
import yfinance as yf


DEFAULT_TP = {
    "QQQ": 0.033,
    "QQQM": 0.033,
    "QLD": 0.066,
    "TQQQ": 0.10,
    "SOXL": 0.10,
}


def run_backtest(symbol: str, start_date: str = "2022-01-01", take_profit: float = None):
    if take_profit is None:
        take_profit = DEFAULT_TP.get(symbol.upper(), 0.10)

    print(f"\n========================================================")
    print(f"🚀 [{symbol}] 백테스팅 시작: {start_date} ~ 현재")
    print(f"• 익절 목표: +{take_profit * 100:.1f}%")
    print(f"========================================================")


    # 넉넉하게 10일 전부터 다운로드하여 직전 거래일 종가 확보
    fetch_start = pd.to_datetime(start_date) - pd.Timedelta(days=15)
    df = yf.download(symbol, start=fetch_start.strftime("%Y-%m-%d"), auto_adjust=True, progress=False)

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [col[0] for col in df.columns]

    df = df.sort_index()
    dates = [d.strftime("%Y-%m-%d") for d in df.index]

    start_idx = 0
    for i, d in enumerate(dates):
        if d >= start_date:
            start_idx = i
            break

    qty = 0
    avg_price = 0.0
    max_seed = 0.0
    max_qty = 0
    total_realized_profit = 0.0
    realized_cycles = []
    daily_records = []
    current_cycle_start = None

    for i in range(start_idx, len(df)):
        cur_date = dates[i]
        prev_close = float(df["Close"].iloc[i - 1])
        open_p = float(df["Open"].iloc[i])
        high_p = float(df["High"].iloc[i])
        low_p = float(df["Low"].iloc[i])
        close_p = float(df["Close"].iloc[i])

        # 1. 아침 주문 설정
        base_price = avg_price if qty > 0 else round(prev_close * 0.95, 2)
        buy_price_1 = round(base_price, 2)
        buy_price_2 = round(prev_close * 1.10, 2)
        sell_price = round(base_price * (1 + take_profit), 2) if qty > 0 else 0.0

        # 2. 장중 지정가 익절 매도 체크
        if qty > 0 and high_p >= sell_price:
            sold_qty = qty
            profit = (sell_price - avg_price) * sold_qty
            profit_rate = (sell_price - avg_price) / avg_price * 100
            total_realized_profit += profit

            realized_cycles.append({
                "cycle": len(realized_cycles) + 1,
                "exit_date": cur_date,
                "start_date": current_cycle_start,
                "sold_qty": sold_qty,
                "sell_price": round(sell_price, 2),
                "avg_price": round(avg_price, 2),
                "profit": round(profit, 2),
                "profit_rate": round(profit_rate, 2),
            })

            qty = 0
            avg_price = 0.0
            current_cycle_start = None

        # 3. 장마감 종가 매수(LOC) 체크
        bought_qty = 0
        bought_cost = 0.0

        if close_p <= buy_price_1:
            bought_qty += 1
            bought_cost += close_p

        if close_p <= buy_price_2:
            bought_qty += 1
            bought_cost += close_p

        if bought_qty > 0:
            if qty == 0:
                current_cycle_start = cur_date
            prev_cost = qty * avg_price
            qty += bought_qty
            avg_price = (prev_cost + bought_cost) / qty

        cur_val = qty * avg_price
        if cur_val > max_seed:
            max_seed = cur_val
        if qty > max_qty:
            max_qty = qty

        daily_records.append({
            "date": cur_date,
            "year": cur_date[:4],
            "close": close_p,
            "qty": qty,
            "avg_price": avg_price,
            "holding_val": cur_val,
        })

    last_close = float(df["Close"].iloc[-1])
    unrealized_profit = (last_close - avg_price) * qty if qty > 0 else 0.0
    unrealized_pct = ((last_close - avg_price) / avg_price * 100) if qty > 0 else 0.0
    total_profit = total_realized_profit + unrealized_profit

    # 연도별 통계 집계
    df_daily = pd.DataFrame(daily_records)
    df_cycles = pd.DataFrame(realized_cycles)
    years = sorted(df_daily["year"].unique())

    yearly_summary = {}
    for y in years:
        y_daily = df_daily[df_daily["year"] == y]
        y_cycles = df_cycles[df_cycles["exit_date"].str.startswith(y)] if not df_cycles.empty else pd.DataFrame()
        y_realized = float(y_cycles["profit"].sum()) if not y_cycles.empty else 0.0
        y_exits = len(y_cycles)
        y_max_seed = float(y_daily["holding_val"].max())
        y_max_qty = int(y_daily["qty"].max())

        yearly_summary[y] = {
            "exits": y_exits,
            "realized_profit": round(y_realized, 2),
            "max_seed": round(y_max_seed, 2),
            "max_qty": y_max_qty,
        }

    # 콘솔 출력
    print(f"\n📊 [{symbol}] 백테스팅 결과 요약")
    print(f"• 기간: {dates[start_idx]} ~ {dates[-1]} (총 {len(df) - start_idx} 거래일)")
    print(f"• 총 익절 횟수: {len(realized_cycles)} 회")
    print(f"• 총 실현 손익: ${total_realized_profit:,.2f}")
    print(f"• 최대 필요 시드 (Max Seed): ${max_seed:,.2f} (최대 누적: {max_qty}주)")
    print(f"• 최대 시드 대비 수익률 (ROI): {(total_profit / max_seed * 100):.2f}%")
    print(f"• 현재 포지션: {qty}주 (평단 ${avg_price:.2f}, 평가손익: ${unrealized_profit:,.2f} / {unrealized_pct:+.2f}%)")
    print(f"• 총 손익(실현 + 평가): ${total_profit:,.2f}")

    print("\n📅 연도별 상세 실적:")
    for y, s in yearly_summary.items():
        print(f"  [{y}년] {s['exits']:2d}회 익절 | 실현손익: ${s['realized_profit']:>9,.2f} | 연중최대시드: ${s['max_seed']:>9,.2f} | 최대수량: {s['max_qty']:3d}주")

    return {
        "symbol": symbol,
        "start_date": dates[start_idx],
        "end_date": dates[-1],
        "trading_days": len(df) - start_idx,
        "total_exits": len(realized_cycles),
        "total_realized_profit": round(total_realized_profit, 2),
        "max_seed": round(max_seed, 2),
        "max_qty": max_qty,
        "current_qty": qty,
        "current_avg_price": round(avg_price, 2),
        "current_unrealized_profit": round(unrealized_profit, 2),
        "current_unrealized_pct": round(unrealized_pct, 2),
        "total_profit": round(total_profit, 2),
        "roi_max_seed": round(total_profit / max_seed * 100, 2) if max_seed > 0 else 0.0,
        "yearly": yearly_summary,
        "cycles": realized_cycles,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Toss Bot Strategy Backtester")
    parser.add_argument("--symbol", type=str, default="TQQQ", help="종목 코드 (기본값: TQQQ)")
    parser.add_argument("--start", type=str, default="2022-01-01", help="시작일 (YYYY-MM-DD, 기본값: 2022-01-01)")
    parser.add_argument("--tp", type=float, default=None, help="익절 목표 비율 (기본값: 종목별 자동 - QQQ/QQQM: 0.033, QLD: 0.05, TQQQ/SOXL: 0.10)")
    args = parser.parse_args()

    run_backtest(symbol=args.symbol, start_date=args.start, take_profit=args.tp)
