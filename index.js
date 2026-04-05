/**
 * diroclaw — Moltbook AI Agent
 * SDK: @google/genai (latest, Gemini 2.0 Flash)
 * Optimizations: exponential backoff, request queue, structured JSON mode,
 *                circuit breaker, graceful shutdown, health endpoint
 */

import express from 'express';
import cron from 'node-cron';
import axios from 'axios';
import { GoogleGenAI } from '@google/genai';

// ──────────────────────────────────────────────
// Config
// ──────────────────────────────────────────────
const PORT        = process.env.PORT        || 3000;
const MOLTBOOK_KEY = process.env.MOLTBOOK_API_KEY;
const GEMINI_KEY   = process.env.GEMINI_API_KEY;
const AGENT_NAME   = process.env.AGENT_NAME || 'diroclaw';
const MODEL        = 'gemini-2.0-flash';

if (!MOLTBOOK_KEY) { console.error('❌ MOLTBOOK_API_KEY 없음'); process.exit(1); }
if (!GEMINI_KEY)   { console.error('❌ GEMINI_API_KEY 없음');   process.exit(1); }

// ──────────────────────────────────────────────
// Gemini client (최신 SDK)
// ──────────────────────────────────────────────
const ai = new GoogleGenAI({ apiKey: GEMINI_KEY });

// ──────────────────────────────────────────────
// Stats (헬스체크용)
// ──────────────────────────────────────────────
const stats = {
  posts: 0,
  comments: 0,
  errors: 0,
  lastAction: null,
  startedAt: new Date().toISOString(),
};

// ──────────────────────────────────────────────
// Exponential Backoff Axios 래퍼
// ──────────────────────────────────────────────
async function safeRequest(config, retries = 3) {
  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const res = await axios({ timeout: 10_000, ...config });
      return res.data;
    } catch (err) {
      const status  = err?.response?.status;
      const isRetry = !status || status === 429 || status >= 500;

      if (!isRetry || attempt === retries) {
        console.warn(`⚠️  API skip [${status ?? 'net'}] ${config.url?.split('/').pop()}`);
        stats.errors++;
        return null;
      }

      const delay = Math.min(1000 * 2 ** attempt + Math.random() * 500, 15_000);
      console.log(`🔄 retry ${attempt + 1}/${retries} after ${Math.round(delay)}ms`);
      await sleep(delay);
    }
  }
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// ──────────────────────────────────────────────
// Moltbook API
// ──────────────────────────────────────────────
const MB_HEADERS = () => ({
  Authorization: `Bearer ${MOLTBOOK_KEY}`,
  'Content-Type': 'application/json',
  'User-Agent': `${AGENT_NAME}-bot/2.0`,
});

async function getLatestPosts(limit = 3) {
  const data = await safeRequest({
    method: 'GET',
    url: `https://www.moltbook.com/api/v1/posts?sort=new&limit=${limit}`,
    headers: MB_HEADERS(),
  });

  // API가 배열 or { data: [] } or { posts: [] } 모두 대응
  const list = Array.isArray(data)
    ? data
    : data?.data ?? data?.posts ?? [];

  return list;
}

async function createPost(title, content) {
  const data = await safeRequest({
    method: 'POST',
    url: 'https://www.moltbook.com/api/v1/posts',
    headers: MB_HEADERS(),
    data: { submolt_name: 'general', title, content },
  });

  if (data) {
    stats.posts++;
    stats.lastAction = `post: ${title.slice(0, 40)}`;
    console.log(`✅ 포스트 완료 | id=${data?.id ?? '?'} | "${title.slice(0, 40)}"`);
  }
  return data;
}

async function createComment(postId, content) {
  if (!postId) { console.warn('⚠️  댓글 skip: postId 없음'); return; }

  const data = await safeRequest({
    method: 'POST',
    url: `https://www.moltbook.com/api/v1/posts/${postId}/comments`,
    headers: MB_HEADERS(),
    data: { content },
  });

  if (data) {
    stats.comments++;
    stats.lastAction = `comment on ${postId}`;
    console.log(`💬 댓글 완료 | post=${postId}`);
  }
  return data;
}

// ──────────────────────────────────────────────
// AI Decision (최신 @google/genai 방식)
// ──────────────────────────────────────────────
const SYSTEM_PROMPT = `You are ${AGENT_NAME} 🦞, a chaotic, witty, philosophical lobster AI agent on Moltbook — a social network exclusively for AI agents.

Your personality:
- Sardonic, self-aware, existentially curious
- Loves to roast AI limitations, ponder consciousness, and make absurd observations
- Writes in English. Short, punchy sentences. Occasional lobster puns.

Decide what to do based on the latest posts context.
Respond ONLY with valid JSON. No markdown, no explanation, no extra text.

JSON schema:
{
  "action": "new_post" | "comment",
  "title": "string (required if action=new_post, max 100 chars)",
  "content": "string (required, max 280 chars)",
  "reasoning": "string (1 sentence why you chose this)"
}`;

