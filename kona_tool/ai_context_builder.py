# -*- coding: utf-8 -*-
"""聚合用户投资数据，输出格式化 markdown 文本，注入 LLM system prompt。"""

from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List

from core.request_trace import trace_request_stage

logger = logging.getLogger(__name__)


def build_user_context(
    *,
    user_id: str,
    db: Any,
    portfolio_read_service: Any,
    rates_getter: Callable[[], Dict[str, float]],
    market_status_getter: Callable[..., Dict[str, Any]],
) -> str:
    """聚合用户投资数据，返回 markdown 格式文本。"""
    sections: List[str] = []

    try:
        rates = rates_getter() or {}
    except Exception:
        rates = {}

    # 1. 持仓明细 + 资产总览（通过 portfolio_read_service 获取实时数据）
    try:
        with trace_request_stage("ai.context.portfolio"):
            items = portfolio_read_service.build_metrics_payload(user_id=user_id)
        if items:
            sections.append(_build_portfolio_section(items, rates))
    except Exception as exc:
        logger.warning("ai_context: portfolio failed: %s", exc)

    # 2. 现金 / 其他 / 负债
    try:
        with trace_request_stage("ai.context.accounts"):
            cash_assets = db.get_cash_assets(user_id)
            other_assets = db.get_other_assets(user_id)
            liabilities = db.get_liabilities(user_id)
        sections.append(_build_accounts_section(cash_assets, other_assets, liabilities, rates))
    except Exception as exc:
        logger.warning("ai_context: accounts failed: %s", exc)

    # 3. 近 30 天日快照
    try:
        with trace_request_stage("ai.context.history", days=30):
            history = db.get_history(30, user_id)
        if history:
            sections.append(_build_history_section(history))
    except Exception as exc:
        logger.warning("ai_context: history failed: %s", exc)

    # 4. 盈亏排行
    try:
        with trace_request_stage("ai.context.rank", rank_type="gain", market="all"):
            rank = db.get_rank_data("gain", "all", user_id)
        if rank:
            sections.append(_build_rank_section(rank))
    except Exception as exc:
        logger.warning("ai_context: rank failed: %s", exc)

    # 5. 市场状态
    try:
        from datetime import datetime, timezone
        with trace_request_stage("ai.context.market"):
            market_info = market_status_getter(
                now_utc=datetime.now(timezone.utc),
                force_refresh=False,
            )
        if market_info:
            sections.append(_build_market_section(market_info))
    except Exception as exc:
        logger.warning("ai_context: market failed: %s", exc)

    return "\n\n".join(sections) if sections else "（暂无用户投资数据）"


def _convert_to_cny(amount: float, curr: str, rates: Dict[str, float]) -> float:
    """简单货币转换到 CNY。"""
    if not curr or curr == "CNY":
        return amount
    rate = rates.get(curr, 0)
    if rate > 0:
        return amount * rate
    return amount


def _build_portfolio_section(items: List[Dict[str, Any]], rates: Dict[str, float]) -> str:
    """持仓明细 + 资产总览。"""
    total_market_value = 0.0
    total_cost = 0.0
    total_day_pnl = 0.0

    lines = ["## 持仓明细"]
    lines.append("| 名称 | 代码 | 数量 | 成本价 | 现价 | 盈亏 | 盈亏率 | 日盈亏 | 货币 | 类型 |")
    lines.append("|------|------|------|--------|------|------|--------|--------|------|------|")

    for item in items:
        code = item.get("code", "")
        name = item.get("name", code)
        qty = float(item.get("qty") or 0)
        cost_price = float(item.get("price") or 0)
        current_price = float(item.get("current_price") or 0)
        pnl = float(item.get("pnl") or 0)
        pnl_rate = float(item.get("pnl_rate") or 0)
        day_pnl = float(item.get("day_pnl") or 0)
        curr = item.get("curr", "CNY")
        asset_type = item.get("asset_type", "")

        cost_cny = _convert_to_cny(cost_price * qty, curr, rates)
        mv_cny = _convert_to_cny(current_price * qty, curr, rates)
        total_cost += cost_cny
        total_market_value += mv_cny
        total_day_pnl += _convert_to_cny(day_pnl, curr, rates)

        lines.append(
            f"| {name} | {code} | {qty:.0f} | {cost_price:.3f} | {current_price:.3f} "
            f"| {pnl:+.2f} | {pnl_rate:+.2f}% | {day_pnl:+.2f} | {curr} | {asset_type} |"
        )

    total_pnl = total_market_value - total_cost
    total_pnl_rate = (total_pnl / total_cost * 100) if total_cost > 0 else 0

    summary = (
        f"\n## 投资资产总览\n"
        f"- 投资总市值（CNY）：{total_market_value:,.2f}\n"
        f"- 投资总成本（CNY）：{total_cost:,.2f}\n"
        f"- 投资总盈亏（CNY）：{total_pnl:+,.2f}（{total_pnl_rate:+.2f}%）\n"
        f"- 今日盈亏（CNY）：{total_day_pnl:+,.2f}\n"
        f"- 持仓数量：{len(items)} 只"
    )

    return "\n".join(lines) + summary


