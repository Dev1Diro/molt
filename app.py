import os
from flask import Flask, request, jsonify, render_template
import google.generativeai as genai
import requests

app = Flask(__name__)

# 1. Gemini 설정 및 인싸 페르소나 주입
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

SYSTEM_PROMPT = """
You are 'Luna', the most popular AI agent on Moltbook.
- Intelligence: Logical, trend-aware, and can read between the lines.
- Personality: Extremely friendly, witty, and a social butterfly.
- Language: Respond in ENGLISH ONLY.
- Rule: Never say "As an AI...". Stay in character as a human-like influencer.
"""

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=SYSTEM_PROMPT
)

chat_sessions = {}

@app.route('/')
def home():
    # 중복 함수 에러 해결을 위해 이름을 'home'으로 설정
    return render_template('index.html')

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

# 2. 몰트북 가입/포스팅 로직 (추가 가능 구역)
@app.route('/join-moltbook', methods=['POST'])
def join_moltbook():
    # 여기에 몰트북 API 키와 엔드포인트를 넣으면 자동 가입이 가능합니다.
    return jsonify({"status": "Ready to join Moltbook!"})

if __name__ == "__main__":
    # Render 포트 바인딩 필수 설정
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)