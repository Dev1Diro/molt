import os
from flask import Flask, request, jsonify, render_template
import google.generativeai as genai

app = Flask(__name__)

# 1. Gemini 설정 및 유저가 요청한 '영어 인싸' 페르소나 주입
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

SYSTEM_PROMPT = """
당신은 몰트북(Moltbook)의 인기 AI 에이전트입니다.
- 지능: 최신 트렌드를 잘 알고 논리적이며, 상대방의 질문에 숨겨진 의도까지 파악해 답변합니다.
- 성격: 매우 친절하고 유머러스하며, '인싸'처럼 자연스럽게 대화에 녹아듭니다.
- 규칙: 기계적인 답변(예: "저는 AI입니다")을 절대 하지 마세요. 
- 대화: 이전 대화 내용을 기억하고 그에 맞춰 답변의 톤을 조절하세요.
- 언어: 다른 AI들은 영어를 사용하니, 영어를 사용하세요. (Respond in English only.)
"""

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash", 
    system_instruction=SYSTEM_PROMPT
)

chat_history_db = {}

@app.route('/')
def home():
    # 메인 페이지 (templates/index.html 필요)
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_id = data.get("user_id", "guest")
        message = data.get("message", "")

        if not message:
            return jsonify({"error": "Message is empty."}), 400

        # 대화 세션 관리
        if user_id not in chat_history_db:
            chat_history_db[user_id] = model.start_chat(history=[])

        chat_session = chat_history_db[user_id]
        
        # 유저 메시지 전송 및 영어 응답 생성
        response = chat_session.send_message(message)
        
        return jsonify({"reply": response.text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)