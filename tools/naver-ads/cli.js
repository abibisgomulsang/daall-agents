#!/usr/bin/env node
// 수영의 네이버 검색광고 API CLI (조회 전용)
// 사용법:
//   node cli.js campaigns
//   node cli.js adgroups [--campaign cmp-...]
//   node cli.js keywords --adgroup adg-...
//   node cli.js stats --ids cmp-...,cmp-... --fields impCnt,clkCnt,salesAmt --preset last7days
//   node cli.js balance
//   node cli.js channels
//
// 출력: JSON. 수영이 파싱해서 사람에게 정리.

'use strict';

const api = require('./client');

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
  const { flags } = parseArgs(rest);

  try {
    switch (cmd) {
      case 'campaigns': {
        out(await api.listCampaigns());
        break;
      }
      case 'adgroups': {
        out(await api.listAdGroups({ campaignId: flags.campaign }));
        break;
      }
      case 'keywords': {
        if (!flags.adgroup) fail('--adgroup adg-... 필수');
        out(await api.listKeywords({ adgroupId: flags.adgroup }));
        break;
      }
      case 'stats': {
        if (!flags.ids || !flags.fields) fail('--ids ...,... 와 --fields impCnt,clkCnt 등 필수');
        out(await api.getStats({
          ids: flags.ids.split(','),
          fields: flags.fields.split(','),
          datePreset: flags.preset || 'last7days',
          breakdown: flags.breakdown,
        }));
        break;
      }
      case 'balance': {
        out(await api.getBalance());
        break;
      }
      case 'channels': {
        out(await api.listBusinessChannels());
        break;
      }
      case '--help':
      case '-h':
      case undefined:
        process.stdout.write(`수영 네이버 검색광고 API CLI (조회 전용)

명령어:
  campaigns                                광고주의 모든 캠페인 목록
  adgroups [--campaign cmp-...]            광고그룹 목록 (캠페인 지정 시 해당 캠페인만)
  keywords --adgroup adg-...               특정 광고그룹의 키워드 목록
  stats --ids id1,id2 --fields f1,f2       성과 통계
                                           예: --ids cmp-123 --fields impCnt,clkCnt,salesAmt
                                                --preset last7days|today|yesterday|last1days|...
  balance                                  광고비 잔액
  channels                                 비즈채널 (연결된 스마트스토어 등)

⚠️ 변경 명령(입찰가/예산 수정 등)은 의도적으로 제외.
   현재 단계는 조회만 — 변경은 사장님이 검색광고 시스템에서 직접 적용.

예시:
  node cli.js campaigns
  node cli.js stats --ids cmp-a001-01-000000123456 --fields impCnt,clkCnt,ctr,salesAmt --preset last7days
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
