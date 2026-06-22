# API 엔드포인트 명세

Base URL: `http://localhost:8001`

## GET /api/summary
최신 환율 및 WTI 유가 + 전일 대비 변동

```json
{
  "usd_krw": { "date": "2026-06-22", "value": 1535.0, "change": 11.6 },
  "wti":     { "date": "2026-06-15", "value": 84.65,  "change": -3.97 }
}
```

## GET /api/chart/usdkrw
2년치 원/달러 환율 시계열 데이터

```json
{ "labels": ["2024-06-24", ...], "data": [1389.1, ...] }
```

## GET /api/chart/wti
2년치 WTI 유가 시계열 데이터

```json
{ "labels": ["2024-06-24", ...], "data": [81.43, ...] }
```

## GET /api/chart/energy
2년치 원화 에너지 비용 시계열 데이터 (환율 × WTI, 원/배럴)

```json
{ "labels": ["2024-06-24", ...], "data": [113200.0, ...] }
```

## GET /api/avg_energy
2년 평균 원화 에너지 비용

```json
{ "avg_energy": 103073.0 }
```
