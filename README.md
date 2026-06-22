# exchange_rate ETL

원/달러 환율(ECOS)과 WTI 유가(FRED)를 수집해 MySQL에 적재하는 자동화 파이프라인.

> 원유는 달러로 결제되므로 환율 상승 + 유가 상승이 겹치면 한국의 에너지 비용 이중 타격.
> 두 지표를 함께 수집해 상관관계를 분석하기 위함.

---

## 폴더 구조

```
~/exchange_rate/
├── etl.py        # 메인 ETL 스크립트 (ECOS + FRED 증분 적재)
├── run_etl.sh    # crontab용 자동화 스크립트
├── .env          # API키, DB접속정보 (git 제외)
├── .gitignore
├── venv/         # Python 가상환경
└── README.md
```

---

## 데이터 소스

| 지표 | API | 시리즈 |
|------|-----|--------|
| 원/달러 환율 매매기준율 | 한국은행 ECOS | 통계코드 `731Y001`, 항목 `0000001` |
| WTI 유가 (달러/배럴) | FRED (St. Louis Fed) | `DCOILWTICO` |

---

## DB 구조

**DB명:** `exchange_rate`

```sql
CREATE TABLE usd_krw_daily (
  trade_date  DATE           NOT NULL,
  usd_krw     DECIMAL(10,2)  NOT NULL,
  created_at  TIMESTAMP      DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (trade_date)
);

CREATE TABLE wti_daily (
  trade_date  DATE           NOT NULL,
  wti_usd     DECIMAL(10,2)  NOT NULL,
  created_at  TIMESTAMP      DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (trade_date)
);
```

---

## 실행 방법

### 환경 설정

```bash
cd ~/exchange_rate
python3 -m venv venv
source venv/bin/activate
pip install requests pymysql python-dotenv
```

`.env` 파일 작성:

```
ECOS_API_KEY=your_key
FRED_API_KEY=your_key
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=exchange_rate
```

### 수동 실행

```bash
source venv/bin/activate
python etl.py
```

### 자동 실행 (crontab)

평일 14:00 KST 자동 실행. 로그는 `etl.log`에 누적.

```
0 14 * * 1-5 /home/ubuntu/exchange_rate/run_etl.sh
```

---

## ETL 동작 방식

1. DB에서 `MAX(trade_date)` 조회
2. 데이터 없으면 **초기 적재** (최근 2년치)
3. 데이터 있으면 **증분 적재** (마지막 날짜 다음날 ~ 전날)
4. `INSERT IGNORE`로 중복 방지
