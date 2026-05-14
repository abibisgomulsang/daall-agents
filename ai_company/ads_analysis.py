from __future__ import annotations

import csv
from pathlib import Path


def _to_float(value: str) -> float:
    value = str(value).replace(",", "").strip()
    return float(value) if value else 0.0


def _safe_div(numerator: float, denominator: float) -> float | None:
    if denominator == 0:
        return None
    return numerator / denominator


def _fmt_number(value: float | None, digits: int = 0) -> str:
    if value is None:
        return "-"
    if digits == 0:
        return f"{round(value):,.0f}"
    return f"{value:,.{digits}f}"


def _markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)

def analyze_naver_ads_csv(csv_path: Path) -> str:
    required = {"campaign", "keyword", "cost", "impressions", "clicks", "orders", "revenue"}
    with Path(csv_path).open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"CSV에 필요한 컬럼이 없습니다: {sorted(missing)}")
        source_rows = list(reader)

    analyzed_rows: list[dict[str, float | str | None]] = []
    for row in source_rows:
        cost = _to_float(row["cost"])
        impressions = _to_float(row["impressions"])
        clicks = _to_float(row["clicks"])
        orders = _to_float(row["orders"])
        revenue = _to_float(row["revenue"])

        ctr = _safe_div(clicks, impressions)
        cpc = _safe_div(cost, clicks)
        cvr = _safe_div(orders, clicks)
        roas = _safe_div(revenue, cost)

        if roas is not None and roas >= 3:
            decision = "증액/유지 후보"
        elif roas is not None and roas >= 1.5:
            decision = "문구/랜딩 개선"
        elif clicks >= 50 and (cvr or 0) < 0.02:
            decision = "낭비 가능성 높음"
        else:
            decision = "관찰"

        analyzed_rows.append({
            "campaign": row["campaign"],
            "keyword": row["keyword"],
            "cost": cost,
            "impressions": impressions,
            "clicks": clicks,
            "orders": orders,
            "revenue": revenue,
            "CTR_%": None if ctr is None else ctr * 100,
            "CPC": cpc,
            "CVR_%": None if cvr is None else cvr * 100,
            "ROAS_%": None if roas is None else roas * 100,
            "AI_판정": decision,
        })

    table_rows = []
    for row in analyzed_rows:
        table_rows.append([
            str(row["campaign"]),
            str(row["keyword"]),
            _fmt_number(row["cost"]),
            _fmt_number(row["clicks"]),
            _fmt_number(row["orders"]),
            _fmt_number(row["revenue"]),
            _fmt_number(row["CTR_%"], 2),
            _fmt_number(row["CPC"]),
            _fmt_number(row["CVR_%"], 2),
            _fmt_number(row["ROAS_%"], 1),
            str(row["AI_판정"]),
        ])

    total_cost = sum(float(row["cost"] or 0) for row in analyzed_rows)
    total_revenue = sum(float(row["revenue"] or 0) for row in analyzed_rows)
    total_roas_value = _safe_div(total_revenue, total_cost)
    total_roas = round(total_roas_value * 100, 1) if total_roas_value is not None else 0

    table = _markdown_table(
        ["campaign", "keyword", "cost", "clicks", "orders", "revenue", "CTR_%", "CPC", "CVR_%", "ROAS_%", "AI_판정"],
        table_rows,
    )

    markdown = [
        "# 네이버광고 분석 리포트",
        "",
        f"- 총 광고비: {int(total_cost):,}원",
        f"- 총 매출: {int(total_revenue):,}원",
        f"- 전체 ROAS: {total_roas}%",
        "",
        "## 키워드별 분석",
        "",
        table,
        "",
        "## AI 제안",
        "- ROAS 300% 이상 키워드는 예산 유지 또는 소폭 증액 후보입니다.",
        "- 클릭은 많은데 주문이 낮은 키워드는 상세페이지 첫 이미지/가격/리뷰/배송 메시지를 점검해야 합니다.",
        "- ROAS 150% 미만 키워드는 바로 중지하기보다 광고 문구와 랜딩 메시지 일치 여부를 먼저 확인하세요.",
        "",
        "## 승인 필요",
        "실제 입찰가 변경, 키워드 중지, 광고비 변경은 사장님 승인 후 진행해야 합니다.",
    ]
    return "\n".join(markdown)
