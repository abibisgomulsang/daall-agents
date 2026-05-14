from __future__ import annotations

import json
from pathlib import Path

from .paths import ROOT
from .utils import now_stamp, write_report

REQUIRED_ASSETS = [
    {"slot": "feed_image_4_5", "ratio": "4:5", "required": True},
    {"slot": "reels_cover_9_16", "ratio": "9:16", "required": True},
    {"slot": "story_image_9_16", "ratio": "9:16", "required": False},
]


def _existing_share_cards(product_code: str) -> list[str]:
    folder = ROOT / "03_images" / "share_cards"
    if not folder.exists():
        return []
    return [str(path) for path in sorted(folder.glob(f"*{product_code}*.png"), key=lambda item: item.stat().st_mtime, reverse=True)]


def build_instagram_asset_manifest(product_code: str) -> tuple[str, dict[str, object]]:
    existing_assets = _existing_share_cards(product_code)
    manifest = {
        "product_code": product_code,
        "actual_upload": False,
        "actual_post": False,
        "customer_message": False,
        "required_assets": REQUIRED_ASSETS,
        "existing_local_assets": existing_assets,
        "missing_required_slots": [
            item["slot"]
            for item in REQUIRED_ASSETS
            if item["required"] and not existing_assets
        ],
        "caption_draft": "사줘도 안 놀던 고양이, 움직임을 바꿔보세요. #고양이장난감 #고스틱",
        "preflight": [
            "가격 확인",
            "재고 확인",
            "스마트스토어 링크 확인",
            "이미지 저작권 확인",
            "과장 표현 없음 확인",
            "사장님 승인 파일 확인",
        ],
    }

    lines = [
        f"# 인스타 업로드 전 자산 매니페스트: {product_code}",
        "",
        "- 실제 업로드 여부: 업로드 안 함",
        "- 실제 게시 여부: 게시 안 함",
        "- 고객 메시지 발송 여부: 발송 안 함",
        "",
        "## 필요한 자산 슬롯",
        "",
        "| 슬롯 | 비율 | 필수 |",
        "| --- | --- | --- |",
    ]
    for item in REQUIRED_ASSETS:
        lines.append(f"| {item['slot']} | {item['ratio']} | {'예' if item['required'] else '아니오'} |")

    lines.extend(["", "## 로컬 발견 자산", ""])
    if existing_assets:
        lines.extend(f"- {path}" for path in existing_assets[:8])
    else:
        lines.append("- 발견된 로컬 PNG 없음")

    lines.extend(
        [
            "",
            "## 캡션 초안",
            "",
            manifest["caption_draft"],
            "",
            "## 업로드 전 점검",
            "",
        ]
    )
    lines.extend(f"- {item}" for item in manifest["preflight"])
    lines.extend(
        [
            "",
            "## 안전 메모",
            "",
            "- 이 파일은 업로드 준비 목록이다.",
            "- 실제 인스타그램 업로드/게시/예약은 사장님 승인 전까지 금지다.",
        ]
    )
    return "\n".join(lines), manifest


def write_instagram_asset_manifest(product_code: str) -> tuple[Path, Path]:
    report, manifest = build_instagram_asset_manifest(product_code)
    report_path = write_report(ROOT / "08_reports", f"instagram_asset_manifest_{product_code}", report)
    folder = ROOT / "02_marketing" / "instagram_dry_run"
    folder.mkdir(parents=True, exist_ok=True)
    json_path = folder / f"instagram_asset_manifest_{product_code}_{now_stamp()}.json"
    json_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return report_path, json_path
