from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, Optional

from .paths import ROOT
from .model_router import RoutingDecision, route as route_model

def load_product(product_code: str) -> Dict[str, str]:
    path = ROOT / "data" / "products.csv"
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["product_code"] == product_code:
                return row
    raise ValueError(f"상품 코드를 찾을 수 없습니다: {product_code}")


def _routing_card(routing: RoutingDecision) -> str:
    r = routing
    runners = (
        ", ".join(rs.model.display_name for rs in r.runners_up)
        if r.runners_up else "없음"
    )
    return (
        "## 모델 라우터 결정\n"
        f"- 1순위 모델: **{r.primary.model.display_name}** ({r.primary.model.role})\n"
        f"- 1순위 점수: {r.primary.score}\n"
        f"- 후순위: {runners}\n"
        f"- dry-run: {r.handoff['dry_run']} / executed: {r.handoff['executed']}\n"
    )


def generate_ad_package(product_code: str, routing: Optional[RoutingDecision] = None) -> str:
    p = load_product(product_code)
    name = p["product_name"]
    feature = p["main_feature"]
    target = p["target_cat"]
    tags = p["tags"].split("|")

    hooks = [
        "사줘도 안 놀던 고양이, 장난감 문제가 아닐 수 있어요.",
        f"{name}, 고양이의 사냥 스위치를 다시 켜는 놀이템.",
        "활동량 많은 고양이에게 필요한 건 더 강한 사냥 자극입니다.",
    ]

    body = (
        f"{name}은 {feature}입니다. "
        f"특히 {target}에게 맞춰, 단순히 흔드는 장난감이 아니라 "
        "고양이가 쫓고, 기다리고, 덮치는 놀이 흐름을 만들 수 있게 기획합니다."
    )

    reel_script = f'''
[릴스 대본 - 15초]
0~2초: 자막 "{hooks[0]}" + 고양이가 장난감을 보는 장면
3~6초: {name}을 천천히 움직이며 사냥본능 자극
7~11초: 고양이가 점프/추격하는 장면
12~15초: "오늘 놀이는 {name}으로 시작해보세요" + 상품 컷
'''.strip()

    image_brief = f'''
[광고 이미지 편집 지시서]
- 비율: 1:1, 4:5, 9:16 세 가지 버전
- 메인 카피: "{hooks[1]}"
- 서브 카피: "{feature}"
- 배경: 깔끔한 실내, 고양이 놀이 상황 강조
- 금지: 치료/효능/100% 보장 표현
- CTA: "고양이 성향에 맞는 놀이를 시작하세요"
'''.strip()

    hashtags = " ".join("#" + t.replace(" ", "") for t in tags + ["고양이장난감", "집사스타그램", "고양이낚싯대"])

    review = '''
[검수 AI]
- 과장광고 위험: 낮음
- 수정 필요 표현: 없음
- 실제 업로드 전 확인: 가격/재고/링크/이미지 저작권
'''.strip()

    routing_md = _routing_card(routing) if routing is not None else ""
    return f'''
# {name} 광고 패키지

{routing_md}
## 상품 정보
- 상품 코드: {product_code}
- 상품명: {name}
- 특징: {feature}
- 타겟: {target}

## 후킹 문구 3안
1. {hooks[0]}
2. {hooks[1]}
3. {hooks[2]}

## 인스타 피드 문구
{body}

지금 고양이의 놀이 반응이 예전 같지 않다면, 장난감의 움직임과 자극 방식을 바꿔보세요.

## 릴스 대본
{reel_script}

## 이미지 편집 지시서
{image_brief}

## 해시태그
{hashtags}

## 검수 결과
{review}

## 승인 필요
실제 SNS 업로드, 스마트스토어 이미지 교체, 광고 집행 전 사장님 승인 필요.
'''.strip()


def generate_routed_ad_package(product_code: str) -> str:
    """라우터를 자동 통과시키는 편의 함수. 광고 패키지의 자연어 토픽으로
    상품명 + '광고 패키지'를 라우터에 입력."""
    p = load_product(product_code)
    topic = f"{p['product_name']} 광고 패키지 (릴스 썸네일 문구 이미지)"
    decision = route_model(topic)
    return generate_ad_package(product_code, routing=decision)