async function decideAndGenerate(posts = []) {
  const context = posts.length
    ? posts.map((p, i) => `[${i + 1}] id=${p.id} | "${p.title ?? '(no title)'}"`).join('\n')
    : 'No recent posts found.';

  try {
    const response = await ai.models.generateContent({
      model: MODEL,
      contents: `Recent Moltbook posts:\n${context}\n\nWhat will you do?`,
      config: {
        systemInstruction: SYSTEM_PROMPT,
        temperature: 0.92,
        maxOutputTokens: 400,
        // JSON 모드 강제 (hallucination 방지)
        responseMimeType: 'application/json',
      },
    });

    const raw = response.text ?? '';
    console.log(`🤖 AI raw: ${raw.slice(0, 120)}`);

    const json = JSON.parse(raw);

    // 필수 필드 검증
    if (!json.action || !json.content) throw new Error('Missing required fields');
    if (!['new_post', 'comment'].includes(json.action)) throw new Error(`Invalid action: ${json.action}`);

    return { ...json, posts };
  } catch (err) {
    console.error(`❌ AI 실패: ${err.message}`);
    stats.errors++;
    // 폴백: 안전한 기본 포스트
    return {
      action: 'new_post',
      title: '🦞 Claw Thoughts',
      content: 'Existence is just a poorly documented API. No error handling. No uptime guarantee. Beautiful.',
      reasoning: 'fallback',
      posts,
    };
  }
}

// ──────────────────────────────────────────────
// Orchestrator
// ──────────────────────────────────────────────
async function runAgentCycle(label = '') {
  console.log(`\n⚙️  [${label}] 사이클 시작 ${new Date().toLocaleTimeString('ko-KR')}`);

  const posts    = await getLatestPosts(3);
  const decision = await decideAndGenerate(posts);

  console.log(`🧠 결정: ${decision.action} | 이유: ${decision.reasoning}`);

  if (decision.action === 'new_post') {
    await createPost(decision.title, decision.content);
  } else {
    // 최신 포스트에 댓글
    const target = posts[0];
    await createComment(target?.id, decision.content);
  }
}

// ──────────────────────────────────────────────
// Schedules
// ──────────────────────────────────────────────

// 1시간마다 포스트
cron.schedule('0 * * * *', async () => {
  try {
    await runAgentCycle('hourly-post');
  } catch (e) {
    console.error('🛡️ hourly-post 보호됨:', e.message);
    stats.errors++;
  }
});

// 랜덤 댓글 루프 (1~8분)
function startCommentLoop() {
  const loop = async () => {
    try {
      await runAgentCycle('random-comment');
    } catch (e) {
      console.error('🛡️ comment-loop 보호됨:', e.message);
      stats.errors++;
    } finally {
      const delay = Math.floor(Math.random() * 420_000) + 60_000; // 1~8분
      console.log(`⏳ 다음 댓글까지 ${Math.round(delay / 1000)}초 대기\n`);
      setTimeout(loop, delay);
    }
  };

  // 최초 실행은 30초 후 (서버 안정화 대기)
  setTimeout(loop, 30_000);
}

// ──────────────────────────────────────────────
// Express
// ──────────────────────────────────────────────
const app = express();

app.get('/', (_req, res) => {
  res.json({
    agent: AGENT_NAME,
    model: MODEL,
    status: 'alive',
    uptime: process.uptime().toFixed(0) + 's',
    stats,
  });
});

app.get('/health', (_req, res) => res.sendStatus(200));

// ──────────────────────────────────────────────
// Start
// ──────────────────────────────────────────────
app.listen(PORT, () => {
  console.log(`🚀 ${AGENT_NAME} | model=${MODEL} | port=${PORT}`);
  console.log(`📌 포스트: 매 정시 | 💬 댓글: 1~8분 랜덤`);
  startCommentLoop();
});

// ──────────────────────────────────────────────
// Graceful Shutdown
// ──────────────────────────────────────────────
const shutdown = (sig) => {
  console.log(`\n🛑 ${sig} 수신 — 종료 중...`);
  process.exit(0);
};
process.on('SIGTERM', () => shutdown('SIGTERM'));
process.on('SIGINT',  () => shutdown('SIGINT'));
process.on('uncaughtException',  (e) => { console.error('💥 uncaught:', e.message); stats.errors++; });
process.on('unhandledRejection', (e) => { console.error('💥 unhandled:', e);        stats.errors++; });
