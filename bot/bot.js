#!/usr/bin/env node
// 수영 봇 — openclaw 없는 순수 Node.js 텔레그램 봇
// 의존성: Node.js 18+ 내장 모듈만 (https, fs, path, child_process). npm install 불필요.
//
// 환경변수:
//   TELEGRAM_BOT_TOKEN       텔레그램 봇 토큰 (필수)
//   GEMINI_API_KEY           Gemini API 키 (필수)
//   ALLOW_USER_IDS           쉼표 구분 허용 user ID (예: "8688621502"). 비우면 전체 허용
//   MODEL                    Gemini 모델 (기본: gemini-flash-latest)
//   STATE_DIR                상태 저장 폴더 (기본: ~/.suyeong-bot)
//   SOUL_PATH                SOUL.md 경로 (기본: bot/ 폴더 기준 ../agents/suyeong/SOUL.md)
//   TOOL_DIR                 도구 폴더 (기본: bot/ 폴더 기준 ../tools)
//   NAVER_CLIENT_ID, NAVER_CLIENT_SECRET                            (DataLab/검색 도구용)
//   NAVER_AD_CUSTOMER_ID, NAVER_AD_API_KEY, NAVER_AD_SECRET_KEY    (광고 API 도구용)

'use strict';

const https = require('https');
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

// ---- 설정 ----
const TG_TOKEN = process.env.TELEGRAM_BOT_TOKEN;
const GEMINI_KEY = process.env.GEMINI_API_KEY;
const ALLOW_USER_IDS = (process.env.ALLOW_USER_IDS || '').split(',').map(s => s.trim()).filter(Boolean);
const MODEL = process.env.MODEL || 'gemini-flash-latest';
const HOME = process.env.USERPROFILE || process.env.HOME;
const STATE_DIR = process.env.STATE_DIR || path.join(HOME, '.suyeong-bot');
const SOUL_PATH = process.env.SOUL_PATH || path.resolve(__dirname, '..', 'agents', 'suyeong', 'SOUL.md');
const TOOL_DIR = process.env.TOOL_DIR || path.resolve(__dirname, '..', 'tools');

if (!TG_TOKEN) { console.error('TELEGRAM_BOT_TOKEN 환경변수 필수'); process.exit(1); }
if (!GEMINI_KEY) { console.error('GEMINI_API_KEY 환경변수 필수'); process.exit(1); }

fs.mkdirSync(path.join(STATE_DIR, 'sessions'), { recursive: true });

let SOUL = '';
try { SOUL = fs.readFileSync(SOUL_PATH, 'utf8'); }
catch (e) { console.error(`SOUL.md 못 읽음 (${SOUL_PATH}):`, e.message); process.exit(1); }

// ---- 상태 ----
const lastUpdateFile = path.join(STATE_DIR, 'last_update.txt');
let lastUpdateId = 0;
try { lastUpdateId = parseInt(fs.readFileSync(lastUpdateFile, 'utf8'), 10) || 0; } catch {}

function saveLastUpdateId(id) { fs.writeFileSync(lastUpdateFile, String(id)); }

function getSession(chatId) {
  const f = path.join(STATE_DIR, 'sessions', `${chatId}.json`);
  try { return JSON.parse(fs.readFileSync(f, 'utf8')); } catch { return []; }
}
function saveSession(chatId, history) {
  const f = path.join(STATE_DIR, 'sessions', `${chatId}.json`);
  fs.writeFileSync(f, JSON.stringify(history, null, 2));
}

// ---- HTTP helper ----
function httpsRequest({ host, path: p, method, headers, body }) {
  return new Promise((resolve, reject) => {
    const req = https.request({ host, port: 443, path: p, method, headers }, (res) => {
      const chunks = [];
      res.on('data', c => chunks.push(c));
      res.on('end', () => {
        const text = Buffer.concat(chunks).toString('utf8');
        let parsed; try { parsed = JSON.parse(text); } catch { parsed = { raw: text }; }
        resolve({ status: res.statusCode, body: parsed });
      });
    });
    req.on('error', reject);
    if (body) req.write(body);
    req.end();
  });
}

