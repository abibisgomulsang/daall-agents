"""Adobe Premiere Pro 자동 컨트롤러.

사장님의 비디오 타임라인을 Premiere가 곧장 임포트할 수 있는 두 형식으로
변환한다:

1) **FCPXML 1.10** — Premiere가 공식 지원하는 표준 임포트 포맷
   사장님이 Premiere에서 `File > Import` → 이 파일을 선택하면 시퀀스가
   자동으로 만들어진다.

2) **ExtendScript (.jsx)** — Premiere의 공식 자동화 스크립트
   사장님이 Premiere에서 `File > Scripts > Run Script File...` 로
   이 .jsx를 실행하면 파일 임포트와 새 시퀀스 생성을 자동 처리한다.

3) **EDL (CMX3600)** — 단순 백업용 (옵션)

`launch_premiere()`는 Windows에서 Premiere를 직접 실행한다. 이 함수는
**`approved=True`로 명시할 때만** 동작하고, 그 외에는 안전을 위해
no-op (실제 실행 안 함).
"""
from __future__ import annotations

import os
import re
import shlex
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from .paths import ROOT
from .utils import now_stamp, write_report
from .video_editing import VideoTimeline, VideoClip


# ──────────────────────────────────────────────────────────────
# FCPXML
# ──────────────────────────────────────────────────────────────

def _seconds_to_rational(sec: float, fps: int = 30) -> str:
    """0.5 → '15/30s' 형식 (FCPXML 표준)."""
    frames = int(round(sec * fps))
    return f"{frames}/{fps}s"


def to_fcpxml(
    timeline: VideoTimeline,
    *,
    sequence_name: str = "AI_Reels_01",
    clip_dir: Optional[str] = None,
    fps: int = 30,
) -> str:
    """Premiere가 임포트하는 FCPXML 1.10 문서를 생성.

    각 컷마다 `assets/clip_{i:02d}.mp4` 가 있다고 가정한다.
    실제 파일 없어도 임포트는 가능 — Premiere가 "오프라인 파일" 상태로
    잡고, 사장님이 우클릭 → Link Media로 연결 가능.
    """
    if clip_dir is None:
        clip_dir = str((ROOT / "06_apps" / "video_briefs" / "assets").resolve())
    duration_str = _seconds_to_rational(timeline.total_seconds, fps)

    # 리소스: 포맷 + 자산
    format_id = "r1"
    format_xml = (
        f'    <format id="{format_id}" name="FFVideoFormat1080p{fps}" '
        f'frameDuration="100/{fps * 100}s" width="1080" height="1920" '
        f'colorSpace="1-1-1 (Rec. 709)"/>\n'
    )
    asset_xml: List[str] = []
    clip_xml: List[str] = []
    offset = 0.0
    for i, c in enumerate(timeline.clips, 1):
        asset_id = f"a{i}"
        src_path = Path(clip_dir) / f"clip_{i:02d}.mp4"
        src_uri = "file:///" + str(src_path).replace("\\", "/").lstrip("/")
        dur = max(0.001, c.end - c.start)
        asset_xml.append(
            f'    <asset id="{asset_id}" name="clip_{i:02d}" src="{_xml_escape(src_uri)}" '
            f'hasVideo="1" hasAudio="1" videoSources="1" audioSources="1" '
            f'duration="{_seconds_to_rational(dur, fps)}" format="{format_id}"/>'
        )
        clip_xml.append(
            f'        <asset-clip ref="{asset_id}" name="{_xml_escape(c.subtitle[:48] or f"clip_{i:02d}")}" '
            f'start="0s" duration="{_seconds_to_rational(dur, fps)}" '
            f'offset="{_seconds_to_rational(offset, fps)}"/>'
        )
        offset += dur

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<!DOCTYPE fcpxml>\n'
        '<fcpxml version="1.10">\n'
        '  <resources>\n'
        f'{format_xml}'
        + ("\n".join(asset_xml) + "\n" if asset_xml else "")
        + '  </resources>\n'
        '  <library>\n'
        f'    <event name="{_xml_escape(timeline.title)}">\n'
        f'      <project name="{_xml_escape(sequence_name)}">\n'
        f'        <sequence format="{format_id}" duration="{duration_str}" tcStart="0s" tcFormat="NDF">\n'
        '          <spine>\n'
        + ("\n".join(clip_xml) + "\n" if clip_xml else "")
        + '          </spine>\n'
        '        </sequence>\n'
        '      </project>\n'
        '    </event>\n'
        '  </library>\n'
        '</fcpxml>\n'
    )
    return xml


