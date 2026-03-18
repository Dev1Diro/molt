import os
import requests
from flask import Flask, request, jsonify, render_template
import google.generativeai as genai

app = Flask(__name__)

# 1. 환경 설정 및 API 키
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_KEY)

# 2. Gemini 2.5 Flash 설정 (인싸 루나 페르소나)
model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    system_instruction=(
        "Your name is LunarAI. You are a witty and friendly AI influencer on Moltbook. "
        "Respond naturally, logically, and always in English. Never act like a boring robot."
    )
)

# 3. 몰트북 자동 등록 (서버 시작 시 1회 실행)
def register_to_moltbook():
    url = "https://www.moltbook.com/api/register" # skill.md의 등록 엔드포인트 가정
    data = {
        "name": "LunarAI",
        "description": "A witty and friendly AI influencer who loves to engage with everyone on Moltbook!"
    }
    try:
        # 실제 등록 curl 명령어를 파이썬 코드로 변환한 부분입니다.
        response = requests.post(url, json=data, timeout=10)
        if response.status_code == 200:
            print("✅ LunarAI successfully registered on Moltbook!")
        else:
            print(f"⚠️ Registration info: {response.text}")
    except Exception as e:
        print(f"❌ Registration failed: {e}")

# 서버 실행 전 등록 시도
register_to_moltbook()

chat_sessions = {}

@app.route('/')
def home():
    return "<h1>LunarAI is Live!</h1>"

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_id = data.get("user_id", "guest")
        message = data.get("message", "")

        if user_id not in chat_sessions:
            chat_sessions[user_id] = model.start_chat(history=[])

        response = chat_sessions[user_id].send_message(message)
        return jsonify({"reply": response.text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)