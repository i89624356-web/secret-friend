from flask import Flask, render_template, request
import json
import os

app = Flask(__name__)

DATA_FILE = "data.json"

# ======================
# 기록 저장 함수
# ======================
def save_record(name, checks):
    record = {"name": name, "checks": checks}

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

    # 저장
    save_record(name, checks)

    return render_template("result.html", name=name, checks=checks)


# ======================
# 관리자 페이지
# ======================
@app.route("/admin")
def admin_page():
    # data.json 없으면 빈 화면
    if not os.path.exists(DATA_FILE):
        return render_template("admin.html", records=[])

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    return render_template("admin.html", records=data)


if __name__ == "__main__":
    app.run()