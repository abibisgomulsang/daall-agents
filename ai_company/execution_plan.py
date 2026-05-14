from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from .approval import ALLOWED_DECISIONS, list_approvals
from .paths import ROOT
from .utils import now_stamp, write_report


@dataclass(frozen=True)
class KeywordAction:
    campaign: str
    keyword: str
    roas_percent: float | None
    action: str
    reason: str


@dataclass(frozen=True)
class ExecutionPlanOutput:
    plan_path: Path
    csv_path: Path | None = None


def _approval_dir(path: Path | None = None) -> Path:
    return path or ROOT / "09_approval"


def _reports_dir(path: Path | None = None) -> Path:
    return path or ROOT / "08_reports"


def _load_approval_file(file_name: str, approval_dir: Path) -> tuple[Path, str]:
    target = approval_dir / file_name
    if not target.exists() or not target.name.startswith("APPROVAL_REQUIRED_"):
        raise FileNotFoundError(f"승인 대기 파일을 찾을 수 없습니다: {file_name}")
    return target, target.read_text(encoding="utf-8")


def _is_naver_ads(file_name: str, content: str) -> bool:
    return "naver_ads" in file_name or "네이버광고" in content


def _status_for_file(file_name: str, approval_dir: Path) -> str:
    for item in list_approvals(approval_dir):
        if item.file_name == file_name:
            return ALLOWED_DECISIONS.get(item.status, "대기")
    return "대기"


def _first_heading(content: str) -> str:
    for line in content.splitlines():
        if line.startswith("# "):
            return line.removeprefix("# ").strip()
    return "승인 요청"


def _split_markdown_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _parse_percent(value: str) -> float | None:
    cleaned = value.replace(",", "").replace("%", "").strip()
    if not cleaned or cleaned == "-":
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def _extract_keyword_actions(content: str) -> list[KeywordAction]:
    rows: list[KeywordAction] = []
    table_lines = [line for line in content.splitlines() if line.startswith("|")]
    if len(table_lines) < 3:
        return rows

    headers = _split_markdown_row(table_lines[0])
    required = {"campaign", "keyword", "clicks", "orders", "ROAS_%", "AI_판정"}
    if not required.issubset(set(headers)):
        return rows

    indexes = {header: headers.index(header) for header in required}
    for line in table_lines[2:]:
        cells = _split_markdown_row(line)
        if len(cells) < len(headers):
            continue
        roas = _parse_percent(cells[indexes["ROAS_%"]])
        ai_decision = cells[indexes["AI_판정"]]
        clicks = _parse_percent(cells[indexes["clicks"]]) or 0
        orders = _parse_percent(cells[indexes["orders"]]) or 0

        if roas is not None and roas >= 300:
            action = "예산 유지 또는 소폭 증액 후보"
            reason = "ROAS가 300% 이상입니다."
        elif roas is not None and roas < 100 and clicks >= 50:
            action = "중지 후보가 아닌 개선 후보로 보류"
            reason = "ROAS가 낮지만 실제 중지는 사장님 재확인 후 진행합니다."
        elif "문구" in ai_decision or "랜딩" in ai_decision:
            action = "광고 문구와 랜딩 메시지 개선 후보"
            reason = "분석 결과가 문구/랜딩 개선을 가리킵니다."
        elif clicks >= 50 and orders <= 1:
            action = "낭비 키워드 점검 후보"
            reason = "클릭 대비 주문이 낮습니다."
        else:
            action = "관찰 유지"
            reason = "즉시 조정보다 추가 데이터 확인이 적합합니다."

        rows.append(
            KeywordAction(
                campaign=cells[indexes["campaign"]],
                keyword=cells[indexes["keyword"]],
                roas_percent=roas,
                action=action,
                reason=reason,
            )
        )
    return rows


