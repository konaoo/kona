"""
认证模块 - 可扩展的认证系统

支持多种认证方式：
- Supabase (邮箱验证码)
- 微信登录 (未来)
- Google 登录 (未来)
"""
from .manager import auth_manager
from .provider import AuthProvider

__all__ = ['auth_manager', 'AuthProvider']
