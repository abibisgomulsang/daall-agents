"""비디오 AI — SNS 대본 → 9:16 릴스/쇼츠 타임라인 + 자동 편집 Python 스크립트.

이 모듈은 **dry-run**만 한다. 실제 영상 렌더링/업로드는 사장님 승인 후
별도로 진행한다. 비디오 에이전트는 다음을 산출한다:

1) 타임라인 마크다운 (시작/끝/컷/자막/BGM)
2) MoviePy 기반 Python 자동 편집 스크립트 초안
3) ffmpeg 한 줄 합성 명령 예시
4) SRT 자막 파일 초안

실제 파일이 없어도 사장님이 보고서만 받아 검토할 수 있도록 텍스트 위주.
"""
from __future__ import annotations

import json
import re  # noqa: F401  — premiere 통합에서 사용
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from .paths import ROOT
from .utils import now_stamp, write_report


@dataclass
class VideoClip:
    start: float
    end: float
    description: str
    subtitle: str
    audio: str = "BGM low"


@dataclass
class VideoTimeline:
    title: str
    total_seconds: float
    ratio: str
    clips: List[VideoClip]
    bgm_hint: str
    source_script: str

    def to_markdown(self) -> str:
        lines = [f"# 비디오 타임라인 — {self.title}", ""]
        lines.append(f"- 비율: {self.ratio}")
        lines.append(f"- 총 길이: {self.total_seconds:.1f}초")
        lines.append(f"- BGM 가이드: {self.bgm_hint}")
        lines.append("")
        lines.append("## 컷 시퀀스")
        lines.append("")
        lines.append("| # | 시작 | 끝 | 길이 | 비주얼 | 자막 |")
        lines.append("| --- | ---: | ---: | ---: | --- | --- |")
        for i, c in enumerate(self.clips, 1):
            lines.append(
                f"| {i} | {c.start:.1f}s | {c.end:.1f}s | {c.end - c.start:.1f}s "
                f"| {c.description} | {c.subtitle} |"
            )
        lines.append("")
        lines.append("## 안전 확인")
        lines.append("- 실제 렌더링 여부: 안 함 (dry-run)")
        lines.append("- 실제 업로드 여부: 안 함 (09_approval 승인 후 사장님 직접 진행)")
        lines.append("- 저작권 BGM 사용 금지 — 라이선스 확보된 음원만 사용")
        return "\n".join(lines)


# ────────────────────────────────────────
# 대본 → 타임라인 변환 로직
# ────────────────────────────────────────

def _segment_script(script: str) -> List[str]:
    """대본을 문장 단위 컷으로 분할."""
    if not script:
        return []
    # 줄바꿈 우선, 없으면 마침표/물음표/느낌표 기준
    parts = [s.strip() for s in re.split(r"\n+|(?<=[.!?])\s+", script) if s.strip()]
    # 너무 짧은 조각 합치기
    merged: List[str] = []
    for p in parts:
        if merged and len(merged[-1]) < 12:
            merged[-1] += " " + p
        else:
            merged.append(p)
    return merged


def build_timeline(
    script: str,
    *,
    title: str = "고스틱 릴스",
    target_seconds: float = 15.0,
    ratio: str = "9:16",
    bgm_hint: str = "사냥본능 자극 · 80~100 BPM · 라이선스 음원만",
) -> VideoTimeline:
    if not script or not script.strip():
        raise ValueError("대본이 비어 있습니다.")
    segments = _segment_script(script)
    if not segments:
        raise ValueError("문장 단위로 쪼갤 수 없습니다.")
    # 첫 컷은 후킹 2초 고정
    clips: List[VideoClip] = []
    if target_seconds < 4:
        target_seconds = 4
    hook_end = min(2.0, target_seconds * 0.15)
    clips.append(VideoClip(
        start=0.0,
        end=hook_end,
        description="후킹 — 고양이가 화면 응시 / 강한 자막",
        subtitle=segments[0][:30],
        audio="BGM 인 + 임팩트 효과음",
    ))
    remaining = target_seconds - hook_end
    other_segments = segments[1:] or segments  # 후킹용도 활용 가능
    per_clip = max(2.0, remaining / max(1, len(other_segments)))
    t = hook_end
    for seg in other_segments:
        end = min(target_seconds, t + per_clip)
        clips.append(VideoClip(
            start=t,
            end=end,
            description=_describe_for(seg),
            subtitle=seg[:32],
        ))
        t = end
        if t >= target_seconds:
            break
    return VideoTimeline(
        title=title,
        total_seconds=target_seconds,
        ratio=ratio,
        clips=clips,
        bgm_hint=bgm_hint,
        source_script=script,
    )


