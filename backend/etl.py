import os
import requests
import pymysql
from pathlib import Path
from datetime import date, timedelta
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

ECOS_API_KEY = os.getenv("ECOS_API_KEY")
FRED_API_KEY = os.getenv("FRED_API_KEY")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

# ECOS 통계 코드
STAT_CODE = "731Y001"   # 주요국 통화의 대원화환율
ITEM_CODE = "0000001"   # 원/달러(매매기준율)

# FRED 시리즈 코드
WTI_SERIES = "DCOILWTICO"  # WTI 유가 (달러/배럴)


def get_db_connection():
    """MySQL 연결 객체 생성"""
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset="utf8mb4"
    )


def get_last_date(conn):
    """DB에 저장된 가장 최신 날짜 조회 (증분 기준점)"""
    with conn.cursor() as cursor:
        cursor.execute("SELECT MAX(trade_date) FROM usd_krw_daily")
        result = cursor.fetchone()
        return result[0]  # 데이터 없으면 None


def fetch_ecos_data(start_date: str, end_date: str):
    """ECOS API 호출해서 원/달러 환율 데이터 가져오기"""
    url = (
        f"https://ecos.bok.or.kr/api/StatisticSearch/"
        f"{ECOS_API_KEY}/json/kr/1/1000/"
        f"{STAT_CODE}/D/{start_date}/{end_date}/{ITEM_CODE}"
    )

    response = requests.get(url)
    response.raise_for_status()
    data = response.json()

    # 에러 응답 처리 (데이터 없음 등)
    if "StatisticSearch" not in data:
        print(f"[알림] 응답에 데이터 없음: {data}")
        return []

    rows = data["StatisticSearch"]["row"]
    return rows


def insert_data(conn, rows):
    """MySQL에 증분 INSERT (중복 시 스킵)"""
    if not rows:
        print("[알림] 새로 저장할 데이터가 없습니다.")
        return 0

    inserted_count = 0
    with conn.cursor() as cursor:
        for row in rows:
            trade_date_raw = row["TIME"]          # 예: "20260619"
            usd_krw_raw = row["DATA_VALUE"]        # 예: "1512.80"

            # YYYYMMDD -> YYYY-MM-DD
            trade_date = (
                f"{trade_date_raw[0:4]}-"
                f"{trade_date_raw[4:6]}-"
                f"{trade_date_raw[6:8]}"
            )

            sql = """
                INSERT IGNORE INTO usd_krw_daily (trade_date, usd_krw)
                VALUES (%s, %s)
            """
            cursor.execute(sql, (trade_date, usd_krw_raw))
            inserted_count += cursor.rowcount  # 실제 삽입된 건수만 카운트

    conn.commit()
    return inserted_count


def get_wti_last_date(conn):
    """wti_daily 테이블의 가장 최신 날짜 조회"""
    with conn.cursor() as cursor:
        cursor.execute("SELECT MAX(trade_date) FROM wti_daily")
        result = cursor.fetchone()
        return result[0]


def fetch_fred_wti(start_date: str, end_date: str):
    """FRED API 호출해서 WTI 유가 데이터 가져오기"""
    url = (
        f"https://api.stlouisfed.org/fred/series/observations"
        f"?series_id={WTI_SERIES}"
        f"&api_key={FRED_API_KEY}"
        f"&observation_start={start_date}"
        f"&observation_end={end_date}"
        f"&file_type=json"
    )

    response = requests.get(url)
    response.raise_for_status()
    observations = response.json().get("observations", [])

    # FRED는 데이터 없는 날 value를 "."으로 반환 → 필터링
    return [o for o in observations if o["value"] != "."]


def insert_wti(conn, rows):
    """wti_daily 테이블에 증분 INSERT (중복 시 스킵)"""
    if not rows:
        print("[알림] WTI: 새로 저장할 데이터가 없습니다.")
        return 0

    inserted_count = 0
    with conn.cursor() as cursor:
        for row in rows:
            sql = """
                INSERT IGNORE INTO wti_daily (trade_date, wti_usd)
                VALUES (%s, %s)
            """
            cursor.execute(sql, (row["date"], row["value"]))
            inserted_count += cursor.rowcount

    conn.commit()
    return inserted_count


def main():
    conn = get_db_connection()

    try:
        last_date = get_last_date(conn)
        today = date.today()

        if last_date is None:
            # 데이터가 하나도 없는 경우 → 초기 적재 (2년치)
            start_date = today - timedelta(days=365 * 2)
            print(f"[초기 적재] {start_date} ~ {today}")
        else:
            # 증분 적재 → 마지막 날짜 다음날부터
            start_date = last_date + timedelta(days=1)
            print(f"[증분 적재] {start_date} ~ {today}")

        if start_date > today:
            print("[알림] 이미 최신 상태입니다. 수집할 데이터가 없습니다.")
            return

        start_str = start_date.strftime("%Y%m%d")
        end_str = today.strftime("%Y%m%d")

        rows = fetch_ecos_data(start_str, end_str)
        inserted = insert_data(conn, rows)
        print(f"[USD/KRW 완료] 총 {len(rows)}건 조회, {inserted}건 신규 저장")

        # ── WTI 증분 적재 ──
        wti_last_date = get_wti_last_date(conn)

        if wti_last_date is None:
            wti_start = today - timedelta(days=365 * 2)
            print(f"[WTI 초기 적재] {wti_start} ~ {today}")
        else:
            wti_start = wti_last_date + timedelta(days=1)
            print(f"[WTI 증분 적재] {wti_start} ~ {today}")

        if wti_start <= today:
            wti_rows = fetch_fred_wti(
                wti_start.strftime("%Y-%m-%d"),
                today.strftime("%Y-%m-%d")
            )
            wti_inserted = insert_wti(conn, wti_rows)
            print(f"[WTI 완료] 총 {len(wti_rows)}건 조회, {wti_inserted}건 신규 저장")
        else:
            print("[WTI 알림] 이미 최신 상태입니다.")

    finally:
        conn.close()


if __name__ == "__main__":
    main()