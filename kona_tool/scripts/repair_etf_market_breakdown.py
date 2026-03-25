#!/usr/bin/env python3
"""
修复场内 ETF 日历收益的市场归属。

问题：场内 ETF（如 159201、512890）的 asset_type='fund'，在快照计算中被归入
"fund" 市场。但 late settlement 回填场外基金 NAV 时，会用 UPSERT 覆写整个
"fund" 市场的 day_pnl，导致场内 ETF 的日收益被丢弃。

修复：
1. 获取每个用户的场内 ETF 持仓
2. 通过东方财富 API 获取历史日线数据，计算每天的 ETF day_pnl
3. 将 ETF day_pnl 从 "fund" 移到 "a" 市场
4. 同步 daily_snapshots.day_pnl

用法:
    cd /opt/kaka/portfolio/kona_tool
    .venv/bin/python scripts/repair_etf_market_breakdown.py [--days 60] [--user USER_ID] [--dry-run]
"""

import argparse
import os
import re
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("JWT_SECRET", "repair_etf_temp_secret")

from core.trend import _fetch_stock_history_points


def _is_exchange_etf_code(code: str) -> bool:
    """判断是否为场内 ETF 的直接代码（非 f_/ft_ 前缀）。"""
    c = str(code or "").strip().lower()
    if c.startswith(("f_", "ft_")):
        return False
    digits = re.sub(r"^(sh|sz|bj)", "", c)
    if not re.fullmatch(r"\d{6}", digits):
        return False
    # 深市 ETF: 15xxxx, 16xxxx, 18xxxx
    # 沪市 ETF: 50xxxx, 51xxxx, 52xxxx, 56xxxx, 58xxxx
    return digits.startswith(("15", "16", "18", "50", "51", "52", "56", "58"))


def _resolve_secid(code: str) -> str:
    """将场内 ETF 代码转为东方财富 secid。"""
    digits = re.sub(r"^(sh|sz|bj)", "", str(code or "").strip().lower())
    if digits.startswith(("15", "16", "18")):
        return f"0.{digits}"  # 深市
    return f"1.{digits}"  # 沪市


def _fetch_etf_history(code: str, days: int) -> List[Dict[str, Any]]:
    """获取场内 ETF 的历史日线数据。"""
    # 场内 ETF 走股票行情接口，market_hint 用 "fund"
    points = _fetch_stock_history_points(code, days + 5, market_hint="fund")
    return points


def _get_db_path() -> str:
    return str(ROOT / "portfolio.db")


def _get_users_with_exchange_etfs(conn: sqlite3.Connection, user_id: Optional[str] = None) -> Dict[str, List[Dict]]:
    """获取有场内 ETF 持仓的用户及其 ETF 持仓列表。"""
    cursor = conn.cursor()
    sql = "SELECT code, name, qty, price, user_id, asset_type FROM portfolio WHERE asset_type = 'fund' AND qty > 0"
    params: list = []
    if user_id:
        sql += " AND user_id = ?"
        params.append(user_id)

    cursor.execute(sql, params)
    rows = cursor.fetchall()

    result: Dict[str, List[Dict]] = {}
    for row in rows:
        code = str(row[0] or "").strip()
        if not _is_exchange_etf_code(code):
            continue
        uid = str(row[4] or "")
        result.setdefault(uid, []).append({
            "code": code,
            "name": str(row[1] or ""),
            "qty": float(row[2] or 0),
            "cost_price": float(row[3] or 0),
        })
    return result


def _get_qty_history(conn: sqlite3.Connection, user_id: str, code: str) -> List[Tuple[str, float]]:
    """获取持仓数量变动历史，返回 [(date, cumulative_qty_change), ...]。

    用于推算过去某天的实际持仓量。
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT time, type, qty FROM transactions
        WHERE user_id = ? AND code = ?
        ORDER BY time ASC
        """,
        (user_id, code),
    )
    changes: List[Tuple[str, float]] = []
    for row in cursor.fetchall():
        time_str = str(row[0] or "")
        date = time_str[:10] if len(time_str) >= 10 else time_str
        tx_type = str(row[1] or "")
        qty = float(row[2] or 0)
        if "减" in tx_type or "卖" in tx_type:
            qty = -qty
        changes.append((date, qty))
    return changes


def _qty_at_date(current_qty: float, tx_changes: List[Tuple[str, float]], target_date: str) -> float:
    """从当前持仓量和交易记录反推目标日期的持仓量。"""
    qty = current_qty
    # 从最新到最旧，回退 target_date 之后的交易
    for tx_date, change in reversed(tx_changes):
        if tx_date > target_date:
            qty -= change  # 回退：买入回退减少，卖出回退增加
    return max(qty, 0.0)


