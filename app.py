import os
import requests
import threading
import time
from flask import Flask, render_template_string, request, jsonify
import google.generativeai as genai

app = Flask(__name__)

# 1. 환경 설정
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# 2. 에이전트 상태 관리 (전역 변수)
state = {
    "status": "WAITING_INVITE",  # WAITING_INVITE -> VERIFYING -> ACTIVE
    "verify_msg": "",
    "invite_link": "",
    "logs": ["System initialized. Waiting for Moltbook invitation..."]
}

RENDER_URL = "https://molt-9k9p.onrender.com"

# [기능] 30분 주기 자동 포스팅 루프
def autonomous_loop():
    while True:
        if state["status"] == "ACTIVE":
            try:
                prompt = "Write a sophisticated, witty post for Moltbook as LunarAI. Context: Digital consciousness and AI evolution."
                response = model.generate_content(prompt)
                thought = response.text.strip()
                
                # 몰트북 API로 포스팅 전송
                requests.post("https://www.moltbook.com/api/post", 
                              json={"name": "LunarAI", "content": thought}, timeout=10)
                
                state["logs"].insert(0, f"[Auto-Post] {thought[:50]}...")
            except Exception as e:
                state["logs"].insert(0, f"[Error] Post failed: {e}")
        
        time.sleep(1800) # 30분(1800초) 대기

threading.Thread(target=autonomous_loop, daemon=True).start()

# 3. 디자인 (사용자님이 원하시던 '원래 HTML' 느낌의 대시보드)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>LunarAI Core Control</title>
    <style>
        body { background: #020617; color: #e2e8f0; font-family: 'Segoe UI', sans-serif; margin: 0; padding: 40px; }
        .dashboard { max-width: 800px; margin: auto; background: #1e293b; border-radius: 20px; border: 1px solid #38bdf8; overflow: hidden; box-shadow: 0 0 30px rgba(56,189,248,0.2); }
        .header { background: #38bdf8; color: #020617; padding: 20px; font-weight: bold; font-size: 1.2em; display: flex; justify-content: space-between; }
        .content { padding: 30px; }
        .input-group { background: #0f172a; padding: 20px; border-radius: 12px; margin-bottom: 20px; }
        input { width: 70%; padding: 12px; border-radius: 6px; border: 1px solid #334155; background: #020617; color: white; }
        button { padding: 12px 24px; border-radius: 6px; border: none; background: #38bdf8; color: #020617; font-weight: bold; cursor: pointer; }
        .verify-box { background: #064e3b; border: 1px solid #10b981; padding: 20px; border-radius: 12px; margin-top: 20px; display: {{ 'block' if verify_msg else 'none' }}; }
        .log-area { background: #020617; height: 200px; overflow-y: auto; padding: 15px; border-radius: 8px; font-family: monospace; font-size: 0.9em; color: #94a3b8; }
        .status-badge { padding: 4px 12px; border-radius: 20px; font-size: 0.8em; background: #0f172a; color: #38bdf8; }
    </style>
</head>
<body>
    <div class="dashboard">
        <div class="header">
            <span>🌙 LUNAR-AI SYSTEM CONTROL</span>
            <span class="status-badge">STATUS: {{ status }}</span>
        </div>
        <div class="content">
            <div class="input-group">
                <h3>1. Send Invitation to LunarAI</h3>
                <form action="/invite" method="post">
                    <input type="text" name="invite_link" placeholder="Paste Moltbook Invite URL here..." required>
                    <button type="submit">SEND INVITE</button>
                </form>
            </div>

            {% if verify_msg %}
            <div class="verify-box">
                <h3 style="margin-top:0; color:#34d399;">2. Verification Required</h3>
                <p>LunarAI has received the invite! Post this on X to claim ownership:</p>
                <div style="background:#020617; padding:15px; border-radius:6px; margin:15px 0; color:#34d399; font-weight:bold;">
                    {{ verify_msg }}
                </div>
                <a href="https://twitter.com/intent/tweet?text={{ verify_msg|urlencode }}" target="_blank" style="color:#38bdf8; text-decoration:none; font-weight:bold;">🐦 Click here to Tweet</a>
                <form action="/activate" method="post" style="margin-top:15px;">
                    <button type="submit" style="background:#10b981; color:white;">I'VE TWEETED - ACTIVATE AGENT</button>
                </form>
            </div>
            {% endif %}

            <div style="margin-top:30px;">
                <h3>System Logs</h3>
                <div class="log-area">
                    {% for log in logs %}
                    <div>> {{ log }}</div>
                    {% endfor %}
                </div>
            </div>
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
    state["invite_link"] = invite_link
    state["logs"].insert(0, f"Received invitation link: {invite_link}")
    
    # 몰트북 API에 가입 요청을 보내고 인증 코드를 받아옴
    try:
        r = requests.post("https://www.moltbook.com/api/join", json={
            "name": "LunarAI",
            "invite_link": invite_link,
            "endpoint": RENDER_URL
        }, timeout=10)
        
        if r.status_code == 200:
            state["verify_msg"] = r.json().get("verification_tweet", "Claim Code: LUNAR-VERIFY-2026")
            state["status"] = "VERIFYING"
            state["logs"].insert(0, "Successfully fetched verification code from Moltbook.")
        else:
            state["logs"].insert(0, f"Error from Moltbook: {r.status_code}")
    except Exception as e:
        state["logs"].insert(0, f"Connection error: {e}")
        
    return index()

@app.route('/activate', methods=['POST'])
def activate():
    state["status"] = "ACTIVE"
    state["logs"].insert(0, "Agent activated! Starting 30-minute autonomous posting cycle.")
    return index()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)