"""数据库结构初始化。

这一层只负责：
- 建表
- 旧库字段补齐
- 基础索引

不负责具体业务查询和写入。
"""

from __future__ import annotations

from typing import Any


class DatabaseSchemaManager:
    """承接 DatabaseManager 的结构初始化和兼容迁移入口。"""

    def initialize(self, *, db_manager: Any, cursor: Any) -> None:
        self._create_tables(cursor)
        self._ensure_legacy_columns(cursor)
        db_manager._ensure_portfolio_user_scoped_unique(cursor)
        db_manager._ensure_users_schema(cursor)
        self._create_base_indexes(cursor)
        db_manager._migrate_portfolio_corrections_schema(cursor)
        db_manager._ensure_daily_snapshots_schema(cursor)
        self._create_snapshot_indexes(cursor)
        db_manager._ensure_portfolio_asset_type(cursor)
        db_manager._ensure_b_share_currency(cursor)
        db_manager._ensure_admin_api_policies_defaults(cursor)
        db_manager._backfill_user_daily_activity(cursor)
        self._ensure_ledger_schema(cursor)

    def _create_tables(self, cursor: Any) -> None:
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS portfolio (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL,
                name TEXT NOT NULL,
                qty REAL NOT NULL,
                price REAL NOT NULL,
                curr TEXT NOT NULL DEFAULT 'CNY',
                adjustment REAL DEFAULT 0.0,
                asset_type TEXT DEFAULT 'a',
                user_id TEXT NOT NULL DEFAULT '',
                created_at TIMESTAMP DEFAULT (datetime('now','localtime')),
                updated_at TIMESTAMP DEFAULT (datetime('now','localtime'))
            )
        '''
        )
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                time TEXT NOT NULL,
                code TEXT NOT NULL,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                price REAL NOT NULL,
                qty REAL NOT NULL,
                amount REAL NOT NULL,
                pnl REAL DEFAULT 0.0,
                user_id TEXT,
                created_at TIMESTAMP DEFAULT (datetime('now','localtime'))
            )
        '''
        )
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS cash_assets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                icon TEXT NOT NULL DEFAULT '🏦',
                name TEXT NOT NULL,
                amount REAL NOT NULL,
                curr TEXT NOT NULL DEFAULT 'CNY',
                user_id TEXT,
                created_at TIMESTAMP DEFAULT (datetime('now','localtime')),
                updated_at TIMESTAMP DEFAULT (datetime('now','localtime'))
            )
        '''
        )
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS other_assets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                icon TEXT NOT NULL DEFAULT '📦',
                name TEXT NOT NULL,
                amount REAL NOT NULL,
                curr TEXT NOT NULL DEFAULT 'CNY',
                user_id TEXT,
                created_at TIMESTAMP DEFAULT (datetime('now','localtime')),
                updated_at TIMESTAMP DEFAULT (datetime('now','localtime'))
            )
        '''
        )
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS liabilities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                icon TEXT NOT NULL DEFAULT '💳',
                name TEXT NOT NULL,
                amount REAL NOT NULL,
                curr TEXT NOT NULL DEFAULT 'CNY',
                user_id TEXT,
                created_at TIMESTAMP DEFAULT (datetime('now','localtime')),
                updated_at TIMESTAMP DEFAULT (datetime('now','localtime'))
            )
        '''
        )
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT,
                legacy_needs_password_setup INTEGER NOT NULL DEFAULT 0,
                must_change_password INTEGER NOT NULL DEFAULT 0,
                password_updated_at TIMESTAMP,
                password_reset_at TIMESTAMP,
                password_reset_by TEXT,
                nickname TEXT,
                avatar TEXT,
                register_method TEXT,
                phone TEXT,
                user_number INTEGER,
                ai_credits_balance INTEGER NOT NULL DEFAULT 0,
                is_admin INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'active',
                created_at TIMESTAMP DEFAULT (datetime('now','localtime')),
                build_start_at TIMESTAMP,
                last_login TIMESTAMP,
                last_login_ip TEXT,
                last_login_region TEXT,
                last_active_ip TEXT,
                last_active_region TEXT,
                last_active_at TIMESTAMP
            )
        '''
        )
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS ai_credit_ledger (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                delta INTEGER NOT NULL,
                balance_after INTEGER NOT NULL,
                reason TEXT NOT NULL,
                source TEXT NOT NULL,
                request_id TEXT,
                operator_user_id TEXT,
                created_at TIMESTAMP DEFAULT (datetime('now','localtime'))
            )
        '''
        )
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS admin_audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                admin_user_id TEXT NOT NULL,
                action TEXT NOT NULL,
                target_type TEXT,
                target_id TEXT,
                method TEXT NOT NULL,
                path TEXT NOT NULL,
                ip TEXT,
                request_body TEXT,
                status_code INTEGER NOT NULL,
                result TEXT NOT NULL,
                error TEXT,
                created_at TIMESTAMP DEFAULT (datetime('now','localtime'))
            )
        '''
        )
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS invite_codes (
                code TEXT PRIMARY KEY,
                batch_id TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                created_by TEXT,
                created_at TIMESTAMP DEFAULT (datetime('now','localtime')),
                used_by_user_id TEXT,
                used_at TIMESTAMP,
                note TEXT
            )
        '''
        )
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS auth_refresh_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                token_hash TEXT UNIQUE NOT NULL,
                device_id TEXT,
                issued_at TIMESTAMP NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                revoked_at TIMESTAMP,
                last_used_at TIMESTAMP
            )
        '''
        )
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS runtime_configs (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_by TEXT,
                updated_at TIMESTAMP DEFAULT (datetime('now','localtime'))
            )
        '''
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS admin_api_policies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scope_key TEXT UNIQUE NOT NULL,
                scope_type TEXT NOT NULL,
                enabled INTEGER NOT NULL DEFAULT 1,
                limit_per_min INTEGER,
                note TEXT,
                updated_by TEXT,
                updated_at TIMESTAMP DEFAULT (datetime('now','localtime'))
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS price_alert_reports (
                report_date TEXT PRIMARY KEY,
                tested_at_utc TEXT NOT NULL,
                total_assets INTEGER NOT NULL DEFAULT 0,
                alert_count INTEGER NOT NULL DEFAULT 0,
                summary_json TEXT NOT NULL DEFAULT '{}',
                items_json TEXT NOT NULL DEFAULT '[]',
                updated_at TIMESTAMP DEFAULT (datetime('now','localtime'))
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS provider_test_reports (
                report_slot TEXT PRIMARY KEY,
                tested_at_utc TEXT NOT NULL,
                summary_json TEXT NOT NULL DEFAULT '{}',
                providers_json TEXT NOT NULL DEFAULT '{}',
                updated_at TIMESTAMP DEFAULT (datetime('now','localtime'))
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS user_daily_activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                activity_date TEXT NOT NULL,
                first_seen_at TIMESTAMP DEFAULT (datetime('now','localtime')),
                last_seen_at TIMESTAMP DEFAULT (datetime('now','localtime')),
                UNIQUE(user_id, activity_date)
            )
            """
        )
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS daily_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                total_asset REAL NOT NULL,
                total_invest REAL NOT NULL,
                total_cash REAL NOT NULL,
                total_other REAL NOT NULL,
                total_liability REAL NOT NULL,
                total_pnl REAL NOT NULL,
                day_pnl REAL NOT NULL,
                user_id TEXT NOT NULL DEFAULT '',
                updated_at TIMESTAMP DEFAULT (datetime('now','localtime')),
                UNIQUE(date, user_id)
            )
        '''
        )
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS daily_snapshot_market_breakdowns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                user_id TEXT NOT NULL DEFAULT '',
                market TEXT NOT NULL,
                day_pnl REAL NOT NULL,
                source TEXT NOT NULL DEFAULT 'exact',
                confidence REAL NOT NULL DEFAULT 1.0,
                meta_json TEXT,
                updated_at TIMESTAMP DEFAULT (datetime('now','localtime')),
                UNIQUE(date, user_id, market)
            )
        '''
        )
        cursor.execute(
            '''
            CREATE TABLE IF NOT EXISTS asset_adjustments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_type TEXT NOT NULL,
                asset_id INTEGER NOT NULL,
                mode TEXT NOT NULL,
                delta REAL NOT NULL,
                note TEXT NOT NULL DEFAULT '',
                balance_after REAL NOT NULL,
                user_id TEXT,
                created_at TIMESTAMP DEFAULT (datetime('now','localtime'))
            )
        '''
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS portfolio_adjustment_ledger (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL DEFAULT '',
                code TEXT NOT NULL,
                event_type TEXT NOT NULL,
                amount REAL NOT NULL,
                curr TEXT NOT NULL DEFAULT 'CNY',
                note TEXT NOT NULL DEFAULT '',
                source TEXT NOT NULL DEFAULT 'manual',
                related_tx_id INTEGER,
                created_at TIMESTAMP DEFAULT (datetime('now','localtime')),
                updated_at TIMESTAMP DEFAULT (datetime('now','localtime'))
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS portfolio_correction_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL DEFAULT '',
                code TEXT NOT NULL,
                correction_type TEXT NOT NULL,
                before_qty REAL,
                after_qty REAL,
                before_price REAL,
                after_price REAL,
                note TEXT NOT NULL DEFAULT '',
                legacy_ledger_id INTEGER,
                created_at TIMESTAMP DEFAULT (datetime('now','localtime')),
                updated_at TIMESTAMP DEFAULT (datetime('now','localtime'))
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS portfolio_legacy_adjustment_states (
                user_id TEXT PRIMARY KEY,
                ignore_legacy_adjustment INTEGER NOT NULL DEFAULT 0,
                note TEXT NOT NULL DEFAULT '',
                updated_at TIMESTAMP DEFAULT (datetime('now','localtime'))
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS investment_ledgers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT DEFAULT '',
                sort_order INTEGER DEFAULT 0,
                is_default INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT (datetime('now','localtime')),
                updated_at TIMESTAMP DEFAULT (datetime('now','localtime')),
                UNIQUE(user_id, name)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS ledger_daily_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                ledger_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                total_market_value REAL DEFAULT 0,
                total_cost REAL DEFAULT 0,
                total_pnl REAL DEFAULT 0,
                total_pnl_rate REAL DEFAULT 0,
                day_pnl REAL DEFAULT 0,
                holdings_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT (datetime('now','localtime')),
                UNIQUE(user_id, ledger_id, date),
                FOREIGN KEY (ledger_id) REFERENCES investment_ledgers(id)
            )
            """
        )

    def _ensure_legacy_columns(self, cursor: Any) -> None:
        def _ensure_column(table: str, column: str, col_def: str) -> None:
            cursor.execute(f"PRAGMA table_info({table})")
            cols = [row[1] for row in cursor.fetchall()]
            if column not in cols:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col_def}")

        _ensure_column("portfolio", "user_id", "user_id TEXT NOT NULL DEFAULT ''")
        _ensure_column("portfolio", "logo_url", "logo_url TEXT")
        _ensure_column("transactions", "user_id", "user_id TEXT")
        _ensure_column("transactions", "curr", "curr TEXT")
        _ensure_column("transactions", "market", "market TEXT")
        _ensure_column("transactions", "effective_date", "effective_date TEXT")
        _ensure_column("cash_assets", "user_id", "user_id TEXT")
        _ensure_column("other_assets", "user_id", "user_id TEXT")
        _ensure_column("liabilities", "user_id", "user_id TEXT")
        _ensure_column("cash_assets", "icon", "icon TEXT NOT NULL DEFAULT '🏦'")
        _ensure_column("other_assets", "icon", "icon TEXT NOT NULL DEFAULT '📦'")
        _ensure_column("liabilities", "icon", "icon TEXT NOT NULL DEFAULT '💳'")
        _ensure_column("cash_assets", "curr", "curr TEXT NOT NULL DEFAULT 'CNY'")
        _ensure_column("other_assets", "curr", "curr TEXT NOT NULL DEFAULT 'CNY'")
        _ensure_column("liabilities", "curr", "curr TEXT NOT NULL DEFAULT 'CNY'")
        _ensure_column("cash_assets", "created_at", "created_at TIMESTAMP DEFAULT (datetime('now','localtime'))")
        _ensure_column("cash_assets", "updated_at", "updated_at TIMESTAMP DEFAULT (datetime('now','localtime'))")
        _ensure_column("other_assets", "created_at", "created_at TIMESTAMP DEFAULT (datetime('now','localtime'))")
        _ensure_column("other_assets", "updated_at", "updated_at TIMESTAMP DEFAULT (datetime('now','localtime'))")
        _ensure_column("liabilities", "created_at", "created_at TIMESTAMP DEFAULT (datetime('now','localtime'))")
        _ensure_column("liabilities", "updated_at", "updated_at TIMESTAMP DEFAULT (datetime('now','localtime'))")
        _ensure_column("daily_snapshots", "user_id", "user_id TEXT DEFAULT ''")
        _ensure_column("daily_snapshot_market_breakdowns", "user_id", "user_id TEXT DEFAULT ''")
        _ensure_column("daily_snapshot_market_breakdowns", "source", "source TEXT NOT NULL DEFAULT 'exact'")
        _ensure_column("daily_snapshot_market_breakdowns", "confidence", "confidence REAL NOT NULL DEFAULT 1.0")
        _ensure_column("daily_snapshot_market_breakdowns", "meta_json", "meta_json TEXT")
        _ensure_column(
            "daily_snapshot_market_breakdowns",
            "updated_at",
            "updated_at TIMESTAMP DEFAULT (datetime('now','localtime'))",
        )

    def _create_base_indexes(self, cursor: Any) -> None:
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_portfolio_user_id ON portfolio(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_portfolio_code ON portfolio(code)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_code ON transactions(code)")
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_transactions_user_effective_date"
            " ON transactions(user_id, effective_date)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_transactions_user_market_effective_date"
            " ON transactions(user_id, market, effective_date)"
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cash_assets_user_id ON cash_assets(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_other_assets_user_id ON other_assets(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_liabilities_user_id ON liabilities(user_id)")
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_ai_credit_ledger_user_created ON ai_credit_ledger(user_id, created_at DESC)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_ai_credit_ledger_request_id ON ai_credit_ledger(request_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_asset_adjustments_asset"
            " ON asset_adjustments(asset_type, asset_id, user_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_portfolio_adjustment_ledger_user_code"
            " ON portfolio_adjustment_ledger(user_id, code)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_portfolio_adjustment_ledger_user_created"
            " ON portfolio_adjustment_ledger(user_id, created_at DESC)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_portfolio_adjustment_ledger_related_tx"
            " ON portfolio_adjustment_ledger(related_tx_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_portfolio_correction_logs_user_code"
            " ON portfolio_correction_logs(user_id, code)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_portfolio_correction_logs_user_created"
            " ON portfolio_correction_logs(user_id, created_at DESC)"
        )
        cursor.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_portfolio_correction_logs_legacy_ledger"
            " ON portfolio_correction_logs(legacy_ledger_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_portfolio_legacy_adjustment_states_ignore"
            " ON portfolio_legacy_adjustment_states(ignore_legacy_adjustment)"
        )

    def _create_snapshot_indexes(self, cursor: Any) -> None:
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_daily_snapshots_date ON daily_snapshots(date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_daily_snapshots_user_id ON daily_snapshots(user_id)")
        cursor.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_daily_snapshots_date_user_unique ON daily_snapshots(date, user_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_daily_snapshots_user_date_id ON daily_snapshots(user_id, date DESC, id DESC)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_market_breakdowns_user_date ON daily_snapshot_market_breakdowns(user_id, date)"
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_market_breakdowns_date ON daily_snapshot_market_breakdowns(date)")
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_market_breakdowns_source ON daily_snapshot_market_breakdowns(source)"
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_admin_audit_logs_admin_user_id ON admin_audit_logs(admin_user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_admin_audit_logs_created_at ON admin_audit_logs(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_admin_audit_logs_action ON admin_audit_logs(action)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_invite_codes_status ON invite_codes(status)")
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_invite_codes_status_created_code ON invite_codes(status, created_at DESC, code ASC)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_invite_codes_created_code ON invite_codes(created_at DESC, code ASC)"
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_invite_codes_batch_id ON invite_codes(batch_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_auth_refresh_tokens_user_id ON auth_refresh_tokens(user_id)")
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_auth_refresh_tokens_expires_at ON auth_refresh_tokens(expires_at)"
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_runtime_configs_updated_at ON runtime_configs(updated_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_admin_api_policies_scope_type ON admin_api_policies(scope_type)")
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_price_alert_reports_tested_at ON price_alert_reports(tested_at_utc)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_provider_test_reports_tested_at ON provider_test_reports(tested_at_utc)"
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_daily_activity_date ON user_daily_activity(activity_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_daily_activity_user_id ON user_daily_activity(user_id)")
        cursor.execute("DROP TABLE IF EXISTS email_verification_codes")
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_investment_ledgers_user_id ON investment_ledgers(user_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_ledger_daily_snapshots_user_ledger_date"
            " ON ledger_daily_snapshots(user_id, ledger_id, date)"
        )

    def _ensure_ledger_schema(self, cursor: Any) -> None:
        """多账本迁移：为现有表添加 ledger_id 列，为现有用户创建默认账本。"""

        def _has_column(table: str, column: str) -> bool:
            cursor.execute(f"PRAGMA table_info({table})")
            return column in [row[1] for row in cursor.fetchall()]

        if not _has_column("portfolio", "ledger_id"):
            # 1. 为每个现有用户创建默认账本
            cursor.execute(
                "SELECT DISTINCT user_id FROM portfolio WHERE COALESCE(user_id, '') != ''"
            )
            user_ids = [row[0] for row in cursor.fetchall()]
            for uid in user_ids:
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO investment_ledgers (user_id, name, is_default, sort_order)
                    VALUES (?, '默认账本', 1, 0)
                    """,
                    (uid,),
                )

            # 2. 为四张表添加 ledger_id 列
            for table in ("portfolio", "transactions", "portfolio_adjustment_ledger", "portfolio_correction_logs"):
                cursor.execute(
                    f"ALTER TABLE {table} ADD COLUMN ledger_id INTEGER NOT NULL DEFAULT 0"
                )

            # 3. 将现有数据的 ledger_id 更新为对应用户的默认账本 ID
            for uid in user_ids:
                cursor.execute(
                    "SELECT id FROM investment_ledgers WHERE user_id = ? AND is_default = 1",
                    (uid,),
                )
                row = cursor.fetchone()
                if row:
                    ledger_id = row[0]
                    for table in ("portfolio", "transactions", "portfolio_adjustment_ledger", "portfolio_correction_logs"):
                        user_col_condition = "user_id = ?" if table != "transactions" else "user_id = ?"
                        cursor.execute(
                            f"UPDATE {table} SET ledger_id = ? WHERE {user_col_condition}",
                            (ledger_id, uid),
                        )

        # 4. 无论是不是老库，都要确保旧唯一索引不会被重新建回来
        cursor.execute("DROP INDEX IF EXISTS idx_portfolio_code_user_unique")
        cursor.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_portfolio_code_user_ledger_unique"
            " ON portfolio(code, user_id, ledger_id)"
        )

        # 5. 为新列添加索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_portfolio_ledger_id ON portfolio(ledger_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_ledger_id ON transactions(ledger_id)")
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_portfolio_adjustment_ledger_ledger_id"
            " ON portfolio_adjustment_ledger(ledger_id)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_portfolio_correction_logs_ledger_id"
            " ON portfolio_correction_logs(ledger_id)"
        )
