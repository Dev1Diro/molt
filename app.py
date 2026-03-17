import os
import logging
from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
from google.api_core.exceptions import GoogleAPIError

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API 키 설정
api_key = os.environ.get("GOOGLE_API_KEY")
if not api_key:
    logger.error("GOOGLE_API_KEY 환경 변수가 설정되지 않았습니다")
    raise ValueError("GOOGLE_API_KEY 환경 변수가 필요합니다")

genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask_agent():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"response": "유효한 JSON이 필요합니다", "status": "error"}), 400
        
        msg = data.get('message', '').strip()
        if not msg:
            return jsonify({"response": "메시지가 비어있습니다", "status": "error"}), 400
        
        # 제미나이의 응답 생성
        response = model.generate_content(msg)
        
        if not response or not response.text:
            return jsonify({"response": "응답을 생성할 수 없습니다", "status": "error"}), 500
        
        logger.info(f"성공적인 요청: {msg[:50]}...")
        return jsonify({"response": response.text, "status": "success"}), 200
        
    except GoogleAPIError as e:
        logger.error(f"Google API 오류: {str(e)}")
        return jsonify({"response": "API 오류가 발생했습니다", "status": "error"}), 500
    except Exception as e:
        logger.error(f"예상치 못한 오류: {str(e)}")
        return jsonify({"response": "서버 오류가 발생했습니다", "status": "error"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, debug=False)