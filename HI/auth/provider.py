"""
认证提供者抽象基类

所有认证方式都需要实现这个接口，便于扩展新的登录方式
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass


@dataclass
class AuthResult:
    """认证结果"""
    success: bool
    user_id: Optional[str] = None
    email: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    error: Optional[str] = None


@dataclass
class UserInfo:
    """用户信息"""
    user_id: str
    email: Optional[str] = None
    name: Optional[str] = None
    avatar: Optional[str] = None
    provider: str = "unknown"


class AuthProvider(ABC):
    """
    认证提供者抽象基类
    
    实现新的登录方式只需继承此类并实现所有抽象方法
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """提供者名称，如 'supabase', 'wechat', 'google'"""
        pass
    
    @abstractmethod
    async def send_code(self, email: str) -> Tuple[bool, Optional[str]]:
        """
        发送验证码
        
        Args:
            email: 邮箱地址
            
        Returns:
            (成功?, 错误信息)
        """
        pass
    
    @abstractmethod
    async def verify_code(self, email: str, code: str) -> AuthResult:
        """
        验证码校验
        
        Args:
            email: 邮箱地址
            code: 验证码
            
        Returns:
            AuthResult 认证结果
        """
        pass
    
    @abstractmethod
    async def refresh_session(self, refresh_token: str) -> AuthResult:
        """
        刷新会话
        
        Args:
            refresh_token: 刷新令牌
            
        Returns:
            AuthResult 新的认证结果
        """
        pass
    
    @abstractmethod
    async def logout(self) -> bool:
        """
        登出
        
        Returns:
            是否成功
        """
        pass
    
    @abstractmethod
    async def get_user(self, access_token: str) -> Optional[UserInfo]:
        """
        获取用户信息
        
        Args:
            access_token: 访问令牌
            
        Returns:
            UserInfo 或 None
        """
        pass
