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
APP_VERSION = "v10.4"

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
    """主页"""
    response = make_response(render_template('index.html', version=APP_VERSION))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    response.headers['X-App-Version'] = APP_VERSION
    return response


@app.route('/test')
def test_page():
    """测试页面"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>分类测试</title>
        <style>
            body { font-family: sans-serif; padding: 20px; background: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; }
            .btn-group { margin: 20px 0; }
            button { padding: 10px 20px; margin: 5px; cursor: pointer; }
            button.active { background: #007bff; color: white; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            th, td { padding: 10px; border: 1px solid #ddd; text-align: left; }
            th { background: #f0f0f0; }
            .info { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
            pre { background: #f5f5f5; padding: 10px; border-radius: 4px; overflow-x: auto; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>分类功能测试</h1>
            
            <div class="info">
                <h3>当前状态</h3>
                <p>currentCategory: <strong id="currentCat">all</strong></p>
                <p>点击按钮切换分类，查看API请求和数据</p>
            </div>
            
            <div class="btn-group">
                <button onclick="switchCategory('all')" id="btn-all" class="active">全部</button>
                <button onclick="switchCategory('stock_cn')" id="btn-stock_cn">A股</button>
                <button onclick="switchCategory('stock_hk')" id="btn-stock_hk">港股</button>
                <button onclick="switchCategory('stock_us')" id="btn-stock_us">美股</button>
                <button onclick="switchCategory('fund')" id="btn-fund">基金</button>
            </div>
            
            <div class="info">
                <h3>API请求日志</h3>
                <pre id="log"></pre>
            </div>
            
            <div class="info">
                <h3>返回数据</h3>
                <pre id="data">点击按钮获取数据...</pre>
            </div>
            
            <h2>持仓表格</h2>
            <table>
                <thead>
                    <tr>
                        <th>代码</th>
                        <th>名称</th>
                        <th>数量</th>
                        <th>价格</th>
                    </tr>
                </thead>
                <tbody id="tableBody">
                </tbody>
            </table>
        </div>
        
        <script>
            let currentCategory = 'all';
            
            function log(message) {
                const logEl = document.getElementById('log');
                logEl.innerHTML = message + '\\n' + logEl.innerHTML;
            }
            
            async function switchCategory(type) {
                log(`=== 切换分类 ===`);
                log(`从: ${currentCategory}`);
                log(`到: ${type}`);
                
                currentCategory = type;
                document.getElementById('currentCat').innerText = currentCategory;
                
                // 更新按钮状态
                document.querySelectorAll('button').forEach(btn => btn.classList.remove('active'));
                document.getElementById('btn-' + type).classList.add('active');
                
                // 构建API URL
                const apiUrl = currentCategory === 'all' ? '/api/portfolio' : `/api/portfolio?type=${currentCategory}`;
                log(`请求URL: ${apiUrl}`);
                
                try {
                    const response = await fetch(apiUrl);
                    const data = await response.json();
                    
                    log(`返回数据数量: ${data.length}`);
                    log(`数据: ${JSON.stringify(data.map(d => d.code))}`);
                    
                    document.getElementById('data').innerText = JSON.stringify(data, null, 2);
                    
                    // 更新表格
                    const tbody = document.getElementById('tableBody');
                    tbody.innerHTML = data.map(item => `
                        <tr>
                            <td>${item.code}</td>
                            <td>${item.name}</td>
                            <td>${item.qty}</td>
                            <td>${item.price}</td>
                        </tr>
                    `).join('');
                } catch (error) {
                    log(`错误: ${error}`);
                }
            }
            
            // 页面加载时获取全部数据
            window.onload = () => switchCategory('all');
        </script>
    </body>
    </html>
    '''


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
    logger.info(f"API: get_portfolio called with type={asset_type}")
    data = db.get_portfolio(asset_type)
    logger.info(f"API: returning {len(data)} records")
    return jsonify(data)


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


@app.route('/health')
def health():
    """健康检查"""
    return jsonify({"status": "ok", "version": "10.0"})


if __name__ == '__main__':
    logger.info("Starting Portfolio Management System v10.0...")
    logger.info(f"Database: {config.DATABASE_PATH}")
    logger.info(f"Server: http://{config.HOST}:{config.PORT}")
    
    # 自动打开浏览器
    threading.Thread(target=open_browser, daemon=True).start()
    
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)