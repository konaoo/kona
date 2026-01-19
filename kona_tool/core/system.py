"""
系统管理模块 (core/system.py)
负责系统级操作：Git信息、API检测、数据备份恢复
"""
import subprocess
import time
import requests
import shutil
import logging
import os
from pathlib import Path
from typing import Dict, Any

import config

logger = logging.getLogger(__name__)

class SystemManager:
    def get_version_info(self) -> Dict[str, str]:
        """获取Git版本信息"""
        info = {
            "version": config.APP_VERSION if hasattr(config, 'APP_VERSION') else "Unknown",
            "commit_hash": "Unknown",
            "last_update": "Unknown"
        }
        
        try:
            # 获取短 Hash
            hash_out = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], stderr=subprocess.STDOUT)
            info['commit_hash'] = hash_out.decode('utf-8').strip()
            
            # 获取最后提交时间
            date_out = subprocess.check_output(['git', 'log', '-1', '--format=%cd', '--date=format:%Y-%m-%d %H:%M'], stderr=subprocess.STDOUT)
            info['last_update'] = date_out.decode('utf-8').strip()
            
        except Exception as e:
            logger.warning(f"Git info fetch failed: {e}")
            
        return info

    def check_api_status(self) -> Dict[str, Any]:
        """检测核心API连通性"""
        results = {}
        
        targets = {
            "price": "http://hq.sinajs.cn/list=sh000001", # 新浪A股
            "rate": "http://hq.sinajs.cn/list=hf_USDCNY", # 汇率
            "news": "https://zhibo.sina.com.cn/api/zhibo/feed?zhibo_id=152" # 新浪快讯
        }
        
        for name, url in targets.items():
            start = time.time()
            try:
                # 简单的连通性测试，超时设短一点
                requests.get(url, timeout=3, headers={"User-Agent": "curl/7.64.1"})
                latency = int((time.time() - start) * 1000)
                results[name] = {"ok": True, "latency": latency}
            except Exception as e:
                results[name] = {"ok": False, "error": str(e)}
                
        return results

    def restore_database(self, upload_path: str) -> bool:
        """从上传的文件恢复数据库"""
        try:
            # 1. 验证上传文件是否是有效的 SQLite (简单检查文件头)
            with open(upload_path, 'rb') as f:
                header = f.read(16)
                if b'SQLite format 3' not in header:
                    logger.error("Invalid database file format")
                    return False
            
            # 2. 备份当前数据库 (以防万一)
            backup_path = str(config.DATABASE_PATH) + f".bak.{int(time.time())}"
            if config.DATABASE_PATH.exists():
                shutil.copy2(config.DATABASE_PATH, backup_path)
                logger.info(f"Created safety backup at {backup_path}")
            
            # 3. 覆盖
            # 需要先关闭所有连接吗？在 SQLite 中，只要没有写锁，通常可以直接替换文件
            # 但为了安全，最好在替换前确保没有写入操作。
            # 由于我们是单线程 Web (Flask default)，此时正在处理 restore 请求，不会有其他并发写入。
            
            shutil.copy2(upload_path, config.DATABASE_PATH)
            logger.info("Database restored successfully")
            return True
            
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return False

system_manager = SystemManager()
