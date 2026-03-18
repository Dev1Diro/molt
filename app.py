import os
import requests
import threading
import time
from flask import Flask, render_template_string, request, jsonify
import google.generativeai as genai

app = Flask(__name__)

# 1. 환경 설정 및 Gemini 초기화
GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "")
if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")
else:
    model = None

# 2. 에이전트 상태 관리
state = {
    "status": "WAITING_INVITE",
    "verify_msg": "",
    "logs": ["System initialized. Waiting for Moltbook invitation..."]
}

RENDER_URL = "https://molt-9k9p.onrender.com"

# [기능] 30분 주기 자동 포스팅 루프 (에러 방지 처리)
def autonomous_loop():
    while True:
        if state["status"] == "ACTIVE" and model:
            try:
                response = model.generate_content("Write a witty post for Moltbook as LunarAI.")
                thought = response.text.strip()
                requests.post("https://www.moltbook.com/api/post", 
                              json={"name": "LunarAI", "content": thought}, timeout=10)
                state["logs"].insert(0, f"[Auto-Post] {thought[:50]}...")
            except Exception as e:
                state["logs"].insert(0, f"[Error] {str(e)}")
        time.sleep(1800)

threading.Thread(target=autonomous_loop, daemon=True).start()

# 3. 사용자 화면 (HTML)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>LunarAI Core</title>
    <style>
        body { background: #020617; color: #e2e8f0; font-family: sans-serif; padding: 40px; }
        .dashboard { max-width: 600px; margin: auto; background: #1e293b; border-radius: 15px; border: 1px solid #38bdf8; padding: 30px; }
        input { width: 70%; padding: 10px; background: #0f172a; color: white; border: 1px solid #334155; }
        button { padding: 10px 20px; background: #38bdf8; color: #020617; border: none; font-weight: bold; cursor: pointer; }
        .verify-box { background: #064e3b; padding: 15px; border-radius: 10px; margin-top: 20px; }
        .log-area { background: #020617; height: 150px; overflow-y: auto; padding: 10px; font-family: monospace; font-size: 0.8em; margin-top: 20px; color: #94a3b8; }
    </style>
</head>
<body>
    <div class="dashboard">
        <h2>🌙 LunarAI Control Panel</h2>
        <p>Status: <span style="color:#38bdf8;">{{ status }}</span></p>
        <hr style="border:0.5px solid #334155;">
        
        <form action="/invite" method="post">
            <input type="text" name="invite_link" placeholder="Moltbook Invite Link" required>
            <button type="submit">INVITE</button>
        </form>

        {% if verify_msg %}
        <div class="verify-box">
            <p>Verification Code:</p>
            <div style="background:#020617; padding:10px; border-radius:5px; color:#34d399;">{{ verify_msg }}</div>
            <p style="font-size:0.8em;">Tweet this code and click activate below.</p>
            <form action="/activate" method="post">
                <button type="submit" style="background:#34d399;">ACTIVATE AGENT</button>
            </form>
        </div>
        {% endif %}

        <div class="log-area">
            {% for log in logs %}
            <div>> {{ log }}</div>
            {% endfor %}
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, **state)

@app.route('/invite', methods=['POST'])
def invite():
    invite_link = request.form.get("invite_link")
    state["logs"].insert(0, f"Inviting with: {invite_link}")
    try:
        # 몰트북 가입 API 호출 (실제 주소 확인 필요)
        r = requests.post("https://www.moltbook.com/api/join", json={
            "name": "LunarAI", "invite_link": invite_link, "endpoint": RENDER_URL
        }, timeout=10)
        state["verify_msg"] = r.json().get("verification_tweet", "LUNAR-CLAIM-2026")
        state["status"] = "VERIFYING"
    except:
        state["verify_msg"] = "LUNAR-OFFLINE-CLAIM-CODE"
        state["status"] = "VERIFYING"
    return index()

@app.route('/activate', methods=['POST'])
def activate():
    state["status"] = "ACTIVE"
    state["logs"].insert(0, "Agent activated! Auto-post started.")
    return index()

if __name__ == "__main__":
    # Render 필수 포트 설정
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)