def _describe_for(segment: str) -> str:
    seg = segment.lower()
    if any(w in seg for w in ("점프", "쫓", "달려", "사냥")):
        return "고양이 점프/추격 슬로우 컷"
    if any(w in seg for w in ("리필", "세트", "옵션")):
        return "상품 리필/세트 클로즈업 + 텍스트 카드"
    if any(w in seg for w in ("후킹", "주목", "보세요", "혹시")):
        return "집사 시점 POV 컷 + 큰 자막"
    if any(w in seg for w in ("리뷰", "후기")):
        return "리뷰 캡처 + 별점 강조"
    return "사용 장면 미디엄 샷 + 자막"


# ────────────────────────────────────────
# Python 편집 스크립트(초안) 생성
# ────────────────────────────────────────

def to_moviepy_script(timeline: VideoTimeline, *, output: str = "out_release.mp4") -> str:
    """타임라인을 MoviePy 자동 편집 스크립트 초안으로 변환.

    사장님이 실제 mp4들을 준비한 뒤 input 파일 이름만 채우면 동작한다.
    이 스크립트는 **자동 실행되지 않는다.** 검토 후 사장님이 직접 실행.
    """
    lines = [
        "# 자동 생성 — 비디오 AI dry-run",
        "# 실행 전 input/output 파일 경로 확인 후 사장님이 직접 실행하세요.",
        "# pip install moviepy",
        "from moviepy.editor import VideoFileClip, concatenate_videoclips, TextClip, CompositeVideoClip, AudioFileClip",
        "",
        "FPS = 30",
        "SIZE = (1080, 1920)  # 9:16",
        "BGM_PATH = 'assets/bgm_licensed.mp3'  # 라이선스 음원만",
        "OUT = " + repr(output),
        "",
        "clips = []",
    ]
    for i, c in enumerate(timeline.clips, 1):
        dur = c.end - c.start
        lines.append(f"# 컷 {i}: {c.description}")
        lines.append(f"src_{i} = VideoFileClip('assets/clip_{i:02d}.mp4').subclip(0, {dur:.2f}).resize(SIZE)")
        lines.append(
            f"txt_{i} = TextClip({c.subtitle!r}, fontsize=64, color='white', "
            f"font='Malgun-Gothic-Bold', stroke_color='black', stroke_width=4)"
            f".set_position(('center', 'bottom')).set_duration({dur:.2f})"
        )
        lines.append(f"clips.append(CompositeVideoClip([src_{i}, txt_{i}]))")
        lines.append("")
    lines.extend([
        "final = concatenate_videoclips(clips, method='compose')",
        "if BGM_PATH:",
        "    bgm = AudioFileClip(BGM_PATH).subclip(0, final.duration).volumex(0.4)",
        "    final = final.set_audio(bgm)",
        "final.write_videofile(OUT, fps=FPS, codec='libx264', audio_codec='aac')",
    ])
    return "\n".join(lines)


def to_ffmpeg_command(timeline: VideoTimeline, *, output: str = "out_release.mp4") -> str:
    """간단한 ffmpeg concat 명령 (입력 파일은 사장님이 준비)."""
    return (
        "# 1) inputs.txt 파일을 만들고:\n"
        "# file 'assets/clip_01.mp4'\n"
        "# file 'assets/clip_02.mp4'\n"
        "# ...\n"
        "ffmpeg -f concat -safe 0 -i inputs.txt -vf "
        '"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920" '
        f"-c:v libx264 -r 30 -pix_fmt yuv420p {output}"
    )


def to_srt(timeline: VideoTimeline) -> str:
    """SRT 자막 초안."""
    def ts(seconds: float) -> str:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = seconds % 60
        return f"{h:02d}:{m:02d}:{s:06.3f}".replace(".", ",")

    out_lines: List[str] = []
    for i, c in enumerate(timeline.clips, 1):
        out_lines.append(str(i))
        out_lines.append(f"{ts(c.start)} --> {ts(c.end)}")
        out_lines.append(c.subtitle)
        out_lines.append("")
    return "\n".join(out_lines)


