# Premiere Pro 직접 컨트롤 — 사용 가이드

## 동작 원리 (요약)

비디오 AI가 SNS 대본을 받아서 다음 3가지를 자동으로 만듭니다.

| 산출물 | Premiere에서 하는 일 | 파일 |
|---|---|---|
| **FCPXML 1.10** | `File > Import` → 시퀀스 자동 생성 (1080×1920, 30fps) | `import_to_premiere.fcpxml` |
| **ExtendScript .jsx** | `File > Scripts > Run Script File...` → bin 자동 만들고 클립 임포트 | `auto_import.jsx` |
| **EDL** (백업) | 위 두 방식이 실패할 때 사용 | `backup.edl` |

같은 폴더의 `README.md`에 사장님이 클릭해야 할 순서가 정리되어 있습니다.

## 명령

```powershell
cd D:\AI_COMPANY
.\.venv\Scripts\Activate.ps1

# 산출물만 만들기 (가장 안전, 권장)
python -m ai_company.main premiere-control --script "후킹 자막. 사용 장면. 점프 컷. 결과 컷." --title "고스틱 릴스 01"

# Premiere Pro 자동 실행까지 (사장님 명시 승인)
python -m ai_company.main premiere-control --script "..." --launch --approve
```

`--launch` 만으로는 절대 실행되지 않습니다. **`--approve`도 함께 줘야** Windows에서 Premiere가 켜집니다 (안전 가드 2중).

## 사장님이 Premiere에서 하실 일 (3분 컷)

### 방법 A — ExtendScript (가장 빠름)

1. Premiere Pro 열기 → **새 프로젝트 만들기** (또는 기존 프로젝트 열기)
2. 메뉴 `File > Scripts > Run Script File...`
3. 만든 폴더의 `auto_import.jsx` 선택
4. 비디오 AI가 `<영상 제목>` bin에 클립 N개를 임포트합니다
5. 사장님이 컷을 끌어다 타임라인 완성 → 직접 Export

### 방법 B — FCPXML (시퀀스까지 자동)

1. Premiere Pro 열기
2. 메뉴 `File > Import` → `import_to_premiere.fcpxml`
3. 시퀀스가 자동 생성됩니다 (9:16, 30fps)
4. 클립이 오프라인이면 우클릭 → **Link Media** 로 실제 mp4 연결

## 클립 파일 준비

비디오 AI는 실제 mp4 파일을 만들지 **않습니다**. 사장님이 촬영본을 다음 경로에 두시면 됩니다:

```
06_apps/video_briefs/<stamp>/assets/clip_01.mp4
06_apps/video_briefs/<stamp>/assets/clip_02.mp4
...
```

파일이 없어도 FCPXML 임포트는 됩니다 — Premiere가 "오프라인" 상태로 잡고, 나중에 Link Media로 연결할 수 있습니다.

## 안전 가드 (자동)

- 기존 Premiere 프로젝트는 절대 수정하지 않습니다 (ExtendScript는 새 bin만)
- 자동 렌더링 / 자동 Export — 없음
- 자동 SNS 업로드 — 없음
- `--launch` + `--approve` 두 플래그 없으면 Premiere 자동 실행 안 됨
- BGM 라이선스 경고 모든 산출물에 명시

## 통합 흐름

`boss-command`나 `multi-meeting`이 "영상/편집" 키워드를 만나면 자동으로 비디오 AI를 회의에 부르고, 6단계 실행 준비에서 Premiere 산출물이 함께 만들어집니다:

```powershell
python -m ai_company.main boss-command --message "고스틱 릴스 영상 편집해줘" --live --multi
```

→ `08_reports/boss_command_*.md` 안에 비디오 패키지 + Premiere 산출물 위치가 함께 정리됨.

## 트러블슈팅

| 증상 | 해결 |
|---|---|
| Premiere에서 FCPXML 임포트 실패 | ExtendScript(`auto_import.jsx`) 방식으로 시도 |
| ExtendScript에 "프로젝트 없음" 경고 | Premiere에서 새 프로젝트를 먼저 만들고 다시 실행 |
| 클립이 오프라인 상태 | 우클릭 → Link Media → 실제 mp4 경로 지정 |
| `--launch --approve` 줬는데 안 켜짐 | Premiere가 설치된 표준 경로(`Program Files/Adobe/...`)에 있는지 확인. 콘솔에 경로 진단 출력됨 |
| .jsx에서 한글 깨짐 | Premiere에서 스크립트 인코딩이 UTF-8인지 확인. 우리는 UTF-8로 저장함 |
