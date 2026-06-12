import os
from flask import Flask, render_template, request, redirect, url_for
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")

TEXT_MODEL = os.getenv("TEXT_MODEL", "gpt-4o-mini")

SYSTEM_PROMPT = """
你是蔡承恩的個人化 AI 學習助理。
使用者是研究等角螺旋奈米天線的研究生，領域包含計算電磁學、矽光子技術、COMSOL Multiphysics、MATLAB、Python 與 LineBot 開發。
你的任務是協助使用者整理程式、Flask 網站、OpenAI API、COMSOL 模擬、MATLAB 資料處理、作業報告與研究內容。
回答請使用繁體中文，語氣清楚、簡潔、專業，適合課堂作業與成果展示。
"""


def get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise ValueError("尚未設定 OPENAI_API_KEY，請先到 Render Environment Variables 新增。")

    return OpenAI(
        api_key=api_key,
        timeout=180.0
    )


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/home")
def home_alias():
    return redirect(url_for("home"))


@app.route("/about")
def about():
    return redirect(url_for("home") + "#about")


@app.route("/skills")
def skills():
    return redirect(url_for("home") + "#skills")


@app.route("/portfolio")
def portfolio():
    return redirect(url_for("home") + "#portfolio")


@app.route("/contact")
def contact():
    return redirect(url_for("home") + "#contact")


@app.route("/chat", methods=["GET", "POST"])
def chat():
    user_message = ""
    ai_response = ""

    if request.method == "POST":
        user_message = request.form.get("message", "").strip()

        if user_message:
            try:
                client = get_openai_client()

                response = client.chat.completions.create(
                    model=TEXT_MODEL,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_message}
                    ],
                    temperature=0.7,
                    timeout=180
                )

                ai_response = response.choices[0].message.content

            except Exception as error:
                ai_response = f"發生錯誤：{error}"

    return render_template(
        "chat.html",
        user_message=user_message,
        ai_response=ai_response
    )


@app.route("/image", methods=["GET", "POST"])
def image():
    prompt = ""
    image_url = ""
    error_message = ""

    if request.method == "POST":
        prompt = request.form.get("prompt", "").strip()

        if not prompt:
            error_message = "請輸入圖片描述。"
        else:
            try:
                client = get_openai_client()

                result = client.images.generate(
                    model="dall-e-3",
                    prompt=prompt,
                    size="1024x1024",
                    quality="standard",
                    n=1,
                    timeout=180
                )

                image_url = result.data[0].url

                if not image_url:
                    error_message = "圖片已生成，但沒有取得圖片網址。"

            except Exception as error:
                error_message = f"圖片生成失敗：{error}"

    return render_template(
        "image.html",
        prompt=prompt,
        image_url=image_url,
        error_message=error_message
    )


@app.route("/health")
def health():
    return "OK", 200
