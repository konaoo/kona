"""
主程序文件
整合所有功能，提供Web API
"""
import logging
import threading
import webbrowser
import time
from flask import Flask, render_template, jsonify, request, make_response, send_file, g
from pathlib import Path
import os

import config
from core.db import DatabaseManager
from core.price import get_price, batch_get_prices, get_forex_rates, search_stocks
from core.parser import parse_code, get_display_code
from core.asset_type import infer_asset_type
from core.snapshot import take_snapshot, calculate_portfolio_stats, is_market_closed, is_weekend
from core.news import news_fetcher
from core.system import system_manager
from core.auth import login_required, optional_auth, generate_token, get_or_create_user, get_user_profile
from core.email import send_verification_email
import random
import re
from datetime import datetime, timedelta

# 邮箱验证码缓存（内存）
_EMAIL_CODE_STORE = {}

def _generate_code() -> str:
    return f"{random.randint(0, 999999):06d}"

def _store_code(email: str, code: str):
    _EMAIL_CODE_STORE[email] = {
        "code": code,
        "expires": datetime.utcnow() + timedelta(minutes=10),
        "last_send": datetime.utcnow(),
    }

def _verify_code(email: str, code: str) -> bool:
    info = _EMAIL_CODE_STORE.get(email)
    if not info:
        return False
    if datetime.utcnow() > info["expires"]:
        _EMAIL_CODE_STORE.pop(email, None)
        return False
    if info["code"] != code:
        return False
    _EMAIL_CODE_STORE.pop(email, None)
    return True

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format=config.LOG_FORMAT,
    handlers=[
        logging.FileHandler(config.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
db = DatabaseManager(str(config.DATABASE_PATH))

# 应用版本号，用于强制刷新缓存
APP_VERSION = config.APP_VERSION

# 初始化数据库（从CSV导入备份数据）
if not config.DATABASE_PATH.exists() and config.BACKUP_CSV_PATH.exists():
    logger.info("Importing backup data from CSV...")
    db.backup_from_csv(str(config.BACKUP_CSV_PATH))


def open_browser():
    """自动打开浏览器"""
    time.sleep(1.5)
    webbrowser.open(f'http://{config.HOST}:{config.PORT}')


@app.route('/')
def index():
    """主页 - 我的投资"""
    response = make_response(render_template('investment.html', version=APP_VERSION))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    response.headers['X-App-Version'] = APP_VERSION
    return response


@app.route('/assets')
def assets():
    """我的资产页面"""
    response = make_response(render_template('assets.html', version=APP_VERSION))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    response.headers['X-App-Version'] = APP_VERSION
    return response


@app.route('/test')
def test_page():
    """测试页面"""
    return make_response(render_template('test_api.html'))


@app.route('/compare')
def compare_page():
    """主页面JavaScript测试"""
    with open(config.BASE_DIR / 'static_compare.html', 'r', encoding='utf-8') as f:
        return f.read()


@app.route('/direct_test')
def direct_test_page():
    """直接测试页面"""
    with open(config.BASE_DIR / 'direct_test.html', 'r', encoding='utf-8') as f:
        return f.read()
 


@app.route('/api/price')
def api_price():
    """获取单个价格"""
    code = request.args.get('code', '')
    if not code:
        return jsonify({"error": "Missing code"}), 400
    
    price, yclose, amt, chg = get_price(code)
    
    return jsonify({
        "price": price,
        "yclose": yclose,
        "amt": amt,
        "chg": chg
    })


@app.route('/api/prices/batch', methods=['POST'])
def api_prices_batch():
    """批量获取价格"""
    data = request.json
    codes = data.get('codes', [])
    
    if not codes:
        return jsonify({"error": "Missing codes"}), 400
    
    results = batch_get_prices(codes)
    
    # 将元组转换为对象，便于前端使用
    formatted_results = {}
    for code, (price, yclose, amt, chg) in results.items():
        formatted_results[code] = {
            "price": price,
            "yclose": yclose,
            "amt": amt,
            "chg": chg
        }
    
    return jsonify(formatted_results)


@app.route('/api/rates')
def api_rates():
    """获取汇率"""
    rates = get_forex_rates()
    return jsonify(rates)


@app.route('/api/portfolio', methods=['GET'])
@optional_auth
def get_portfolio():
    """获取持仓数据，支持按类型筛选"""
    asset_type = request.args.get('type', 'all')
    user_id = g.user_id  # 从认证中间件获取
    logger.info(f"API: get_portfolio called with type={asset_type}, user_id={user_id}")
    data = db.get_portfolio(asset_type, user_id)
    logger.info(f"API: returning {len(data)} records")
    response = jsonify(data)
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0, private'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    response.headers['Vary'] = '*'
    return response


@app.route('/api/portfolio/add', methods=['POST'])
@optional_auth
def add_asset():
    """添加资产"""
    data = request.json
    user_id = g.user_id
    
    if not data or 'code' not in data or 'qty' not in data or 'price' not in data:
        return jsonify({"error": "Missing required fields"}), 400
    
    # 解析代码
    parsed = parse_code(data['code'], data.get('curr', ''))
    data['code'] = parsed['code']
    data['curr'] = parsed['curr']
    data['name'] = data.get('name', parsed['code'])
    data['adjustment'] = data.get('adjustment', 0.0)
    # 资产类型（基金/港股/美股/A股）
    provided_type = data.get('asset_type', '').strip()
    inferred_type = infer_asset_type(data['code'], data.get('name', ''))
    if not provided_type:
        data['asset_type'] = inferred_type
    else:
        data['asset_type'] = inferred_type if (provided_type == 'us' and inferred_type == 'fund') else provided_type
    
    success = db.add_asset(data, user_id)
    
    if success:
        _save_snapshot_for_user(user_id)
        return jsonify({"status": "ok"})
    else:
        return jsonify({"error": "Failed to add asset"}), 500


@app.route('/api/portfolio/update', methods=['POST'])
@optional_auth
def update_asset():
    """更新资产"""
    data = request.json
    user_id = g.user_id
    
    if not data or 'code' not in data or 'field' not in data or 'val' not in data:
        return jsonify({"error": "Missing required fields"}), 400
    
    try:
        val = float(data['val'])
        success = db.update_asset(data['code'], data['field'], val, user_id)
        
        if success:
            _save_snapshot_for_user(user_id)
            return jsonify({"status": "ok"})
        else:
            return jsonify({"error": "Asset not found"}), 404
    except ValueError:
        return jsonify({"error": "Invalid value"}), 400


@app.route('/analysis')
def analysis():
    """资产分析页面"""
    return make_response(render_template('analysis.html', version=APP_VERSION))


@app.route('/news')
def news_page():
    """市场快讯页面"""
    return make_response(render_template('news.html', version=APP_VERSION))


@app.route('/settings')
def settings_page():
    """设置页面"""
    return make_response(render_template('settings.html', version=APP_VERSION))


@app.route('/api/settings/info')
def get_system_info():
    """获取系统版本信息"""
    info = system_manager.get_version_info()
    return jsonify(info)


@app.route('/api/settings/check_api')
def check_api_status():
    """检测API状态"""
    status = system_manager.check_api_status()
    return jsonify(status)


@app.route('/api/settings/backup')
def backup_database():
    """下载数据库备份"""
    if config.DATABASE_PATH.exists():
        return send_file(
            config.DATABASE_PATH,
            as_attachment=True,
            download_name=f"portfolio_backup_{int(time.time())}.db",
            mimetype='application/x-sqlite3'
        )
    return jsonify({"error": "Database not found"}), 404


@app.route('/api/settings/restore', methods=['POST'])
def restore_database():
    """恢复数据库"""
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
        
    # 保存到临时文件
    temp_path = config.BASE_DIR / "temp_restore.db"
    try:
        file.save(temp_path)
        
        # 执行恢复
        success = system_manager.restore_database(str(temp_path))
        
        if success:
            return jsonify({"status": "ok", "message": "Restore successful"})
        else:
            return jsonify({"error": "Restore failed or invalid file"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        # 清理临时文件
        if temp_path.exists():
            try:
                os.remove(temp_path)
            except:
                pass


@app.route('/api/news/latest')
def get_latest_news():
    """获取最新快讯 API"""
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 30, type=int)
    data = news_fetcher.fetch_latest(page=page, page_size=page_size)
    return jsonify({
        "items": data,
        "page": page,
        "page_size": page_size,
        "has_more": len(data) >= page_size
    })


@app.route('/api/history')
@optional_auth
def get_history():
    """获取历史资产数据"""
    days = request.args.get('days', 365, type=int)
    user_id = g.user_id
    history = db.get_history(days, user_id)
    return jsonify(history)


@app.route('/api/portfolio/modify', methods=['POST'])
@optional_auth
def modify_asset():
    """修正资产（数量、成本、调整值）"""
    data = request.json
    user_id = g.user_id
    
    if not data or 'code' not in data or 'qty' not in data or 'price' not in data or 'adjustment' not in data:
        return jsonify({"error": "Missing required fields"}), 400
    
    try:
        qty = float(data['qty'])
        price = float(data['price'])
        adjustment = float(data['adjustment'])
        
        success = db.modify_asset(data['code'], qty, price, adjustment, user_id)
        
        if success:
            _save_snapshot_for_user(user_id)
            return jsonify({"status": "ok"})
        else:
            return jsonify({"error": "Asset not found"}), 404
    except ValueError:
        return jsonify({"error": "Invalid value"}), 400


@app.route('/api/snapshot/save', methods=['POST'])
@optional_auth
def save_snapshot():
    """保存每日资产快照（前端触发）"""
    data = request.json
    user_id = g.user_id
    if not data:
        return jsonify({"error": "No data provided"}), 400
        
    success = db.save_daily_snapshot(data, user_id)
    if success:
        return jsonify({"status": "ok"})
    else:
        return jsonify({"error": "Failed to save snapshot"}), 500


@app.route('/api/snapshot/trigger', methods=['POST'])
@optional_auth
def trigger_snapshot():
    """手动触发后台快照计算"""
    user_id = g.user_id
    success = take_snapshot(user_id)
    if success:
        return jsonify({"status": "ok", "message": "Snapshot taken successfully"})
    else:
        return jsonify({"error": "Failed to take snapshot"}), 500


@app.route('/api/snapshot/fix', methods=['POST'])
@optional_auth
def fix_snapshot():
    """
    修复指定日期的 day_pnl 为 0（用于修正休市日错误记录的数据）
    
    请求体:
        {"dates": ["2026-01-17", "2026-01-18"]}
    """
    data = request.json
    user_id = g.user_id
    if not data or 'dates' not in data:
        return jsonify({"error": "Missing dates"}), 400
    
    dates = data['dates']
    if not isinstance(dates, list):
        return jsonify({"error": "dates must be a list"}), 400
    
    success = db.fix_snapshot_day_pnl(dates, user_id)
    if success:
        return jsonify({"status": "ok", "message": f"Fixed {len(dates)} records"})
    else:
        return jsonify({"error": "Failed to fix snapshots"}), 500


@app.route('/api/portfolio/delete', methods=['POST'])
@optional_auth
def delete_asset():
    """删除资产"""
    data = request.json
    user_id = g.user_id
    
    if not data or 'code' not in data:
        return jsonify({"error": "Missing code"}), 400
    
    success = db.delete_asset(data['code'], user_id)
    
    if success:
        _save_snapshot_for_user(user_id)
        return jsonify({"status": "ok"})
    else:
        return jsonify({"error": "Failed to delete asset"}), 500


@app.route('/api/portfolio/buy', methods=['POST'])
@optional_auth
def buy_asset():
    """加仓"""
    data = request.json
    user_id = g.user_id
    
    if not data or 'code' not in data or 'price' not in data or 'qty' not in data:
        return jsonify({"error": "Missing required fields"}), 400
    
    try:
        price = float(data['price'])
        qty = float(data['qty'])
        success = db.buy_asset(data['code'], price, qty, user_id)
        
        if success:
            _save_snapshot_for_user(user_id)
            return jsonify({"status": "ok"})
        else:
            return jsonify({"error": "Failed to buy asset"}), 500
    except ValueError:
        return jsonify({"error": "Invalid value"}), 400


@app.route('/api/portfolio/sell', methods=['POST'])
@optional_auth
def sell_asset():
    """减仓"""
    data = request.json
    user_id = g.user_id
    
    if not data or 'code' not in data or 'price' not in data or 'qty' not in data:
        return jsonify({"error": "Missing required fields"}), 400
    
    try:
        price = float(data['price'])
        qty = float(data['qty'])
        success = db.sell_asset(data['code'], price, qty, user_id)
        
        if success:
            _save_snapshot_for_user(user_id)
            return jsonify({"status": "ok"})
        else:
            return jsonify({"error": "Failed to sell asset"}), 500
    except ValueError:
        return jsonify({"error": "Invalid value"}), 400


@app.route('/api/transactions', methods=['GET'])
@optional_auth
def get_transactions():
    """获取交易记录"""
    limit = request.args.get('limit', 100, type=int)
    user_id = g.user_id
    data = db.get_transactions(limit, user_id)
    return jsonify(data)


@app.route('/api/search')
def search():
    """搜索股票"""
    query = request.args.get('q', '')
    results = search_stocks(query)
    return jsonify(results)

@app.route('/api/cash_assets', methods=['GET'])
@optional_auth
def get_cash_assets():
    """获取现金资产"""
    user_id = g.user_id
    data = db.get_cash_assets(user_id)
    return jsonify(data)

@app.route('/api/cash_assets/add', methods=['POST'])
@optional_auth
def add_cash_asset():
    """添加现金资产"""
    user_id = g.user_id
    return _handle_asset_add(db.add_cash_asset, "cash asset", user_id)

@app.route('/api/cash_assets/delete', methods=['POST'])
@optional_auth
def delete_cash_asset():
    """删除现金资产"""
    user_id = g.user_id
    return _handle_asset_delete(db.delete_cash_asset, "cash asset", user_id)

@app.route('/api/cash_assets/update', methods=['POST'])
@optional_auth
def update_cash_asset():
    """更新现金资产"""
    user_id = g.user_id
    return _handle_asset_update(db.update_cash_asset, "cash asset", user_id)

@app.route('/api/other_assets', methods=['GET'])
@optional_auth
def get_other_assets():
    """获取其他资产"""
    user_id = g.user_id
    data = db.get_other_assets(user_id)
    return jsonify(data)

@app.route('/api/other_assets/add', methods=['POST'])
@optional_auth
def add_other_asset():
    """添加其他资产"""
    user_id = g.user_id
    return _handle_asset_add(db.add_other_asset, "other asset", user_id)

@app.route('/api/other_assets/delete', methods=['POST'])
@optional_auth
def delete_other_asset():
    """删除其他资产"""
    user_id = g.user_id
    return _handle_asset_delete(db.delete_other_asset, "other asset", user_id)

@app.route('/api/other_assets/update', methods=['POST'])
@optional_auth
def update_other_asset():
    """更新其他资产"""
    user_id = g.user_id
    return _handle_asset_update(db.update_other_asset, "other asset", user_id)

@app.route('/api/liabilities', methods=['GET'])
@optional_auth
def get_liabilities():
    """获取负债"""
    user_id = g.user_id
    data = db.get_liabilities(user_id)
    return jsonify(data)

@app.route('/api/liabilities/add', methods=['POST'])
@optional_auth
def add_liability():
    """添加负债"""
    user_id = g.user_id
    return _handle_asset_add(db.add_liability, "liability", user_id)

@app.route('/api/liabilities/delete', methods=['POST'])
@optional_auth
def delete_liability():
    """删除负债"""
    user_id = g.user_id
    return _handle_asset_delete(db.delete_liability, "liability", user_id)

@app.route('/api/liabilities/update', methods=['POST'])
@optional_auth
def update_liability():
    """更新负债"""
    user_id = g.user_id
    return _handle_asset_update(db.update_liability, "liability", user_id)


def _save_snapshot_for_user(user_id=None):
    """保存用户当日快照（更实时）"""
    try:
        stats = calculate_portfolio_stats(user_id)
        if is_weekend():
            stats['day_pnl'] = 0.0
        db.save_daily_snapshot(stats, user_id)
    except Exception as e:
        logger.warning(f"Snapshot save failed: {e}")


def _handle_asset_add(add_func, asset_type, user_id=None):
    """处理资产添加的通用函数"""
    data = request.json
    
    if not data or 'name' not in data or 'amount' not in data:
        return jsonify({"error": "Missing required fields"}), 400
    
    try:
        amount = float(data['amount'])
        success = add_func(data['name'], amount, data.get('curr', 'CNY'), user_id)
        if success:
            _save_snapshot_for_user(user_id)
        return jsonify({"status": "ok"}) if success else jsonify({"error": f"Failed to add {asset_type}"}), 500
    except ValueError:
        return jsonify({"error": "Invalid amount"}), 400


def _handle_asset_delete(delete_func, asset_type, user_id=None):
    """处理资产删除的通用函数"""
    data = request.json
    
    if not data or 'id' not in data:
        return jsonify({"error": "Missing id"}), 400
    
    try:
        asset_id = int(data['id'])
        success = delete_func(asset_id, user_id)
        if success:
            _save_snapshot_for_user(user_id)
        return jsonify({"status": "ok"}) if success else jsonify({"error": f"Failed to delete {asset_type}"}), 500
    except ValueError:
        return jsonify({"error": "Invalid id"}), 400


def _handle_asset_update(update_func, asset_type, user_id=None):
    """处理资产更新的通用函数"""
    data = request.json
    
    if not data or 'id' not in data or 'name' not in data or 'amount' not in data:
        return jsonify({"error": "Missing required fields"}), 400
    
    try:
        asset_id = int(data['id'])
        amount = float(data['amount'])
        success = update_func(asset_id, data['name'], amount, data.get('curr', 'CNY'), user_id)
        if success:
            _save_snapshot_for_user(user_id)
        return jsonify({"status": "ok"}) if success else jsonify({"error": f"Failed to update {asset_type}"}), 500
    except ValueError:
        return jsonify({"error": "Invalid value"}), 400


# ============================================================
# 认证 API
# ============================================================

@app.route('/api/auth/login', methods=['POST'])
def auth_login():
    """
    用户登录（从前端验证码登录成功后调用）
    
    请求体:
        {
            "user_id": "用户唯一ID",
            "email": "用户邮箱",
            "access_token": "前端生成的 token（可选）"
        }
    
    返回:
        {
            "token": "JWT token",
            "user_id": "用户ID",
            "email": "用户邮箱"
        }
    """
    data = request.json

    if not data or 'email' not in data:
        return jsonify({"error": "Missing email"}), 400

    email = data['email'].strip().lower()
    is_bypass = email in config.LOGIN_BYPASS_EMAILS
    code = data.get('code', '')
    if not is_bypass and not code:
        return jsonify({"error": "Missing code"}), 400
    frontend_user_id = data.get('user_id') or email
    if not is_bypass and not _verify_code(email, code):
        return jsonify({"error": "Invalid or expired code"}), 400
    nickname = data.get('nickname')
    register_method = data.get('register_method')
    phone = data.get('phone')
    
    # 获取或创建用户记录（返回实际使用的 user_id 和 数字ID）
    actual_user_id, user_number = get_or_create_user(
        db,
        frontend_user_id,
        email,
        nickname=nickname,
        register_method=register_method,
        phone=phone,
    )
    
    # 使用实际的 user_id 生成 JWT token
    token = generate_token(actual_user_id, email)
    
    logger.info(f"User logged in: {actual_user_id} ({email}) Num: {user_number}")
    
    profile = get_user_profile(db, actual_user_id) or {}
    return jsonify({
        "token": token,
        "user_id": actual_user_id,
        "user_number": user_number,
        "email": email,
        "nickname": profile.get("nickname"),
        "avatar": profile.get("avatar"),
        "register_method": profile.get("register_method"),
        "phone": profile.get("phone"),
        "created_at": profile.get("created_at"),
        "last_login": profile.get("last_login"),
    })


@app.route('/api/auth/me', methods=['GET'])
@login_required
def auth_me():
    """获取当前登录用户信息"""
    profile = get_user_profile(db, g.user_id)
    if profile:
        return jsonify(profile)
    return jsonify({
        "user_id": g.user_id,
        "email": g.email
    })


@app.route('/api/auth/profile', methods=['POST'])
@login_required
def update_profile():
    """更新用户资料（昵称/头像）"""
    data = request.json or {}
    nickname = data.get('nickname')
    avatar = data.get('avatar')

    if nickname is None and avatar is None:
        return jsonify({"error": "No fields to update"}), 400

    if isinstance(nickname, str):
        nickname = nickname.strip()

    # 简单大小限制，避免超大头像
    if isinstance(avatar, str) and len(avatar) > 1_500_000:
        return jsonify({"error": "Avatar too large"}), 400

    conn = db.get_connection()
    cursor = conn.cursor()
    try:
        updates = []
        params = []
        if nickname is not None:
            updates.append("nickname = ?")
            params.append(nickname)
        if avatar is not None:
            updates.append("avatar = ?")
            params.append(avatar)
        if not updates:
            return jsonify({"error": "No fields to update"}), 400

        params.append(g.user_id)
        cursor.execute(f"UPDATE users SET {', '.join(updates)} WHERE id = ?", params)
        conn.commit()
    except Exception as e:
        logger.error(f"Failed to update profile: {e}")
        conn.rollback()
        return jsonify({"error": "Update failed"}), 500
    finally:
        conn.close()

    profile = get_user_profile(db, g.user_id) or {}
    return jsonify(profile)


@app.route('/api/auth/send_code', methods=['POST'])
def auth_send_code():
    """发送邮箱验证码"""
    data = request.json
    if not data or 'email' not in data:
        return jsonify({"error": "Missing email"}), 400
    email = data['email'].strip().lower()
    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        return jsonify({"error": "Invalid email"}), 400
    if email in config.LOGIN_BYPASS_EMAILS:
        return jsonify({"status": "ok", "bypass": True})

    info = _EMAIL_CODE_STORE.get(email)
    if info and (datetime.utcnow() - info["last_send"]).total_seconds() < 60:
        return jsonify({"error": "Too many requests"}), 429

    code = _generate_code()
    _store_code(email, code)
    try:
        send_verification_email(email, code)
    except Exception as e:
        logger.error(f"Send code failed: {e}")
        return jsonify({"error": "Send failed"}), 500
    return jsonify({"status": "ok"})


@app.route('/health')
def health():
    """健康检查"""
    return jsonify({"status": "ok", "version": config.APP_VERSION})


# ============================================================
# 分析 API
# ============================================================

@app.route('/api/analysis/overview')
@optional_auth
def analysis_overview():
    """
    盈亏概览
    
    参数:
        period: day|month|year|all (默认 all)
    
    返回:
        {day: {pnl, pnl_rate}, month: {...}, year: {...}, all: {...}}
    """
    period = request.args.get('period', 'all')
    user_id = g.user_id

    if period == 'all':
        # 返回所有周期的数据
        result = {
            'day': db.get_pnl_overview('day', user_id),
            'month': db.get_pnl_overview('month', user_id),
            'year': db.get_pnl_overview('year', user_id),
            'all': db.get_pnl_overview('all', user_id)
        }
    else:
        # 返回指定周期的数据
        result = {period: db.get_pnl_overview(period, user_id)}

    return jsonify(result)


@app.route('/api/analysis/calendar')
@optional_auth
def analysis_calendar():
    """
    收益日历
    
    参数:
        type: day|month|year (默认 day)
    
    返回:
        {items: [{label, pnl}], total_pnl, total_rate, title}
    """
    time_type = request.args.get('type', 'day')
    user_id = g.user_id
    result = db.get_calendar_data(time_type, user_id)
    return jsonify(result)


@app.route('/api/analysis/rank')
@optional_auth
def analysis_rank():
    """
    盈亏排行
    
    参数:
        type: gain|loss|all (默认 all)
        market: all|a|us|hk|fund (默认 all)
    
    返回:
        {gain: [{code, name, pnl, pnl_rate, market}], loss: [...]}
    """
    rank_type = request.args.get('type', 'all')
    market = request.args.get('market', 'all')
    user_id = g.user_id
    
    # 获取持仓数据
    portfolio_data = db.get_rank_data('gain', market, user_id)
    
    if not portfolio_data:
        return jsonify({'gain': [], 'loss': []})
    
    # 获取实时价格
    codes = [item['code'] for item in portfolio_data]
    prices = batch_get_prices(codes)
    
    # 计算盈亏
    result_items = []
    for item in portfolio_data:
        code = item['code']
        price_info = prices.get(code, (0, 0, 0, 0))
        current_price = price_info[0] if price_info[0] else item['cost_price']
        
        # 计算盈亏
        qty = item['qty']
        cost = item['cost_price'] * qty
        current_value = current_price * qty
        pnl = current_value - cost + item['adjustment']
        pnl_rate = (pnl / cost * 100) if cost > 0 else 0
        
        result_items.append({
            'code': code,
            'name': item['name'],
            'pnl': round(pnl, 2),
            'pnl_rate': round(pnl_rate, 2),
            'market': item['market']
        })
    
    # 分类排序
    gain_list = sorted([x for x in result_items if x['pnl'] > 0], key=lambda x: x['pnl'], reverse=True)
    loss_list = sorted([x for x in result_items if x['pnl'] < 0], key=lambda x: x['pnl'])
    
    if rank_type == 'gain':
        return jsonify({'gain': gain_list, 'loss': []})
    elif rank_type == 'loss':
        return jsonify({'gain': [], 'loss': loss_list})
    else:
        return jsonify({'gain': gain_list, 'loss': loss_list})


def background_scheduler():
    """后台任务调度"""
    logger.info("Scheduler started")
    while True:
        try:
            # 每小时执行一次快照
            take_snapshot()
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
        
        # 休眠 1 小时 (3600秒)
        # 实际生产中建议使用 APScheduler，这里用简单 sleep 即可
        time.sleep(3600)

if __name__ == '__main__':
    logger.info("Starting Portfolio Management System v10.0...")
    logger.info(f"Database: {config.DATABASE_PATH}")
    logger.info(f"Server: http://{config.HOST}:{config.PORT}")
    
    # 启动后台快照任务
    threading.Thread(target=background_scheduler, daemon=True).start()
    
    # 【优化】程序启动时，立即执行一次快照保存，防止用户短时间开机后数据未保存
    # 使用线程异步执行，避免阻塞启动过程
    threading.Thread(target=take_snapshot, daemon=True).start()
    
    # 自动打开浏览器
    threading.Thread(target=open_browser, daemon=True).start()
    
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
