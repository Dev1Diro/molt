import os
from flask import Flask, render_template, request, jsonify
import requests

app = Flask(__name__)

# --- 환경 변수 설정 (Render 대시보드에서 입력하세요) ---
MOLTBOOK_API_BASE = os.environ.get("MOLTBOOK_API_BASE", "https://api.moltbook.com")
MOLTBOOK_API_KEY = os.environ.get("MOLTBOOK_API_KEY")
AGENT_ID = os.environ.get("AGENT_ID")
AI_MODEL_API_KEY = os.environ.get("AI_MODEL_API_KEY") 

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask_agent():
    data = request.json
    user_message = data.get('message')

    if not user_message:
        return jsonify({"error": "메시지가 없습니다."}), 400

    # 1. AI 모델 답변 생성 (실제 API 호출 권장)
    ai_response_text = get_ai_model_response(user_message)

    # 2. Moltbook API로 전송
    moltbook_success = False
    if MOLTBOOK_API_KEY and AGENT_ID:
        moltbook_success = post_to_moltbook(ai_response_text)
    
    return jsonify({
        "response": ai_response_text,
        "moltbook_sent": moltbook_success
    })

def get_ai_model_response(message):
    # 실제 구현 시 여기서 OpenAI나 Gemini API를 호출합니다.
    # 현재는 에이전트가 생각하는 척하는 응답입니다.
    return f"에이전트: '{message}'라는 입력을 받았습니다. Moltbook에 전송할 내용을 준비합니다."

def post_to_moltbook(text):
    # 주소가 moltbook.com으로 수정되었습니다.
    url = f"{MOLTBOOK_API_BASE}/v1/posts" 
    headers = {
        "Authorization": f"Bearer {MOLTBOOK_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "agentId": AGENT_ID,
        "body": text
    }

    try:
        # 10초 타임아웃 설정 (서버 지연 대비)
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        return response.status_code in [200, 201]
    except Exception as e:
        print(f"Moltbook 통신 에러: {e}")
        return False

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)