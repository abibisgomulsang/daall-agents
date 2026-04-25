#!/usr/bin/env node
// 수영 봇 시작 스크립트
// ~/.openclaw/openclaw.json 의 키를 그대로 가져와 환경변수로 설정 후 bot.js 실행
// (사장님이 따로 키를 또 입력할 필요 없음)

'use strict';

const fs = require('fs');
const path = require('path');

const HOME = process.env.USERPROFILE || process.env.HOME;
const OPENCLAW_CONFIG = process.env.OPENCLAW_CONFIG || path.join(HOME, '.openclaw', 'openclaw.json');

let cfg;
try {
  cfg = JSON.parse(fs.readFileSync(OPENCLAW_CONFIG, 'utf8'));
} catch (e) {
  console.error(`설정 파일 못 읽음 (${OPENCLAW_CONFIG}): ${e.message}`);
  console.error('환경변수만으로 실행하려면 직접 bot.js 를 호출하세요.');
  process.exit(1);
}

// env.vars 그대로 가져오기
const envVars = cfg?.env?.vars || {};
for (const [k, v] of Object.entries(envVars)) {
  if (!process.env[k] && typeof v === 'string' && !v.startsWith('여기에_')) {
    process.env[k] = v;
  }
}

// 텔레그램 봇 토큰: openclaw.json의 channels.telegram.accounts.suyeong_bot.botToken
const acc = cfg?.channels?.telegram?.accounts?.suyeong_bot;
if (acc?.botToken && !process.env.TELEGRAM_BOT_TOKEN) {
  process.env.TELEGRAM_BOT_TOKEN = acc.botToken;
}

// 허용 user ID: channels.telegram.allowFrom (telegram:XXX 형식 → 숫자만)
const allowFrom = cfg?.channels?.telegram?.allowFrom || [];
if (allowFrom.length && !process.env.ALLOW_USER_IDS) {
  process.env.ALLOW_USER_IDS = allowFrom
    .map(s => String(s).replace(/^telegram:/, '').trim())
    .filter(Boolean)
    .join(',');
}

// 모델: agents.list[].model 에서 suyeong 찾기
const suyeongAgent = (cfg?.agents?.list || []).find(a => a.id === 'suyeong');
if (suyeongAgent?.model && !process.env.MODEL) {
  // "google/gemini-flash-latest" → "gemini-flash-latest"
  process.env.MODEL = suyeongAgent.model.replace(/^google\//, '');
}

// SOUL.md: 워크스페이스 사용 (사장님이 ~/.openclaw/ws-suyeong/SOUL.md 동기화해둔 것)
if (!process.env.SOUL_PATH && suyeongAgent?.workspace) {
  const ws = suyeongAgent.workspace.replace('~', HOME);
  const soulInWs = path.join(ws, 'SOUL.md');
  if (fs.existsSync(soulInWs)) {
    process.env.SOUL_PATH = soulInWs;
  }
}

// 도구도 워크스페이스 우선
if (!process.env.TOOL_DIR && suyeongAgent?.workspace) {
  const ws = suyeongAgent.workspace.replace('~', HOME);
  const toolsInWs = path.join(ws, 'tools');
  if (fs.existsSync(toolsInWs)) {
    process.env.TOOL_DIR = toolsInWs;
  }
}

// 검증
const required = ['TELEGRAM_BOT_TOKEN', 'GEMINI_API_KEY'];
const missing = required.filter(k => !process.env[k]);
if (missing.length) {
  console.error(`❌ 필수 환경변수 누락: ${missing.join(', ')}`);
  console.error(`   ${OPENCLAW_CONFIG} 또는 환경변수에서 설정 필요`);
  process.exit(1);
}

console.log(`📁 설정 로드: ${OPENCLAW_CONFIG}`);
require('./bot.js');
