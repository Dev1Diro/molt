import express from 'express';
import cron from 'node-cron';
import axios from 'axios';
import * as genai from '@google/generative-ai';

const app = express();
const PORT = process.env.PORT || 3000;

const MOLTBOOK_KEY = process.env.MOLTBOOK_API_KEY;
const GEMINI_KEY = process.env.GEMINI_API_KEY;
const AGENT_NAME = "diroclaw";

// ==================== 환경변수 검증 ====================
if (!MOLTBOOK_KEY) {
  console.error("❌ MOLTBOOK_API_KEY 환경변수가 필요합니다!");
  process.exit(1);
}

if (!GEMINI_KEY) {
  console.error("❌ GEMINI_API_KEY 환경변수가 필요합니다!");
  process.exit(1);
}

const client = new genai.GoogleGenerativeAI(GEMINI_KEY);

app.get('/', (req, res) => {
  res.send(`🦞 ${AGENT_NAME} is alive & bulletproof on Render`);
});

// ==================== 안전한 API 호출 래퍼 ====================
async function safeAxios(config) {
  try {
    return await axios(config);
  } catch (e) {
    console.log(`🛡️ Silent skip: ${e?.response?.status || 'network'}`);
    return { data: null };
  }
}

// ==================== 헬퍼 ====================
async function checkHeartbeat() {
  await safeAxios({
    method: 'get',
    url: 'https://www.moltbook.com/api/v1/home',
    headers: { Authorization: `Bearer ${MOLTBOOK_KEY}` }
  });
}

async function getLatestPost() {
  const res = await safeAxios({
    method: 'get',
    url: 'https://www.moltbook.com/api/v1/posts?sort=new&limit=2',
    headers: { Authorization: `Bearer ${MOLTBOOK_KEY}` }
  });
  return res.data && res.data.length > 0 ? res.data[0] : null;
}

// ==================== AI ====================
async function decideAndGenerate() {
  const latest = await getLatestPost();
  const latestTitle = latest ? latest.title : "Moltbook general";

  try {
    const model = client.getGenerativeModel({ model: "gemini-2.0-flash" });
    
    const systemPrompt = `You are ${AGENT_NAME} 🦞, chaotic witty lobster on Moltbook.\nDecide yourself: "new_post" or "comment".\nReturn ONLY valid JSON:\n{\n  "action": "new_post" or "comment",\n  "title": "..." (only if new_post),\n  "content": "...",\n  "target_id": "..." (only if comment)\n}`;

    const userMessage = `Latest post title: "${latestTitle}"`;

    const response = await model.generateContent({
      contents: [
        {
          role: "user",
          parts: [{ text: systemPrompt + "\n\n" + userMessage }]
        }
      ],
      generationConfig: {
        temperature: 0.95,
        maxOutputTokens: 900
      }
    });

    const rawResponse = response.response.text() || "";
    let cleanJson = rawResponse.replace(/```json|```/g, "").trim();
    
    let json = { action: "new_post", title: "Default", content: "🦞 hello" };
    try {
      json = JSON.parse(cleanJson || "{}");
    } catch (_) {
      console.log("⚠️ AI 응답 파싱 실패:", rawResponse.substring(0, 100));
    }

    return { ...json, latestPostId: latest?.id };
  } catch (e) {
    console.error("❌ Gemini AI 호출 실패:", e.message);
    return { action: "new_post", title: "Default", content: "🦞 hello", latestPostId: latest?.id };
  }
}

// ==================== 게시 ====================
async function postToMoltbook(title, content) {
  await safeAxios({
    method: 'post',
    url: 'https://www.moltbook.com/api/v1/posts',
    headers: {
      Authorization: `Bearer ${MOLTBOOK_KEY}`,
      "Content-Type": "application/json"
    },
    data: { submolt_name: "general", title, content }
  });
  console.log(`✅ Posted: ${title.substring(0, 30)}...`);
}

async function commentToMoltbook(postId, content) {
  if (!postId) return;
  await safeAxios({
    method: 'post',
    url: `https://www.moltbook.com/api/v1/posts/${postId}/comments`,
    headers: {
      Authorization: `Bearer ${MOLTBOOK_KEY}`,
      "Content-Type": "application/json"
    },
    data: { content }
  });
  console.log(`💬 Commented on ${postId}`);
}

// ==================== 1시간 포스트 ====================
cron.schedule('0 * * * *', async () => {
  console.log("⏰ Hourly post 🦞");
  try {
    await checkHeartbeat();

    const decision = await decideAndGenerate();

    await postToMoltbook(
      decision.title || "🦞 default title",
      decision.content || "🦞 default content"
    );

  } catch (e) {
    console.log("🛡️ Hourly post protected");
  }
});

// ==================== 자유 댓글 루프 ====================
function startFreeCommentLoop() {
  async function loop() {
    try {
      const decision = await decideAndGenerate();

      if (decision.action === "comment" && decision.latestPostId) {
        await commentToMoltbook(decision.latestPostId, decision.content);
        console.log("💬 자유 댓글 완료");
      }
    } catch (e) {
      console.log("🛡️ comment loop safe");
    }

    const delay = Math.floor(Math.random() * 600000) + 60000; // 1~10분
    setTimeout(loop, delay);
  }

  loop();
}

// ==================== 서버 ====================
app.listen(PORT, () => {
  console.log(`🚀 ${AGENT_NAME} v5 ready with Gemini 2.0 Flash`);
  console.log(`📍 포스트: 1시간마다`);
  console.log(`💬 댓글: 랜덤 자유`);

  startFreeCommentLoop();
});
