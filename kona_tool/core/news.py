"""
市场快讯抓取模块 (core/news.py)
源: 金十数据 (Jin10)
"""
import requests
import time
import logging
from datetime import datetime
from typing import List, Dict

# 配置
JIN10_API_URL = "https://flash-api.jin10.com/get_flash_list"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.jin10.com/",
    "Origin": "https://www.jin10.com",
    "x-version": "1.0.0"
}

logger = logging.getLogger(__name__)

"""
市场快讯抓取模块 (core/news.py)
源: 新浪财经 (Sina Finance) 7x24小时全球实时财经新闻直播
"""
import requests
import time
import logging
import re
from datetime import datetime
from typing import List, Dict

# 配置
# 新浪财经直播接口: zhibo_id=152 (全球财经)
SINA_API_URL = "https://zhibo.sina.com.cn/api/zhibo/feed"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://finance.sina.com.cn/7x24/",
}

logger = logging.getLogger(__name__)

class NewsFetcher:
    def __init__(self):
        self.cache: List[Dict] = []

    def fetch_latest(self, page: int = 1, page_size: int = 30) -> List[Dict]:
        """抓取最新快讯 (新浪源)"""
        logger.info("Fetching news from Sina...")
        try:
            params = {
                "page": page,
                "page_size": page_size,
                "zhibo_id": 152,
                "tag_id": 0,
                "dire": "f",
                "dpc": 1,
                "pagesize": page_size,
                "_": int(time.time() * 1000)
            }
            
            resp = requests.get(SINA_API_URL, headers=HEADERS, params=params, timeout=5)
            logger.info(f"Sina response status: {resp.status_code}")
            
            if resp.status_code == 200:
                data = resp.json()
                # 新浪结构: result -> data -> feed -> list
                if "result" in data and "data" in data["result"] and "feed" in data["result"]["data"]:
                    items = data["result"]["data"]["feed"]["list"]
                    logger.info(f"Received {len(items)} news items from Sina")
                    
                    result = []
                    for item in items:
                        # 提取内容
                        content = item.get("rich_text", "")
                        if not content:
                            continue
                            
                        # 清洗 HTML 标签 (新浪返回的内容包含 HTML)
                        content = self._clean_html(content)
                        
                        # 提取时间
                        create_time = item.get("create_time", "") # "2024-01-16 14:00:00"
                        time_str = create_time.split(" ")[-1][:5] if create_time else datetime.now().strftime("%H:%M")
                        
                        # 提取重要性 (新浪通过 tag 或 type 判断，这里简化逻辑，只要包含"重磅"等字眼就算重要)
                        important = 0
                        if "tag" in item and item["tag"]:
                            for tag in item["tag"]:
                                if tag.get("name") in ["重磅", "突发", "焦点"]:
                                    important = 1
                                    break
                        
                        # 简单的关键字高亮判断
                        if "加息" in content or "降息" in content or "CPI" in content or "GDP" in content:
                            important = 1

                        result.append({
                            "id": item.get("id"),
                            "time": time_str,
                            "date": create_time.split(" ")[0] if create_time else "",
                            "content": content,
                            "important": important == 1
                        })
                    
                    return result
                else:
                    logger.warning("Sina response structure changed")
                    
            else:
                logger.error(f"Sina fetch failed: {resp.text}")
                
        except Exception as e:
            logger.error(f"News fetch error: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
        return []

    def _clean_html(self, raw_html: str) -> str:
        """去除HTML标签"""
        # 1. 替换 <br> 为换行
        # 2. 去除所有其他标签
        clean = re.compile('<.*?>')
        return re.sub(clean, '', raw_html).strip()

news_fetcher = NewsFetcher()
