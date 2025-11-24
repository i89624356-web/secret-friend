from flask import Flask, render_template, request
import pandas as pd
from datetime import datetime
import os

app = Flask(__name__)

DATA_FILE = "data.csv"

# 데이터 파일 없으면 헤더 추가
if not os.path.exists(DATA_FILE):
    pd.DataFrame(columns=["name", "items", "time"]).to_csv(DATA_FILE, index=False)

@app.route("/")
def home():
    return render_template("form.html")

@app.route("/submit", methods=["POST"])
def submit():
    name = request.form["name"]
    items = request.form.getlist("items")
    
    row = {
        "name": name,
        "items": ",".join(items),
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    df = pd.DataFrame([row])
    df.to_csv(DATA_FILE, mode="a", index=False, header=False)

    return "<h2>제출 완료!</h2>"

@app.route("/admin")
def admin():
    df = pd.read_csv(DATA_FILE)
    return df.to_html()

if __name__ == "__main__":
    app.run(debug=True)