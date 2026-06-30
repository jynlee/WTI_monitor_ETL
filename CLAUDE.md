# CLAUDE.md — WTI_monitor_ETL 프로젝트 컨텍스트

## 프로젝트 개요

원/달러 환율(한국은행 ECOS)과 WTI 유가(FRED)를 수집해 MySQL에 적재하는 ETL 파이프라인 + FastAPI 모니터링 대시보드.

**목적:** 원유는 달러로 결제되므로 환율 상승 + 유가 상승이 겹치면 한국의 에너지 비용 이중 타격 → 두 지표를 함께 수집·시각화해 분석.

---

## 기술 스택

| 역할 | 기술 |
|------|------|
| 언어 | Python 3.12 (venv: `backend/venv/`) |
| 웹 프레임워크 | FastAPI + Uvicorn |
| 템플릿 | Jinja2 |
| 프론트엔드 | HTML/CSS + Chart.js (CDN) |
| DB | MySQL (`exchange_rate` DB) |
| DB 드라이버 | pymysql |
| 환경변수 | python-dotenv (`.env` 루트) |
| 자동화 | bash + crontab |

---

## 폴더 구조

```
~/WTI_monitor_ETL/
├── .env                            # API키·DB 접속정보 (git 제외)
├── .gitignore
├── README.md
├── CLAUDE.md                       # 이 파일
├── backend/
│   ├── app.py                      # FastAPI 서버 (포트 8001)
│   ├── etl.py                      # ETL 메인 스크립트
│   ├── run_etl.sh                  # crontab용 실행 스크립트
│   ├── requirements.txt            # pip 의존성
│   └── venv/                       # 가상환경 (git 제외)
├── frontend/
│   ├── templates/index.html        # 대시보드 UI (Jinja2)
│   └── static/style.css            # 스타일시트
├── db/
│   └── schema.sql                  # 테이블 DDL
└── docs/
    ├── api.md                      # API 엔드포인트 명세
    └── screenshots/                # 대시보드 스크린샷
```

---

## DB 정보

- **host**: localhost / **port**: 3306
- **DB명**: `exchange_rate`
- **접속 계정**: root (비밀번호는 `.env` 참고)

| 테이블 | 컬럼 | 설명 |
|--------|------|------|
| `usd_krw_daily` | `trade_date` DATE PK, `usd_krw` DECIMAL(10,2) | 원/달러 매매기준율 |
| `wti_daily` | `trade_date` DATE PK, `wti_usd` DECIMAL(10,2) | WTI 유가 (달러/배럴) |

---

## 데이터 소스

| 지표 | API | 키 환경변수 |
|------|-----|------------|
| USD/KRW 환율 | 한국은행 ECOS (`731Y001` / `0000001`) | `ECOS_API_KEY` |
| WTI 유가 | FRED (`DCOILWTICO`) | `FRED_API_KEY` |

---

## 실행 방법

### 대시보드 서버

```bash
# 프로젝트 루트에서 실행
source backend/venv/bin/activate
uvicorn backend.app:app --port 8001 --host 0.0.0.0
```

### ETL 수동 실행

```bash
source backend/venv/bin/activate
python backend/etl.py
```

### crontab (평일 14:00 KST 자동 실행)

```
0 14 * * 1-5 /home/ubuntu/WTI_monitor_ETL/backend/run_etl.sh
```

---

## ETL 동작 방식

1. `MAX(trade_date)` 조회 → 데이터 없으면 초기 적재(2년치), 있으면 증분 적재
2. 수집 종료일 = **today** (14:00 실행 기준, 환율 08:10 확정·WTI 전날 미국장 반영 완료)
3. `INSERT IGNORE`로 중복 방지
4. 로그: `backend/etl.log`

---

## FastAPI 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/` | 대시보드 HTML |
| GET | `/api/summary` | 최신 환율·WTI + 전일 대비 변동 |
| GET | `/api/chart/usdkrw` | 2년치 USD/KRW 시계열 |
| GET | `/api/chart/wti` | 2년치 WTI 시계열 |
| GET | `/api/chart/energy` | 2년치 원화 에너지 비용(환율×WTI) |
| GET | `/api/avg_energy` | 2년 평균 원화 에너지 비용 |

---

## 주의사항

- **포트 8001 고정** — 포트 8000은 다른 프로젝트가 점유 중
- **`.env`는 루트에 위치** — `backend/app.py`, `backend/etl.py` 모두 `Path(__file__).parent.parent / ".env"`로 참조
- **Starlette 1.x API** — `TemplateResponse(request, "index.html")` 형태 사용 (구버전 `("index.html", {"request": request})` 아님)
- **venv는 `backend/venv/`** — 루트에 venv 없음
- **커밋 시 Co-Authored-By 제외** — Claude 이름 Contributors에 넣지 않음
- **WTI 컬럼명** — `wti_price` 아닌 `wti_usd`
- **Git 브랜치** — `feature/etl-script`에서 작업 후 `main`에 머지하는 전략 사용
- **GitHub 원격 저장소** — https://github.com/jynlee/WTI_monitor_ETL.git
