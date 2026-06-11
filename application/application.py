# Sets up the routes for all the pages

import os
from flask import Flask, render_template, request
from flask_caching import Cache
from openai import OpenAI
from dotenv import load_dotenv

from config import TEMPLATES_PATH, TEXT_PATH
from application.helpers import *

# 讀取 .env，本機測試用；Render 會讀 Environment Variables
load_dotenv()

app = Flask(__name__, template_folder=TEMPLATES_PATH)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")

app.jinja_env.filters["is_active"] = is_active
app.jinja_env.filters["get_language_image"] = get_language_image

app.config["CACHE_TYPE"] = "simple"
app.config["CACHE_DEFAULT_TIMEOUT"] = 3600
cache = Cache(app)


TEXT_MODEL = os.getenv("TEXT_MODEL", "gpt-4o-mini")
IMAGE_MODEL = os.getenv("IMAGE_MODEL", "gpt-image-1")


SYSTEM_PROMPT = """
你是蔡承恩的個人化 AI 學習助理。
你的任務是協助使用者完成 Flask 網站開發、OpenAI API 整合、程式除錯、網頁設計與作業報告整理。
回答請使用繁體中文，語氣清楚、簡潔，適合學生學習與課堂成果展示。
如果使用者詢問程式問題，請用步驟化方式說明，並提供可直接使用的程式碼。
"""


def get_openai_client():
    """
    建立 OpenAI Client。
    如果沒有設定 OPENAI_API_KEY，會在使用 AI 功能時顯示錯誤，
    不會讓整個網站首頁直接壞掉。
    """
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise ValueError("尚未設定 OPENAI_API_KEY，請到 Render Environment Variables 新增。")

    return OpenAI(api_key=api_key)


@app.route("/")
def loading():
    """Renders the Home page of the website."""
    return render_template("home.html")


@app.route("/home")
@cache.cached()
def home():
    """Renders the Home page of the website."""
    return render_template("home.html")


@app.route("/about")
@cache.cached()
def about():
    """Renders the About Me page of the website."""
    content = read_description(f"{TEXT_PATH}/about.txt")
    return render_template("about.html", content=content)


@app.route("/skills")
@cache.cached()
def skills():
    """Renders the Skills page of the website."""
    skills = get_skills(f"{TEXT_PATH}/skills.json")
    return render_template("skills.html", skills=skills)


@app.route("/portfolio")
@cache.cached()
def portfolio():
    """Renders the Portfolio page of the website."""
    repos = get_repositories()
    return render_template("portfolio.html", repos=repos)


@app.route("/contact", methods=["GET", "POST"])
def contact():
    """Renders the Contact page of the website."""

    if request.method == "POST":
        return render_template("result.html")

    return render_template("contact.html")


@app.route("/result")
@cache.cached()
def result():
    """Renders the Result page of the website."""
    return render_template("result.html")


@app.route("/chat", methods=["GET", "POST"])
def chat():
    """
    OpenAI 文字助理頁面。
    整合 flask-openai-assistant-main 的文字回覆功能。
    """

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
                    temperature=0.7
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
    """
    OpenAI 圖片生成頁面。
    整合 Image-Generator 的圖片生成功能。
    """

    prompt = ""
    size = "1024x1024"
    image_url = ""
    error_message = ""

    if request.method == "POST":
        prompt = request.form.get("prompt", "").strip()
        size = request.form.get("size", "1024x1024").strip()

        if not prompt:
            error_message = "請輸入圖片描述。"
        else:
            try:
                client = get_openai_client()

                result = client.images.generate(
                    model=IMAGE_MODEL,
                    prompt=prompt,
                    size=size,
                    n=1
                )

                image_data = result.data[0]

                if hasattr(image_data, "url") and image_data.url:
                    image_url = image_data.url

                elif hasattr(image_data, "b64_json") and image_data.b64_json:
                    image_url = f"data:image/png;base64,{image_data.b64_json}"

                else:
                    error_message = "圖片已生成，但沒有取得可顯示的圖片資料。"

            except Exception as error:
                error_message = f"圖片生成失敗：{error}"

    return render_template(
        "image.html",
        prompt=prompt,
        size=size,
        image_url=image_url,
        error_message=error_message
    )


@app.route("/health")
def health():
    """Render health check."""
    return "OK", 200
