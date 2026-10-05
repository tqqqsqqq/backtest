#!/usr/bin/env python3
"""
Run comparison across NASDAQ family & SOXL:
- QQQ (1x, 3.3% 익절)
- QQQM (1x 미니, 3.3% 익절)
- QLD (2x, 5.0% 익절)
- TQQQ (3x, 10.0% 익절)
- SOXL (3x 반도체, 10.0% 익절)

Exports results to JSON files.
"""

import json
from backtest import run_backtest

SYMBOLS = [
    ("QQQ", 0.033),
    ("QQQM", 0.033),
    ("QLD", 0.05),
    ("TQQQ", 0.10),
    ("SOXL", 0.10),
]

def main():
    print("=" * 60)
    print("1. [2022년 ~ 현재] 전체 종목 백테스팅 실행")
    print("=" * 60)
    results_2022 = {}
    for sym, tp in SYMBOLS:
        results_2022[sym] = run_backtest(sym, start_date="2022-01-01", take_profit=tp)

    with open("results_2022_2026.json", "w", encoding="utf-8") as f:
        json.dump(results_2022, f, indent=2, ensure_ascii=False)
    print("✅ results_2022_2026.json 저장 완료")

    print("\n" + "=" * 60)
    print("2. [2026년 ~ 현재] 전체 종목 백테스팅 실행")
    print("=" * 60)
    results_2026 = {}
    for sym, tp in SYMBOLS:
        results_2026[sym] = run_backtest(sym, start_date="2026-01-01", take_profit=tp)

    with open("results_2026.json", "w", encoding="utf-8") as f:
        json.dump(results_2026, f, indent=2, ensure_ascii=False)
    print("✅ results_2026.json 저장 완료")

if __name__ == "__main__":
    main()
