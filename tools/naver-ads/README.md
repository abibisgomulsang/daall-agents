# 네이버 검색광고 API 도구 (수영 전용 · 조회 전용)

네이버 **검색광고 API** 호출 CLI. 캠페인/광고그룹/키워드/성과 조회.

## 의존성
**없음.** Node.js 내장 모듈(`https`, `crypto`)만 사용.

## 환경변수
`~/.openclaw/openclaw.json` 의 `env.vars` 에:
```json
"NAVER_AD_CUSTOMER_ID": "...",  // 광고주 고객 ID (숫자)
"NAVER_AD_API_KEY": "...",      // 액세스 라이선스
"NAVER_AD_SECRET_KEY": "..."    // 비밀키
```

발급처: 검색광고 시스템 → 도구 → API 사용 관리
https://manage.searchad.naver.com/customers/{고객ID}/tool/api

## 명령어

### `campaigns`
모든 캠페인 목록 조회.

### `adgroups [--campaign cmp-...]`
광고그룹 목록. `--campaign` 지정 시 해당 캠페인 하위만.

### `keywords --adgroup adg-...`
특정 광고그룹의 키워드 목록.

### `stats --ids id1,id2 --fields f1,f2 [--preset ...]`
성과 통계. 사용 가능 필드: `impCnt`, `clkCnt`, `ctr`, `cpc`, `salesAmt`, `crto`, `ccnt`, ...
`--preset`: `today`, `yesterday`, `last7days`, `last14days`, `last30days`

### `balance`
광고비 잔액 (BizMoney).

### `channels`
비즈채널(스마트스토어 등) 목록.

## 출력
모든 명령 → JSON stdout. 에러 → stderr + exit != 0.

## ⚠️ 의도적으로 제외한 기능 (옵션 C)
- 입찰가 변경
- 일예산 변경
- 캠페인 ON/OFF
- 키워드 추가/삭제

→ 변경은 **사장님이 검색광고 시스템에서 직접 적용**.
   추후 옵션 B(변경마다 승인) 또는 A(소액 자동) 단계로 갈 때 별도 모듈 추가.

## 위치
- GitHub: `tools/naver-ads/`
- 런타임: `~/.openclaw/ws-suyeong/tools/naver-ads/`
