"""
主程序文件
整合所有功能，提供Web API
"""
import logging
import threading
import webbrowser
import time
from flask import Flask, render_template, jsonify, request, make_response
from pathlib import Path

import config
from core.db import DatabaseManager
from core.price import get_price, batch_get_prices, get_forex_rates, search_stocks
from core.parser import parse_code, get_display_code
from core.snapshot import take_snapshot

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
APP_VERSION = "v11.0.2"

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
def get_portfolio():
    """获取持仓数据，支持按类型筛选"""
    asset_type = request.args.get('type', 'all')
    timestamp = request.args.get('t')
    logger.info(f"API: get_portfolio called with type={asset_type}, timestamp={timestamp}")
    logger.info(f"Full request URL: {request.url}")
    logger.info(f"All request args: {dict(request.args)}")
    data = db.get_portfolio(asset_type)
    logger.info(f"API: returning {len(data)} records")
    if len(data) > 0:
        logger.info(f"Sample codes: {[d['code'] for d in data[:5]]}")
    response = jsonify(data)
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0, private'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    response.headers['Vary'] = '*'
    return response


@app.route('/api/portfolio/add', methods=['POST'])
def add_asset():
    """添加资产"""
    data = request.json
    
    if not data or 'code' not in data or 'qty' not in data or 'price' not in data:
        return jsonify({"error": "Missing required fields"}), 400
    
    # 解析代码
    parsed = parse_code(data['code'], data.get('curr', ''))
    data['code'] = parsed['code']
    data['curr'] = parsed['curr']
    data['name'] = data.get('name', parsed['code'])
    data['adjustment'] = data.get('adjustment', 0.0)
    
    success = db.add_asset(data)
    
    if success:
        return jsonify({"status": "ok"})
    else:
        return jsonify({"error": "Failed to add asset"}), 500


@app.route('/api/portfolio/update', methods=['POST'])
def update_asset():
    """更新资产"""
    data = request.json
    
    if not data or 'code' not in data or 'field' not in data or 'val' not in data:
        return jsonify({"error": "Missing required fields"}), 400
    
    try:
        val = float(data['val'])
        success = db.update_asset(data['code'], data['field'], val)
        
        if success:
            return jsonify({"status": "ok"})
        else:
            return jsonify({"error": "Asset not found"}), 404
    except ValueError:
        return jsonify({"error": "Invalid value"}), 400


@app.route('/analysis')
def analysis():
    """资产分析页面"""
    return make_response(render_template('analysis.html', version=APP_VERSION))


@app.route('/api/history')
def get_history():
    """获取历史资产数据"""
    days = request.args.get('days', 365, type=int)
    history = db.get_history(days)
    return jsonify(history)


@app.route('/api/portfolio/modify', methods=['POST'])
def modify_asset():
    """修正资产（数量、成本、调整值）"""
    data = request.json
    
    if not data or 'code' not in data or 'qty' not in data or 'price' not in data or 'adjustment' not in data:
        return jsonify({"error": "Missing required fields"}), 400
    
    try:
        qty = float(data['qty'])
        price = float(data['price'])
        adjustment = float(data['adjustment'])
        
        success = db.modify_asset(data['code'], qty, price, adjustment)
        
        if success:
            return jsonify({"status": "ok"})
        else:
            return jsonify({"error": "Asset not found"}), 404
    except ValueError:
        return jsonify({"error": "Invalid value"}), 400


@app.route('/api/snapshot/save', methods=['POST'])
def save_snapshot():
    """保存每日资产快照（前端触发）"""
    data = request.json
    if not data:
        return jsonify({"error": "No data provided"}), 400
        
    success = db.save_daily_snapshot(data)
    if success:
        return jsonify({"status": "ok"})
    else:
        return jsonify({"error": "Failed to save snapshot"}), 500


@app.route('/api/snapshot/trigger', methods=['POST'])
def trigger_snapshot():
    """手动触发后台快照计算"""
    success = take_snapshot()
    if success:
        return jsonify({"status": "ok", "message": "Snapshot taken successfully"})
    else:
        return jsonify({"error": "Failed to take snapshot"}), 500


@app.route('/api/portfolio/delete', methods=['POST'])
def delete_asset():
    """删除资产"""
    data = request.json
    
    if not data or 'code' not in data:
        return jsonify({"error": "Missing code"}), 400
    
    success = db.delete_asset(data['code'])
    
    if success:
        return jsonify({"status": "ok"})
    else:
        return jsonify({"error": "Failed to delete asset"}), 500


@app.route('/api/portfolio/buy', methods=['POST'])
def buy_asset():
    """加仓"""
    data = request.json
    
    if not data or 'code' not in data or 'price' not in data or 'qty' not in data:
        return jsonify({"error": "Missing required fields"}), 400
    
    try:
        price = float(data['price'])
        qty = float(data['qty'])
        success = db.buy_asset(data['code'], price, qty)
        
        if success:
            return jsonify({"status": "ok"})
        else:
            return jsonify({"error": "Failed to buy asset"}), 500
    except ValueError:
        return jsonify({"error": "Invalid value"}), 400


