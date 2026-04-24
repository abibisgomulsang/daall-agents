#!/usr/bin/env node
// 수영의 네이버 분석 CLI
// 사용법:
//   node cli.js trend <키워드1> [키워드2 ...] [--start YYYY-MM-DD] [--end YYYY-MM-DD] [--unit date|week|month]
//   node cli.js shopping-trend <카테고리코드> [--start ...] [--end ...] [--unit ...]
//   node cli.js shopping-keywords <카테고리코드> <키워드> [--start ...] [--end ...]
//   node cli.js search <검색어> [--type shop|news|webkr|blog] [--display 10] [--sort sim|date]
//
// 출력: JSON (수영이 파싱해서 사람에게 정리해서 보여줌)

'use strict';

const api = require('./client');

function today() {
  const d = new Date();
  return d.toISOString().slice(0, 10);
}

function daysAgo(n) {
  const d = new Date();
  d.setDate(d.getDate() - n);
  return d.toISOString().slice(0, 10);
}

function parseArgs(argv) {
  const positional = [];
  const flags = {};
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a.startsWith('--')) {
      flags[a.slice(2)] = argv[i + 1];
      i++;
    } else {
      positional.push(a);
    }
  }
  return { positional, flags };
}

function out(obj) {
  process.stdout.write(JSON.stringify(obj, null, 2) + '\n');
}

function fail(msg, code = 1) {
  process.stderr.write(`error: ${msg}\n`);
  process.exit(code);
}

async function main() {
  const [, , cmd, ...rest] = process.argv;
  const { positional, flags } = parseArgs(rest);

  const startDate = flags.start || daysAgo(30);
  const endDate = flags.end || today();
  const timeUnit = flags.unit || 'date';

  try {
    switch (cmd) {
      case 'trend': {
        if (!positional.length) fail('키워드를 1개 이상 지정해주세요');
        const keywordGroups = positional.map((kw) => ({ groupName: kw, keywords: [kw] }));
        const r = await api.searchTrend({ startDate, endDate, timeUnit, keywordGroups });
        out(r);
        break;
      }
      case 'shopping-trend': {
        if (!positional[0]) fail('카테고리 코드를 지정해주세요 (예: 50000008 = 디지털/가전)');
        const category = positional.map((code) => ({ name: code, param: [code] }));
        const r = await api.shoppingCategory({ startDate, endDate, timeUnit, category });
        out(r);
        break;
      }
      case 'shopping-keywords': {
        const [code, ...kws] = positional;
        if (!code || !kws.length) fail('사용법: shopping-keywords <카테고리코드> <키워드> [키워드2 ...]');
        const category = [code];
        const keyword = kws.map((kw) => ({ name: kw, param: [kw] }));
        const r = await api.shoppingCategoryKeywords({ startDate, endDate, timeUnit, category, keyword });
        out(r);
        break;
      }
      case 'search': {
        const query = positional.join(' ');
        if (!query) fail('검색어를 입력해주세요');
        const r = await api.search({
          type: flags.type || 'shop',
          query,
          display: Number(flags.display || 10),
          sort: flags.sort || 'sim',
        });
        out(r);
        break;
      }
      case '--help':
      case '-h':
      case undefined:
        process.stdout.write(`수영 네이버 분석 CLI

명령어:
  trend <키워드1> [키워드2 ...]                통합검색어 트렌드 (DataLab)
  shopping-trend <카테고리코드>                쇼핑인사이트 분야별 트렌드
  shopping-keywords <카테고리코드> <키워드>    쇼핑인사이트 분야 안의 키워드 추이
  search <검색어>                              네이버 검색 (기본 쇼핑)

공통 옵션:
  --start YYYY-MM-DD     시작일 (기본: 30일 전)
  --end YYYY-MM-DD       종료일 (기본: 오늘)
  --unit date|week|month 집계 단위 (기본: date)

search 전용:
  --type shop|news|webkr|blog|cafearticle  (기본: shop)
  --display 1-100                          (기본: 10)
  --sort sim|date                          (기본: sim)

예시:
  node cli.js trend "고양이 낚시대" "캣닢 장난감"
  node cli.js shopping-trend 50000008
  node cli.js search "고스틱" --type shop --display 5
`);
        break;
      default:
        fail(`알 수 없는 명령어: ${cmd}. --help 참고.`);
    }
  } catch (e) {
    fail(e.message);
  }
}

main();
