# 수영 ↔ 가상 사무실 실데이터 파이프라인 구축 보고서

## 1. 수행한 일

사장님이 가상 사무실에 추가하신 **수영(suyeong)** 통합 비서를 외부 텔레그램
비서 → `real_data.json` → 가상 사무실로 이어지는 실데이터 파이프라인의
종단점으로 만들었다.

가상 사무실 페이지는 30초마다 `08_reports/real_data.json`을 폴링하고,
파일이 있으면 그 수치를 기반으로 에이전트들이 대화/회의/산출물을 만든다.
파일이 없으면 `real_data.sample.json`을 폴백으로 사용하고 상단 배지를
노란색 "샘플"로 표시한다.

## 2. 생성/수정한 파일

- 신규: `08_reports/real_data.sample.json` — 표준 스키마 + 데모 수치
- 신규: `docs/REAL_DATA_PIPELINE.md` — 스키마/흐름/안전 규칙 문서
- 수정: `06_apps/virtual_office/app.js` — fetch 로더, 폴링, 신규 이벤트 2종(`real_alert`, `real_data_chat`), 데이터 기반 발언 헬퍼
- 수정: `06_apps/virtual_office/index.html` — 상단 strip에 `realDataBadge` 추가
- 수정: `06_apps/virtual_office/styles.css` — 배지 색상 + 알림 강조 스타일
- 수정: `tests/test_smoke.py` — 실데이터 통합 코드 검증 + 샘플 JSON 스키마 검증
- 신규 본 보고서

## 3. 가상 사무실 동작 변경

| 항목 | 변경 전 | 변경 후 |
|---|---|---|
| 이벤트 분포 (실데이터 없음) | pair_chat 45% / meeting 25% / move 15% / artifact 15% | 동일 |
| 이벤트 분포 (실데이터 있음) | — | real_alert 18% / real_data_chat 14% / pair_chat 23% / meeting 20% / move 13% / artifact 12% |
| 상단 strip | "사무실 가동 중 · …" | "… · 🌊 실데이터 · ROAS 1.42 · 알림 3" 배지 추가 |
| 알림 표시 | 없음 | `alerts[]`이 새로 들어오면 활동 로그 상단에 색깔 강조 |
| 산출물 생성 | 고정 8종 풀에서 랜덤 | + 알림 릴레이 시 "[실데이터] {제목} 후속 메모" 자동 생성 |

## 4. 실데이터 발언 예시

샘플 데이터(ROAS 1.42, REFILL01 재고 2개) 기준 자동 생성되는 대화:

- 데이터 → CEO: "현재 ROAS 1.42 — 목표 2.0 미달. 낭비 키워드 1순위: '고양이 장난감' (ROAS 0.72)"
- 스마트스토어 → CEO: "재고 경고: REFILL01 2개 · 일평균 1.8개 → 발주 검토(승인 후 실행)."
- 수영 → 데이터: "🌊 ROAS 1.42 (목표 2.0 미달) — 데이터에 전달했습니다."

각 발언은 대화록 탭에 마크다운 형식(`## [시각] 화자 → 청자 · ...`)으로 남고,
산출물 탭에도 자동 메모가 누적된다.

## 5. 텔레그램 비서가 파일 쓰는 방법 (안내)

수영이 사장님 명령으로 데이터를 갱신할 때는 다음 파일을 덮어쓰면 된다:

```
D:\AI_COMPANY\08_reports\real_data.json
```

스키마는 `docs/REAL_DATA_PIPELINE.md`의 표준 형식을 따른다. 모든 키는
옵션이므로 일부만 채워서 보내도 가상 사무실은 조용히 무시하고 가상
시나리오로 폴백한다.

## 6. 안전 확인

- `real_data.json`은 **수치만** 담는 파일. API 키 / 비밀번호 / 쿠키 / 토큰
  포함 금지 (스키마 문서에 명시)
- 가상 사무실은 표시·해설만. 실제 입찰 변경 / 발주 / 업로드는 **항상
  09_approval 파일 만들고 사장님 승인 후에만** 진행
- 알림 강조 색은 info=파랑 / warning=노랑 / danger=빨강 — 시각적 분리만 하고
  자동 외부 실행은 없음
- `file://` 프로토콜에서 fetch가 차단되는 경우 자동 폴백(콘솔 에러 안 띄움)
- 폴링 주기 30초 — 사장님 PC 부하 거의 없음

## 7. 사장님 확인 필요한 부분

- 폴링 주기(30초)가 너무 빈번하거나 적절한지
- 알림 컬러 매핑(info 파랑 / warning 노랑 / danger 빨강) 톤
- 수영의 자리 좌표(현재 `secretaryDesk: (300, 240)`) — 사무실 평면도와 어울리는지
- 실데이터 발언 톤(현재는 "ROAS 1.42 — 목표 미달") — 사장님 말투에 맞게 조정 가능

## 8. 사용 방법

```powershell
# 서버 켜기 (file:// 직접 열기보다 권장 — fetch가 안정적)
powershell -ExecutionPolicy Bypass -File .\scripts\start_local_viewer.ps1 -OpenBrowser

# 가상 사무실 열기
start http://127.0.0.1:8765/06_apps/virtual_office/index.html
```

처음 열면 상단 strip에 노란색 "🌊 샘플 · ROAS 1.42" 배지가 보입니다.
텔레그램 비서 수영이 `real_data.json`을 덮어쓰면 30초 안에 자동으로
초록색 "🌊 실데이터 · ROAS X.XX" 배지로 전환됩니다.

## 9. 다음 추천 작업

- 텔레그램 비서 수영의 실제 파일 쓰기 어댑터 (Hermes/n8n과 연결)
- `real_data.json`에 timestamp 검사 추가 — N분 이상 갱신 안 되면 "데이터 오래됨" 경고
- 대화록 탭의 실데이터 발언을 `10_meetings/`에 영구 저장
- 가상 사무실에서 alert.owner가 09_approval 파일 자동 생성 트리거