@app.route('/api/portfolio/sell', methods=['POST'])
def sell_asset():
    """减仓"""
    data = request.json
    
    if not data or 'code' not in data or 'price' not in data or 'qty' not in data:
        return jsonify({"error": "Missing required fields"}), 400
    
    try:
        price = float(data['price'])
        qty = float(data['qty'])
        success = db.sell_asset(data['code'], price, qty)
        
        if success:
            return jsonify({"status": "ok"})
        else:
            return jsonify({"error": "Failed to sell asset"}), 500
    except ValueError:
        return jsonify({"error": "Invalid value"}), 400


@app.route('/api/transactions', methods=['GET'])
def get_transactions():
    """获取交易记录"""
    limit = request.args.get('limit', 100, type=int)
    data = db.get_transactions(limit)
    return jsonify(data)


@app.route('/api/search')
def search():
    """搜索股票"""
    query = request.args.get('q', '')
    results = search_stocks(query)
    return jsonify(results)

@app.route('/api/cash_assets', methods=['GET'])
def get_cash_assets():
    """获取现金资产"""
    data = db.get_cash_assets()
    return jsonify(data)

@app.route('/api/cash_assets/add', methods=['POST'])
def add_cash_asset():
    """添加现金资产"""
    return _handle_asset_add(db.add_cash_asset, "cash asset")

@app.route('/api/cash_assets/delete', methods=['POST'])
def delete_cash_asset():
    """删除现金资产"""
    return _handle_asset_delete(db.delete_cash_asset, "cash asset")

@app.route('/api/cash_assets/update', methods=['POST'])
def update_cash_asset():
    """更新现金资产"""
    return _handle_asset_update(db.update_cash_asset, "cash asset")

@app.route('/api/other_assets', methods=['GET'])
def get_other_assets():
    """获取其他资产"""
    data = db.get_other_assets()
    return jsonify(data)

@app.route('/api/other_assets/add', methods=['POST'])
def add_other_asset():
    """添加其他资产"""
    return _handle_asset_add(db.add_other_asset, "other asset")

@app.route('/api/other_assets/delete', methods=['POST'])
def delete_other_asset():
    """删除其他资产"""
    return _handle_asset_delete(db.delete_other_asset, "other asset")

@app.route('/api/other_assets/update', methods=['POST'])
def update_other_asset():
    """更新其他资产"""
    return _handle_asset_update(db.update_other_asset, "other asset")

@app.route('/api/liabilities', methods=['GET'])
def get_liabilities():
    """获取负债"""
    data = db.get_liabilities()
    return jsonify(data)

@app.route('/api/liabilities/add', methods=['POST'])
def add_liability():
    """添加负债"""
    return _handle_asset_add(db.add_liability, "liability")

@app.route('/api/liabilities/delete', methods=['POST'])
def delete_liability():
    """删除负债"""
    return _handle_asset_delete(db.delete_liability, "liability")

@app.route('/api/liabilities/update', methods=['POST'])
def update_liability():
    """更新负债"""
    return _handle_asset_update(db.update_liability, "liability")


def _handle_asset_add(add_func, asset_type):
    """处理资产添加的通用函数"""
    data = request.json
    
    if not data or 'name' not in data or 'amount' not in data:
        return jsonify({"error": "Missing required fields"}), 400
    
    try:
        amount = float(data['amount'])
        success = add_func(data['name'], amount, data.get('curr', 'CNY'))
        return jsonify({"status": "ok"}) if success else jsonify({"error": f"Failed to add {asset_type}"}), 500
    except ValueError:
        return jsonify({"error": "Invalid amount"}), 400


def _handle_asset_delete(delete_func, asset_type):
    """处理资产删除的通用函数"""
    data = request.json
    
    if not data or 'id' not in data:
        return jsonify({"error": "Missing id"}), 400
    
    try:
        asset_id = int(data['id'])
        success = delete_func(asset_id)
        return jsonify({"status": "ok"}) if success else jsonify({"error": f"Failed to delete {asset_type}"}), 500
    except ValueError:
        return jsonify({"error": "Invalid id"}), 400


def _handle_asset_update(update_func, asset_type):
    """处理资产更新的通用函数"""
    data = request.json
    
    if not data or 'id' not in data or 'name' not in data or 'amount' not in data:
        return jsonify({"error": "Missing required fields"}), 400
    
    try:
        asset_id = int(data['id'])
        amount = float(data['amount'])
        success = update_func(asset_id, data['name'], amount, data.get('curr', 'CNY'))
        return jsonify({"status": "ok"}) if success else jsonify({"error": f"Failed to update {asset_type}"}), 500
    except ValueError:
        return jsonify({"error": "Invalid value"}), 400


@app.route('/health')
def health():
    """健康检查"""
    return jsonify({"status": "ok", "version": "10.0"})


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