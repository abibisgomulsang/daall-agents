# 네이버 분석 도구 (수영 전용)

네이버 개발자 센터의 **DataLab(검색트렌드 + 쇼핑인사이트)** 와 **검색 API** 를 호출해서 광고 분석에 활용하는 CLI.

## 의존성
**없음.** Node.js 내장 모듈(`https`)만 사용. `npm install` 불필요.

요구: Node.js 18+ (현재 시스템엔 이미 깔려있음)

## 환경변수
`~/.openclaw/openclaw.json` 의 `env.vars` 에 등록:
```json
"NAVER_CLIENT_ID": "...",
"NAVER_CLIENT_SECRET": "..."
```

## 명령어

### `trend <키워드1> [키워드2 ...]`
DataLab 통합검색어 트렌드. 여러 키워드 동시 비교 가능.
```
node cli.js trend "고양이 낚시대" "캣닢 장난감" "고양이 와이어"
```

### `shopping-trend <카테고리코드>`
쇼핑인사이트 분야별 클릭 트렌드.
주요 카테고리 코드 일부:
- `50000008` 디지털/가전
- `50000007` 생활/건강
- `50000006` 패션잡화
- `50000003` 화장품/미용
- `50000005` 출산/육아
- 전체 코드: https://datalab.naver.com/shoppingInsight/sCategory.naver

```
node cli.js shopping-trend 50000007
```

### `shopping-keywords <카테고리코드> <키워드> [...]`
특정 분야 안에서 키워드별 클릭 추이.
```
node cli.js shopping-keywords 50000007 "고양이 장난감" "캣타워"
```

### `search <검색어>`
네이버 검색 결과 가져오기 (경쟁 상품 조사).
```
node cli.js search "냥와이어" --type shop --display 10
```
타입: `shop`(기본), `news`, `webkr`, `blog`, `cafearticle`, `image`

## 공통 옵션
- `--start YYYY-MM-DD` (기본: 30일 전)
- `--end YYYY-MM-DD` (기본: 오늘)
- `--unit date|week|month` (기본: date)

## 출력
모든 명령어가 **JSON을 stdout에 출력**합니다 (수영이 파싱해서 사람에게 표 형태로 정리).
에러는 stderr로 가고 exit code != 0.

## 위치
- GitHub: `tools/naver-analysis/`
- 런타임: `~/.openclaw/ws-suyeong/tools/naver-analysis/` (수영이 `node` 로 호출)

## 절대 하지 말 것
- 브라우저 자동화로 네이버 로그인 시도 ❌
- 광고비 조정 시도 ❌ (이 API에는 그 권한 없음)

광고비 자동 조정이 필요하면 별도로 **네이버 검색광고 API** 발급 후 `tools/naver-ads/` 에 추가 예정.
