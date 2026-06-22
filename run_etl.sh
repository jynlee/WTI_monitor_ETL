#!/bin/bash

# 이 스크립트가 있는 디렉토리를 기준으로 실행
# (crontab은 작업 디렉토리가 HOME이라 절대경로로 고정)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_FILE="$SCRIPT_DIR/etl.log"

{
    echo "=========================================="
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ETL 시작"

    # venv 활성화 후 etl.py 실행
    source "$SCRIPT_DIR/venv/bin/activate"
    python "$SCRIPT_DIR/etl.py"

    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ETL 종료"
} >> "$LOG_FILE" 2>&1
