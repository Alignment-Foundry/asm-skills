#!/usr/bin/env python3
"""
Nous Portal Credits CLI

Queries the Nous Portal /api/oauth/account endpoint using the Hermes OAuth
session and displays current credits, subscription, and usage info.

Usage:
  ./nous-credits.py                    # Human-readable report
  ./nous-credits.py --json             # JSON output (cron-friendly)
  ./nous-credits.py --quiet            # One-line summary only
  ./nous-credits.py --force-fresh      # Bypass cache, hit the API fresh
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone

# ── Hermes imports (enabled via the Hermes venv) ──────────────────────────
_HERMES_VENV_PYTHON = "{hermes_home}/hermes-agent/venv/bin/python"


def _import_hermes() -> tuple:
    """Import Hermes modules needed for portal auth."""
    sys.path.insert(0, "{hermes_home}/hermes-agent")
    try:
        from hermes_cli.nous_account import (
            NousPortalAccountInfo,
            get_nous_portal_account_info,
            nous_portal_topup_url,
        )
        return get_nous_portal_account_info, NousPortalAccountInfo, nous_portal_topup_url
    except ImportError as e:
        raise ImportError(
            f"Could not import Hermes modules. Run this script with the Hermes venv:\n"
            f"  {_HERMES_VENV_PYTHON} {__file__} ...\n"
            f"Error: {e}"
        )


# ── Formatting helpers ──────────────────────────────────────────────────────


def _fmt_dollar(value: float | None) -> str:
    if value is None:
        return "—"
    return f"${value:,.2f}"


def _fmt_date(value: str | None) -> str:
    if not value:
        return "—"
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M UTC")
    except (ValueError, TypeError):
        return value


def _fmt_bool(value: bool | None, yes: str = "Yes", no: str = "No") -> str:
    if value is True:
        return yes
    if value is False:
        return no
    return "Unknown"


# ── Report builders ─────────────────────────────────────────────────────────


def build_report(info: object, *, force_fresh: bool = False) -> dict:
    """Build a structured dict from the account info."""
    get_nous_portal_account_info, NousPortalAccountInfo, _ = _import_hermes()
    if info is None:
        info = get_nous_portal_account_info(force_fresh=force_fresh)

    report: dict = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": str(getattr(info, "source", "none")),
        "fresh": bool(getattr(info, "fresh", False)),
        "logged_in": bool(getattr(info, "logged_in", False)),
        "error": None,
    }

    if getattr(info, "error", None):
        report["error"] = str(info.error)
        return report

    if not info.logged_in:
        report["error"] = "Not logged into Nous Portal. Run `hermes portal` to log in."
        return report

    # ── Subscription ──────────────────────────────────────────────────────
    sub = getattr(info, "subscription", None)
    report["subscription"] = {
        "plan": getattr(sub, "plan", None) if sub else None,
        "tier": getattr(sub, "tier", None) if sub else None,
        "monthly_charge": getattr(sub, "monthly_charge", None) if sub else None,
        "monthly_credits": getattr(sub, "monthly_credits", None) if sub else None,
        "current_period_end": getattr(sub, "current_period_end", None) if sub else None,
        "credits_remaining": getattr(sub, "credits_remaining", None) if sub else None,
        "rollover_credits": getattr(sub, "rollover_credits", None) if sub else None,
    }

    # ── Paid Service Access ───────────────────────────────────────────────
    access = getattr(info, "paid_service_access_info", None)
    report["paid_service_access"] = {
        "allowed": getattr(info, "paid_service_access", None),
        "is_paid": bool(getattr(info, "paid_service_access", False)),
        "has_active_subscription": getattr(access, "has_active_subscription", None) if access else None,
        "active_subscription_is_paid": getattr(access, "active_subscription_is_paid", None) if access else None,
        "subscription_tier": getattr(access, "subscription_tier", None) if access else None,
        "subscription_monthly_charge": getattr(access, "subscription_monthly_charge", None) if access else None,
        "subscription_credits_remaining": getattr(access, "subscription_credits_remaining", None) if access else None,
        "purchased_credits_remaining": getattr(access, "purchased_credits_remaining", None) if access else None,
        "total_usable_credits": getattr(access, "total_usable_credits", None) if access else None,
    }

    # ── Tool Access (free pool) ───────────────────────────────────────────
    tool = getattr(info, "tool_access", None)
    report["tool_access"] = {
        "enabled": getattr(tool, "enabled", False) if tool else False,
        "coverage": dict(getattr(tool, "coverage", {})) if tool else {},
    }

    # ── Account ───────────────────────────────────────────────────────────
    report["account"] = {
        "org_name": getattr(info, "org_name", None),
        "org_slug": getattr(info, "org_slug", None),
        "email": getattr(info, "email", None),
        "portal_base_url": getattr(info, "portal_base_url", None),
        "inference_base_url": getattr(info, "inference_base_url", None),
    }

    return report


def print_human_report(report: dict) -> None:
    """Pretty-print the credit report for human consumption."""
    if report.get("error"):
        print(f"⚠️  {report['error']}")
        sys.exit(1)

    source_label = {
        "jwt": "JWT (cached)",
        "account_api": "Portal API (fresh)",
    }.get(report.get("source", ""), report.get("source", ""))

    print(f"┌─ Nous Portal Credits ─────────────────────────────{'─' * 5}┐")
    print(f"│ {'Source:':<18} {source_label:<40} │")
    if report.get("fresh"):
        print(f"│ {'Cache:':<18} {'Fresh from API':<40} │")
    print(f"├────────────────────────────────────────────────────────────┤")

    # ── Sub total ────────────────────────────────────────────────────────
    sub = report.get("subscription", {})
    plan_label = sub.get("plan") or "—"
    tier = sub.get("tier")
    charge = sub.get("monthly_charge")
    credits_rem = sub.get("credits_remaining")
    monthly_cred = sub.get("monthly_credits")
    rollover = sub.get("rollover_credits")
    period_end = sub.get("current_period_end")

    print(f"│ {'Plan:':<18} {plan_label:<20}", end="")
    if tier is not None:
        print(f"{'Tier:':<10} {tier}")
    else:
        print()

    if charge is not None:
        print(f"│ {'Monthly:':<18} {_fmt_dollar(charge):<20}{'Credits/mo:':<10} {_fmt_dollar(monthly_cred)}")

    if credits_rem is not None:
        print(f"│ {'Credits left:':<18} {_fmt_dollar(credits_rem):<20}{'Rollover:':<10} {_fmt_dollar(rollover) if rollover is not None else '—'}")

    if period_end:
        print(f"│ {'Period ends:':<18} {_fmt_date(period_end)}")

    # ── Paid service access ──────────────────────────────────────────────
    access = report.get("paid_service_access", {})
    total = access.get("total_usable_credits")
    sub_cred = access.get("subscription_credits_remaining")
    purch_cred = access.get("purchased_credits_remaining")
    has_sub = access.get("has_active_subscription")
    sub_paid = access.get("active_subscription_is_paid")
    tier_info = access.get("subscription_tier")

    if any(v is not None for v in [total, sub_cred, purch_cred, has_sub]):
        print(f"├────────────────────────────────────────────────────────────┤")
        print(f"│ {'Credits Summary':<52} │")
        print(f"│ {'Total usable:':<18} {_fmt_dollar(total):<20}{'Active sub:':<10} {_fmt_bool(has_sub, 'Yes', 'No')}")

        if sub_cred is not None:
            print(f"│ {'Subscription:':<18} {_fmt_dollar(sub_cred)}")
        if purch_cred is not None:
            print(f"│ {'Purchased:':<18} {_fmt_dollar(purch_cred)}")
        if sub_paid is not None:
            print(f"│ {'Paid sub:':<18} {_fmt_bool(sub_paid, 'Yes', 'No')}")

    # ── Tool access ──────────────────────────────────────────────────────
    tool = report.get("tool_access", {})
    if tool.get("enabled"):
        covered = [k for k, v in tool.get("coverage", {}).items() if v]
        if covered:
            print(f"├────────────────────────────────────────────────────────────┤")
            print(f"│ {'Tool Pool:':<18} {'Active — ' + ', '.join(covered):<40} │")
    else:
        print(f"│ {'Tool Pool:':<18} {'Inactive or free-tier only':<40} │")

    # ── Account ──────────────────────────────────────────────────────────
    acct = report.get("account", {})
    email = acct.get("email")
    org = acct.get("org_name")
    if email or org:
        print(f"├────────────────────────────────────────────────────────────┤")
        if email:
            print(f"│ {'User:':<18} {email:<40} │")
        if org:
            slug = acct.get("org_slug")
            label = f"{org} ({slug})" if slug else org
            print(f"│ {'Org:':<18} {label:<40} │")

    print(f"└────────────────────────────────────────────────────────────┘")


def print_markdown_report(report: dict) -> None:
    """Pretty-print as a Markdown pipe table for Telegram delivery."""
    if report.get("error"):
        print(f"⚠️ {report['error']}")
        return

    source_label = {
        "jwt": "JWT (cached)",
        "account_api": "Portal API (fresh)",
    }.get(report.get("source", ""), report.get("source", ""))
    fresh = report.get("fresh", False)
    source_line = f"{source_label}" + (" *(fresh)*" if fresh else "")

    sub = report.get("subscription", {})
    access = report.get("paid_service_access", {})

    rows = []
    rows.append(("Source", source_line))
    rows.append(("Plan", sub.get("plan") or "—"))
    if sub.get("tier") is not None:
        rows.append(("Tier", str(sub.get("tier"))))
    if sub.get("monthly_charge") is not None:
        rows.append(("Monthly", _fmt_dollar(sub.get("monthly_charge"))))
        rows.append(("Credits/mo", _fmt_dollar(sub.get("monthly_credits"))))
    if sub.get("credits_remaining") is not None:
        rows.append(("Credits left", _fmt_dollar(sub.get("credits_remaining"))))
    if sub.get("rollover_credits") is not None:
        rows.append(("Rollover", _fmt_dollar(sub.get("rollover_credits"))))
    if sub.get("current_period_end"):
        rows.append(("Period ends", _fmt_date(sub.get("current_period_end"))))

    total = access.get("total_usable_credits")
    sub_cred = access.get("subscription_credits_remaining")
    purch_cred = access.get("purchased_credits_remaining")
    has_sub = access.get("has_active_subscription")

    if any(v is not None for v in [total, sub_cred, purch_cred, has_sub]):
        if total is not None:
            rows.append(("Total usable", _fmt_dollar(total)))
        if sub_cred is not None:
            rows.append(("Subscription credits", _fmt_dollar(sub_cred)))
        if purch_cred is not None:
            rows.append(("Purchased credits", _fmt_dollar(purch_cred)))
        if has_sub is not None:
            rows.append(("Active sub", _fmt_bool(has_sub, "Yes", "No")))

    acct = report.get("account", {})
    if acct.get("email"):
        rows.append(("User", acct["email"]))
    if acct.get("org_name"):
        slug = acct.get("org_slug")
        org_label = f"{acct['org_name']} ({slug})" if slug else acct["org_name"]
        rows.append(("Org", org_label))

    # Print header
    print(f"## Nous Portal Credits\n")
    print(f"| {'Field':<22} | {'Value':<36} |")
    print(f"| {'-'*22} | {'-'*36} |")
    for label, value in rows:
        print(f"| {label:<22} | {str(value):<36} |")

    # Low-credit alert
    total_val = total if total is not None else sub.get("credits_remaining")
    if total_val is not None and total_val < 5.0:
        print(f"\n⚠️ Credits running low — **${total_val:.2f}** remaining")


def print_quiet_report(report: dict) -> None:
    """One-line summary, suitable for status bar or watch."""
    if report.get("error"):
        print(f"⚠ {report['error']}")
        return

    sub = report.get("subscription", {})
    access = report.get("paid_service_access", {})
    total = access.get("total_usable_credits")
    sub_cred = sub.get("credits_remaining", access.get("subscription_credits_remaining"))
    purch_cred = access.get("purchased_credits_remaining")
    plan = sub.get("plan") or ""
    is_paid = access.get("is_paid")
    tier = access.get("subscription_tier")

    parts = []
    if total is not None:
        parts.append(f"usable ${total:.2f}")
    if sub_cred is not None:
        parts.append(f"sub ${sub_cred:.2f}")
    if purch_cred is not None:
        parts.append(f"purch ${purch_cred:.2f}")

    if not parts:
        if is_paid is True:
            parts.append("paid access")
            if tier is not None:
                parts.append(f"tier {tier}")
        elif is_paid is False:
            parts.append("free tier")

    prefix = f"[{plan}] " if plan else "Nous: "
    status = " | ".join(parts) if parts else "No credit data (try --force-fresh)"
    print(f"{prefix}{status}")


def check_low_credits(report: dict, threshold: float = 5.0) -> bool:
    """Return True if total usable credits are below threshold."""
    access = report.get("paid_service_access", {})
    total = access.get("total_usable_credits")
    if total is not None and total < threshold:
        return True
    sub_cred = report.get("subscription", {}).get("credits_remaining")
    if sub_cred is not None and sub_cred < threshold:
        return True
    return False


# ── Main ────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Check Nous Portal credits and subscription balance.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output raw JSON (for cron/programmatic use)",
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="One-line summary only",
    )
    parser.add_argument(
        "--markdown", "--tg",
        action="store_true",
        help="Format as Markdown pipe table (Telegram-friendly)",
    )
    parser.add_argument(
        "--force-fresh",
        action="store_true",
        help="Skip cache, fetch from portal API directly",
    )
    parser.add_argument(
        "--check-threshold",
        type=float,
        default=None,
        metavar="DOLLARS",
        help="Exit code 2 when total usable credits < this amount",
    )
    args = parser.parse_args()

    try:
        get_nous_portal_account_info, _, nous_portal_topup_url = _import_hermes()
        info = get_nous_portal_account_info(force_fresh=args.force_fresh)
        report = build_report(info, force_fresh=args.force_fresh)
    except Exception as e:
        print(json.dumps({"error": str(e), "timestamp": datetime.now(timezone.utc).isoformat()}))
        sys.exit(1)

    if args.json:
        print(json.dumps(report, indent=2, default=str))
    elif args.markdown:
        print_markdown_report(report)
    elif args.quiet:
        print_quiet_report(report)
    else:
        print_human_report(report)

    # Threshold check (exit code 2 = low credits alert)
    threshold = args.check_threshold
    if threshold is not None and check_low_credits(report, threshold):
        topup = nous_portal_topup_url(getattr(info, "portal_base_url", None))
        print(f"\n⚠️  Credits below ${threshold:.2f}! Top up: {topup}")
        sys.exit(2)


if __name__ == "__main__":
    main()
