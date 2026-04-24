// 네이버 검색광고 API 클라이언트 (조회 전용 — 옵션 C)
// 인증: X-API-KEY + X-Customer + HMAC-SHA256 서명
// 의존성: Node.js 내장 모듈만 (https, crypto)

'use strict';

const https = require('https');
const crypto = require('crypto');

const HOST = 'api.searchad.naver.com';

function getCreds() {
  const customerId = process.env.NAVER_AD_CUSTOMER_ID;
  const apiKey = process.env.NAVER_AD_API_KEY;
  const secretKey = process.env.NAVER_AD_SECRET_KEY;
  if (!customerId || !apiKey || !secretKey) {
    throw new Error(
      '네이버 검색광고 API 인증정보가 없습니다. ~/.openclaw/openclaw.json env.vars에 ' +
      'NAVER_AD_CUSTOMER_ID / NAVER_AD_API_KEY / NAVER_AD_SECRET_KEY 설정 후 게이트웨이 재시작 필요.'
    );
  }
  return { customerId, apiKey, secretKey };
}

// HMAC-SHA256(secret, "{timestamp}.{method}.{path}") → base64
function sign({ timestamp, method, path, secretKey }) {
  const msg = `${timestamp}.${method}.${path}`;
  return crypto.createHmac('sha256', secretKey).update(msg).digest('base64');
}

// path는 query string 제외한 순수 경로
function request({ method, path, query, body }) {
  const { customerId, apiKey, secretKey } = getCreds();
  const timestamp = String(Date.now());
  const signature = sign({ timestamp, method, path, secretKey });

  const headers = {
    'X-Timestamp': timestamp,
    'X-API-KEY': apiKey,
    'X-Customer': String(customerId),
    'X-Signature': signature,
    'User-Agent': 'suyeong-naver-ads/1.0',
  };
  if (body) {
    headers['Content-Type'] = 'application/json';
    headers['Content-Length'] = Buffer.byteLength(body);
  }

  const fullPath = query ? `${path}?${query}` : path;
  const opts = { host: HOST, port: 443, method, path: fullPath, headers };

  return new Promise((resolve, reject) => {
    const req = https.request(opts, (res) => {
      const chunks = [];
      res.on('data', (c) => chunks.push(c));
      res.on('end', () => {
        const text = Buffer.concat(chunks).toString('utf8');
        let parsed;
        try { parsed = JSON.parse(text); } catch { parsed = { raw: text }; }
        if (res.statusCode < 200 || res.statusCode >= 300) {
          const err = new Error(
            `네이버 광고 API ${res.statusCode}: ${parsed.title || parsed.detail || parsed.code || text.slice(0, 200)}`
          );
          err.statusCode = res.statusCode;
          err.body = parsed;
          return reject(err);
        }
        resolve(parsed);
      });
    });
    req.on('error', reject);
    if (body) req.write(body);
    req.end();
  });
}

// ---- 조회 (Read-only) ----
async function listCampaigns() {
  return request({ method: 'GET', path: '/ncc/campaigns' });
}

async function listAdGroups({ campaignId } = {}) {
  const query = campaignId ? new URLSearchParams({ campaignId }).toString() : '';
  return request({ method: 'GET', path: '/ncc/adgroups', query });
}

async function listKeywords({ adgroupId }) {
  if (!adgroupId) throw new Error('listKeywords: adgroupId 필수');
  const query = new URLSearchParams({ adgroupId }).toString();
  return request({ method: 'GET', path: '/ncc/keywords', query });
}

// 일/요일/시간/지역별 통계 (대상 ID 종류: cmp, adg, kwd, ad, etc.)
// 사용 예: getStats({ ids: ['nkw-...'], fields: ['impCnt','clkCnt','salesAmt'], datePreset: 'last7days' })
async function getStats({ ids, fields, datePreset, timeRange, breakdown }) {
  if (!ids?.length || !fields?.length) {
    throw new Error('getStats: ids와 fields 필수');
  }
  const params = {
    ids: ids.join(','),
    fields: JSON.stringify(fields),
  };
  if (datePreset) params.datePreset = datePreset;
  if (timeRange) params.timeRange = JSON.stringify(timeRange);
  if (breakdown) params.breakdown = breakdown;
  const query = new URLSearchParams(params).toString();
  return request({ method: 'GET', path: '/stats', query });
}

// 광고주 잔액
async function getBalance() {
  return request({ method: 'GET', path: '/billing/bizmoney' });
}

// 비즈채널 (스마트스토어 등)
async function listBusinessChannels() {
  return request({ method: 'GET', path: '/ncc/channels' });
}

// 추정 입찰가 (어떤 키워드가 얼마면 1위 갈지 등)
async function getKeywordsByIds({ ids }) {
  if (!ids?.length) throw new Error('getKeywordsByIds: ids 필수');
  const query = `ids=${ids.join(',')}`;
  return request({ method: 'GET', path: '/ncc/keywords', query });
}

module.exports = {
  listCampaigns,
  listAdGroups,
  listKeywords,
  getKeywordsByIds,
  getStats,
  getBalance,
  listBusinessChannels,
  // 변경 함수는 옵션 C라 의도적으로 노출 안 함. 추후 필요 시 별도 모듈로 분리.
};
