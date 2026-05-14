# 모델 라우터 (Model Router)

사장님이 공유한 아키텍처를 코드와 문서로 영구화한 것이다.

## 전체 흐름

```txt
사장님
   ↓ 텔레그램/대시보드 명령
[Hermes AI / AgentAU / n8n]
   ↓
[CEO 오케스트레이터 AI]
   ↓
[모델 라우터]  ← 본 문서가 정의하는 단계
   ├─ Codex / ChatGPT  : 코딩, 시스템 구축, 전략
   ├─ Claude           : 긴 문서, 고급 코딩, 기획서, 검토
   ├─ Gemini           : 리서치, 트렌드 조사, 아이디어 확장
   ├─ Ollama (로컬)    : 내 PC 로컬 반복작업
   └─ 이미지 AI        : 광고 이미지, 썸네일
   ↓
[AI 회의]
   ↓
[실행 준비물 생성]
   ↓
[사장님 승인]
   ↓
[실행 (실제 채널 반영)]
```

모델 라우터는 작업 설명을 받아 어느 패널로 보낼지 점수화하고, dry-run
핸드오프 페이로드를 만든다. **실제 모델 호출은 하지 않는다.**

## 모델 매핑 요약

| 모델 | 역할 | 강점 키워드 예시 |
|---|---|---|
| Codex / ChatGPT | 코딩, 시스템 구축, 전략 | 코드, 자동화, 스크립트, 전략, CLI |
| Claude | 긴 문서, 고급 코딩, 기획서, 검토 | 기획서, 검수, 리뷰, 상세페이지, 설계 |
| Gemini | 리서치, 트렌드 조사, 아이디어 확장 | 리서치, 트렌드, 경쟁사, 시장, 키워드 조사 |
| Ollama (로컬) | 반복작업, 로컬 처리 | 분류, 태그, 라벨링, 초안, 반복, 대량 |
| 이미지 AI | 광고 이미지/썸네일 | 이미지, 썸네일, 포스터, 디자인, 비주얼 |

상세 키워드와 점수 가중치는 `ai_company/model_router.py`의 `MODEL_PROFILES`
에 정의돼 있다.

## 사용 방법

```powershell
python -m ai_company.main model-router --task "고스틱 광고 릴스 썸네일 시안 만들어줘"
python -m ai_company.main model-router --task "스마트스토어 상세페이지 검수해줘"
python -m ai_company.main model-router --task "고양이 MBTI 앱 경쟁 서비스 조사"
python -m ai_company.main model-router --task "최근 리뷰 200건을 긍정/부정으로 분류"
python -m ai_company.main model-router --task "Next.js 추천 웹앱 백엔드 리팩터링"
```

결과는 `08_reports/`에 두 가지로 저장된다.

- `model_router_decision_*.md` — 사람이 읽는 보고서 (1순위 / 후순위 / 사유)
- `model_router_handoff_*.json` — AI 회의 단계로 넘기는 dry-run 페이로드

## 안전 규칙

- 라우터 자체는 **실제 API 호출/모델 다운로드/메시지 발송을 하지 않는다.**
- 모델별 안전 노트는 보고서에 함께 출력된다.
- 외부 채널 반영(스마트스토어/네이버광고/SNS)은 9_approval 승인 파일 작성 후
  사장님 승인 단계에서만 진행한다.
- API 키, 비밀번호, `.env` 내용은 라우터 보고서에 출력하지 않는다.

## 확장 포인트

- 모델 추가: `MODEL_PROFILES`에 `ModelProfile` 항목 추가.
- 가중치 조정: `keyword_weight`, `strength_weight`를 조정.
- 다중 라우팅(병렬 모델 호출 권장): 후순위 점수가 1순위와 근접할 경우
  AI 회의 단계에서 양쪽 모두에게 보내도록 오케스트레이터가 결정한다.
- Hermes/AgentAU 연동: `handoff` JSON을 그대로 n8n webhook payload로 사용
  가능하다 (`ai_company/integrations.py`의 n8n payload 샘플과 호환).