def build_video_package(
    script: str,
    *,
    title: str = "고스틱 릴스",
    target_seconds: float = 15.0,
) -> tuple[VideoTimeline, str, str, str]:
    """타임라인 + MoviePy 스크립트 + ffmpeg 명령 + SRT 자막 한 번에."""
    tl = build_timeline(script, title=title, target_seconds=target_seconds)
    py = to_moviepy_script(tl)
    ff = to_ffmpeg_command(tl)
    srt = to_srt(tl)
    return tl, py, ff, srt


def write_video_package(
    script: str,
    *,
    title: str = "고스틱 릴스",
    target_seconds: float = 15.0,
    include_premiere: bool = True,
) -> tuple[Path, Path, Path, Path]:
    """모든 산출물을 06_apps/video_briefs/{stamp}/ 폴더에 저장.

    include_premiere=True 면 Premiere Pro 임포트용 FCPXML/.jsx/EDL도 함께 생성.
    """
    tl, py, ff, srt = build_video_package(script, title=title, target_seconds=target_seconds)
    stamp = now_stamp()
    folder = ROOT / "06_apps" / "video_briefs" / stamp
    folder.mkdir(parents=True, exist_ok=True)
    md_path = folder / "timeline.md"
    py_path = folder / "auto_edit_moviepy.py"
    ff_path = folder / "ffmpeg_concat.sh"
    srt_path = folder / "subtitles.srt"
    md_path.write_text(tl.to_markdown(), encoding="utf-8")
    py_path.write_text(py, encoding="utf-8")
    ff_path.write_text(ff, encoding="utf-8")
    srt_path.write_text(srt, encoding="utf-8")

    premiere_lines: list[str] = []
    if include_premiere:
        try:
            from .premiere_controller import write_premiere_package
            seq_name = re.sub(r"[^A-Za-z0-9가-힣_\- ]", "_", title) or "AI_Reels_01"
            pkg = write_premiere_package(tl, sequence_name=seq_name, output_subdir=stamp)
            premiere_lines = [
                "",
                "## Premiere Pro 자동 컨트롤 산출물",
                f"- FCPXML 임포트: `{pkg.fcpxml_path}`",
                f"- ExtendScript (.jsx): `{pkg.jsx_path}`",
                f"- EDL 백업: `{pkg.edl_path}`",
                f"- 가이드: `{pkg.readme_path}`",
            ]
        except Exception as e:
            premiere_lines = [
                "",
                "## Premiere Pro 산출물",
                f"_생성 실패: {e}_",
            ]

    # 08_reports 에 종합 보고서도 한 부
    summary_lines = [
        "# 비디오 AI 산출물 보고서",
        "",
        f"- 제목: {title}",
        f"- 길이: {target_seconds:.1f}초 · 비율 {tl.ratio}",
        f"- 컷 개수: {len(tl.clips)}",
        "",
        "## 입력 대본 (앞 200자)",
        "",
        "```",
        script[:200] + ("…" if len(script) > 200 else ""),
        "```",
        "",
        "## 산출물 위치",
        "",
        f"- 타임라인: `{md_path}`",
        f"- Python 자동 편집(MoviePy): `{py_path}`",
        f"- ffmpeg 명령: `{ff_path}`",
        f"- SRT 자막: `{srt_path}`",
    ]
    summary_lines.extend(premiere_lines)
    summary_lines.extend([
        "",
        "## 안전 확인",
        "- 실제 영상 렌더링 안 함 (입력 mp4 파일도 준비 안 됨)",
        "- 실제 업로드 안 함 — 09_approval 승인 후 사장님이 직접 실행",
        "- Premiere 자동 실행 — `--launch` 옵션 + 사장님 승인 시만",
        "- BGM은 라이선스 확보 음원만 사용",
    ])
    summary_path = write_report(
        ROOT / "08_reports",
        "video_brief",
        "\n".join(summary_lines),
    )
    return md_path, py_path, srt_path, summary_path


__all__ = [
    "VideoClip",
    "VideoTimeline",
    "build_timeline",
    "to_moviepy_script",
    "to_ffmpeg_command",
    "to_srt",
    "build_video_package",
    "write_video_package",
]
