# 비디오 AI(Video Editor) 영입 보고서

## 1. 사장님 요청 그대로

> 가상 사무실에 비디오 에이전트(Video Editor)를 한 명 더 추가하자.
> 이 친구는 SNS 에이전트가 쓴 대본을 받아서 실제 영상 편집을 위한
> 타임라인 설계나 자동 편집 스크립트(Python)를 짜주는 역할을 할 거야.

## 2. 영입 결과 한눈에

| 항목 | 위치 | 결과 |
|---|---|---|
| 매트릭스 카드 | `06_apps/agent_matrix/agents_data.js` | 🎬 보라 카드, 상태 active |
| 멀티 회의 멤버 | `ai_company/agent_persona.py` | 페르소나 등록 (model_pref=ollama, 폴백 OpenAI 가능) |
| CEO 작업 분배 | `ai_company/ceo_assigner.py` | "비디오/영상/편집/타임라인" 키워드 → video, SNS 작업 시 자동 동참 |
| 작업 분해 | `ai_company/ceo_orchestrator.py` | 5개 서브태스크 자동 |
| 실행 준비 산출물 | `ai_company/video_editing.py` (신규) | 타임라인 .md + MoviePy .py + ffmpeg .sh + SRT 자막 |
| CLI 단독 | `python -m ai_company.main video-timeline --script "..."` | 한 줄로 패키지 생성 |
| boss-command 통합 | `boss_pipeline.py` | "영상/편집" 키워드면 6단계에서 자동 호출 |
| 자동 모델 매핑 | `agents_data.js` | `video → codex_chatgpt` (코딩 작업 적합) |
| 가상 사무실 자리 | `06_apps/virtual_office/app.js` | 스튜디오(스튜디오 우측 책상) |

## 3. 산출물 4종 — 자동 생성되는 파일

비디오 AI가 한 번 호출되면 `06_apps/video_briefs/<stamp>/` 폴더에 다음이 떨어집니다:

```
timeline.md            ← 9:16 컷별 타임라인 (시작/끝/자막/BGM 표)
auto_edit_moviepy.py   ← MoviePy 기반 Python 자동 편집 스크립트 초안
ffmpeg_concat.sh       ← ffmpeg concat 한 줄 명령 예시
subtitles.srt          ← SRT 자막 초안
```

그리고 `08_reports/video_brief_*.md` 에 종합 보고서 한 부가 더 남습니다.

**MoviePy 스크립트는 자동 실행되지 않습니다.** 사장님이 실제 mp4 클립을
준비한 뒤 직접 `python auto_edit_moviepy.py` 로 돌리시면 됩니다. BGM도
라이선스 확보된 음원만 쓰도록 주석으로 명시했습니다.

## 4. 사장님 명령

```powershell
cd D:\AI_COMPANY
.\.venv\Scripts\Activate.ps1

# (A) 단독 호출 — SNS 대본만 넘기기
python -m ai_company.main video-timeline --script "사줘도 안 놀던 고양이..."

# (B) 7단계 흐름 안에서 자동 진행 — boss-command가 키워드로 감지
python -m ai_company.main boss-command --message "고스틱 릴스 영상 편집해줘" --live --multi

# (C) 멀티 회의로 비디오 AI 의견 받기
python -m ai_company.main multi-meeting --topic "고스틱 광고 릴스 컷 편집 전략"
```

(B)에서는 6단계 "실행 준비"가 자동으로 비디오 패키지를 산출합니다.

## 5. 페르소나 카드

| 필드 | 값 |
|---|---|
| key | video |
| 이름 | 비디오 AI |
| 모델 (기본) | Ollama gemma4:latest (무료) |
| 폴백 / 부스트 | OpenAI ChatGPT (코딩 강세) |
| 시스템 프롬프트 핵심 | "9:16 릴스/쇼츠 컷 타임라인 + MoviePy 자동 편집 Python 스크립트. 실제 업로드 안 함." |
| 말투 | 타임라인·컷·자막·BGM |
| 메모리 폴더 | `11_memory/agents/video_ai/rounds.jsonl` |

## 6. 회의에서의 위치

SNS 작업이 들어오면 ceo_assigner가 회의 멤버에 **자동으로 비디오 AI를 합석**시킵니다.
반대로 비디오 작업이면 SNS·마케팅·검수가 같이 들어와서 한 팀을 구성합니다.

```
ceo_assigner.assign("고스틱 릴스 편집해줘")
   ↓
{
  "primary_owner_key": "video",
  "member_keys": ["video", "sns", "marketing", "review"],
  ...
}
```

## 7. 비용 영향

비디오 AI 기본은 Ollama라 **추가 비용 0**. 코딩이 복잡해서 ChatGPT로 승격할 경우에만
일일 캡(₩1,000)에서 약 ₩50~100 소비. 캡 초과 위험이면 자동으로 Ollama로 강등.

## 8. 안전 확인

- [x] 실제 영상 렌더링 — 하지 않음 (스크립트만 산출)
- [x] 실제 SNS 업로드 — 하지 않음 (09_approval 승인 후 사장님 직접 실행)
- [x] BGM 라이선스 경고 — 모든 산출물에 명시
- [x] 외부 API 호출 — 캡 검사 후만, 키 없으면 Ollama 폴백
- [x] 프롬프트/응답 본문 저장 — 안 함 (라운드 메타데이터만)

## 9. 다음 추천 작업

- 가상 사무실 페이지에 비디오 AI 책상 강조 표시 (스튜디오 영역)
- `video_editing`에 Premiere/Final Cut용 XML 출력 추가
- SNS AI ↔ 비디오 AI 직접 패스 (SNS가 대본 만들면 자동으로 video-timeline 호출)
