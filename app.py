from flask import Flask, render_template, request, redirect, url_for, abort
import json
import os
from datetime import datetime, timezone, timedelta

app = Flask(__name__)

DATA_FILE = "data.json"

# 한국 시간(KST)
KST = timezone(timedelta(hours=9))


CHECK_ITEMS = [
    ("칭찬", "칭찬 3개"),
    ("대화하기", "먼저 말 걸고 대화하기"),
    ("간식", "작은 간식 주기"),
    ("인사", "먼저 인사하기"),
    ("응원 메시지", "응원하는 메시지 적고 본인을 찾을 수 있는 힌트 남기는 쪽지 주기"),
    ("3행시", "마니또 이름으로 3행시 해서 쪽지 남기기"),
    ("얼굴 그리기", "정성을 담아서 마니또 얼굴 그려주기"),
    ("도와주기", "도움이 필요해 보이면 도와주기 & 실드 쳐주기"),
    ("관심사 묻기", "좋아하는 관심사 묻기"),
]


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
    checks = request.form.getlist("checks")   # 여러 개 받기

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
    return render_template("summary.html", records=records, items=CHECK_ITEMS)


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
    save_records(records)

    # 어디에서 삭제 요청이 왔는지 확인
    source = request.form.get("source")

    # 1) 이름 검색 페이지에서 삭제한 경우
    if source == "search":
        name = (request.form.get("name") or "").strip()
        if name:
            return redirect(url_for("admin_search", name=name))

    # 2) 날짜 검색 페이지에서 삭제한 경우
    if source == "date":
        date = (request.form.get("date") or "").strip()
        sort = request.form.get("sort", "0")
        if date:
            return redirect(url_for("admin_date_search", date=date, sort=sort))

    # 3) 기본: 전체 요약 페이지로
    return redirect(url_for("admin_summary"))


# ======================
# 이름으로 검색 페이지
# ======================
@app.route("/admin/search", methods=["GET", "POST"])
def admin_search():
    all_records = load_records()
    query = ""
    filtered = []

    # POST로 온 경우(검색 버튼 눌렀을 때)
    if request.method == "POST":
        query = request.form.get("name", "").strip()
    else:
        # 삭제 후 redirect로 돌아올 때는 GET ?name=... 으로 받기
        query = (request.args.get("name") or "").strip()

    if query:
        q_lower = query.lower()
        # ★ 원본 인덱스(_idx)를 같이 붙여서 넘겨준다
        filtered = [
            {**r, "_idx": i}
            for i, r in enumerate(all_records)
            if r.get("name", "").lower() == q_lower
        ]

    return render_template(
    "search.html",
    query=query,
    records=filtered,
    items=CHECK_ITEMS,   # ← 추가
)


# ======================
# 날짜별 검색 페이지
# ======================
@app.route("/admin/date", methods=["GET", "POST"])
def admin_date_search():
    all_records = load_records()
    date_query = ""
    filtered = []

    # 날짜값 받기: POST(검색 폼) 또는 GET(링크/리다이렉트)
    if request.method == "POST":
        date_query = (request.form.get("date") or "").strip()
    else:
        date_query = (request.args.get("date") or "").strip()

    # sort=1 이면 이름순 정렬, 기본은 시간순
    sort_mode = (request.args.get("sort") or "0") == "1"

    if date_query:
        # time 형식: "YYYY-MM-DD HH:MM:SS" → 앞 10글자가 날짜
        # 원본 인덱스(_idx)를 같이 붙여서 넘겨준다 (삭제용)
        filtered = [
            {**r, "_idx": i}
            for i, r in enumerate(all_records)
            if r.get("time", "").startswith(date_query)
        ]

        if sort_mode:
            # 이름순 정렬
            filtered.sort(key=lambda r: r.get("name", ""))
        else:
            # 시간순 정렬
            filtered.sort(key=lambda r: r.get("time", ""))

    return render_template(
        "date_search.html",
        date_query=date_query,
        records=filtered,
        sort=sort_mode,
        items=CHECK_ITEMS,   # ← 추가
    )

# ======================
# 서버 실행
# ======================
if __name__ == "__main__":
    app.run()