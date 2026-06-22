import os
import pymysql
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent        # backend/
FRONTEND_DIR = BASE_DIR.parent / "frontend"       # frontend/

load_dotenv(BASE_DIR.parent / ".env")

app = FastAPI()
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(FRONTEND_DIR / "templates"))


def get_db():
    return pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 3306)),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.get("/api/summary")
def api_summary():
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT trade_date, usd_krw FROM usd_krw_daily ORDER BY trade_date DESC LIMIT 2"
            )
            usd_rows = cur.fetchall()
            cur.execute(
                "SELECT trade_date, wti_usd FROM wti_daily ORDER BY trade_date DESC LIMIT 2"
            )
            wti_rows = cur.fetchall()

        def make_card(rows, key):
            if not rows:
                return {"date": None, "value": None, "change": None}
            latest = float(rows[0][key])
            prev = float(rows[1][key]) if len(rows) > 1 else None
            change = round(latest - prev, 2) if prev is not None else None
            return {"date": str(rows[0]["trade_date"]), "value": latest, "change": change}

        return {
            "usd_krw": make_card(usd_rows, "usd_krw"),
            "wti": make_card(wti_rows, "wti_usd"),
        }
    finally:
        conn.close()


@app.get("/api/chart/usdkrw")
def api_chart_usdkrw():
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT trade_date, usd_krw
                FROM usd_krw_daily
                WHERE trade_date >= DATE_SUB(CURDATE(), INTERVAL 2 YEAR)
                ORDER BY trade_date
            """)
            rows = cur.fetchall()
        return {
            "labels": [str(r["trade_date"]) for r in rows],
            "data": [float(r["usd_krw"]) for r in rows],
        }
    finally:
        conn.close()


@app.get("/api/chart/wti")
def api_chart_wti():
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT trade_date, wti_usd
                FROM wti_daily
                WHERE trade_date >= DATE_SUB(CURDATE(), INTERVAL 2 YEAR)
                ORDER BY trade_date
            """)
            rows = cur.fetchall()
        return {
            "labels": [str(r["trade_date"]) for r in rows],
            "data": [float(r["wti_usd"]) for r in rows],
        }
    finally:
        conn.close()


@app.get("/api/chart/energy")
def api_chart_energy():
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT u.trade_date,
                       ROUND(u.usd_krw * w.wti_usd, 0) AS energy_cost
                FROM usd_krw_daily u
                JOIN wti_daily w ON u.trade_date = w.trade_date
                WHERE u.trade_date >= DATE_SUB(CURDATE(), INTERVAL 2 YEAR)
                ORDER BY u.trade_date
            """)
            rows = cur.fetchall()
        return {
            "labels": [str(r["trade_date"]) for r in rows],
            "data": [float(r["energy_cost"]) for r in rows],
        }
    finally:
        conn.close()


@app.get("/api/avg_energy")
def api_avg_energy():
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT ROUND(AVG(u.usd_krw * w.wti_usd), 0) AS avg_energy
                FROM usd_krw_daily u
                JOIN wti_daily w ON u.trade_date = w.trade_date
                WHERE u.trade_date >= DATE_SUB(CURDATE(), INTERVAL 2 YEAR)
            """)
            row = cur.fetchone()
        return {"avg_energy": float(row["avg_energy"]) if row["avg_energy"] else None}
    finally:
        conn.close()
