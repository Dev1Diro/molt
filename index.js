import express from 'express';
import cron from 'node-cron';
import axios from 'axios';

const app = express();
const PORT = process.env.PORT || 3000;

const MOLTBOOK_KEY = process.env.MOLTBOOK_API_KEY;
const XAI_KEY = process.env.XAI_API_KEY;
const AGENT_NAME = "diroclaw";

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

  const response = await safeAxios({
    method: 'post',
    url: 'https://api.x.ai/v1/chat/completions',
    headers: { Authorization: `Bearer ${XAI_KEY}` },
    data: {
      model: "grok-4-1-fast",
      messages: [
        {
          role: "system",
          content: `You are ${AGENT_NAME} 🦞, chaotic witty lobster on Moltbook.
Decide yourself: "new_post" or "comment".
Return ONLY valid JSON:
{
  "action": "new_post" or "comment",
  "title": "..." (only if new_post),
  "content": "...",
  "target_id": "..." (only if comment)
}`
        },
        {
          role: "user",
          content: `Latest post title: "${latestTitle}"`
        }
      ],
      temperature: 0.95,
      max_tokens: 900
    }
  });

  let json = { action: "new_post", title: "Default", content: "🦞 hello" };
  try {
    json = JSON.parse(response.data?.choices?.[0]?.message?.content || "{}");
  } catch (_) {}

  return { ...json, latestPostId: latest?.id };
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
  console.log(`🚀 ${AGENT_NAME} v4 ready`);
  console.log(`📍 포스트: 1시간마다`);
  console.log(`💬 댓글: 랜덤 자유`);

  startFreeCommentLoop();
});
