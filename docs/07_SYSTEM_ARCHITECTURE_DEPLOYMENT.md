# ⚙️ [검토 보고서 7] 토스 봇 시스템 아키텍처 & Docker 클라우드 배포 운영 가이드

**작성일**: 2026-10-05  
**대상 시스템**: Toss Order Bot (Python 3.11, Docker, GCP Compute Engine, Telegram Bot API)

---

## 1. 시스템 전체 아키텍처

```
[클라우드 서버 (GCP VM)]
   │
   ├── Docker Container (toss-bot-container)
   │     ├── Python 3.11 애플리케이션 (toss_order_bot.py)
   │     ├── APScheduler (뉴욕 시간 08:30 / 장 시작 1시간 전 자동 실행)
   │     └── python-telegram-bot (대화형 인터랙티브 봇)
   │
   ├── 볼륨 마운트 (Host Storage)
   │     ├── config.json (토스 API 키, 시크릿 키, 텔레그램 봇 토큰)
   │     └── toss_orders.db (SQLite 주문 내역 및 상태 영구 저장)
   │
   └── 외부 통신 연동
         ├── 토스증권 OpenAPI (OAuth2 토큰 갱신, LOC 주문, 지정가 매도, 잔고 조회)
         └── 텔레그램 메신저 (알림 전송, 실시간 조회, 인라인 키보드 명령)
```

---

## 2. 매매 전략 실행 파이프라인

1. **매일 뉴욕 시간 08:30 (장 시작 1시간 전 자동 트리거)**:
   - 토스 OpenAPI OAuth2 Access Token 자동 갱신
   - 직전 거래일 종가 및 현재 보유 수량(`qty`), 평단가(`avg_price`) 조회
   - 취소되거나 거부된 과거 주문 DB 자동 클린업
2. **주문 전송**:
   - **매수 ① (LOC)**: 평단가(미보유 시 전일종가 × 0.95)에 1주
   - **매수 ② (LOC)**: 전일종가 × 1.10에 1주
   - **매도 (DAY LIMIT)**: 보유 시 평단가 × (1 + 목표익절률)에 전량 지정가 매도
3. **텔레그램 알림**:
   - 등록된 주문 내역 및 가격 정보를 관리자 텔레그램으로 즉시 보고

---

## 3. 원클릭 클라우드 배포 스크립트 (`deploy.sh`)

GCP VM 서버에서 최신 코드를 당겨와 도커 컨테이너를 무중단 재빌드/재시작하는 스크립트입니다:

```bash
#!/bin/bash
set -e

echo "🚀 [Toss Bot] 최신 코드 배포 및 컨테이너 갱신 시작..."
git pull origin main

echo "🐳 Docker 이미지 빌드 중..."
docker build -t toss-bot:latest .

echo "🛑 기존 컨테이너 중지 및 삭제..."
docker stop toss-bot-container 2>/dev/null || true
docker rm toss-bot-container 2>/dev/null || true

echo "▶️ 신규 컨테이너 실행 중..."
docker run -d \
  --name toss-bot-container \
  --restart always \
  -e TZ=Asia/Seoul \
  -v $(pwd)/config.json:/app/config.json \
  -v $(pwd)/toss_orders.db:/app/toss_orders.db \
  toss-bot:latest

echo "✅ 배포 완료! 컨테이너 상태:"
docker ps --filter "name=toss-bot-container"
```

---

## 4. 텔레그램 주요 명령어

| 명령어 | 기능 설명 |
| :--- | :--- |
| `/balance` | 실시간 보유 수량, 평단가, 현재가, 전일종가 대비 변동률(`+X.XX%`), 평가손익 조회 |
| `/symbol` | 운용 종목 변경 (`TQQQ`, `SOXL`, `BOTH`) - 인라인 키보드 버튼 지원 |
| `/cancel_all`| 당일 접수된 미체결 주문 전체 취소 및 DB 자동 정리 |
| `/order` | 장 시작 전 수동 주문 즉시 실행 |
| `/help` | 명령어 사용법 및 도움말 안내 |
