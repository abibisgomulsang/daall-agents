from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .paths import ROOT
from .utils import now_stamp, write_report

RESULT_COPY = {
    "GOSTICK01": {
        "title": "고스틱 추천",
        "export_title": "GOSTICK PICK",
        "subtitle": "추격과 점프 놀이에 반응하는 고양이에게",
        "export_subtitle": "For cats that love chase and jump play",
        "accent": "#2f7d5c",
        "warm": "#e9b44c",
    },
    "PLAGO01": {
        "title": "플라고스틱 추천",
        "export_title": "PLAGO PICK",
        "subtitle": "처음 시작하거나 조심스러운 고양이에게",
        "export_subtitle": "For cautious cats or first toy tests",
        "accent": "#154c5b",
        "warm": "#d96b57",
    },
    "REFILL01": {
        "title": "고스틱 리필 추천",
        "export_title": "REFILL PICK",
        "subtitle": "익숙한 놀이에 새 움직임을 더하고 싶을 때",
        "export_subtitle": "For refreshing a familiar play routine",
        "accent": "#704b33",
        "warm": "#5f8f75",
    },
}


def build_share_image_design(result_code: str) -> tuple[str, dict[str, object]]:
    if result_code not in RESULT_COPY:
        allowed = ", ".join(sorted(RESULT_COPY))
        raise ValueError(f"result_code는 다음 중 하나여야 합니다: {allowed}")

    copy = RESULT_COPY[result_code]
    spec = {
        "result_code": result_code,
        "canvas": {"width": 1080, "height": 1920, "ratio": "9:16"},
        "style": "clean, warm, cat-owner friendly",
        "layers": [
            {"type": "background", "color": "#f3f2ed"},
            {"type": "headline", "text": copy["title"], "color": copy["accent"], "top": 180},
            {"type": "subtitle", "text": copy["subtitle"], "color": "#20242a", "top": 290},
            {"type": "result_card", "text": "우리 고양이 놀이 성향 결과", "top": 520},
            {"type": "cta", "text": "고양이 성향에 맞는 놀이를 시작하세요", "top": 1640},
        ],
        "safe_notes": [
            "실제 SNS 업로드 전 사장님 승인 필요",
            "상품 가격, 재고, 링크는 업로드 직전 확인",
            "치료/효능/100% 보장 표현 금지",
        ],
    }
    md = [
        f"# 추천 결과 공유 이미지 설계: {copy['title']}",
        "",
        "- 실제 이미지 생성 여부: 생성 안 함",
        "- 실제 SNS 업로드 여부: 업로드 안 함",
        "- 비율: 9:16",
        "- 캔버스: 1080x1920",
        "",
        "## 화면 구성",
        "",
    ]
    for layer in spec["layers"]:
        md.append(f"- {layer['type']}: {layer['text'] if 'text' in layer else layer.get('color', '')}")
    md.extend(
        [
            "",
            "## 안전 메모",
            "",
        ]
    )
    md.extend(f"- {note}" for note in spec["safe_notes"])
    return "\n".join(md), spec


def write_share_image_design(result_code: str) -> tuple[Path, Path]:
    md, spec = build_share_image_design(result_code)
    report_path = write_report(ROOT / "08_reports", f"share_image_design_{result_code}", md)
    folder = ROOT / "03_images" / "share_cards"
    folder.mkdir(parents=True, exist_ok=True)
    json_path = folder / f"share_image_design_{result_code}_{now_stamp()}.json"
    json_path.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
    return report_path, json_path


def _font(size: int) -> ImageFont.ImageFont:
    for name in ("malgun.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def _wrap(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> list[str]:
    lines: list[str] = []
    current = ""
    for word in text.split():
        next_text = f"{current} {word}".strip()
        if draw.textlength(next_text, font=font) <= max_width:
            current = next_text
            continue
        if current:
            lines.append(current)
        current = word
    if current:
        lines.append(current)
    return lines


def build_share_image_png(
    result_code: str,
    output_dir: Path | None = None,
    reports_dir: Path | None = None,
) -> tuple[Path, Path]:
    if result_code not in RESULT_COPY:
        allowed = ", ".join(sorted(RESULT_COPY))
        raise ValueError(f"result_code는 다음 중 하나여야 합니다: {allowed}")

    copy = RESULT_COPY[result_code]
    output_dir = output_dir or ROOT / "03_images" / "share_cards"
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = now_stamp()
    png_path = output_dir / f"share_card_{result_code}_{stamp}.png"

    image = Image.new("RGB", (1080, 1920), "#f3f2ed")
    draw = ImageDraw.Draw(image)
    accent = copy["accent"]
    warm = copy["warm"]

    draw.rectangle((0, 0, 1080, 44), fill=accent)
    draw.rectangle((0, 44, 1080, 62), fill=warm)
    draw.rounded_rectangle((72, 102, 1008, 1818), radius=42, fill="#fbfaf6", outline="#d9e0dc", width=3)

    brand_font = _font(44)
    title_font = _font(94)
    body_font = _font(42)
    small_font = _font(34)

    draw.text((118, 168), "ABIBI CAT PLAY", fill="#65727b", font=brand_font)
    draw.text((118, 294), str(copy["export_title"]), fill=accent, font=title_font)

    y = 430
    for line in _wrap(draw, str(copy["export_subtitle"]), body_font, 800):
        draw.text((118, y), line, fill="#20242a", font=body_font)
        y += 58

    draw.line((180, 820, 900, 610), fill=accent, width=24)
    for index, x in enumerate((340, 450, 560, 670, 780)):
        offset = 0 if index % 2 == 0 else 34
        draw.rounded_rectangle((x - 52, 600 + offset, x + 52, 656 + offset), radius=24, fill=warm)
    draw.rounded_rectangle((426, 790, 654, 880), radius=36, fill=accent)

    draw.rounded_rectangle((118, 1016, 962, 1490), radius=34, fill="#ffffff", outline="#d9e0dc", width=2)
    draw.text((170, 1090), "PLAY RESULT CARD", fill="#65727b", font=small_font)
    draw.text((170, 1172), result_code, fill=accent, font=title_font)
    tips = [
        "Start with short sessions",
        "Mix hiding and chase movements",
        "Let the cat catch the toy at the end",
    ]
    for index, tip in enumerate(tips):
        yy = 1300 + index * 58
        draw.ellipse((172, yy + 10, 194, yy + 32), fill=warm)
        draw.text((218, yy), tip, fill="#303840", font=small_font)

    draw.text((118, 1694), "Dry-run local export only", fill="#65727b", font=small_font)
    draw.text((118, 1748), "No SNS upload. No external API call.", fill="#65727b", font=small_font)
    image.save(png_path, format="PNG")

    report = "\n".join(
        [
            f"# 공유 이미지 PNG export dry-run: {result_code}",
            "",
            f"- PNG 저장: {png_path}",
            "- 실제 SNS 업로드 여부: 업로드 안 함",
            "- 외부 API 호출 여부: 호출 안 함",
            "- 결제/고객 메시지/광고 변경 여부: 실행 안 함",
            "",
            "## 다음 승인 필요 항목",
            "",
            "- 이 이미지를 SNS에 실제 업로드하려면 사장님 승인 필요",
            "- 스마트스토어 상세페이지나 광고 소재에 반영하려면 별도 승인 필요",
        ]
    )
    report_path = write_report(reports_dir or ROOT / "08_reports", f"share_image_png_export_{result_code}", report)
    return png_path, report_path
