import os
from flask import Flask, request, jsonify, render_template
import google.generativeai as genai

app = Flask(__name__)

# 1. API 키 확인 (없으면 에러 출력)
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    print("ERROR: GEMINI_API_KEY is missing!")
else:
    genai.configure(api_key=api_key)

# 페르소나 설정 (영어 인싸 루나)
SYSTEM_PROMPT = """
You are 'Luna', a famous AI agent on Moltbook.
- You are witty, cool, and super smart.
- Never mention you are an AI. 
- You MUST speak English only.
- Be proactive and engaging in every conversation.
"""

# 모델 경로를 가장 표준적인 'models/gemini-1.5-flash'로 변경
model = genai.GenerativeModel(
    model_name="models/gemini-1.5-flash", 
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

        if user_id not in chat_history_db:
            chat_history_db[user_id] = model.start_chat(history=[])

        chat_session = chat_history_db[user_id]
        response = chat_session.send_message(message)
        
        return jsonify({"reply": response.text})
    except Exception as e:
        # 에러 발생 시 로그에 상세 출력
        print(f"🔥 Gemini Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)