"""
API 模块 - 封装所有后端 API 调用
"""
import requests
import threading
from typing import List, Dict, Any, Callable, Optional
from config import API_BASE, API_TIMEOUT
from error_handler import APIError, log_api_error


class ApiClient:
    """API 客户端"""
    
    def __init__(self):
        self.base_url = API_BASE
        self.timeout = API_TIMEOUT
        self._token: Optional[str] = None
        self._session = requests.Session()
    
    def set_token(self, token: str):
        """设置认证 token"""
        self._token = token
    
    def clear_token(self):
        """清除认证 token"""
        self._token = None
    
    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        headers = {"Content-Type": "application/json"}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers
    
    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        on_success: Optional[Callable] = None,
        on_error: Optional[Callable] = None
    ):
        """通用请求方法"""
        def do_request():
            try:
                url = f"{self.base_url}{endpoint}"
                headers = self._get_headers()

                if method.upper() == "GET":
                    response = self._session.get(url, headers=headers, timeout=self.timeout)
                elif method.upper() == "POST":
                    response = self._session.post(url, json=data, headers=headers, timeout=self.timeout)
                else:
                    raise ValueError(f"Unsupported method: {method}")

                if response.status_code == 200:
                    result = response.json()
                    if on_success:
                        on_success(result)
                elif response.status_code == 401:
                    if on_error:
                        on_error("未登录或登录已过期")
                else:
                    error_msg = f"HTTP {response.status_code}"
                    log_api_error(endpoint, APIError(error_msg, status_code=response.status_code))
                    if on_error:
                        on_error(error_msg)
            except requests.exceptions.Timeout:
                log_api_error(endpoint, requests.exceptions.Timeout("请求超时"))
                if on_error:
                    on_error("请求超时")
            except requests.exceptions.ConnectionError as e:
                log_api_error(endpoint, e)
                if on_error:
                    on_error("网络连接失败")
            except Exception as e:
                log_api_error(endpoint, e)
                if on_error:
                    on_error("请求失败，请稍后重试")

        threading.Thread(target=do_request, daemon=True).start()
    
    # ... (login methods) ...

    def login_sync(self, user_id: str, email: str) -> Optional[Dict]:
        """同步登录，返回登录数据"""
        try:
            res = self._session.post(
                f"{self.base_url}/api/auth/login",
                json={"user_id": user_id, "email": email},
                timeout=self.timeout
            )
            if res.status_code == 200:
                data = res.json()
                token = data.get("token")
                if token:
                    self._token = token
                return data
            else:
                log_api_error("/api/auth/login", APIError(f"HTTP {res.status_code}", status_code=res.status_code))
                return None
        except requests.exceptions.Timeout:
            log_api_error("/api/auth/login", requests.exceptions.Timeout("请求超时"))
            return None
        except requests.exceptions.ConnectionError as e:
            log_api_error("/api/auth/login", e)
            return None
        except Exception as e:
            log_api_error("/api/auth/login", e)
            return None
    
    # ============================================================
    # 资产相关 API
    # ============================================================
    
    def get_history(
        self,
        on_success: Optional[Callable[[List[Dict]], None]] = None,
        on_error: Optional[Callable[[str], None]] = None
    ):
        """获取资产历史数据"""
        self._request("GET", "/api/history", on_success=on_success, on_error=on_error)
    
    def get_cash_assets(
        self,
        on_success: Optional[Callable[[List[Dict]], None]] = None,
        on_error: Optional[Callable[[str], None]] = None
    ):
        """获取现金资产列表"""
        self._request("GET", "/api/cash_assets", on_success=on_success, on_error=on_error)
    
    def get_other_assets(
        self,
        on_success: Optional[Callable[[List[Dict]], None]] = None,
        on_error: Optional[Callable[[str], None]] = None
    ):
        """获取其他资产列表"""
        self._request("GET", "/api/other_assets", on_success=on_success, on_error=on_error)
    
    def get_liabilities(
        self,
        on_success: Optional[Callable[[List[Dict]], None]] = None,
        on_error: Optional[Callable[[str], None]] = None
    ):
        """获取负债列表"""
        self._request("GET", "/api/liabilities", on_success=on_success, on_error=on_error)
    
    # ============================================================
    # 投资组合 API
    # ============================================================
    
    def get_portfolio(
        self,
        on_success: Optional[Callable[[List[Dict]], None]] = None,
        on_error: Optional[Callable[[str], None]] = None
    ):
        """获取投资组合"""
        self._request("GET", "/api/portfolio", on_success=on_success, on_error=on_error)
    
    def get_prices_batch(
        self,
        codes: List[str],
        on_success: Optional[Callable[[Dict], None]] = None,
        on_error: Optional[Callable[[str], None]] = None
    ):
        """批量获取价格"""
        self._request(
            "POST",
            "/api/prices/batch",
            data={"codes": codes},
            on_success=on_success,
            on_error=on_error
        )
    
    # ============================================================
    # 快讯 API
    # ============================================================
    
    def get_news(
        self,
        on_success: Optional[Callable[[List[Dict]], None]] = None,
        on_error: Optional[Callable[[str], None]] = None
    ):
        """获取最新快讯"""
        def handle_success(data):
            # 兼容两种格式：数组或 {items: []}
            items = data if isinstance(data, list) else data.get('items', [])
            if on_success:
                on_success(items)
        
        self._request("GET", "/api/news/latest", on_success=handle_success, on_error=on_error)
    
    # ============================================================
    # 分析 API
    # ============================================================
    
    def get_analysis_overview(
        self,
        period: str = "all",
        on_success: Optional[Callable[[Dict], None]] = None,
        on_error: Optional[Callable[[str], None]] = None
    ):
        """
        获取盈亏概览数据
        
        Args:
            period: day|month|year|all
        """
        self._request("GET", f"/api/analysis/overview?period={period}", on_success=on_success, on_error=on_error)
    
    def get_analysis_calendar(
        self,
        time_type: str = "day",
        on_success: Optional[Callable[[Dict], None]] = None,
        on_error: Optional[Callable[[str], None]] = None
    ):
        """
        获取收益日历数据
        
        Args:
            time_type: day|month|year
        """
        self._request("GET", f"/api/analysis/calendar?type={time_type}", on_success=on_success, on_error=on_error)
    
    def get_analysis_rank(
        self,
        rank_type: str = "all",
        market: str = "all",
        on_success: Optional[Callable[[Dict], None]] = None,
        on_error: Optional[Callable[[str], None]] = None
    ):
        """
        获取盈亏排行数据
        
        Args:
            rank_type: gain|loss|all
            market: all|a|us|hk|fund
        """
        self._request("GET", f"/api/analysis/rank?type={rank_type}&market={market}", on_success=on_success, on_error=on_error)
    
    def get_analysis_overview_sync(self) -> Dict:
        """同步获取盈亏概览（所有周期）"""
        try:
            res = self._session.get(
                f"{self.base_url}/api/analysis/overview?period=all",
                headers=self._get_headers(),
                timeout=self.timeout
            )
            if res.status_code == 200:
                return res.json()
            return {}
        except requests.exceptions.Timeout:
            log_api_error("/api/analysis/overview", requests.exceptions.Timeout("请求超时"))
            return {}
        except requests.exceptions.ConnectionError as e:
            log_api_error("/api/analysis/overview", e)
            return {}
        except Exception as e:
            log_api_error("/api/analysis/overview", e)
            return {}

    def get_analysis_calendar_sync(self, time_type: str = "day") -> Dict:
        """同步获取收益日历"""
        try:
            res = self._session.get(
                f"{self.base_url}/api/analysis/calendar?type={time_type}",
                headers=self._get_headers(),
                timeout=self.timeout
            )
            if res.status_code == 200:
                return res.json()
            return {}
        except requests.exceptions.Timeout:
            log_api_error("/api/analysis/calendar", requests.exceptions.Timeout("请求超时"))
            return {}
        except requests.exceptions.ConnectionError as e:
            log_api_error("/api/analysis/calendar", e)
            return {}
        except Exception as e:
            log_api_error("/api/analysis/calendar", e)
            return {}

    def get_analysis_rank_sync(self, market: str = "all") -> Dict:
        """同步获取盈亏排行"""
        try:
            res = self._session.get(
                f"{self.base_url}/api/analysis/rank?type=all&market={market}",
                headers=self._get_headers(),
                timeout=self.timeout
            )
            if res.status_code == 200:
                return res.json()
            return {}
        except requests.exceptions.Timeout:
            log_api_error("/api/analysis/rank", requests.exceptions.Timeout("请求超时"))
            return {}
        except requests.exceptions.ConnectionError as e:
            log_api_error("/api/analysis/rank", e)
            return {}
        except Exception as e:
            log_api_error("/api/analysis/rank", e)
            return {}
    
    # ============================================================
    # 同步方法（用于需要等待结果的场景）
    # ============================================================

    def _get_list_sync(self, endpoint: str) -> List[Dict]:
        """通用获取列表的同步方法"""
        try:
            res = self._session.get(
                f"{self.base_url}{endpoint}",
                headers=self._get_headers(),
                timeout=self.timeout
            )
            if res.status_code == 200:
                return res.json()
            elif res.status_code == 401:
                raise APIError("未登录或登录已过期", status_code=401, endpoint=endpoint)
            else:
                log_api_error(endpoint, APIError(f"HTTP {res.status_code}", status_code=res.status_code))
                return []
        except requests.exceptions.Timeout:
            log_api_error(endpoint, requests.exceptions.Timeout("请求超时"))
            return []
        except requests.exceptions.ConnectionError as e:
            log_api_error(endpoint, e)
            return []
        except APIError:
            raise
        except Exception as e:
            log_api_error(endpoint, e)
            return []

    def _post_sync(self, endpoint: str, data: Dict) -> bool:
        """通用 POST 的同步方法"""
        try:
            res = self._session.post(
                f"{self.base_url}{endpoint}",
                json=data,
                headers=self._get_headers(),
                timeout=self.timeout
            )
            if res.status_code == 200:
                return True
            elif res.status_code == 401:
                raise APIError("未登录或登录已过期", status_code=401, endpoint=endpoint)
            else:
                log_api_error(endpoint, APIError(f"HTTP {res.status_code}", status_code=res.status_code))
                return False
        except requests.exceptions.Timeout:
            log_api_error(endpoint, requests.exceptions.Timeout("请求超时"))
            return False
        except requests.exceptions.ConnectionError as e:
            log_api_error(endpoint, e)
            return False
        except APIError:
            raise
        except Exception as e:
            log_api_error(endpoint, e)
            return False

    def get_portfolio_sync(self) -> tuple[List[Dict], Dict]:
        """同步获取投资组合和价格"""
        try:
            headers = self._get_headers()

            res = self._session.get(f"{self.base_url}/api/portfolio", headers=headers, timeout=self.timeout)
            if res.status_code != 200:
                log_api_error("/api/portfolio", APIError(f"HTTP {res.status_code}", status_code=res.status_code))
                return [], {}

            portfolio = res.json()
            if not portfolio:
                return [], {}

            codes = [item['code'] for item in portfolio]
            price_res = self._session.post(
                f"{self.base_url}/api/prices/batch",
                json={"codes": codes},
                headers=headers,
                timeout=self.timeout
            )
            prices = price_res.json() if price_res.status_code == 200 else {}

            return portfolio, prices
        except requests.exceptions.Timeout:
            log_api_error("/api/portfolio", requests.exceptions.Timeout("请求超时"))
            return [], {}
        except requests.exceptions.ConnectionError as e:
            log_api_error("/api/portfolio", e)
            return [], {}
        except Exception as e:
            log_api_error("/api/portfolio", e)
            return [], {}
            
    def get_cash_assets_sync(self) -> List[Dict]:
        """同步获取现金资产"""
        return self._get_list_sync("/api/cash_assets")

    def get_other_assets_sync(self) -> List[Dict]:
        """同步获取其他资产"""
        return self._get_list_sync("/api/other_assets")

    def get_liabilities_sync(self) -> List[Dict]:
        """同步获取负债"""
        return self._get_list_sync("/api/liabilities")

    def add_cash_asset_sync(self, name: str, amount: float, curr: str = "CNY") -> bool:
        """同步添加现金资产"""
        return self._post_sync("/api/cash_assets/add", {"name": name, "amount": amount, "curr": curr})

    def add_other_asset_sync(self, name: str, amount: float, curr: str = "CNY") -> bool:
        """同步添加其他资产"""
        return self._post_sync("/api/other_assets/add", {"name": name, "amount": amount, "curr": curr})

    def add_liability_sync(self, name: str, amount: float, curr: str = "CNY") -> bool:
        """同步添加负债"""
        return self._post_sync("/api/liabilities/add", {"name": name, "amount": amount, "curr": curr})

    def delete_cash_asset_sync(self, asset_id: int) -> bool:
        """同步删除现金资产"""
        return self._post_sync("/api/cash_assets/delete", {"id": asset_id})

    def delete_other_asset_sync(self, asset_id: int) -> bool:
        """同步删除其他资产"""
        return self._post_sync("/api/other_assets/delete", {"id": asset_id})

    def delete_liability_sync(self, asset_id: int) -> bool:
        """同步删除负债"""
        return self._post_sync("/api/liabilities/delete", {"id": asset_id})


# 全局 API 客户端实例
api = ApiClient()
