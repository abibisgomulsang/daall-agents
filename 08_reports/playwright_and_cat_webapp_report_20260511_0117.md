# Playwright Dry-run 및 고양이 추천 웹앱 MVP 보고서

## 1. 수행 목적

외부 사이트 실제 조작 없이 Playwright 자동화 설계를 만들고, 고양이 장난감 추천 웹앱 MVP를 정적 웹앱으로 구현했다.

## 2. Playwright dry-run

명령:

```powershell
python -m ai_company.main playwright-dry-run --target naver_ads
```

생성:

```txt
08_reports/playwright_dry_run_naver_ads_20260511_011628.md
```

안전 범위:
- 실제 브라우저 자동화 실행 안 함
- 외부 사이트 로그인 안 함
- 입찰가/광고비/키워드 변경 안 함

## 3. 고양이 장난감 추천 웹앱 MVP

생성 위치:

```txt
06_apps/cat_toy_recommender
```

구성:
- `index.html`
- `styles.css`
- `app.js`
- `README.md`

현재 기능:
- 질문 3개
- 고스틱, 플라고스틱, 고스틱 리필 추천
- 결과 이유와 놀이 팁 표시

## 4. 테스트 결과

- `.\.venv\Scripts\python.exe -m pytest`
- 결과: 12 passed
- `node --check 06_apps\cat_toy_recommender\app.js`
- 결과: 성공

## 5. 안전 확인

- 스마트스토어 연결 없음
- 결제/주문 없음
- 외부 업로드 없음
- 네이버광고 실제 변경 없음
