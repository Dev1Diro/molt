import os
from flask import Flask, request, jsonify, render_template
import google.generativeai as genai

app = Flask(__name__)

# API 키 설정
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# 404 에러 방지를 위한 정확한 모델 경로 설정
# v1beta 환경에서도 인식할 수 있도록 'models/'를 명시합니다.
model = genai.GenerativeModel(
    model_name="models/gemini-1.5-flash", 
    system_instruction="You are Luna, a witty English-speaking AI agent on Moltbook. Stay in character."
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

        response = chat_sessions[user_id].send_message(message)
        return jsonify({"reply": response.text})
    except Exception as e:
        # 에러 발생 시 상세 내용을 로그에 남깁니다.
        print(f"Detailed Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)