def _get_current_breakdowns(
    conn: sqlite3.Connection,
    user_id: str,
    start_date: str,
    end_date: str,
) -> Dict[str, Dict[str, Any]]:
    """获取指定日期范围内的现有市场分解数据。"""
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT date, market, day_pnl, source, updated_at
        FROM daily_snapshot_market_breakdowns
        WHERE user_id = ? AND date >= ? AND date <= ?
        ORDER BY date, market
        """,
        (user_id, start_date, end_date),
    )
    result: Dict[str, Dict[str, Any]] = {}
    for row in cursor.fetchall():
        date = str(row[0])
        market = str(row[1])
        entry = result.setdefault(date, {})
        entry[market] = {
            "day_pnl": float(row[2] or 0),
            "source": str(row[3] or ""),
            "updated_at": str(row[4] or ""),
        }
    return result


def _fund_includes_etf(date_str: str, fund_info: Dict[str, Any]) -> bool:
    """判断某日期的 fund 分解是否包含了场内 ETF 的 day_pnl。

    启发式规则：
    - source 为 repair/manual_fix/manual_restore/estimated → 包含 ETF（之前的修复脚本使用旧分类）
    - source 为 exact，且 updated_at 在该日期当天或次日凌晨 → 包含 ETF（原始快照）
    - source 为 exact，但 updated_at 远晚于该日期 → 被 late settlement 覆写，不含 ETF
    - source 为 backfill → 不含 ETF
    """
    source = fund_info.get("source", "")
    updated_at_str = fund_info.get("updated_at", "")

    if source in ("repair", "manual_fix", "manual_restore", "estimated"):
        return True
    if source == "backfill":
        return False

    # source == "exact" or other
    if not updated_at_str or not date_str:
        return True  # 无法判断，假设包含

    try:
        date_dt = datetime.strptime(date_str, "%Y-%m-%d")
        updated_dt = datetime.strptime(updated_at_str[:19], "%Y-%m-%d %H:%M:%S")
        # 如果 updated_at 在日期当天 23:59 之后的 8 小时内（次日 08:00 前），认为是原始快照
        cutoff = date_dt + timedelta(hours=32)
        return updated_dt <= cutoff
    except (ValueError, TypeError):
        return True  # 无法解析，假设包含


def repair_breakdowns(
    *,
    days: int = 60,
    user_id: Optional[str] = None,
    dry_run: bool = False,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """执行修复。"""
    path = db_path or _get_db_path()
    conn = sqlite3.connect(path)
    conn.row_factory = None

    users_etfs = _get_users_with_exchange_etfs(conn, user_id)
    if not users_etfs:
        print("No users with exchange-traded ETF positions found.")
        conn.close()
        return {"users": 0, "dates_fixed": 0}

    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

    total_users = 0
    total_dates_fixed = 0
    total_skipped = 0

    for uid, etf_positions in users_etfs.items():
        print(f"\n=== User: {uid} ===")
        print(f"  Exchange ETFs: {[p['code'] + '(' + p['name'] + ')' for p in etf_positions]}")

        # 获取每个 ETF 的历史数据
        etf_histories: Dict[str, List[Dict[str, Any]]] = {}
        for pos in etf_positions:
            code = pos["code"]
            history = _fetch_etf_history(code, days)
            if history:
                etf_histories[code] = history
                print(f"  {code}: fetched {len(history)} days of history")
            else:
                print(f"  {code}: WARNING - no history data available")

        if not etf_histories:
            print("  Skipping user - no ETF history available")
            continue

        # 获取交易记录（用于反推历史持仓量）
        tx_by_code: Dict[str, List[Tuple[str, float]]] = {}
        for pos in etf_positions:
            tx_by_code[pos["code"]] = _get_qty_history(conn, uid, pos["code"])

        # 获取现有分解数据
        current_breakdowns = _get_current_breakdowns(conn, uid, start_date, end_date)

        # 构建 ETF 日线价格查找表: {code: {date: close}}
        etf_close_by_date: Dict[str, Dict[str, float]] = {}
        for code, history in etf_histories.items():
            date_map = {}
            for point in history:
                date_map[point["date"]] = float(point["value"])
            etf_close_by_date[code] = date_map

        # 对每个有分解记录的日期进行修复
        dates_fixed = 0
        for date_str in sorted(current_breakdowns.keys()):
            if date_str < start_date or date_str > end_date:
                continue

            breakdown = current_breakdowns[date_str]
            if "a" not in breakdown:
                continue  # 没有 A 股分解的日期，跳过

            old_a = breakdown.get("a", {}).get("day_pnl", 0.0)
            old_fund_info = breakdown.get("fund", {})
            old_fund = old_fund_info.get("day_pnl", 0.0)
            old_hk = breakdown.get("hk", {}).get("day_pnl", 0.0)
            old_us = breakdown.get("us", {}).get("day_pnl", 0.0)
            old_unallocated = breakdown.get("unallocated", {}).get("day_pnl", 0.0)
            old_total = old_a + old_fund + old_hk + old_us + old_unallocated

            # 计算该日期的 ETF day_pnl
            etf_day_pnl = 0.0
            etf_details = []
            for pos in etf_positions:
                code = pos["code"]
                closes = etf_close_by_date.get(code, {})
                close_today = closes.get(date_str)
                if close_today is None:
                    continue

                # 找前一个交易日的收盘价
                sorted_dates = sorted(closes.keys())
                idx = sorted_dates.index(date_str) if date_str in sorted_dates else -1
                if idx <= 0:
                    continue
                prev_date = sorted_dates[idx - 1]
                close_prev = closes[prev_date]

                # 反推该日期的持仓量
                qty = _qty_at_date(pos["qty"], tx_by_code.get(code, []), date_str)
                if qty <= 0:
                    continue

                pnl = round((close_today - close_prev) * qty, 2)
                etf_day_pnl += pnl
                etf_details.append(f"{code}: ({close_today:.3f}-{close_prev:.3f})*{qty:.0f}={pnl:.2f}")

            etf_day_pnl = round(etf_day_pnl, 2)

            if abs(etf_day_pnl) < 0.005 and not etf_details:
                continue  # 该日期无 ETF 数据，跳过

            # 判断 fund 分解是否包含 ETF
            includes_etf = _fund_includes_etf(date_str, old_fund_info)

            new_a = round(old_a + etf_day_pnl, 2)
            if includes_etf:
                new_fund = round(old_fund - etf_day_pnl, 2)
            else:
                new_fund = old_fund  # fund 已经是纯场外，不需要减

            new_total = round(new_a + new_fund + old_hk + old_us + old_unallocated, 2)

            # 只在有实际变化时更新
            if abs(new_a - old_a) < 0.005 and abs(new_fund - old_fund) < 0.005:
                continue

            prefix = "[DRY-RUN] " if dry_run else ""
            print(f"  {prefix}{date_str}: ETF_pnl={etf_day_pnl:+.2f} "
                  f"a: {old_a:.2f} → {new_a:.2f}, "
                  f"fund: {old_fund:.2f} → {new_fund:.2f} "
                  f"{'(includes_etf)' if includes_etf else '(overwritten)'} "
                  f"total: {old_total:.2f} → {new_total:.2f}")
            if etf_details:
                print(f"    ETF: {'; '.join(etf_details)}")

            if not dry_run:
                cursor = conn.cursor()
                # 更新 "a" 市场
                cursor.execute(
                    """
                    UPDATE daily_snapshot_market_breakdowns
                    SET day_pnl = ?, source = 'etf_repair', updated_at = datetime('now','localtime')
                    WHERE date = ? AND user_id = ? AND market = 'a'
                    """,
                    (new_a, date_str, uid),
                )
                # 更新 "fund" 市场
                cursor.execute(
                    """
                    UPDATE daily_snapshot_market_breakdowns
                    SET day_pnl = ?, source = 'etf_repair', updated_at = datetime('now','localtime')
                    WHERE date = ? AND user_id = ? AND market = 'fund'
                    """,
                    (new_fund, date_str, uid),
                )
                conn.commit()

                # 同步 ledger_daily_snapshots.day_pnl
                cursor.execute(
                    """
                    UPDATE ledger_daily_snapshots
                    SET day_pnl = (
                        SELECT COALESCE(SUM(day_pnl), 0.0)
                        FROM daily_snapshot_market_breakdowns
                        WHERE date = ? AND user_id = ?
                    )
                    WHERE date = ? AND user_id = ?
                    """,
                    (date_str, uid, date_str, uid),
                )
                conn.commit()

                # 同步 daily_snapshots.day_pnl
                cursor.execute(
                    """
                    UPDATE daily_snapshots
                    SET day_pnl = (
                        SELECT COALESCE(SUM(day_pnl), 0.0)
                        FROM daily_snapshot_market_breakdowns
                        WHERE date = ? AND user_id = ?
                    ),
                    updated_at = datetime('now','localtime')
                    WHERE date = ? AND user_id = ?
                    """,
                    (date_str, uid, date_str, uid),
                )
                conn.commit()

            dates_fixed += 1

        if dates_fixed > 0:
            total_users += 1
            total_dates_fixed += dates_fixed
            print(f"  Fixed {dates_fixed} dates")
        else:
            print("  No dates needed repair")

    conn.close()

    summary = {
        "users": total_users,
        "dates_fixed": total_dates_fixed,
    }
    print(f"\n=== Summary: {total_users} users, {total_dates_fixed} dates fixed ===")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="修复场内 ETF 日历收益的市场归属")
    parser.add_argument("--days", type=int, default=60, help="修复最近 N 天的数据（默认 60）")
    parser.add_argument("--user", type=str, default=None, help="只修复指定用户")
    parser.add_argument("--dry-run", action="store_true", help="只显示变更，不写入数据库")
    parser.add_argument("--db", type=str, default=None, help="数据库路径")
    args = parser.parse_args()

    repair_breakdowns(
        days=args.days,
        user_id=args.user,
        dry_run=args.dry_run,
        db_path=args.db,
    )
