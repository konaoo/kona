#!/usr/bin/env python3
"""
一次性迁移脚本：修正历史快照中因错误汇率（7.25）导致的偏差。

使用方法：
    cd /path/to/kona_tool
    python3 fix_snapshot_rates.py [--dry-run]

原理：
    1. 查出所有 USD/HKD 持仓（portfolio 表中 curr != 'CNY'）
    2. 对每条历史快照，计算外币资产在 total_pnl 和 total_invest 中的占比
    3. 把外币部分从旧汇率还原为原始币种金额，再乘以当天的真实汇率
    4. day_pnl 同理修正
    5. 写回数据库
"""
import sys
import os
import sqlite3
import json
import logging
from datetime import datetime, timedelta

# 把项目根目录加入路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ── 配置 ──────────────────────────────────────────────
OLD_USD_RATE = 7.25   # 之前新浪挂了之后一直在用的默认值
OLD_HKD_RATE = 0.93

DRY_RUN = "--dry-run" in sys.argv


def fetch_historical_rates(dates):
    """
    获取指定日期列表的真实 USD/CNY 汇率。
    使用 exchangerate-api.com，该 API 只提供当日汇率，
    由于历史区间很短（2.4 ~ 2.27），直接用当前汇率作为修正基准。
    如果需要更精确，可接入付费历史汇率 API。
    """
    import requests
    try:
        r = requests.get("https://open.er-api.com/v6/latest/USD", timeout=10)
        data = r.json()
        if data.get("result") == "success":
            cny = float(data["rates"].get("CNY", 6.85))
            hkd_per_usd = float(data["rates"].get("HKD", 7.82))
            hkd_to_cny = cny / hkd_per_usd if hkd_per_usd > 0 else 0.88
            logger.info(f"当前实时汇率: USD/CNY={cny}, HKD/CNY={round(hkd_to_cny, 4)}")
            # 2月4日到2月27日汇率波动很小，统一用当前值
            return {d: {"USD": round(cny, 4), "HKD": round(hkd_to_cny, 4)} for d in dates}
    except Exception as e:
        logger.error(f"获取汇率失败: {e}")

    # 兜底
    logger.warning("使用兜底汇率 USD=7.0, HKD=0.9")
    return {d: {"USD": 7.0, "HKD": 0.9} for d in dates}


def get_foreign_asset_pnl_ratio(conn):
    """
    计算外币资产在投资组合中的盈亏占比。
    返回 {curr: 该币种盈亏占总盈亏的比例} 和 {curr: 该币种市值占总市值的比例}
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT code, qty, price, curr, adjustment
        FROM portfolio
        WHERE curr IS NOT NULL AND curr != ''
    """)
    rows = cursor.fetchall()

    pnl_by_curr = {}  # curr -> pnl (用旧汇率算的 CNY 值)
    mv_by_curr = {}   # curr -> mv (用旧汇率算的 CNY 值)

    for code, qty, cost_price, curr, adj in rows:
        curr = (curr or "CNY").upper()
        adj = float(adj or 0)
        qty = float(qty or 0)
        cost_price = float(cost_price or 0)

        old_rate = OLD_USD_RATE if curr == "USD" else (OLD_HKD_RATE if curr == "HKD" else 1.0)

        # 用成本价作为近似（我们没有每天的实时价格）
        # 对于 total_pnl 的比例拆分足够了
        item_mv = cost_price * qty * old_rate
        item_pnl = adj * old_rate  # adjustment 是累计已实现盈亏

        pnl_by_curr[curr] = pnl_by_curr.get(curr, 0) + item_pnl
        mv_by_curr[curr] = mv_by_curr.get(curr, 0) + item_mv

    return pnl_by_curr, mv_by_curr


