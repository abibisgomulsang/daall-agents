# 사장님 원본 아키텍처 재정렬 보고서

## 1. 왜 다시 만들었나

사장님이 보내주신 원본 흐름:

```
사장님 → Hermes/AgentAU/n8n → CEO 오케스트레이터 → 모델 라우터 →
       AI 회의 → 실행 준비 → 사장님 승인
```

그리고 모델별 담당:

```
Codex / ChatGPT : 코딩, 시스템 구축, 전략
Claude          : 긴 문서, 고급 코딩, 기획서, 검토
Gemini          : 리서치, 트렌드 조사, 아이디어 확장
Ollama          : 내 컴퓨터 로컬 반복작업
이미지 AI        : 광고 이미지 / 썸네일 제작
```

제가 중간에 "코딩=Claude, 디자인=ChatGPT"로 매핑을 비틀었던 점, 그리고
7단계가 하나의 명령으로 묶여 있지 않았던 점을 모두 사장님 원본대로
되돌렸습니다.

## 2. 새/되돌린 파일

| 파일 | 변경 내용 |
|---|---|
| `ai_company/model_router.py` | 매핑을 원본 아키텍처대로 복구 (Codex=코딩·전략, Claude=긴 문서·검수) |
| `06_apps/agent_matrix/agents_data.js` | 자동 오케스트레이션 매핑 동기화 (developer/naverads → codex_chatgpt) |
| `ai_company/ceo_orchestrator.py` (신규) | CEO가 작업 분해·우선순위·책임 직원·위험 요소를 만드는 단계 |
| `ai_company/boss_pipeline.py` (신규) | 7단계 통합 파이프라인 `run_boss_command()` |
| `ai_company/main.py` | `boss-command --message "..." [--live]` CLI 추가 |
| `tests/test_smoke.py` | 원본 매핑 검증 + 7단계 파이프라인 검증 3건 추가 |
| `docs/COMMAND_FLOW.md` (신규) | 사장님 시점 가이드 |
| `TASK_BOARD.md` | 항목 갱신 |

## 3. 명령

```powershell
cd D:\AI_COMPANY
.\.venv\Scripts\Activate.ps1
python -m ai_company.main boss-command --message "고스틱 광고 효율 개선해줘"
```

이 한 줄에서 자동으로:

1. **Hermes 인바운드** — 메시지 수신 mock (외부 호출 없음)
2. **AgentAU/n8n** — 큐 진입 mock
3. **CEO 오케스트레이터** — 작업 분해, 책임 직원 선정, 위험 요소 식별
4. **모델 라우터** — Codex/Claude/Gemini/Ollama/이미지 AI 중 1순위 결정
5. **AI 회의** — 직원별 의견 + CEO 결론
6. **실행 준비** — 작업 종류 자동 감지 → 광고 패키지/이미지 시안/네이버광고 분석
7. **사장님 승인 대기** — 09_approval 자동 생성

결과는 `08_reports/boss_command_*.md` 한 파일로 묶이고, 각 단계 산출물도
개별 폴더에 저장됩니다.

## 4. 모델 매핑 (원본대로)

| 작업 키워드 | 모델 |
|---|---|
| 코딩 / 코드 / 백엔드 / CLI / 시스템 / 자동화 / 전략 / 마케팅 기획 | **Codex / ChatGPT** |
| 긴 문서 / 검수 / 검토 / 리뷰 / 상세페이지 / 기획서 / 고급 코딩 / 아키텍처 | **Claude** |
| 리서치 / 트렌드 / 경쟁사 조사 / 아이디어 확장 | **Gemini** |
| 분류 / 태그 / 반복 / 라벨링 / 대량 / 벌크 | **Ollama (로컬)** |
| 이미지 / 썸네일 / 포스터 / 비주얼 / DALL-E / Stable Diffusion | **이미지 AI** |

## 5. 사장님 시점 사용 흐름 (3분 컷)

1. **명령 한 줄**
   ```powershell
   python -m ai_company.main boss-command --message "고스틱 광고 만들어줘"
   ```
2. **결과 보고서 열기** — 콘솔이 알려주는 경로
3. **마지막 09_approval 파일 검토** — 산출물 OK/NG 결정
4. **OK면** 직접 외부 채널에 반영 / **NG면** 무시

외부 채널 자동 반영은 어떤 경우에도 일어나지 않습니다.

## 6. 안전 확인

- [x] 외부 API 자동 호출: 4단계 AI 회의에서 `--live` 명시할 때만
- [x] 비용 캡 자동 차단 (일일 ₩1,000 / 월 ₩30,000 기본)
- [x] 위험 키워드 자동 차단 + 09_approval 자동 생성
- [x] API 키 값 노출: 어디에도 출력 안 됨
- [x] 스마트스토어/네이버광고/SNS 자동 반영: 끝까지 없음
- [x] D:\AI_COMPANY 밖 파일 수정: 없음

## 7. 다음 추천 작업

- `boss-command --live` 호출 결과를 사장님이 한 번 확인 (회의 단계에서 Ollama 실제 호출)
- 시뮬레이터 채팅에서 `boss-command` 호출하도록 `local_viewer_server` 라우팅
- 가상 사무실 페이지에 "지금 진행 중인 7단계" 표시 (현재는 활동 로그만)
- AgentAU/n8n 실제 webhook 연결 (사장님 승인 후)
