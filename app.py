from flask import Flask, render_template, request, redirect, url_for, abort, make_response
import json
import os
from datetime import datetime, timezone, timedelta
import csv
import io

app = Flask(__name__)

DATA_FILE = "data.json"

# 한국 시간(KST)
KST = timezone(timedelta(hours=9))


MISSIONS = [
    ("칭찬", "칭찬 3개"),
    ("대화하기", "먼저 말 걸고 대화하기"),
    ("간식", "작은 간식 주기"),
    ("인사", "먼저 인사하기"),
    ("응원 메시지", "응원하는 메시지 적고 본인을 찾을 수 있는 힌트 남기는 쪽지 주기"),
    ("3행시", "마니또 이름으로 3행시"),
    ("얼굴 그리기", "정성을 담아서 마니또 얼굴 그려주기"),
    ("노래 한소절", "마니또 앞에서 노래 한 소절 부르기"),
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
        "checks": checks,  # 문자열 또는 리스트 저장
        "time": datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S"),
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
    checks = request.form.getlist("checks")  # 여러 개 받기

    save_record(name, checks)

    return render_template("result.html", name=name, checks=checks)


# ======================
# 관리자 페이지 (요약 + 링크)
# ======================
@app.route("/admin")
def admin_page():
    data = load_records()

    # 전체 기록 (정렬 없이 원본 순서)
    records = data

    # 마지막 5개 기록 (최신순)
    summary = data[-5:][::-1]

    return render_template("admin.html", records=records, summary=summary)


# ======================
# 관리자 전체 표 페이지 (/admin/summary)
#   - sort=1 → 이름순
#   - sort=0 → 저장된 순서
#   - 각 record에 원본 인덱스(_idx) 부여
# ======================
@app.route("/admin/summary")
def admin_summary():
    all_records = load_records()

    # sort 파라미터: 1이면 이름순
    sort_mode = (request.args.get("sort") or "0") == "1"

    # 원본 인덱스(_idx)를 들고 있는 리스트로 변환
    records = [
        {**r, "_idx": i}
        for i, r in enumerate(all_records)
    ]

    if sort_mode:
        # 이름 기준으로 정렬 (표시 순서만 바뀜, _idx는 그대로 유지)
        records.sort(key=lambda r: r.get("name", ""))

    return render_template("summary.html", records=records, missions=MISSIONS, sort=sort_mode)


# ======================
# /admin/summary 결과를 CSV(엑셀)로 다운로드
# ======================
@app.route("/admin/summary/export")
def export_summary():
    all_records = load_records()
    sort_mode = (request.args.get("sort") or "0") == "1"

    # admin_summary와 동일하게 _idx를 붙여서 정렬
    rows = [
        {**r, "_idx": i}
        for i, r in enumerate(all_records)
    ]

    if sort_mode:
        rows.sort(key=lambda r: r.get("name", ""))

    # CSV 작성
    output = io.StringIO()
    writer = csv.writer(output)

    # 헤더: 번호, 이름, 미션들, 제출 시각
    header = ["번호", "이름"] + [col for col, _ in MISSIONS] + ["제출 시각"]
    writer.writerow(header)

    for idx, r in enumerate(rows, start=1):
        name = r.get("name", "")
        checks = r.get("checks", [])

        # checks를 리스트로 통일
        if isinstance(checks, str):
            checks_list = [checks]
        elif isinstance(checks, list):
            checks_list = checks
        else:
            checks_list = []

        row = [idx, name]

        # 각 미션별로 O / -
        for _, value in MISSIONS:
            row.append("O" if value in checks_list else "-")

        row.append(r.get("time", ""))
        writer.writerow(row)

    csv_text = output.getvalue()

    # 윈도우 엑셀에서 한글 안 깨지게 cp949(EUC-KR)로 인코딩
    csv_bytes = csv_text.encode("cp949", "ignore")

    response = make_response(csv_bytes)
    filename = "summary_name.csv" if sort_mode else "summary_order.csv"
    response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    response.headers["Content-Type"] = "text/csv; charset=cp949"


    return response


# ======================
# 이름 수정 페이지 (/admin/edit/<idx>)
#   - GET : 수정 페이지 표시
#   - POST: 이름 저장 후 /admin/summary로 리다이렉트
# ======================
@app.route("/admin/edit/<int:idx>", methods=["GET", "POST"])
def edit_page(idx):
    records = load_records()

    if idx < 0 or idx >= len(records):
        abort(404)

    if request.method == "POST":
        new_name = (request.form.get("name") or "").strip()
        sort_mode = request.form.get("sort", "0")

        if new_name:
            records[idx]["name"] = new_name
            save_records(records)

        return redirect(url_for("admin_summary", sort=sort_mode))

    # GET 요청 → 현재 이름을 들고 수정 페이지 렌더링
    current_name = records[idx].get("name", "")
    sort_mode = request.args.get("sort", "0")

    return render_template(
        "edit_name.html",
        name=current_name,
        idx=idx,
        sort=sort_mode,
    )


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

    # 3) 전체 요약(/admin/summary)에서 삭제한 경우
    if source == "summary":
        sort = request.form.get("sort", "0")
        return redirect(url_for("admin_summary", sort=sort))

    # 4) 기본: 전체 요약 페이지로
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

    return render_template("search.html", query=query, records=filtered, missions=MISSIONS)


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
        missions=MISSIONS,
    )


# ======================
# 서버 실행
# ======================
if __name__ == "__main__":
    app.run()