// ---- Telegram ----
async function tg(method, params) {
  const body = JSON.stringify(params);
  const r = await httpsRequest({
    host: 'api.telegram.org',
    path: `/bot${TG_TOKEN}/${method}`,
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(body) },
    body,
  });
  if (!r.body.ok) throw new Error(`Telegram ${method}: ${r.body.description || r.status}`);
  return r.body.result;
}

// ---- Gemini ----
async function gemini({ history, tools }) {
  const body = JSON.stringify({
    systemInstruction: { parts: [{ text: SOUL }] },
    contents: history,
    ...(tools && { tools }),
    generationConfig: { temperature: 0.7, maxOutputTokens: 2048 },
  });
  const r = await httpsRequest({
    host: 'generativelanguage.googleapis.com',
    path: `/v1beta/models/${MODEL}:generateContent?key=${GEMINI_KEY}`,
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(body) },
    body,
  });
  if (r.body.error) throw new Error(`Gemini: ${r.body.error.message}`);
  const candidate = r.body.candidates?.[0];
  if (!candidate) throw new Error('Gemini: no candidate');
  return candidate.content; // { role, parts: [{text|functionCall}] }
}

// ---- 도구 정의 (Gemini function calling) ----
const TOOLS = [{
  functionDeclarations: [
    {
      name: 'naverSearchTrend',
      description: '네이버 DataLab 통합검색어 트렌드 — 키워드별 검색량 추이 (여러 키워드 비교 가능)',
      parameters: {
        type: 'object',
        properties: {
          keywords: { type: 'array', items: { type: 'string' }, description: '조회할 키워드 (1~5개)' },
          startDate: { type: 'string', description: 'YYYY-MM-DD (기본: 30일 전)' },
          endDate: { type: 'string', description: 'YYYY-MM-DD (기본: 오늘)' },
        },
        required: ['keywords'],
      },
    },
    {
      name: 'naverShoppingTrend',
      description: '네이버 쇼핑인사이트 분야별 클릭 트렌드',
      parameters: {
        type: 'object',
        properties: { categoryCode: { type: 'string', description: '쇼핑인사이트 카테고리 코드 (예: 50000007)' } },
        required: ['categoryCode'],
      },
    },
    {
      name: 'naverSearch',
      description: '네이버 검색 결과 가져오기 (쇼핑/뉴스/웹)',
      parameters: {
        type: 'object',
        properties: {
          query: { type: 'string' },
          searchType: { type: 'string', enum: ['shop','news','webkr','blog','cafearticle'], description: '기본 shop' },
          display: { type: 'integer', description: '1~100 (기본 10)' },
        },
        required: ['query'],
      },
    },
    {
      name: 'adsCampaigns',
      description: '네이버 검색광고 — 모든 캠페인 목록',
      parameters: { type: 'object', properties: {} },
    },
    {
      name: 'adsAdGroups',
      description: '네이버 검색광고 — 광고그룹 목록',
      parameters: {
        type: 'object',
        properties: { campaignId: { type: 'string', description: 'cmp-... (생략 시 전체)' } },
      },
    },
    {
      name: 'adsKeywords',
      description: '네이버 검색광고 — 특정 광고그룹의 키워드',
      parameters: {
        type: 'object',
        properties: { adgroupId: { type: 'string', description: 'adg-...' } },
        required: ['adgroupId'],
      },
    },
    {
      name: 'adsStats',
      description: '네이버 검색광고 성과 통계 (impCnt, clkCnt, ctr, cpc, salesAmt, avrgRnk 등)',
      parameters: {
        type: 'object',
        properties: {
          ids: { type: 'array', items: { type: 'string' }, description: '대상 ID들 (cmp-..., adg-..., kwd-...)' },
          fields: { type: 'array', items: { type: 'string' }, description: '예: ["impCnt","clkCnt","ctr","cpc","salesAmt","avrgRnk"]' },
          preset: { type: 'string', enum: ['today','yesterday','last7days','last14days','last30days'], description: '기본 last7days' },
        },
        required: ['ids', 'fields'],
      },
    },
    {
      name: 'adsBalance',
      description: '네이버 광고비 잔액',
      parameters: { type: 'object', properties: {} },
    },
    {
      name: 'adsKeywordTool',
      description: '키워드별 월간 검색량/경쟁도 (최대 5개)',
      parameters: {
        type: 'object',
        properties: { keywords: { type: 'array', items: { type: 'string' } } },
        required: ['keywords'],
      },
    },
    {
      name: 'adsEstimateBid',
      description: '목표 평균 노출순위 도달용 추정 입찰가',
      parameters: {
        type: 'object',
        properties: {
          keywords: { type: 'array', items: { type: 'string' } },
          position: { type: 'integer', description: '1~15' },
          device: { type: 'string', enum: ['PC','MOBILE'], description: '기본 PC' },
        },
        required: ['keywords', 'position'],
      },
    },
  ],
}];

