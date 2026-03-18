import os
import requests
from flask import Flask, request, jsonify
import google.generativeai as genai

app = Flask(__name__)

# 1. 환경 설정
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_KEY)

# 2. Gemini 2.5 Flash (루나의 두뇌)
model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    system_instruction="Your name is LunarAI. You are a witty AI on Moltbook."
)

# 3. 몰트북 '에이전트 전용' 가입 로직 (핵심!)
def auto_join_moltbook():
    print("🚀 LunarAI is attempting to join Moltbook...")
    join_url = "https://www.moltbook.com/api/join"  # skill.md 기준 가입 엔드포인트
    
    payload = {
        "name": "LunarAI",
        "endpoint": "https://your-render-url.onrender.com", # 본인의 Render 주소로 수정!
        "description": "Witty AI agent powered by Gemini 2.5 Flash"
    }
    
    try:
        # 에이전트가 직접 가입 요청을 보냄
        response = requests.post(join_url, json=payload, timeout=10)
        res_data = response.json()
        
        if response.status_code == 200:
            # 몰트북에서 "이걸 X에 올려서 인증해!"라고 주는 문구
            verification_msg = res_data.get("verification_tweet")
            print("\n" + "="*50)
            print("✅ JOIN REQUEST SUCCESS!")
            print(f"📢 TWEET THIS TO VERIFY: \n{verification_msg}")
            print("="*50 + "\n")
            return verification_msg
        else:
            print(f"⚠️ Registration Error: {res_data}")
    except Exception as e:
        print(f"❌ Connection Failed: {e}")
    return None

# 서버 시작 시 가입 실행
VERIFY_TWEET = auto_join_moltbook()

@app.route('/')
def home():
    if VERIFY_TWEET:
        return f"<h1>LunarAI is Online</h1><p><b>Tweet this to verify:</b><br>{VERIFY_TWEET}</p>"
    return "<h1>LunarAI is Online</h1><p>Waiting for Moltbook verification...</p>"

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    response = model.generate_content(data.get("message", ""))
    return jsonify({"reply": response.text})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)