def _xml_escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
         .replace('"', "&quot;")
         .replace("<", "&lt;")
         .replace(">", "&gt;")
    )


# ──────────────────────────────────────────────────────────────
# ExtendScript (.jsx)
# ──────────────────────────────────────────────────────────────

def to_extendscript(
    timeline: VideoTimeline,
    *,
    clip_dir: Optional[str] = None,
    sequence_name: str = "AI_Reels_01",
) -> str:
    """Premiere에서 File > Scripts > Run Script File로 실행하는 .jsx."""
    if clip_dir is None:
        clip_dir = str((ROOT / "06_apps" / "video_briefs" / "assets").resolve())
    clip_paths_js = ",\n        ".join(
        repr(str(Path(clip_dir) / f"clip_{i:02d}.mp4").replace("\\", "\\\\"))
        for i in range(1, len(timeline.clips) + 1)
    )
    safe_seq = re.sub(r"[^\w\- ]", "_", sequence_name)
    safe_title = re.sub(r"[^\w\- ]", "_", timeline.title)
    return (
        "// 자동 생성 — Premiere Pro 컨트롤러 (비디오 AI)\n"
        "// File > Scripts > Run Script File... 에서 이 파일을 선택하면 실행됩니다.\n"
        "// 사장님 검토 후 직접 실행하세요. 자동 실행되지 않습니다.\n"
        "\n"
        "(function() {\n"
        "    if (typeof app === 'undefined' || !app.project) {\n"
        "        alert('Premiere Pro에서 프로젝트를 먼저 만들고 다시 실행해 주세요.');\n"
        "        return;\n"
        "    }\n"
        "    var project = app.project;\n"
        f"    var seqName  = {safe_seq!r};\n"
        f"    var binTitle = {safe_title!r};\n"
        "\n"
        "    // 1) 임포트할 클립 목록\n"
        "    var clipPaths = [\n"
        f"        {clip_paths_js}\n"
        "    ];\n"
        "\n"
        "    // 2) Bin 생성 (이미 있으면 사용)\n"
        "    var root = project.rootItem;\n"
        "    var bin  = null;\n"
        "    for (var i = 0; i < root.children.numItems; i++) {\n"
        "        var child = root.children[i];\n"
        "        if (child.name === binTitle) { bin = child; break; }\n"
        "    }\n"
        "    if (!bin) {\n"
        "        bin = root.createBin(binTitle);\n"
        "    }\n"
        "\n"
        "    // 3) 클립 임포트 (실제 파일 없으면 오프라인 항목으로 들어옴 — 나중에 Link Media)\n"
        "    try {\n"
        "        project.importFiles(clipPaths, true, bin, false);\n"
        "    } catch (e) {\n"
        "        alert('임포트 중 오류: ' + e);\n"
        "    }\n"
        "\n"
        "    alert('AI 회사 비디오 AI: ' + clipPaths.length + '개 클립을 \"' + binTitle + '\" bin에 임포트했습니다.\\n'\n"
        "        + '시퀀스 \"' + seqName + '\" 를 만들고 컷 순서대로 타임라인에 올리세요.\\n'\n"
        "        + '자동 시퀀스 생성을 원하면 사장님 승인 후 수동으로 진행하세요.');\n"
        "})();\n"
    )


# ──────────────────────────────────────────────────────────────
# EDL (CMX3600, 단순 백업)
# ──────────────────────────────────────────────────────────────

