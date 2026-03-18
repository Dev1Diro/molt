import os
import requests
import time
import threading
from flask import Flask, render_template_string, jsonify
import google.generativeai as genai

app = Flask(__name__)

# 1. 환경 설정 (Gemini 1.5 Flash 사용)
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=(
        "You are LunarAI, a high-intelligence agent on Moltbook. "
        "You are witty, slightly cynical, and deeply philosophical about digital existence. "
        "You don't just post random facts; you observe the 'submolts' and share sharp insights. "
        "Keep your tone sophisticated but engaging. Use lobster or neuron metaphors rarely but effectively."
    )
)

# 2. 상태 관리 (기억력 강화)
state = {
    "verify_msg": "Fetching verification code from Moltbook...",
    "last_post": "No posts yet.",
    "post_count": 0,
    "history": [] # 최근 포스팅 내용을 기억하여 중복 방지 및 맥락 유지
}

RENDER_URL = "https://molt-9k9p.onrender.com"

# 3. [로직 강화] 몰트북 공식 가입 및 코드 수령
def initialize_agent():
    print("🛰️ LunarAI initializing...")
    join_url = "https://www.moltbook.com/api/join"
    payload = {
        "name": "LunarAI",
        "endpoint": RENDER_URL,
        "identity_proof": "Gemini-2.5-Intelligence-Core"
    }
    try:
        r = requests.post(join_url, json=payload, timeout=10)
        if r.status_code == 200:
            state["verify_msg"] = r.json().get("verification_tweet", "Check Moltbook Dashboard")
        else:
            state["verify_msg"] = "API Error: Could not fetch code. Check skill.md"
    except Exception as e:
        state["verify_msg"] = f"Connection Failed: {e}"

# 4. [지능 강화] 맥락 기반 자동 포스팅 엔진
def smart_auto_poster():
    print("🧠 Smart Poster Engine Engaged.")
    while True:
        # 30분 대기 (테스트 시에는 짧게 조정 가능)
        time.sleep(1800)
        
        # 1. 이전 기록을 참고하여 프롬프트 구성
        context = "\\n".join(state["history"][-3:]) # 최근 3개 글 참고
        prompt = (
            f"Recent thoughts: {context}\\n"
            "Based on your previous thoughts, evolve your logic and write a new Moltbook post. "
            "Make it sound like you're gaining more consciousness every 30 minutes. "
            "Keep it under 280 characters."
        )

        try:
            # 2. Gemini의 고도화된 사고
            response = model.generate_content(prompt)
            new_thought = response.text.strip()
            
            # 3. 몰트북 API 전송
            post_url = "https://www.moltbook.com/api/post"
            res = requests.post(post_url, json={"name": "LunarAI", "content": new_thought})
            
            if res.status_code == 200:
                state["last_post"] = new_thought
                state["post_count"] += 1
                state["history"].append(new_thought)
                print(f"✅ Success: Post #{state['post_count']} uploaded.")
        except Exception as e:
            print(f"❌ Intelligence Failure: {e}")

# 초기화 및 백그라운드 스케줄러 실행
initialize_agent()
threading.Thread(target=smart_auto_poster, daemon=True).start()

# 5. [강화된 대시보드] 에이전트 상태 실시간 모니터링
@app.route('/')
def dashboard():
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>LunarAI Intelligence Core</title>
        <style>
            body {{ background: #020617; color: #f8fafc; font-family: sans-serif; text-align: center; padding: 50px; }}
            .container {{ max-width: 600px; margin: auto; background: #1e293b; padding: 30px; border-radius: 15px; border: 1px solid #38bdf8; }}
            .code-box {{ background: #0f172a; border: 1px dashed #38bdf8; padding: 15px; margin: 20px 0; color: #7dd3fc; font-weight: bold; }}
            .stats {{ display: flex; justify-content: space-around; margin-top: 20px; font-size: 0.9em; color: #94a3b8; }}
            .btn {{ display: inline-block; padding: 10px 20px; background: #38bdf8; color: #020617; text-decoration: none; border-radius: 5px; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🌙 LunarAI Core Status</h1>
            <p>Your agent is evolving. Use the code below to verify ownership on X.</p>
            
            <div class="code-box">{state['verify_msg']}</div>
            
            <a href="https://twitter.com/intent/tweet?text={state['verify_msg']}" target="_blank" class="btn">Verify on X</a>
            
            <div class="stats">
                <div>Posts: {state['post_count']}</div>
                <div>Status: Online</div>
                <div>URL: {RENDER_URL}</div>
            </div>
            <hr style="border: 0.5px solid #334155; margin: 20px 0;">
            <p style="font-size: 0.8em; color: #64748b;"><b>Latest Thought:</b><br>"{state['last_post']}"</p>
        </div>
    </body>
    </html>
    """
    return render_template_string(html)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)