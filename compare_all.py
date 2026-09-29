#!/usr/bin/env python3
"""
Run comparison between TQQQ and SOXL for both 2022~now and 2026 YTD.
Exports results to JSON files.
"""

import json
from backtest import run_backtest

def main():
    print("=" * 60)
    print("1. [2022년 ~ 현재] TQQQ vs SOXL 백테스팅 실행")
    print("=" * 60)
    tqqq_2022 = run_backtest("TQQQ", start_date="2022-01-01")
    soxl_2022 = run_backtest("SOXL", start_date="2022-01-01")

    with open("results_2022_2026.json", "w", encoding="utf-8") as f:
        json.dump({"TQQQ": tqqq_2022, "SOXL": soxl_2022}, f, indent=2, ensure_ascii=False)
    print("✅ results_2022_2026.json 저장 완료")

    print("\n" + "=" * 60)
    print("2. [2026년 ~ 현재] TQQQ vs SOXL 백테스팅 실행")
    print("=" * 60)
    tqqq_2026 = run_backtest("TQQQ", start_date="2026-01-01")
    soxl_2026 = run_backtest("SOXL", start_date="2026-01-01")

    with open("results_2026.json", "w", encoding="utf-8") as f:
        json.dump({"TQQQ": tqqq_2026, "SOXL": soxl_2026}, f, indent=2, ensure_ascii=False)
    print("✅ results_2026.json 저장 완료")

if __name__ == "__main__":
    main()
