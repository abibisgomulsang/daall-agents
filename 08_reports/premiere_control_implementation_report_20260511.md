# Adobe Premiere Pro 직접 컨트롤 — 구축 보고서

## 1. 한 줄 요약

비디오 AI가 만든 9:16 타임라인을 **Premiere Pro가 곧장 임포트할 수 있는 3가지
산출물**(FCPXML / ExtendScript / EDL)로 자동 변환하고, 사장님이 명시 승인하시면
Windows에서 Premiere도 직접 실행합니다.

## 2. 왜 이 방식인가 (안전 결정)

| 가능한 방식 | 채택 여부 | 이유 |
|---|---|---|
| FCPXML 자동 생성 | ✅ 채택 | Premiere 공식 임포트 포맷, 안정적 |
| ExtendScript .jsx | ✅ 채택 | Adobe 공식 자동화 API, bin/임포트 자동 |
| EDL | ✅ 백업 | FCPXML/.jsx 실패 시 비상용 |
| UI 자동화 (pywinauto/AutoHotkey) | ❌ 거부 | 사장님 프로젝트 깨질 위험, 버전 의존 |
| `aerender` 같은 CLI | ❌ 거부 | Premiere에는 없음 (After Effects 전용) |

위 두 가지는 **사장님 기존 프로젝트를 절대 수정하지 않습니다.** ExtendScript는 새 bin만 만들고, FCPXML은 새 시퀀스만 추가합니다.

## 3. 신규 모듈

| 파일 | 역할 |
|---|---|
| `ai_company/premiere_controller.py` | FCPXML 1.10 빌더 + ExtendScript(.jsx) 빌더 + EDL 빌더 + `launch_premiere()` |
| `docs/PREMIERE_CONTROL.md` | 사장님 시점 사용 가이드 |

## 4. 수정한 모듈

| 파일 | 변경 |
|---|---|
| `ai_company/video_editing.py` | `write_video_package()`에서 Premiere 패키지 자동 동시 생성 (`include_premiere=True`) |
| `ai_company/agent_persona.py` | 비디오 AI 시스템 프롬프트에 "Premiere FCPXML/.jsx 자동화 가능" 명시 |
| `ai_company/main.py` | `premiere-control --script "..." [--launch --approve]` CLI 추가 |
| `tests/test_smoke.py` | FCPXML 핵심 태그/ExtendScript 함수/안전 가드 2건 추가 |

## 5. 새 CLI 명령

```powershell
cd D:\AI_COMPANY
.\.venv\Scripts\Activate.ps1

# (A) 산출물만 만들기 (안전, 권장 — 사장님이 Premiere 직접 여시는 흐름)
python -m ai_company.main premiere-control --script "후킹 자막. 점프 컷. 결과 컷." --title "고스틱 릴스 01"

# (B) Premiere Pro 자동 실행까지 (이중 안전 가드)
python -m ai_company.main premiere-control --script "..." --launch --approve

# (C) 기존 video-timeline도 Premiere 산출물 자동 포함
python -m ai_company.main video-timeline --script "..." --title "고스틱 릴스"

# (D) boss-command가 키워드 감지 시 자동 호출
python -m ai_company.main boss-command --message "고스틱 릴스 편집해줘" --live --multi
```

`--launch`만으로는 절대 Premiere가 실행되지 않습니다. **`--approve` 까지 명시할 때만** 실행 — 사장님 안전 가드 2중.

## 6. 산출물 4종 (한 번에 자동 생성)

`06_apps/video_briefs/<stamp>/premiere/` 폴더에:

```
import_to_premiere.fcpxml   ← File > Import 로 임포트, 시퀀스 자동 생성
auto_import.jsx             ← File > Scripts > Run Script File 로 실행, bin 자동 만들고 클립 임포트
backup.edl                  ← CMX3600 EDL 백업
README.md                   ← 사장님 시점 가이드
```

종합 보고서는 `08_reports/premiere_package_*.md` 에 한 부 더.

## 7. 사장님이 Premiere에서 하실 일 (3분 컷)

### 방법 A — ExtendScript (가장 빠름)

1. Premiere Pro 열기 → 새 프로젝트
2. `File > Scripts > Run Script File...` → `auto_import.jsx`
3. AI 회사가 `<제목>` bin에 클립 임포트
4. 컷 끌어다 타임라인 → 사장님이 직접 Export

### 방법 B — FCPXML (시퀀스까지 자동)

1. Premiere Pro 열기
2. `File > Import` → `import_to_premiere.fcpxml`
3. 시퀀스 자동 생성 (1080×1920 9:16, 30fps)
4. 클립 오프라인이면 우클릭 → Link Media

## 8. 안전 가드 (자동)

- 기존 Premiere 프로젝트 절대 수정 없음 (ExtendScript는 새 bin만)
- 자동 렌더링 / 자동 Export — 없음
- 자동 SNS 업로드 — 없음
- Premiere 자동 실행 — `--launch` + `--approve` 두 플래그 동시 명시 시만
- BGM 라이선스 경고 모든 산출물에 명시
- 외부 채널 반영 — 끝까지 없음

## 9. 통합 흐름 — 이미 동작 중

```
사장님 명령 "고스틱 릴스 영상 편집해줘"
   ↓
boss-command 7단계
   ↓ 5단계 멀티 에이전트 회의 — SNS/비디오/마케팅/검수 합석
   ↓ 6단계 실행 준비
   └→ video_editing.write_video_package(include_premiere=True)
       ├→ timeline.md
       ├→ auto_edit_moviepy.py
       ├→ subtitles.srt
       └→ premiere/
           ├→ import_to_premiere.fcpxml
           ├→ auto_import.jsx
           ├→ backup.edl
           └→ README.md
   ↓ 7단계 09_approval 자동 생성
```

## 10. 안전 체크리스트

- [x] FCPXML 1.10 표준 준수 (Premiere 공식 임포트 가능)
- [x] ExtendScript는 새 bin만 만들고 기존 프로젝트 수정 안 함
- [x] 자동 실행 2중 가드 (`--launch` + `--approve`)
- [x] Premiere 미설치 / 경로 못 찾을 때 친절한 안내 메시지
- [x] 한글 시퀀스 이름 안전 처리 (특수문자 자동 sanitize)
- [x] 산출물 위치는 모두 `06_apps/video_briefs/<stamp>/` 안

## 11. 다음 추천 작업

- **자막 BurnIn 옵션** — FCPXML title 트랙으로 자막 자동 삽입
- **Premiere Pro UXP 플러그인** — 외부 jsx 대신 정식 플러그인으로 승격 (사장님 결정 후)
- **렌더 큐 자동화** — Adobe Media Encoder의 `ame` CLI 연결 (승인 후만)
- **결과 미리보기** — 가상 사무실 페이지에서 산출물 위치 자동 표시
