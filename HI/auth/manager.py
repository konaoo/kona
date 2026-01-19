"""
认证管理器

统一管理认证状态、Token 存储、提供者切换
"""
import os
import json
import logging
from typing import Optional, Callable, Dict, Any
from pathlib import Path

from .provider import AuthProvider, AuthResult, UserInfo

logger = logging.getLogger(__name__)


class AuthManager:
    """
    认证管理器
    
    - 管理当前认证提供者
    - 管理认证状态 (token, user_id)
    - 持久化 token 到本地
    - 提供统一的认证接口
    """
    
    def __init__(self):
        self._provider: Optional[AuthProvider] = None
        self._access_token: Optional[str] = None
        self._refresh_token: Optional[str] = None
        self._user_id: Optional[str] = None
        self._email: Optional[str] = None
        self._user_info: Optional[UserInfo] = None
        self._on_auth_change: Optional[Callable[[bool], None]] = None
        
        # Token 存储路径
        self._storage_path = Path.home() / ".kona" / "auth.json"
        
        # 尝试加载已保存的 token
        self._load_stored_auth()
    
    def set_provider(self, provider: AuthProvider):
        """
        设置认证提供者
        
        Args:
            provider: 认证提供者实例
        """
        self._provider = provider
        logger.info(f"Auth provider set to: {provider.name}")
    
    def set_on_auth_change(self, callback: Callable[[bool], None]):
        """
        设置认证状态变化回调
        
        Args:
            callback: 回调函数，参数为是否已登录
        """
        self._on_auth_change = callback
    
    @property
    def is_logged_in(self) -> bool:
        """是否已登录"""
        return self._access_token is not None
    
    @property
    def user_id(self) -> Optional[str]:
        """当前用户 ID"""
        return self._user_id
    
    @property
    def email(self) -> Optional[str]:
        """当前用户邮箱"""
        return self._email
    
    @property
    def access_token(self) -> Optional[str]:
        """访问令牌"""
        return self._access_token
    
    @property
    def user_info(self) -> Optional[UserInfo]:
        """用户信息"""
        return self._user_info
    
    async def send_code(self, email: str) -> tuple[bool, Optional[str]]:
        """
        发送验证码
        
        Args:
            email: 邮箱地址
            
        Returns:
            (成功?, 错误信息)
        """
        if not self._provider:
            return False, "No auth provider configured"
        
        return await self._provider.send_code(email)
    
    async def verify_code(self, email: str, code: str) -> AuthResult:
        """
        验证码校验并登录
        
        Args:
            email: 邮箱地址
            code: 验证码
            
        Returns:
            AuthResult
        """
        if not self._provider:
            return AuthResult(success=False, error="No auth provider configured")
        
        result = await self._provider.verify_code(email, code)
        
        if result.success:
            self._access_token = result.access_token
            self._refresh_token = result.refresh_token
            self._user_id = result.user_id
            self._email = result.email
            
            # 保存到本地
            self._save_auth()
            
            # 通知状态变化
            if self._on_auth_change:
                self._on_auth_change(True)
            
            logger.info(f"User logged in: {self._user_id}")
            
            # 异步同步到后端（不阻塞登录流程）
            import threading
            threading.Thread(
                target=self._sync_with_backend,
                args=(result.user_id, email),
                daemon=True
            ).start()
        
        return result
    
    def _sync_with_backend(self, user_id: str, email: str):
        """同步用户信息到后端，获取 JWT token"""
        try:
            from api import api
            backend_token = api.login_sync(user_id, email)
            if backend_token:
                logger.info(f"Backend JWT token obtained for user: {user_id}")
            else:
                logger.warning("Failed to get backend JWT token")
        except Exception as e:
            logger.error(f"Failed to sync with backend: {e}")
    
    async def refresh_session(self) -> bool:
        """
        刷新会话
        
        Returns:
            是否成功
        """
        if not self._provider or not self._refresh_token:
            return False
        
        result = await self._provider.refresh_session(self._refresh_token)
        
        if result.success:
            self._access_token = result.access_token
            self._refresh_token = result.refresh_token
            self._save_auth()
            logger.info("Session refreshed")
            return True
        
        return False
    
    async def logout(self):
        """登出"""
        if self._provider:
            await self._provider.logout()
        
        self._access_token = None
        self._refresh_token = None
        self._user_id = None
        self._email = None
        self._user_info = None
        
        # 清除本地存储
        self._clear_stored_auth()
        
        # 通知状态变化
        if self._on_auth_change:
            self._on_auth_change(False)
        
        logger.info("User logged out")
    
    async def get_current_user(self) -> Optional[UserInfo]:
        """获取当前用户信息"""
        if not self._provider or not self._access_token:
            return None
        
        self._user_info = await self._provider.get_user(self._access_token)
        return self._user_info
    
    def get_auth_header(self) -> Dict[str, str]:
        """
        获取 API 请求的认证头
        
        Returns:
            {"Authorization": "Bearer <token>"}
        """
        if self._access_token:
            return {"Authorization": f"Bearer {self._access_token}"}
        return {}
    
    def _save_auth(self):
        """保存认证信息到本地"""
        try:
            self._storage_path.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                "access_token": self._access_token,
                "refresh_token": self._refresh_token,
                "user_id": self._user_id,
                "email": self._email,
                "provider": self._provider.name if self._provider else None
            }
            
            with open(self._storage_path, 'w') as f:
                json.dump(data, f)
            
            logger.debug("Auth saved to local storage")
        except Exception as e:
            logger.error(f"Failed to save auth: {e}")
    
    def _load_stored_auth(self):
        """从本地加载认证信息"""
        try:
            if self._storage_path.exists():
                with open(self._storage_path, 'r') as f:
                    data = json.load(f)
                
                self._access_token = data.get("access_token")
                self._refresh_token = data.get("refresh_token")
                self._user_id = data.get("user_id")
                self._email = data.get("email")
                
                if self._access_token:
                    logger.info(f"Auth loaded from storage: {self._user_id}")
        except Exception as e:
            logger.error(f"Failed to load auth: {e}")
    
    def _clear_stored_auth(self):
        """清除本地存储的认证信息"""
        try:
            if self._storage_path.exists():
                os.remove(self._storage_path)
                logger.debug("Auth storage cleared")
        except Exception as e:
            logger.error(f"Failed to clear auth storage: {e}")


# 全局认证管理器实例
auth_manager = AuthManager()