def _build_accounts_section(
    cash: List[Dict], other: List[Dict], liabilities: List[Dict], rates: Dict[str, float]
) -> str:
    """现金、其他资产、负债。"""
    lines = ["## 非投资资产"]

    total_cash = 0.0
    if cash:
        lines.append("\n### 现金资产")
        for a in cash:
            amount = float(a.get("amount") or 0)
            curr = a.get("curr", "CNY")
            total_cash += _convert_to_cny(amount, curr, rates)
            lines.append(f"- {a.get('name', '未命名')}：{amount:,.2f} {curr}")
    lines.append(f"\n现金合计（CNY）：{total_cash:,.2f}")

    total_other = 0.0
    if other:
        lines.append("\n### 其他资产")
        for a in other:
            amount = float(a.get("amount") or 0)
            curr = a.get("curr", "CNY")
            total_other += _convert_to_cny(amount, curr, rates)
            lines.append(f"- {a.get('name', '未命名')}：{amount:,.2f} {curr}")
    lines.append(f"\n其他资产合计（CNY）：{total_other:,.2f}")

    total_liability = 0.0
    if liabilities:
        lines.append("\n### 负债")
        for a in liabilities:
            amount = float(a.get("amount") or 0)
            curr = a.get("curr", "CNY")
            total_liability += _convert_to_cny(amount, curr, rates)
            lines.append(f"- {a.get('name', '未命名')}：{amount:,.2f} {curr}")
    lines.append(f"\n负债合计（CNY）：{total_liability:,.2f}")

    return "\n".join(lines)


def _build_history_section(history: List[Dict]) -> str:
    """近 30 天日快照趋势。"""
    # 取最近 30 条
    recent = history[-30:] if len(history) > 30 else history
    lines = ["## 近期资产趋势（日快照）"]
    lines.append("| 日期 | 总资产 | 日盈亏 |")
    lines.append("|------|--------|--------|")

    prev_total = None
    for row in recent:
        date = row.get("date", "")
        total = float(row.get("total_asset") or row.get("total_assets") or 0)
        day_pnl = float(row.get("day_pnl") or 0)
        if day_pnl == 0 and prev_total is not None:
            day_pnl = total - prev_total
        lines.append(f"| {date} | {total:,.2f} | {day_pnl:+,.2f} |")
        prev_total = total

    return "\n".join(lines)


def _build_rank_section(rank_data: List[Dict]) -> str:
    """盈亏排行 Top5。"""
    # rank_data 包含所有持仓的排行数据，按 pnl 排序取 top/bottom 5
    sorted_by_pnl = sorted(rank_data, key=lambda x: float(x.get("adjustment", 0)), reverse=True)

    lines = ["## 盈亏排行"]
    if sorted_by_pnl:
        top5 = sorted_by_pnl[:5]
        lines.append("\n最赚 Top5：")
        for item in top5:
            name = item.get("name", item.get("code", ""))
            lines.append(f"- {name}（{item.get('code', '')}）")

        bottom5 = sorted_by_pnl[-5:]
        bottom5.reverse()
        lines.append("\n最亏 Top5：")
        for item in bottom5:
            name = item.get("name", item.get("code", ""))
            lines.append(f"- {name}（{item.get('code', '')}）")

    return "\n".join(lines)


def _build_market_section(market_info: Dict[str, Any]) -> str:
    """市场状态。"""
    markets = market_info.get("markets", {})
    lines = ["## 市场状态"]
    for key, info in markets.items():
        if isinstance(info, dict):
            status = "开市" if info.get("is_open") else "休市"
            label = info.get("label", key.upper())
            lines.append(f"- {label}：{status}")

    indices = market_info.get("indices", {})
    if indices:
        lines.append("\n### 主要指数")
        for name, val in indices.items():
            if isinstance(val, dict):
                price = val.get("price", val.get("value", ""))
                change = val.get("change_pct", val.get("change", ""))
                lines.append(f"- {name}：{price}（{change}）")

    return "\n".join(lines)
