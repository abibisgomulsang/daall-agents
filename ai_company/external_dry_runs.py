from __future__ import annotations

import csv
import json
from pathlib import Path

from .approval import format_approval_request
from .paths import ROOT
from .utils import now_stamp, write_report


def _write_json(folder: Path, prefix: str, payload: dict[str, object]) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{prefix}_{now_stamp()}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def build_smartstore_fetch_dry_run() -> tuple[str, dict[str, object]]:
    payload = {
        "source": "smartstore_dry_run",
        "dry_run": True,
        "actual_login": False,
        "actual_api_call": False,
        "products": [
            {"product_code": "GOSTICK01", "product_name": "고스틱", "price": 12000, "stock": None, "status": "unknown"},
            {"product_code": "PLAGO01", "product_name": "플라고스틱", "price": 7000, "stock": None, "status": "unknown"},
            {"product_code": "REFILL01", "product_name": "고스틱 리필", "price": 2900, "stock": None, "status": "unknown"},
        ],
        "blocked_actions": ["login", "product_update", "price_update", "stock_update"],
    }
    lines = [
        "# 스마트스토어 상품 데이터 가져오기 Dry-run",
        "",
        "- 실제 로그인 여부: 로그인 안 함",
        "- 실제 API 호출 여부: 호출 안 함",
        "- 상품 수정 여부: 수정 안 함",
        "",
        "## 로컬 기준 상품",
        "",
        "| 상품 코드 | 상품명 | 가격 | 재고 | 상태 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in payload["products"]:
        lines.append(
            f"| {item['product_code']} | {item['product_name']} | {item['price']} | - | unknown |"
        )
    lines.extend(
        [
            "",
            "## 다음 단계",
            "",
            "- 실제 스마트스토어 API 연동 전 승인 파일 확인",
            "- API 키/토큰은 출력하지 않음",
            "- 가져온 데이터는 로컬 CSV/JSON으로 먼저 저장",
        ]
    )
    return "\n".join(lines), payload


def write_smartstore_fetch_dry_run() -> tuple[Path, Path, Path]:
    md, payload = build_smartstore_fetch_dry_run()
    report_path = write_report(ROOT / "08_reports", "smartstore_fetch_dry_run", md)
    json_path = _write_json(ROOT / "04_smartstore" / "dry_run", "smartstore_products", payload)
    approval = format_approval_request(
        task_name="스마트스토어 상품 데이터 가져오기",
        target="스마트스토어 상품 목록 API 또는 관리자 화면",
        before="로컬 샘플 상품 데이터만 사용",
        after="승인 후 실제 상품 데이터를 읽어 로컬 파일로 저장",
        expected_effect="상품명, 가격, 재고, 상태 기반 분석 준비",
        risks=["로그인 세션 사용 위험", "API 토큰 노출 위험", "상품 수정 화면 접근 위험"],
        rollback="연동 비활성화, 로컬 dry-run 데이터만 사용",
        source_markdown=md,
    )
    approval_path = write_report(ROOT / "09_approval", "APPROVAL_REQUIRED_smartstore_fetch", approval)
    return report_path, json_path, approval_path


def build_naver_ads_api_dry_run() -> tuple[str, dict[str, object]]:
    payload = {
        "source": "naver_ads_api_dry_run",
        "dry_run": True,
        "actual_api_call": False,
        "mutation_allowed": False,
        "endpoints": [
            {"name": "keyword_report", "method": "GET", "writes": False},
            {"name": "bid_update", "method": "PUT", "writes": True, "blocked": True},
            {"name": "budget_update", "method": "PUT", "writes": True, "blocked": True},
        ],
    }
    lines = [
        "# 네이버광고 API Dry-run 어댑터",
        "",
        "- 실제 API 호출 여부: 호출 안 함",
        "- 입찰가 변경 여부: 변경 안 함",
        "- 광고비 변경 여부: 변경 안 함",
        "",
        "## 엔드포인트 계획",
        "",
        "| 이름 | 메서드 | 쓰기 여부 | 상태 |",
        "| --- | --- | --- | --- |",
    ]
    for item in payload["endpoints"]:
        status = "차단" if item.get("blocked") else "읽기 후보"
        lines.append(f"| {item['name']} | {item['method']} | {'예' if item['writes'] else '아니오'} | {status} |")
    lines.extend(
        [
            "",
            "## 안전 기준",
            "",
            "- API 키/비밀키 출력 금지",
            "- 읽기 API도 실제 호출 전 승인 파일 확인",
            "- 쓰기 API는 별도 최종 승인 없이는 차단",
        ]
    )
    return "\n".join(lines), payload


def write_naver_ads_api_dry_run() -> tuple[Path, Path, Path]:
    md, payload = build_naver_ads_api_dry_run()
    report_path = write_report(ROOT / "08_reports", "naver_ads_api_dry_run", md)
    json_path = _write_json(ROOT / "05_naver_ads" / "dry_run", "naver_ads_api_plan", payload)
    approval = format_approval_request(
        task_name="네이버광고 API 읽기 연동",
        target="네이버광고 API",
        before="CSV 샘플 분석만 사용",
        after="승인 후 읽기 API로 리포트를 로컬 저장",
        expected_effect="키워드/광고비/ROAS 분석 자동화 준비",
        risks=["API 키 노출 위험", "쓰기 API 오작동 위험", "광고비/입찰 변경 위험"],
        rollback="API 연동 비활성화, CSV 분석으로 복귀",
        source_markdown=md,
    )
    approval_path = write_report(ROOT / "09_approval", "APPROVAL_REQUIRED_naver_ads_api_read", approval)
    return report_path, json_path, approval_path


def build_instagram_upload_dry_run(product_code: str) -> tuple[str, dict[str, object]]:
    payload = {
        "source": "instagram_upload_dry_run",
        "dry_run": True,
        "actual_upload": False,
        "product_code": product_code,
        "caption": "사줘도 안 놀던 고양이, 움직임을 바꿔보세요. #고양이장난감 #고스틱",
        "assets_required": ["feed_image_4_5", "reels_cover_9_16"],
        "preflight": ["가격 확인", "재고 확인", "링크 확인", "이미지 저작권 확인"],
    }
    lines = [
        f"# 인스타 업로드 승인형 Dry-run 패키지: {product_code}",
        "",
        "- 실제 업로드 여부: 업로드 안 함",
        "- 게시/예약 여부: 게시 안 함",
        "- 고객 메시지 발송 여부: 발송 안 함",
        "",
        "## 캡션 초안",
        "",
        payload["caption"],
        "",
        "## 업로드 전 확인",
        "",
    ]
    lines.extend(f"- {item}" for item in payload["preflight"])
    return "\n".join(lines), payload


def write_instagram_upload_dry_run(product_code: str) -> tuple[Path, Path, Path]:
    md, payload = build_instagram_upload_dry_run(product_code)
    report_path = write_report(ROOT / "08_reports", f"instagram_upload_dry_run_{product_code}", md)
    json_path = _write_json(ROOT / "02_marketing" / "instagram_dry_run", f"instagram_upload_{product_code}", payload)
    approval = format_approval_request(
        task_name=f"{product_code} 인스타 업로드",
        target="인스타그램 피드/릴스",
        before="로컬 콘텐츠 초안 상태",
        after="승인 후 인스타그램 게시 후보",
        expected_effect="SNS 유입과 상품 관심도 개선",
        risks=["실제 게시 후 수정 비용", "가격/재고/링크 오류", "이미지 저작권 위험"],
        rollback="게시물 삭제 또는 비공개, 광고 비활성화",
        source_markdown=md,
    )
    approval_path = write_report(ROOT / "09_approval", f"APPROVAL_REQUIRED_instagram_upload_{product_code}", approval)
    return report_path, json_path, approval_path


def export_payload_csv(json_path: Path, csv_path: Path) -> Path:
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    products = payload.get("products", [])
    if not products:
        return csv_path
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(products[0].keys()))
        writer.writeheader()
        writer.writerows(products)
    return csv_path
