"""일일/월간 비용 캡 — 호출 전에 확인하고 초과 시 차단.

기본 캡:
- 일일: 1,000원
- 월간: 30,000원

환경변수로 조정:
- DAILY_LLM_CAP_KRW
- MONTHLY_LLM_CAP_KRW

캡 확인 함수만 제공. 실제 차감은 호출 후 usage_log가 담당.
"""
from __future__ import annotations

import os
from typing import Tuple

from .usage_log import daily_summary, monthly_summary


def _cap_daily() -> float:
    return float(os.environ.get("DAILY_LLM_CAP_KRW", "1000"))


def _cap_monthly() -> float:
    return float(os.environ.get("MONTHLY_LLM_CAP_KRW", "30000"))


def check_cap(estimated_krw: float = 0.0) -> Tuple[bool, str]:
    """이 호출이 캡을 초과할지 검사.

    Returns:
        (ok, reason). ok=False면 호출 차단해야 한다.
    """
    day = daily_summary()
    month = monthly_summary()
    cap_d = _cap_daily()
    cap_m = _cap_monthly()
    day_used = float(day.get("total_cost_krw_est", 0.0))
    month_used = float(month.get("total_cost_krw_est", 0.0))
    after_d = day_used + max(0.0, float(estimated_krw or 0))
    after_m = month_used + max(0.0, float(estimated_krw or 0))
    if after_d > cap_d:
        return False, (
            f"일일 캡 ₩{int(cap_d):,} 초과 위험 "
            f"(현재 ₩{day_used:,.0f}, 이번 호출 ₩{estimated_krw:,.0f} 추정). "
            "환경변수 DAILY_LLM_CAP_KRW 로 조정하거나 다음 날 시도."
        )
    if after_m > cap_m:
        return False, (
            f"월간 캡 ₩{int(cap_m):,} 초과 위험 "
            f"(현재 ₩{month_used:,.0f}, 이번 호출 ₩{estimated_krw:,.0f} 추정). "
            "환경변수 MONTHLY_LLM_CAP_KRW 로 조정하거나 다음 달 시도."
        )
    return True, "ok"


def caps_status() -> dict:
    day = daily_summary()
    month = monthly_summary()
    return {
        "daily_cap_krw": _cap_daily(),
        "daily_used_krw": float(day.get("total_cost_krw_est", 0.0)),
        "daily_calls": int(day.get("total_calls", 0)),
        "monthly_cap_krw": _cap_monthly(),
        "monthly_used_krw": float(month.get("total_cost_krw_est", 0.0)),
        "monthly_calls": int(month.get("total_calls", 0)),
    }


__all__ = ["check_cap", "caps_status"]
