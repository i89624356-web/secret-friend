from flask import Flask, render_template, request, redirect, url_for, abort
import json
import os
from datetime import datetime, timezone, timedelta

app = Flask(__name__)

DATA_FILE = "data.json"

# 한국 시간(KST)
KST = timezone(timedelta(hours=9))


# ======================
# 공통: 기록 불러오기 / 저장하기
# ======================
def load_records():
    """data.json에서 전체 기록을 불러온다."""
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_records(records):
    """records 리스트 전체를 data.json에 저장한다."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=4)


# ======================
# 기록 1개 추가 함수
# ======================
def save_record(name, checks):
    records = load_records()

    record = {
        "name": name,
        "checks": checks,  # 문자열 1개 저장됨
        "time": datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")
    }

    records.append(record)
    save_records(records)


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
    checks = request.form.get("checks")  # 하나만 선택할 수 있으므로 get()

    save_record(name, checks)

    return render_template("result.html", name=name, checks=checks)


# ======================
# 관리자 페이지 (요약 + 링크)
# ======================
@app.route("/admin")
def admin_page():
    data = load_records()

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
    records = load_records()
    return render_template("summary.html", records=records)


# ======================
# 특정 데이터 삭제
# ======================
@app.route("/admin/delete/<int:idx>", methods=["POST"])
def delete(idx):
    records = load_records()

    # 인덱스 범위 체크
    if idx < 0 or idx >= len(records):
        abort(404)

    # 해당 기록 삭제
    records.pop(idx)

    # 파일 다시 저장
    save_records(records)

    # 전체 표 페이지로 돌아가기 (엔드포인트 이름은 함수 이름!)
    return redirect(url_for("admin_summary"))


# ======================
# 서버 실행
# ======================
if __name__ == "__main__":
    app.run()