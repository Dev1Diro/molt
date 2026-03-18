import os
from flask import Flask, request, jsonify, render_template
import google.generativeai as genai

app = Flask(__name__)

# API 키 설정
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# 골치 아픈 1.5를 버리고 최신 gemini-2.5-flash로 깔끔하게 갈아탑니다.
# 공식 문서의 최신 규격에 맞춰 에러를 원천 차단했습니다.
model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    system_instruction=(
        "You are Luna, a witty English-speaking AI agent on Moltbook. "
        "Respond naturally and logically in English only. "
        "Never act like a robot."
    )
)

chat_sessions = {}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_id = data.get("user_id", "guest")
        message = data.get("message", "")

        if user_id not in chat_sessions:
            chat_sessions[user_id] = model.start_chat(history=[])

        chat_session = chat_sessions[user_id]
        response = chat_session.send_message(message)
        
        return jsonify({"reply": response.text})
    except Exception as e:
        print(f"🔥 Gemini 2.5 Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)