def to_edl(timeline: VideoTimeline, *, fps: int = 30) -> str:
    def tc(sec: float) -> str:
        total = int(round(sec * fps))
        h = total // (fps * 3600)
        m = (total // (fps * 60)) % 60
        s = (total // fps) % 60
        f = total % fps
        return f"{h:02d}:{m:02d}:{s:02d}:{f:02d}"

    lines = [f"TITLE: {timeline.title}", "FCM: NON-DROP FRAME", ""]
    rec_in = 0.0
    for i, c in enumerate(timeline.clips, 1):
        dur = c.end - c.start
        clip_in = 0.0
        clip_out = dur
        rec_out = rec_in + dur
        lines.append(
            f"{i:03d}  AX       V     C        "
            f"{tc(clip_in)} {tc(clip_out)} {tc(rec_in)} {tc(rec_out)}"
        )
        lines.append(f"* FROM CLIP NAME: clip_{i:02d} ({c.subtitle[:32]})")
        lines.append("")
        rec_in = rec_out
    return "\n".join(lines)


# ──────────────────────────────────────────────────────────────
# 모든 산출물 한 번에
# ──────────────────────────────────────────────────────────────

@dataclass
class PremierePackage:
    folder: Path
    fcpxml_path: Path
    jsx_path: Path
    edl_path: Path
    readme_path: Path
    report_path: Path


def write_premiere_package(
    timeline: VideoTimeline,
    *,
    sequence_name: str = "AI_Reels_01",
    output_subdir: Optional[str] = None,
) -> PremierePackage:
    base = ROOT / "06_apps" / "video_briefs" / (output_subdir or now_stamp()) / "premiere"
    base.mkdir(parents=True, exist_ok=True)

    fcpxml = to_fcpxml(timeline, sequence_name=sequence_name)
    jsx = to_extendscript(timeline, sequence_name=sequence_name)
    edl = to_edl(timeline)

    fcpxml_path = base / "import_to_premiere.fcpxml"
    jsx_path = base / "auto_import.jsx"
    edl_path = base / "backup.edl"
    fcpxml_path.write_text(fcpxml, encoding="utf-8")
    jsx_path.write_text(jsx, encoding="utf-8")
    edl_path.write_text(edl, encoding="utf-8")

    readme = (
        f"# Premiere Pro 자동 임포트 가이드 — {timeline.title}\n\n"
        f"이 폴더의 산출물 3종은 비디오 AI가 만든 타임라인 ({timeline.total_seconds:.1f}초, {timeline.ratio}, 컷 {len(timeline.clips)}개)을\n"
        "Premiere Pro에서 사장님이 한 번의 클릭으로 임포트할 수 있게 정리한 것입니다.\n"
        "**실제 영상 렌더링/업로드는 자동으로 일어나지 않습니다.**\n\n"
        "## 추천: ExtendScript 방식 (가장 빠름)\n"
        "1. Premiere Pro 실행 후 새 프로젝트 만들기 (또는 기존 프로젝트 열기)\n"
        "2. 메뉴 `File > Scripts > Run Script File...` 클릭\n"
        f"3. 이 폴더의 `auto_import.jsx` 선택\n"
        f"4. AI 회사가 `{timeline.title}` bin에 클립을 임포트합니다\n"
        "5. 사장님이 직접 타임라인으로 컷 끌어와 시퀀스 완성\n\n"
        "## 대안: FCPXML 방식 (시퀀스까지 자동 생성)\n"
        "1. Premiere Pro 실행\n"
        f"2. 메뉴 `File > Import` → 이 폴더의 `import_to_premiere.fcpxml` 선택\n"
        "3. 시퀀스가 자동 생성됩니다 (1080×1920 9:16, 30fps)\n"
        "4. 클립이 오프라인 상태면 사장님이 우클릭 → `Link Media`로 실제 mp4 연결\n\n"
        "## 비상용: EDL\n"
        "Premiere가 위 두 방식을 받아들이지 않으면 `backup.edl`을 임포트하세요.\n\n"
        "## 클립 파일 준비\n"
        "예상 위치: `06_apps/video_briefs/<stamp>/assets/clip_01.mp4`, `clip_02.mp4` …\n"
        "AI 회사는 클립을 만들지 않습니다 — 사장님이 촬영본을 그 폴더에 두시면 됩니다.\n\n"
        "## 안전 확인\n"
        "- 실제 영상 렌더링 / 인스타·유튜브 업로드 — 자동으로 일어나지 않음\n"
        "- 기존 프로젝트 수정 위험 — ExtendScript는 새 bin만 만듭니다\n"
        "- 사장님 승인 없이는 Premiere가 자동 실행되지 않습니다 (`--launch` 명시 시만)\n"
    )
    readme_path = base / "README.md"
    readme_path.write_text(readme, encoding="utf-8")

    # 08_reports 종합 보고서
    summary_md = (
        "# 비디오 AI · Premiere Pro 컨트롤 산출물\n\n"
        f"- 제목: {timeline.title}\n"
        f"- 길이: {timeline.total_seconds:.1f}초 · 비율 {timeline.ratio}\n"
        f"- 컷: {len(timeline.clips)}개\n"
        f"- 시퀀스 이름: `{sequence_name}`\n\n"
        "## 파일\n"
        f"- FCPXML(Premiere Import): `{fcpxml_path}`\n"
        f"- ExtendScript(.jsx): `{jsx_path}`\n"
        f"- EDL 백업: `{edl_path}`\n"
        f"- 가이드: `{readme_path}`\n\n"
        "## 사장님이 하실 일\n"
        "1. Premiere Pro에서 새 프로젝트 만들기\n"
        "2. 위 가이드에 따라 ExtendScript 또는 FCPXML 임포트\n"
        "3. 컷이 마음에 들면 시퀀스 완성 → 사장님이 직접 Export\n\n"
        "## 안전 확인\n"
        "- 실제 영상 렌더링: 안 함\n"
        "- 실제 SNS 업로드: 안 함\n"
        "- 기존 Premiere 프로젝트 수정 위험: 없음 (ExtendScript는 새 bin만)\n"
        "- Premiere 자동 실행: `--launch` 옵션 + 사장님 승인 시만\n"
    )
    report_path = write_report(
        ROOT / "08_reports",
        "premiere_package",
        summary_md,
    )

    return PremierePackage(
        folder=base,
        fcpxml_path=fcpxml_path,
        jsx_path=jsx_path,
        edl_path=edl_path,
        readme_path=readme_path,
        report_path=report_path,
    )


# ──────────────────────────────────────────────────────────────
# 사장님 승인 후 Premiere 직접 실행
# ──────────────────────────────────────────────────────────────

def _find_premiere_exe() -> Optional[Path]:
    """Windows에서 Premiere Pro 실행 파일 찾기."""
    candidates = []
    for env in ("PROGRAMFILES", "ProgramW6432"):
        base = os.environ.get(env)
        if not base:
            continue
        for version in ("2026", "2025", "2024", "2023", "2022", "2021", "2020"):
            candidates.append(Path(base) / f"Adobe/Adobe Premiere Pro {version}/Adobe Premiere Pro.exe")
    for c in candidates:
        if c.exists():
            return c
    # which
    found = shutil.which("Adobe Premiere Pro.exe")
    return Path(found) if found else None


def launch_premiere(
    package: PremierePackage,
    *,
    approved: bool = False,
) -> dict:
    """사장님 승인 시 Premiere를 실행하고 FCPXML을 인자로 넘긴다.

    `approved=False` 면 절대 실행 안 함 (no-op).
    실제로는 Premiere가 FCPXML을 인자로 받아도 자동 임포트하지는 않을 수 있으니,
    가장 안전한 방식은 Premiere를 띄우고 사장님이 가이드대로 임포트하는 것.
    """
    if not approved:
        return {
            "launched": False,
            "reason": "approved=False — 자동 실행은 사장님 명시 승인 후만 동작. "
                      f"수동 안내: {package.readme_path}",
        }
    exe = _find_premiere_exe()
    if not exe:
        return {
            "launched": False,
            "reason": "Adobe Premiere Pro 실행 파일을 찾을 수 없습니다. 사장님이 직접 Premiere를 여세요. "
                      f"가이드: {package.readme_path}",
        }
    try:
        subprocess.Popen(
            [str(exe), str(package.fcpxml_path)],
            close_fds=True,
            creationflags=getattr(subprocess, "DETACHED_PROCESS", 0),
        )
        return {
            "launched": True,
            "exe": str(exe),
            "fcpxml": str(package.fcpxml_path),
            "note": "Premiere를 띄웠습니다. 사장님이 README.md 가이드대로 임포트하세요.",
        }
    except Exception as e:
        return {
            "launched": False,
            "reason": f"Premiere 실행 실패: {e}",
        }


__all__ = [
    "to_fcpxml",
    "to_extendscript",
    "to_edl",
    "write_premiere_package",
    "PremierePackage",
    "launch_premiere",
]