def fix_snapshots():
    db_path = str(config.DATABASE_PATH)
    logger.info(f"数据库路径: {db_path}")
    conn = sqlite3.connect(db_path)

    # 1. 查出所有用户
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT user_id FROM daily_snapshots")
    user_ids = [row[0] for row in cursor.fetchall()]
    logger.info(f"找到 {len(user_ids)} 个用户的快照数据")

    for uid in user_ids:
        uid_display = uid or "(默认用户)"
        logger.info(f"\n{'='*50}")
        logger.info(f"处理用户: {uid_display}")

        # 2. 查出该用户所有快照
        cursor.execute("""
            SELECT date, total_invest, total_pnl, day_pnl, total_asset,
                   total_cash, total_other, total_liability
            FROM daily_snapshots
            WHERE user_id = ?
            ORDER BY date
        """, (uid or '',))
        snapshots = cursor.fetchall()
        if not snapshots:
            logger.info("  无快照数据，跳过")
            continue

        dates = [row[0] for row in snapshots]
        logger.info(f"  快照范围: {dates[0]} ~ {dates[-1]}，共 {len(snapshots)} 条")

        # 3. 获取真实汇率
        real_rates = fetch_historical_rates(dates)

        # 4. 查出该用户的外币资产
        cursor.execute("""
            SELECT code, qty, price, curr, adjustment
            FROM portfolio
            WHERE (user_id = ? OR (user_id IS NULL AND ? = ''))
              AND curr IS NOT NULL AND curr != '' AND UPPER(curr) != 'CNY'
        """, (uid or '', uid or ''))
        foreign_assets = cursor.fetchall()

        if not foreign_assets:
            logger.info("  无外币资产，无需修正")
            continue

        # 计算外币资产的 PnL 和 MV 在旧汇率下的值
        foreign_pnl_old_rate = 0.0   # 外币 adjustment 在旧汇率下的 CNY 值
        foreign_mv_old_rate = 0.0    # 外币市值在旧汇率下的 CNY 值

        # 记录每个币种的资产
        asset_detail = {}
        for code, qty, cost_price, curr, adj in foreign_assets:
            curr = (curr or "USD").upper()
            qty = float(qty or 0)
            cost_price = float(cost_price or 0)
            adj = float(adj or 0)
            old_rate = OLD_USD_RATE if curr == "USD" else (OLD_HKD_RATE if curr == "HKD" else 1.0)

            mv_old = cost_price * qty * old_rate
            foreign_mv_old_rate += mv_old

            if curr not in asset_detail:
                asset_detail[curr] = {"codes": [], "old_rate": old_rate}
            asset_detail[curr]["codes"].append(code)

        logger.info(f"  外币资产: {', '.join(f'{k}({len(v[\"codes\"])}只)' for k, v in asset_detail.items())}")

        # 5. 查出总市值用于计算外币占比
        # 由于我们不知道每天的具体价格，使用一个近似方法：
        # 假设每条快照中外币市值占比 ≈ 当前外币持仓成本占总投资的比例
        cursor.execute("""
            SELECT SUM(price * qty * CASE
                WHEN UPPER(curr) = 'USD' THEN ?
                WHEN UPPER(curr) = 'HKD' THEN ?
                ELSE 1.0
            END)
            FROM portfolio
            WHERE (user_id = ? OR (user_id IS NULL AND ? = ''))
        """, (OLD_USD_RATE, OLD_HKD_RATE, uid or '', uid or ''))
        total_cost_old = float(cursor.fetchone()[0] or 0)

        if total_cost_old <= 0:
            logger.info("  总持仓成本为 0，跳过")
            continue

        # 外币占比
        foreign_ratio = foreign_mv_old_rate / total_cost_old if total_cost_old > 0 else 0
        cny_ratio = 1 - foreign_ratio
        logger.info(f"  外币占比: {foreign_ratio:.2%}，CNY 占比: {cny_ratio:.2%}")

        # 6. 逐条修正
        updates = []
        for row in snapshots:
            date_str = row[0]
            old_invest = float(row[1] or 0)
            old_total_pnl = float(row[2] or 0)
            old_day_pnl = float(row[3] or 0)
            old_total_asset = float(row[4] or 0)
            total_cash = float(row[5] or 0)
            total_other = float(row[6] or 0)
            total_liability = float(row[7] or 0)

            day_rates = real_rates.get(date_str, {"USD": 7.0, "HKD": 0.9})

            # 对每个外币币种应用修正
            # 简化处理：所有外币资产统一用 USD 汇率（因为主要外币资产是 USD）
            primary_curr = "USD"  # 如有多币种可扩展
            new_rate = day_rates.get(primary_curr, 7.0)
            old_rate = OLD_USD_RATE

            rate_factor = new_rate / old_rate  # 修正系数

            # 修正公式：CNY 部分不变 + 外币部分 × 修正系数
            new_invest = old_invest * cny_ratio + old_invest * foreign_ratio * rate_factor
            new_total_pnl = old_total_pnl * cny_ratio + old_total_pnl * foreign_ratio * rate_factor
            new_day_pnl = old_day_pnl * cny_ratio + old_day_pnl * foreign_ratio * rate_factor
            new_total_asset = total_cash + new_invest + total_other - total_liability

            updates.append((
                round(new_invest, 2),
                round(new_total_pnl, 2),
                round(new_day_pnl, 2),
                round(new_total_asset, 2),
                date_str,
                uid or '',
            ))

            if old_invest != round(new_invest, 2):
                logger.info(
                    f"  {date_str}: invest {old_invest:.0f} → {new_invest:.0f}, "
                    f"pnl {old_total_pnl:.0f} → {new_total_pnl:.0f}, "
                    f"day_pnl {old_day_pnl:.0f} → {new_day_pnl:.0f}"
                )

        # 7. 写回
        if DRY_RUN:
            logger.info(f"  [DRY RUN] 跳过写入，共 {len(updates)} 条")
        else:
            cursor.executemany("""
                UPDATE daily_snapshots
                SET total_invest = ?,
                    total_pnl = ?,
                    day_pnl = ?,
                    total_asset = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE date = ? AND user_id = ?
            """, updates)
            conn.commit()
            logger.info(f"  ✅ 已修正 {len(updates)} 条快照")

    conn.close()
    logger.info("\n完成！")


if __name__ == "__main__":
    if DRY_RUN:
        logger.info("=" * 50)
        logger.info("DRY RUN 模式 - 不会写入数据库")
        logger.info("=" * 50)
    fix_snapshots()