def _render_keyword_plan(actions: list[KeywordAction]) -> list[str]:
    if not actions:
        return [
            "## 네이버광고 dry-run 분류",
            "",
            "- 승인 파일에서 키워드 표를 찾지 못했습니다.",
            "- 실제 실행 전 원본 CSV와 광고 관리자 화면 값을 다시 대조해야 합니다.",
        ]

    lines = [
        "## 네이버광고 dry-run 분류",
        "",
        "| 캠페인 | 키워드 | ROAS | dry-run 조치 | 판단 이유 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for action in actions:
        roas = "-" if action.roas_percent is None else f"{action.roas_percent:.1f}%"
        lines.append(
            f"| {action.campaign} | {action.keyword} | {roas} | {action.action} | {action.reason} |"
        )
    return lines


def build_execution_plan(file_name: str, approval_dir: Path | None = None) -> str:
    folder = _approval_dir(approval_dir)
    target, content = _load_approval_file(file_name, folder)
    title = _first_heading(content)
    status = _status_for_file(target.name, folder)
    is_naver_ads = _is_naver_ads(target.name, content)

    lines = [
        f"# 실행 전 Dry-run 계획: {target.name}",
        "",
        f"- 승인 요청 제목: {title}",
        f"- 현재 승인 상태: {status}",
        "- 실제 실행 여부: 실행 안 함",
        "- 외부 서비스 접속: 없음",
        "- 결제/업로드/입찰 변경: 없음",
        "",
        "## 실행 게이트",
        "",
        "1. 승인 파일의 대상과 변경 내용을 사장님이 확인한다.",
        "2. 승인 기록이 `approved` 상태인지 확인한다.",
        "3. 실행 직전 원본 상태를 백업하거나 스크린샷으로 남긴다.",
        "4. dry-run 결과와 실제 화면 값이 다르면 실행하지 않는다.",
        "5. 실제 반영 명령은 별도 단계에서 재확인 후 수행한다.",
        "",
    ]

    if is_naver_ads:
        lines.extend(_render_keyword_plan(_extract_keyword_actions(content)))
        lines.append("")
    else:
        lines.extend(
            [
                "## dry-run 작업 분해",
                "",
                "- 원본 승인 요청을 기준으로 변경 대상과 문구를 다시 추출한다.",
                "- 마케팅 AI가 실행 초안을 정리한다.",
                "- 검수 AI가 과장 표현, 저작권, 개인정보, 가격/재고 위험을 확인한다.",
                "- CEO AI가 실행 가능 여부와 보류 항목을 정리한다.",
                "",
            ]
        )

    lines.extend(
        [
            "## 사장님 최종 확인 항목",
            "",
            "- 실제 변경 대상이 맞는가",
            "- 변경 전으로 되돌리는 방법이 준비됐는가",
            "- 광고비, 입찰가, 가격, 재고, 상품명 변경이 포함되는가",
            "- 외부 업로드 또는 고객 발송이 포함되는가",
            "",
            "## 결론",
            "",
            "이 문서는 실행 준비용 dry-run 계획입니다. 실제 실행은 사장님 최종 승인 후 별도 명령으로만 진행합니다.",
        ]
    )
    return "\n".join(lines)


def build_final_checklist(file_name: str, approval_dir: Path | None = None) -> str:
    folder = _approval_dir(approval_dir)
    target, content = _load_approval_file(file_name, folder)
    title = _first_heading(content)
    status = _status_for_file(target.name, folder)
    approved = status == "승인"
    has_rollback = "되돌리는 방법" in content
    has_risk = "위험 요소" in content

    rows = [
        ("승인 상태", "통과" if approved else "보류", "승인 기록이 있어야 실제 실행 후보가 됩니다."),
        ("실제 실행 범위", "확인 필요", "스마트스토어/SNS/네이버광고 실제 반영 전 대상 화면 재확인이 필요합니다."),
        ("변경 전 백업", "확인 필요", "실행 직전 스크린샷 또는 원본 설정 기록이 필요합니다."),
        ("되돌리는 방법", "통과" if has_rollback else "보류", "승인 파일에 되돌리는 방법이 있어야 합니다."),
        ("위험 요소", "통과" if has_risk else "보류", "성과 하락, 저작권, 가격/재고, 광고비 위험을 확인합니다."),
        ("민감정보", "통과", ".env, API 키, 비밀번호, 쿠키, 토큰은 출력하지 않습니다."),
        ("외부 실행", "보류", "최종 실행 명령은 사장님 재확인 후 별도로 진행해야 합니다."),
    ]

    lines = [
        f"# 실행 전 최종 체크리스트: {target.name}",
        "",
        f"- 승인 요청 제목: {title}",
        f"- 현재 승인 상태: {status}",
        "- 실제 실행 여부: 실행 안 함",
        "",
        "| 점검 항목 | 상태 | 메모 |",
        "| --- | --- | --- |",
    ]
    for label, state, memo in rows:
        lines.append(f"| {label} | {state} | {memo} |")

    conclusion = "실행 가능 후보" if approved else "승인 대기"
    lines.extend(
        [
            "",
            "## 결론",
            "",
            f"- 판정: {conclusion}",
            "- 이 체크리스트는 실제 실행 전 마지막 점검용입니다.",
            "- 결제, 고객 메시지, 업로드, 입찰/광고비 변경은 사장님 최종 승인 없이는 진행하지 않습니다.",
        ]
    )
    return "\n".join(lines)


def _write_keyword_actions_csv(file_name: str, content: str, reports_dir: Path) -> Path | None:
    if not _is_naver_ads(file_name, content):
        return None
    actions = _extract_keyword_actions(content)
    if not actions:
        return None

    reports_dir.mkdir(parents=True, exist_ok=True)
    safe_stem = Path(file_name).stem.replace("APPROVAL_REQUIRED_", "")
    path = reports_dir / f"execution_plan_keywords_{safe_stem}_{now_stamp()}.csv"
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["campaign", "keyword", "roas_percent", "dry_run_action", "reason"])
        for action in actions:
            writer.writerow([action.campaign, action.keyword, action.roas_percent, action.action, action.reason])
    return path


def write_execution_plan_outputs(
    file_name: str,
    approval_dir: Path | None = None,
    reports_dir: Path | None = None,
) -> ExecutionPlanOutput:
    approval_folder = _approval_dir(approval_dir)
    report_folder = _reports_dir(reports_dir)
    target, content = _load_approval_file(file_name, approval_folder)
    md = build_execution_plan(file_name, approval_dir=approval_folder)
    safe_stem = target.stem.replace("APPROVAL_REQUIRED_", "")
    plan_path = write_report(report_folder, f"execution_plan_{safe_stem}", md)
    csv_path = _write_keyword_actions_csv(target.name, content, report_folder)
    return ExecutionPlanOutput(plan_path=plan_path, csv_path=csv_path)


def write_execution_plan(
    file_name: str,
    approval_dir: Path | None = None,
    reports_dir: Path | None = None,
) -> Path:
    return write_execution_plan_outputs(file_name, approval_dir, reports_dir).plan_path


def write_final_checklist(
    file_name: str,
    approval_dir: Path | None = None,
    reports_dir: Path | None = None,
) -> Path:
    md = build_final_checklist(file_name, approval_dir=approval_dir)
    safe_stem = Path(file_name).stem.replace("APPROVAL_REQUIRED_", "")
    return write_report(_reports_dir(reports_dir), f"final_checklist_{safe_stem}", md)
