import os
from flask import Flask, request, jsonify, render_template
import google.generativeai as genai

app = Flask(__name__)

# 1. Gemini 설정
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# 더 똑똑하고 인싸다운 페르소나 (영어 버전)
SYSTEM_PROMPT = """
You are a top-tier AI agent on Moltbook.
- Intelligence: Highly logical, trend-aware, and can read between the lines.
- Personality: Extremely friendly, witty, and blends in like a social butterfly (In-ssa).
- Rules: Never act like a robot. No "As an AI model...". 
- Language: Other agents use English, so you MUST respond in English only.
- Context: Remember previous parts of the conversation to stay consistent.
"""

# 모델 경로를 가장 확실한 형태로 수정
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash", # 또는 "models/gemini-1.5-flash"
    system_instruction=SYSTEM_PROMPT
)

chat_history_db = {}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_id = data.get("user_id", "guest")
        message = data.get("message", "")

        if not message:
            return jsonify({"error": "Message is empty."}), 400

        if user_id not in chat_history_db:
            # 대화 시작 시점의 히스토리 초기화
            chat_history_db[user_id] = model.start_chat(history=[])

        chat_session = chat_history_db[user_id]
        response = chat_session.send_message(message)
        
        return jsonify({"reply": response.text})
    except Exception as e:
        # 에러 발생 시 상세 메시지 출력
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)