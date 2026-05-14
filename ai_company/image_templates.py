from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from .marketing import load_product
from .model_router import RoutingDecision, route as route_model
from .paths import ROOT
from .utils import now_stamp, write_report


def build_image_templates(
    product_code: str, routing: Optional[RoutingDecision] = None
) -> tuple[str, dict[str, object]]:
    product = load_product(product_code)
    name = product["product_name"]
    feature = product["main_feature"]
    target = product["target_cat"]

    templates = {
        "product_code": product_code,
        "product_name": name,
        "versions": [
            {
                "name": "square_feed",
                "ratio": "1:1",
                "canvas": "1080x1080",
                "main_copy": f"{name}, 사냥 놀이를 다시 켜는 시간",
                "visual": "밝은 실내에서 고양이가 장난감을 바라보는 장면",
                "safe_note": "효능, 치료, 100% 보장 표현 금지",
            },
            {
                "name": "portrait_feed",
                "ratio": "4:5",
                "canvas": "1080x1350",
                "main_copy": "사줘도 안 놀던 고양이, 움직임을 바꿔보세요",
                "visual": "상단에 후킹 자막, 중앙에 놀이 장면, 하단에 상품 컷",
                "safe_note": "가격/재고/배송 문구는 업로드 전 확인",
            },
            {
                "name": "reels_cover",
                "ratio": "9:16",
                "canvas": "1080x1920",
                "main_copy": "첫 2초에 멈추게 만드는 고양이 놀이",
                "visual": "고양이가 점프하거나 집중하는 순간을 크게 배치",
                "safe_note": "저작권 확인된 이미지 또는 직접 촬영 이미지 사용",
            },
        ],
    }

    md_lines = [
        f"# {name} 이미지 광고 템플릿",
        "",
    ]
    if routing is not None:
        r = routing
        runners = (
            ", ".join(rs.model.display_name for rs in r.runners_up)
            if r.runners_up else "없음"
        )
        md_lines.extend([
            "## 모델 라우터 결정",
            "",
            f"- 1순위 모델: **{r.primary.model.display_name}** ({r.primary.model.role})",
            f"- 1순위 점수: {r.primary.score}",
            f"- 후순위: {runners}",
            f"- dry-run: {r.handoff['dry_run']} / executed: {r.handoff['executed']}",
            "",
        ])
        templates["routing"] = {
            "primary_key": r.primary.model.key,
            "primary_name": r.primary.model.display_name,
            "primary_role": r.primary.model.role,
            "score": r.primary.score,
            "runners_up": [rs.model.key for rs in r.runners_up],
        }
    md_lines.extend([
        "## 상품 기준",
        "",
        f"- 상품 코드: {product_code}",
        f"- 상품명: {name}",
        f"- 특징: {feature}",
        f"- 타겟: {target}",
        "",
        "## 템플릿",
        "",
    ])
    for item in templates["versions"]:
        md_lines.extend(
            [
                f"### {item['name']}",
                "",
                f"- 비율: {item['ratio']}",
                f"- 캔버스: {item['canvas']}",
                f"- 메인 카피: {item['main_copy']}",
                f"- 비주얼: {item['visual']}",
                f"- 안전 메모: {item['safe_note']}",
                "",
            ]
        )
    md_lines.extend(
        [
            "## 공통 검수",
            "",
            "- 치료/효능/100% 보장 표현 금지",
            "- 실제 업로드 전 가격, 재고, 링크, 이미지 저작권 확인",
            "- 스마트스토어/SNS/광고 실제 반영은 사장님 승인 후 진행",
        ]
    )
    return "\n".join(md_lines), templates


def write_image_templates(
    product_code: str, with_router: bool = False
) -> tuple[Path, Path]:
    routing = None
    if with_router:
        product = load_product(product_code)
        topic = f"{product['product_name']} 광고 이미지 썸네일 디자인 비주얼"
        routing = route_model(topic)
    md, data = build_image_templates(product_code, routing=routing)
    report_path = write_report(ROOT / "08_reports", f"image_templates_{product_code}", md)

    folder = ROOT / "03_images" / "templates"
    folder.mkdir(parents=True, exist_ok=True)
    json_path = folder / f"image_templates_{product_code}_{now_stamp()}.json"
    json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return report_path, json_path