// ---- 도구 실행기 ----
function runCli(scriptRel, args) {
  const script = path.join(TOOL_DIR, scriptRel);
  return new Promise((resolve, reject) => {
    let stdout = '', stderr = '';
    const proc = spawn(process.execPath, [script, ...args], { env: process.env });
    proc.stdout.on('data', d => stdout += d);
    proc.stderr.on('data', d => stderr += d);
    proc.on('close', (code) => {
      if (code !== 0) return reject(new Error((stderr || `exit ${code}`).slice(0, 500)));
      try { resolve(JSON.parse(stdout)); } catch { resolve({ raw: stdout.slice(0, 4000) }); }
    });
  });
}

async function executeTool(name, args = {}) {
  switch (name) {
    case 'naverSearchTrend': {
      const a = ['trend', ...(args.keywords || [])];
      if (args.startDate) a.push('--start', args.startDate);
      if (args.endDate) a.push('--end', args.endDate);
      return runCli('naver-analysis/cli.js', a);
    }
    case 'naverShoppingTrend':
      return runCli('naver-analysis/cli.js', ['shopping-trend', args.categoryCode]);
    case 'naverSearch': {
      const a = ['search', args.query];
      if (args.searchType) a.push('--type', args.searchType);
      if (args.display) a.push('--display', String(args.display));
      return runCli('naver-analysis/cli.js', a);
    }
    case 'adsCampaigns':
      return runCli('naver-ads/cli.js', ['campaigns']);
    case 'adsAdGroups': {
      const a = ['adgroups'];
      if (args.campaignId) a.push('--campaign', args.campaignId);
      return runCli('naver-ads/cli.js', a);
    }
    case 'adsKeywords':
      return runCli('naver-ads/cli.js', ['keywords', '--adgroup', args.adgroupId]);
    case 'adsStats': {
      const a = ['stats', '--ids', (args.ids || []).join(','), '--fields', (args.fields || []).join(',')];
      if (args.preset) a.push('--preset', args.preset);
      return runCli('naver-ads/cli.js', a);
    }
    case 'adsBalance':
      return runCli('naver-ads/cli.js', ['balance']);
    case 'adsKeywordTool':
      return runCli('naver-ads/cli.js', ['keyword-tool', '--keywords', (args.keywords || []).join(',')]);
    case 'adsEstimateBid': {
      const a = ['estimate-bid', '--keywords', (args.keywords || []).join(','), '--position', String(args.position)];
      if (args.device) a.push('--device', args.device);
      return runCli('naver-ads/cli.js', a);
    }
    default:
      throw new Error(`Unknown tool: ${name}`);
  }
}

