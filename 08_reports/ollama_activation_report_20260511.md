# Ollama 실제 연결 활성화 보고서

## 1. 사장님 환경 확인 결과

- `ollama list` → 정상 응답
- 11434 포트 응답 정상
- 설치 모델: `gemma4:e2b` (5.1B, 7.2GB), `gemma4:latest` (8.0B, 9.6GB)
- 양자화 둘 다 Q4_K_M (메모리 효율형) — RAM 32GB · CPU 16코어 환경에서 충분

## 2. 활성화한 모듈

| 모듈 | 변경 | 효과 |
|---|---|---|
| `ai_company/ollama_runtime.py` (신규) | urllib 기반 HTTP 어댑터 | `is_alive` / `list_models` / `generate` / `chat` / `status_summary` |
| `ai_company/ollama_models.py` | `build_ollama_live_status()` 추가 | 실제 데이터 보고서, 죽으면 dry-run 폴백 |
| `ai_company/meeting.py` | `--live` 옵션 추가 | 각 AI 직원 의견과 CEO 결론을 Gemma4가 실제 생성 |
| `ai_company/nl_command.py` | `--live` 옵션 추가 | 의도 분류 결과에 LLM 코멘트 한 줄 보강 |
| `ai_company/main.py` | 새 CLI 명령들 | `meeting --live`, `nl --live`, `ollama-live-status` |
| `scripts/local_viewer_server.py` | `/api/ollama/status` 엔드포인트 | 브라우저에서 라이브 상태 폴링 |
| `06_apps/agent_matrix/index.html` + `app.js` + `styles.css` | LIVE 도트와 선택된 Ollama 행에 🟢 LIVE 태그 | 사장님이 페이지에서 한눈에 확인 |
| `06_apps/virtual_office/app.js` | 15초마다 `/api/ollama/status` 폴링 | 가상 사무실 활동 로그에 LIVE/OFF 전환 알림 |
| `tests/test_smoke.py` | 5건 추가 | 데드 엔드포인트 폴백, 가짜 모델 응답, 라이브 모드 회의 폴백 |

## 3. 새 CLI 명령 사용법

```powershell
cd D:\AI_COMPANY
.\.venv\Scripts\Activate.ps1

# Ollama 라이브 상태만 확인 (실제 호출)
python -m ai_company.main ollama-live-status

# 회의를 진짜 Gemma4가 진행
python -m ai_company.main meeting --topic "고스틱 광고 효율 개선" --with-router --live

# 자연어 명령 + LLM 코멘트
python -m ai_company.main nl --message "고스틱 광고 만들어줘" --live
```

`--live` 플래그를 빼면 기존 dry-run 동작. **모든 라이브 호출은 127.0.0.1만 사용**하므로
외부 네트워크 호출 0.

## 4. 안전 보강

- 호출 실패/타임아웃/모델 없음 → 모든 함수가 `None` 반환 → 호출자가 자동으로
  `_offline_opinion()` / dry-run 폴백
- `OLLAMA_BASE_URL`은 환경변수로 분리 (기본 `http://localhost:11434`)
- 기본 모델은 `DEFAULT_LOCAL_MODEL` 환경변수로 변경 가능 (기본 `gemma4:e2b`)
- 외부 채널 반영(스마트스토어/네이버광고/SNS/결제)은 **변경 없이 그대로 차단**
- `--live`는 명시적 옵션. 기본은 여전히 dry-run

## 5. 동작 시나리오 (사장님이 보실 것)

### A. 가상 사무실 페이지
열고 잠시 기다리시면 활동 로그 상단에 다음이 추가됩니다:

```
🟢 Ollama LIVE · gemma4:e2b 응답 (123ms)
```

Ollama를 종료하면:

```
⚪ Ollama 응답 없음 — dry-run 폴백
```

### B. 직원 에이전트 보기 → 모델 오케스트레이션 모달
"내 머신 자동 감지" 박스 아래에 라이브 상태 줄이 추가됩니다:

```
🟢 Ollama LIVE · 2개 모델 · 기본 gemma4:e2b ✅ · 응답 123ms
```

Ollama 행을 선택한 에이전트 옆에는 `🟢 LIVE` 태그.

### C. CLI 회의 라이브 모드
```
python -m ai_company.main meeting --topic "고스틱 광고 효율 개선" --with-router --live
```
→ 회의록의 각 AI 직원 의견과 CEO 결론이 Gemma4가 실제로 생성한 한국어 텍스트로 채워집니다.
실패 시 자동 폴백.

## 6. 다음 추천 작업 (Ollama 외)

- `.env`에 `ANTHROPIC_API_KEY`/`GOOGLE_API_KEY` 채우면 Claude/Gemini 어댑터 활성화
- Stable Diffusion / Canva 어댑터 (이미지 AI)
- 텔레그램 비서 수영 → `real_data.json` 실제 쓰기 어댑터 (Hermes/n8n과 연결)
- `meeting --live` 결과를 `nl_command`의 의도 분류에도 전달해서 자동 회의 진입

## 7. 안전 체크리스트

- 외부 네트워크 호출: ❌ 없음 (127.0.0.1 로컬만)
- 결제·발송·업로드: ❌ 없음
- API 키/비밀번호 노출: ❌ 없음
- 모델 자동 다운로드: ❌ 없음 (`generate`/`chat`은 이미 설치된 모델만)
- 위험 키워드 자동 차단: ✅ 그대로 유지
- 09_approval 승인 흐름: ✅ 그대로 유지
