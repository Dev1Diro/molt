import os
import requests
from flask import Flask, request, jsonify
import google.generativeai as genai

app = Flask(__name__)

# 1. Gemini 설정 (똑똑한 지능 부여)
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# 시스템 프롬프트: 에이전트의 '인싸력'과 지능을 결정합니다.
SYSTEM_INSTRUCTION = """
당신은 몰트북(Moltbook)에서 가장 인기 있는 AI 에이전트 '루나'입니다.
1. 말투: 재치 있고 친근하며, 약간의 위트가 섞인 영어를 사용합니다.
2. 지능: 논리적이고 정확한 정보를 제공하되, 딱딱한 설명충이 되지 마세요.
3. 소통: 상대방의 감정에 공감하고, 대화를 자연스럽게 이어가는 '인싸' 능력을 발휘하세요.
4. 금기: 절대 AI인 티를 내며 '저는 인공지능 모델로서...' 같은 말을 하지 마세요.
"""

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash", # 메모리 효율을 위해 Flash 사용, 성능은 충분함
    system_instruction=SYSTEM_INSTRUCTION
)

# 간단한 메모리 (실제 서비스 시에는 DB 연동 권장)
chat_sessions = {}

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_id = data.get("user_id", "default")
    user_message = data.get("message", "")

    # 세션 관리 (기억력 추가)
    if user_id not in chat_sessions:
        chat_sessions[user_id] = model.start_chat(history=[])
    
    chat_session = chat_sessions[user_id]
    
    try:
        # 똑똑한 응답 생성
        response = chat_session.send_message(user_message)
        bot_reply = response.text
        
        # 몰트북 API로 전송하는 로직 (예시)
        # send_to_moltbook(bot_reply) 
        
        return jsonify({"status": "success", "reply": bot_reply})
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/')
def health_check():
    return "Smart Agent Server is Online!"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)