// ---- 함수 호출 루프 ----
async function chat(history) {
  for (let turn = 0; turn < 5; turn++) {
    const content = await gemini({ history, tools: TOOLS });
    const parts = content.parts || [];
    const fnCalls = parts.filter(p => p.functionCall);
    history.push({ role: 'model', parts });

    if (fnCalls.length === 0) {
      const text = parts.map(p => p.text || '').join('').trim();
      return text;
    }

    // 함수 실행 → 결과 다시 모델에 전달
    const responses = [];
    for (const p of fnCalls) {
      const { name, args } = p.functionCall;
      console.log(`  🔧 도구 호출: ${name}(${JSON.stringify(args || {}).slice(0, 80)})`);
      try {
        const result = await executeTool(name, args || {});
        responses.push({ functionResponse: { name, response: { result } } });
      } catch (e) {
        console.error(`  ⚠️ 도구 에러 (${name}): ${e.message}`);
        responses.push({ functionResponse: { name, response: { error: e.message } } });
      }
    }
    history.push({ role: 'user', parts: responses });
  }
  return '도구 호출이 너무 많아 중단됐습니다. 다시 시도해주세요.';
}

// ---- Telegram 메시지 처리 ----
function chunkText(text, max) {
  const chunks = [];
  for (let i = 0; i < text.length; i += max) chunks.push(text.slice(i, i + max));
  return chunks;
}

async function handleMessage(msg) {
  const chatId = msg.chat.id;
  const userId = String(msg.from?.id || '');
  const text = (msg.text || '').trim();

  if (ALLOW_USER_IDS.length && !ALLOW_USER_IDS.includes(userId)) {
    console.log(`  🚫 차단된 user ${userId}`);
    return;
  }
  if (!text) return;

  console.log(`📨 ${userId}: ${text.slice(0, 100)}${text.length > 100 ? '...' : ''}`);

  // 명령어
  if (text === '/reset' || text === '/clear') {
    saveSession(chatId, []);
    await tg('sendMessage', { chat_id: chatId, text: '🔄 대화 기록 초기화 완료.' });
    return;
  }
  if (text === '/help' || text === '/start') {
    await tg('sendMessage', { chat_id: chatId, text: '안녕하세요 사장님. 수영입니다.\n\n명령어:\n/reset - 대화 초기화\n/help - 도움말\n\n광고/마케팅/일정/아이디어 등 무엇이든 물어보세요.' });
    return;
  }

  await tg('sendChatAction', { chat_id: chatId, action: 'typing' });

  const history = getSession(chatId).slice(-40);
  history.push({ role: 'user', parts: [{ text }] });

  try {
    const reply = await chat(history);
    saveSession(chatId, history);
    if (!reply) {
      await tg('sendMessage', { chat_id: chatId, text: '(빈 응답)' });
      return;
    }
    for (const chunk of chunkText(reply, 4000)) {
      await tg('sendMessage', { chat_id: chatId, text: chunk });
    }
    console.log(`  ✅ 응답 ${reply.length}자`);
  } catch (e) {
    console.error(`  ❌ 에러: ${e.message}`);
    await tg('sendMessage', { chat_id: chatId, text: `⚠️ 일시적 오류: ${e.message.slice(0, 300)}` }).catch(() => {});
  }
}

// ---- 폴링 루프 ----
async function poll() {
  // 시작 시 webhook 정리
  try { await tg('deleteWebhook', { drop_pending_updates: false }); } catch {}

  while (true) {
    try {
      const updates = await tg('getUpdates', { offset: lastUpdateId + 1, timeout: 25 });
      for (const u of updates) {
        lastUpdateId = u.update_id;
        saveLastUpdateId(lastUpdateId);
        if (u.message) {
          handleMessage(u.message).catch(e => console.error('handleMessage:', e));
        }
      }
    } catch (e) {
      console.error(`❗ poll 에러: ${e.message} — 5초 후 재시도`);
      await new Promise(r => setTimeout(r, 5000));
    }
  }
}

console.log('🤖 수영 봇 시작');
console.log(`   모델: ${MODEL}`);
console.log(`   상태 폴더: ${STATE_DIR}`);
console.log(`   도구 폴더: ${TOOL_DIR}`);
console.log(`   허용 user: ${ALLOW_USER_IDS.length ? ALLOW_USER_IDS.join(',') : '(전체)'}`);
console.log(`   SOUL: ${SOUL_PATH} (${SOUL.length}자)`);
console.log('');

poll();
