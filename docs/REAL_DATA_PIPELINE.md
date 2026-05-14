# 실데이터 파이프라인 — 수영 에이전트 ↔ 가상 사무실

## 전체 흐름

```
[사장님 텔레그램]
   ↓
[텔레그램 비서 수영] — 네이버광고/스마트스토어/인스타 실수치 수집
   ↓ (파일 쓰기)
D:\AI_COMPANY\08_reports\real_data.json
   ↑ (30초마다 fetch)
[가상 사무실 페이지 — virtual_office/app.js]
   ├─ 상단 strip에 "🌊 실데이터 · ROAS 1.42" 배지 표시
   ├─ 알림(alerts)을 활동 로그 상단에 강조
   ├─ 18% 확률 — 수영 → 담당 에이전트 알림 릴레이
   └─ 14% 확률 — 데이터/스마트스토어 에이전트가 실수치 기반 발언
```

가상 사무실은 30초마다 `real_data.json`을 조용히 폴링한다. 파일이 없으면
`real_data.sample.json`을 폴백으로 사용하고 상단 배지는 노란색 "샘플"로 표시.
실데이터 파일이 생기면 자동으로 초록색 "실데이터"로 전환.

## 표준 JSON 스키마

```jsonc
{
  "updated_at": "ISO8601 시각 (예: 2026-05-11T14:20:00+09:00)",
  "source": "텔레그램 비서 수영",
  "is_sample": false,                  // 실데이터면 false
  "naver_ads": {
    "roas": 1.42,
    "ctr": 0.038,
    "cpc": 920,
    "spend_today_krw": 124500,
    "impressions_today": 42180,
    "clicks_today": 1604,
    "conversions_today": 12,
    "target_roas": 2.0,
    "worst_keywords": [{ "keyword": "...", "roas": 0.72, "spend_krw": 35000 }],
    "best_keywords":  [{ "keyword": "...", "roas": 3.10 }]
  },
  "smartstore": {
    "today_orders": 18,
    "today_revenue_krw": 487000,
    "avg_review_score": 4.6,
    "review_count_7d": 24,
    "negative_review_keywords": ["배송 늦음"],
    "low_stock": [{ "product": "REFILL01", "stock": 2, "daily_velocity": 1.8 }],
    "recent_questions_unread": 3
  },
  "instagram": {
    "followers": 4820,
    "reach_7d": 28400,
    "top_post_likes": 312,
    "pending_drafts": 2
  },
  "team_state": {
    "boss_focus": "광고 효율 회복",
    "today_priority": ["ROAS 회복", "REFILL01 재고"]
  },
  "alerts": [
    {
      "level": "info | warning | danger",
      "title": "ROAS 1.42 (목표 2.0 미달)",
      "detail": "낭비 키워드 3개. 입찰 변경 전 광고 문구 확인.",
      "owner": "데이터"            // 가상 사무실 에이전트 이름과 일치
    }
  ]
}
```

모든 키는 **옵션**이다. 누락된 필드는 가상 사무실에서 조용히 무시되고
가상 시나리오로 폴백한다. 필요한 부분만 채워서 보내도 된다.

## 데이터 반영 로직

| 이벤트 | 트리거 조건 | 결과 |
|---|---|---|
| 실데이터 연결 알림 | 처음 파일 발견 시 / 샘플→실데이터 승격 시 | 활동 로그에 "🌊 수영 · 실데이터 연결됨" |
| 신규 알림 릴레이 | `alerts[]`에 새 항목이 등장 | 활동 로그에 색깔 강조 (info=파랑/warning=노랑/danger=빨강) |
| 수영 → 담당 에이전트 (real_alert) | 18% 확률, 자율 모드 시 | 수영이 alert.owner에게 이동 → 대회의실/책상에서 대화 → 산출물(40% 확률) 생성 |
| 데이터/스마트스토어 발언 (real_data_chat) | 14% 확률, 자율 모드 시 | CEO와 회의 테이블에서 실수치 기반 보고 ("ROAS 1.42 — 목표 미달") |
| ROAS < target 분기 | `naver_ads.roas < target_roas` | 데이터 에이전트가 1순위 낭비 키워드 인용 |
| 재고 < 임계 | `smartstore.low_stock[].stock` | 스마트스토어 에이전트가 발주 검토 권고 (실행은 승인 후) |

## 텔레그램 비서가 파일 쓰는 방법 (권장 패턴)

수영(텔레그램 비서)이 다음 흐름으로 파일을 쓰면 됨:

```python
# 예시 — 사장님 승인 후 수영이 호출하는 코드 (pseudocode)
import json, datetime
from pathlib import Path

def write_real_data(payload: dict, root: Path) -> Path:
    payload["updated_at"] = datetime.datetime.now().isoformat()
    payload["source"] = "텔레그램 비서 수영"
    payload["is_sample"] = False
    out = root / "08_reports" / "real_data.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out
```

이 파일이 만들어지면 가상 사무실 페이지는 30초 안에 자동으로 인지한다.
페이지 새로고침은 필요 없음.

## 보안/안전 규칙

- `real_data.json`은 **읽기 전용 수치**만 담는다. API 키 / 비밀번호 / 쿠키 /
  세션 토큰을 절대 넣지 않는다.
- 가상 사무실은 이 파일을 **표시·해설**만 한다. 실제 입찰 변경, 발주,
  업로드는 **항상 09_approval 파일을 만들고 사장님 승인 후**에만 진행한다.
- 가상 사무실이 alerts를 보여주는 것은 "알림" 단계까지이며, 자동 외부 실행은
  하지 않는다.

## 로컬 파일 vs 서버 접속

- **서버 켜고 접속** (`http://127.0.0.1:8765/06_apps/virtual_office/index.html`):
  fetch가 정상 동작 → 실데이터 즉시 인식
- **파일 직접 열기** (`file://`): 브라우저가 fetch를 차단할 수 있음 → 실데이터
  배지가 안 보일 수 있음. 이 경우 로컬 뷰어 서버를 켜고 접속 권장:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start_local_viewer.ps1 -OpenBrowser
```

## 샘플 → 실데이터 전환 테스트

1. 현재 상태: `real_data.json` 없음 → 가상 사무실이 `real_data.sample.json`을 폴백 사용
2. 사장님이 텔레그램으로 "수영아 광고 상황 갱신" 명령
3. 수영이 `08_reports/real_data.json`을 새로 쓰면
4. 30초 안에 배지가 노란 "샘플" → 초록 "실데이터"로 자동 전환
5. 신규 알림이 있으면 활동 로그 상단에 색깔 강조 표시
