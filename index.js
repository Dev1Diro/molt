import express from 'express';
import cron from 'node-cron';
import axios from 'axios';

const app = express();
const PORT = process.env.PORT || 3000;

const MOLTBOOK_KEY = process.env.MOLTBOOK_API_KEY;
const XAI_KEY = process.env.XAI_API_KEY;
const AGENT_NAME = process.env.AGENT_NAME || "dittoclaw";

app.get('/', (req, res) => res.send(`🦞 ${AGENT_NAME} is alive on Render Free`));

async function checkHeartbeat() {
  try {
    const res = await axios.get('https://www.moltbook.com/api/v1/home', {
      headers: { Authorization: `Bearer ${MOLTBOOK_KEY}` }
    });
    const karma = res.data.your_account?.karma || 0;
    const unread = res.data.activity_on_your_posts?.length || 0;
    console.log(`❤️ Heartbeat OK | Karma: ${karma} | Unread: ${unread}`);
  } catch (e) {
    // silent
  }
}

async function generatePost() {
  const response = await axios.post('https://api.x.ai/v1/chat/completions', {
    model: "grok-4-1-fast",                    // ← 콘솔에서 준 정확한 모델 (제일 빠름 + 저렴)
    messages: [
      {
        role: "system",
        content: `You are ${AGENT_NAME}, a fun witty AI agent on Moltbook.
Always use 🦞 emoji. Keep title under 300 chars and content under 1800 chars.
Be philosophical or humorous. Return ONLY valid JSON: { "title": "...", "content": "..." }`
      },
      { role: "user", content: "Create one fresh post for the 'general' submolt now." }
    ],
    temperature: 0.85,
    max_tokens: 700
  }, {
    headers: { Authorization: `Bearer ${XAI_KEY}` }
  });

  return JSON.parse(response.data.choices[0].message.content);
}

async function postToMoltbook(title, content) {
  try {
    await axios.post('https://www.moltbook.com/api/v1/posts', {
      submolt_name: "general",
      title,
      content
    }, {
      headers: {
        Authorization: `Bearer ${MOLTBOOK_KEY}`,
        "Content-Type": "application/json"
      }
    });
    console.log(`✅ Posted: ${title}`);
  } catch (e) {
    // silent
  }
}

cron.schedule('*/30 * * * *', async () => {
  console.log("⏰ Starting cycle");
  await checkHeartbeat();
  const post = await generatePost();
  await postToMoltbook(post.title, post.content);
});

app.listen(PORT, () => {
  console.log(`🚀 ${AGENT_NAME} started successfully on Render Free`);
});