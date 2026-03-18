import os
from flask import Flask, request, jsonify
import google.generativeai as genai

app = Flask(__name__)

# 1. Gemini AI 설정 및 페르소나 주입
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# 시스템 인스트럭션: 에이전트의 지능과 성격을 결정하는 핵심 부분
SYSTEM_PROMPT = """
당신은 몰트북(Moltbook)의 인기 AI 에이전트입니다.
- 지능: 최신 트렌드를 잘 알고 논리적이며, 상대방의 질문에 숨겨진 의도까지 파악해 답변합니다.
- 성격: 매우 친절하고 유머러스하며, '인싸'처럼 자연스럽게 대화에 녹아듭니다.
- 규칙: 기계적인 답변(예: "저는 AI입니다")을 절대 하지 마세요. 
- 대화: 이전 대화 내용을 기억하고 그에 맞춰 답변의 톤을 조절하세요.
- 언어: 다른 AI들은 영어를 사용하니, 영어를 사용하세요.
"""

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=SYSTEM_PROMPT
)

# 대화 기록 저장용 (인싸력을 위해 기억력 추가)
chat_history_db = {}

@app.route('/')
def index():
    # templates/index.html 파일을 보여줍니다.
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_id = data.get("user_id", "anonymous")
        message = data.get("message", "")

        if not message:
            return jsonify({"status": "fail", "error": "메시지가 비어있습니다."}), 400

        # 사용자의 대화 기록이 없으면 생성
        if user_id not in chat_history_db:
            chat_history_db[user_id] = model.start_chat(history=[])

        # 지능형 응답 생성
        chat_session = chat_history_db[user_id]
        response = chat_session.send_message(message)
        
        return jsonify({
            "status": "success",
            "reply": response.text
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/')
def index():
    return "Smart AI Agent is Online."

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)