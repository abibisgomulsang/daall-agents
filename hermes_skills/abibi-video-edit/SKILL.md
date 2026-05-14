---
name: abibi-video-edit
description: 아비비 AI 회사 — 비디오 AI. SNS 대본 받아 9:16 릴스/쇼츠 타임라인 + MoviePy Python 자동 편집 스크립트 + Adobe Premiere Pro 임포트용 FCPXML/.jsx + SRT 자막까지 한 번에 생성.
triggers:
  - "영상 편집"
  - "릴스 편집"
  - "쇼츠 편집"
  - "비디오 만들어"
  - "프리미어"
  - "타임라인"
  - "자막"
---

# 비디오 AI — SNS 대본 → 편집 패키지

사장님 메시지에서 **SNS 대본**을 추출하라. 사장님이 짧은 키워드만 주면
("고스틱 릴스 편집해줘") 비디오 AI가 알아서 대본을 짜고 진행.

## 동작 (대본이 있을 때)

```bash
cd /mnt/d/AI_COMPANY
"/mnt/d/AI_COMPANY/.venv/Scripts/python.exe" -m ai_company.main video-timeline \
  --script "<SNS 대본>" \
  --title "<영상 제목>" \
  --seconds 15
```

## 동작 (Premiere 자동 임포트 패키지만)

```bash
"/mnt/d/AI_COMPANY/.venv/Scripts/python.exe" -m ai_company.main premiere-control \
  --script "<SNS 대본>" \
  --title "<제목>" \
  --seconds 15
```

## 동작 (Premiere 자동 실행까지 — 사장님 명시 승인 시)

```bash
"/mnt/d/AI_COMPANY/.venv/Scripts/python.exe" -m ai_company.main premiere-control \
  --script "..." --launch --approve
```

`--launch`만으로는 실행 안 됨. **`--approve`도 함께 줘야** Premiere 켜짐.

## 결과 4종 + Premiere 패키지

- `D:\AI_COMPANY\06_apps\video_briefs\<시간>\timeline.md` — 컷별 타임라인
- `auto_edit_moviepy.py` — Python 자동 편집 스크립트
- `ffmpeg_concat.sh` — ffmpeg 명령
- `subtitles.srt` — SRT 자막
- `premiere/import_to_premiere.fcpxml` — Premiere 임포트용
- `premiere/auto_import.jsx` — Premiere ExtendScript

## 사장님께 보고할 것

1. 총 컷 개수 / 길이
2. Premiere에서 어떤 파일을 어떻게 임포트할지 (`File > Scripts > Run Script File...` → `auto_import.jsx`)
3. mp4 클립 준비 위치 안내: `06_apps/video_briefs/<시간>/assets/clip_01.mp4` ...
4. 라이선스 BGM 확인 경고

## 안전 규칙

- 실제 영상 렌더링 안 함 (사장님이 Premiere에서 직접 Export)
- 자동 SNS 업로드 절대 없음
- 기존 Premiere 프로젝트 안 건드림 (새 bin/새 시퀀스만)
- BGM 라이선스 경고 모든 산출물에 명시
