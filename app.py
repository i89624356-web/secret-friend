from flask import Flask, render_template, request
import json
import os
from datetime import datetime, timezone, timedelta

app = Flask(__name__)

DATA_FILE = "data.json"

# 한국 시간(KST)
KST = timezone(timedelta(hours=9))


# ======================
# 기록 저장 함수
# ======================
def save_record(name, checks):
    record = {
        "name": name,
        "checks": checks,
        "time": datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")  # 한국 시간 저장
    }

    # data.json 없으면 빈 리스트 생성
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=4)

    # 기존 데이터 불러오기
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 기록 추가
    data.append(record)

    # 다시 저장
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


# ======================
# 메인 입력 페이지
# ======================
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")


# ======================
# 제출 → 저장 → 결과 페이지
# ======================
@app.route("/result", methods=["POST"])
def result():
    name = request.form.get("name")
    checks = request.form.getlist("checks")

    save_record(name, checks)

    return render_template("result.html", name=name, checks=checks)


# ======================
# 관리자 페이지 (링크 + 최근 5개 요약)
# ======================
@app.route("/admin")
def admin_page():
    if not os.path.exists(DATA_FILE):
        return render_template("admin.html", records=[], summary=[])

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 전체 기록
    records = data

    # 마지막 5개 기록 (최신순)
    summary = data[-5:][::-1]

    return render_template("admin.html", records=records, summary=summary)


# ======================
# 관리자 전체 표 페이지
# ======================
@app.route("/admin/summary")
def admin_summary():
    if not os.path.exists(DATA_FILE):
        records = []
    else:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            records = json.load(f)

    return render_template("summary.html", records=records)


# ======================
# 서버 실행
# ======================
if __name__ == "__main__":
    app.run()