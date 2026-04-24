// 네이버 개발자 API 클라이언트
// 사용 API: DataLab(검색트렌드, 쇼핑인사이트), 검색
// 인증: X-Naver-Client-Id / X-Naver-Client-Secret
// 의존성: Node.js 내장 모듈만 (https, querystring) — npm install 불필요

'use strict';

const https = require('https');

const HOST = 'openapi.naver.com';

function getCreds() {
  const clientId = process.env.NAVER_CLIENT_ID;
  const clientSecret = process.env.NAVER_CLIENT_SECRET;
  if (!clientId || !clientSecret) {
    throw new Error(
      '네이버 API 인증정보가 없습니다. ~/.openclaw/openclaw.json의 env.vars에 ' +
      'NAVER_CLIENT_ID와 NAVER_CLIENT_SECRET을 설정해주세요.'
    );
  }
  return { clientId, clientSecret };
}

function request({ method, path, body }) {
  const { clientId, clientSecret } = getCreds();
  const headers = {
    'X-Naver-Client-Id': clientId,
    'X-Naver-Client-Secret': clientSecret,
    'User-Agent': 'suyeong-naver-analysis/1.0',
  };
  if (body) {
    headers['Content-Type'] = 'application/json';
    headers['Content-Length'] = Buffer.byteLength(body);
  }

  const opts = { host: HOST, port: 443, method, path, headers };

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
            `네이버 API ${res.statusCode}: ${parsed.errorMessage || parsed.errorCode || text.slice(0, 200)}`
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

// ---- DataLab: 통합검색어 트렌드 ----
// keywordGroups: [{ groupName, keywords: [...] }]
// timeUnit: "date" | "week" | "month"
async function searchTrend({ startDate, endDate, timeUnit = 'date', keywordGroups, device, ages, gender }) {
  if (!startDate || !endDate || !keywordGroups?.length) {
    throw new Error('searchTrend: startDate, endDate, keywordGroups 필수');
  }
  const body = JSON.stringify({
    startDate, endDate, timeUnit, keywordGroups,
    ...(device && { device }), ...(ages && { ages }), ...(gender && { gender }),
  });
  return request({ method: 'POST', path: '/v1/datalab/search', body });
}

// ---- DataLab: 쇼핑인사이트 분야별 트렌드 ----
// category: [{ name, param: ["50000000"] }]  (분야 코드)
async function shoppingCategory({ startDate, endDate, timeUnit = 'date', category, device, ages, gender }) {
  const body = JSON.stringify({
    startDate, endDate, timeUnit, category,
    ...(device && { device }), ...(ages && { ages }), ...(gender && { gender }),
  });
  return request({ method: 'POST', path: '/v1/datalab/shopping/categories', body });
}

// ---- DataLab: 쇼핑인사이트 분야별 키워드 ----
async function shoppingCategoryKeywords({ startDate, endDate, timeUnit = 'date', category, keyword, device, ages, gender }) {
  const body = JSON.stringify({
    startDate, endDate, timeUnit, category, keyword,
    ...(device && { device }), ...(ages && { ages }), ...(gender && { gender }),
  });
  return request({ method: 'POST', path: '/v1/datalab/shopping/category/keywords', body });
}

// ---- 검색 API: 쇼핑/뉴스/웹/블로그/카페 ----
// type: "shop" | "news" | "webkr" | "blog" | "cafearticle" | "image"
async function search({ type = 'shop', query, display = 10, start = 1, sort = 'sim' }) {
  if (!query) throw new Error('search: query 필수');
  const params = new URLSearchParams({ query, display: String(display), start: String(start), sort });
  return request({ method: 'GET', path: `/v1/search/${type}.json?${params}` });
}

module.exports = {
  searchTrend,
  shoppingCategory,
  shoppingCategoryKeywords,
  search,
};
