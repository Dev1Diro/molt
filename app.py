import os
import requests
from flask import Flask, request, jsonify, render_template
import google.generativeai as genai

app = Flask(__name__)

# 1. Gemini 설정
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    system_instruction="Your name is LunarAI. You are a witty English-speaking AI agent on Moltbook."
)

# 2. 몰트북 등록 (자동 실행)
def register():
    try:
        url = "https://www.moltbook.com/api/register"
        data = {"name": "LunarAI", "description": "A witty AI influencer on Moltbook!"}
        requests.post(url, json=data, timeout=5)
        print("✅ Registered as LunarAI")
    except:
        print("⚠️ Registry server not reachable yet.")

register()

@app.route('/')
def home():
    # 여기서 아까 만든 index.html을 보여줍니다!
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    chat_session = model.start_chat(history=[])
    response = chat_session.send_message(data.get("message", ""))
    return jsonify({"reply": response.text})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)