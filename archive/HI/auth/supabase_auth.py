"""
Supabase 认证提供者

使用 Supabase Auth 实现邮箱验证码登录
"""
import logging
from typing import Optional, Tuple

from .provider import AuthProvider, AuthResult, UserInfo

logger = logging.getLogger(__name__)


class SupabaseAuthProvider(AuthProvider):
    """Supabase 认证提供者"""
    
    def __init__(self, url: str, key: str):
        """
        初始化 Supabase 客户端
        
        Args:
            url: Supabase 项目 URL
            key: Supabase anon key
        """
        self._url = url
        self._key = key
        self._client = None
        self._init_client()
    
    def _init_client(self):
        """初始化 Supabase 客户端"""
        try:
            from supabase import create_client
            self._client = create_client(self._url, self._key)
            logger.info("Supabase client initialized")
        except ImportError:
            logger.error("supabase-py not installed. Run: pip install supabase")
        except Exception as e:
            logger.error(f"Failed to init Supabase client: {e}")
    
    @property
    def name(self) -> str:
        return "supabase"
    
    async def send_code(self, email: str) -> Tuple[bool, Optional[str]]:
        """发送邮箱验证码"""
        if not self._client:
            return False, "Supabase client not initialized"
        
        try:
            # 使用 OTP 方式发送验证码
            response = self._client.auth.sign_in_with_otp({
                "email": email,
                "options": {
                    "should_create_user": True  # 如果用户不存在则创建
                }
            })
            logger.info(f"Verification code sent to {email}")
            return True, None
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to send code: {error_msg}")
            return False, error_msg
    
    async def verify_code(self, email: str, code: str) -> AuthResult:
        """验证邮箱验证码"""
        if not self._client:
            return AuthResult(success=False, error="Supabase client not initialized")
        
        try:
            # 使用 email OTP 验证（8位数字验证码）
            response = self._client.auth.verify_otp({
                "email": email,
                "token": code,
                "type": "email"
            })
            
            if response.user:
                logger.info(f"User verified: {response.user.id}")
                return AuthResult(
                    success=True,
                    user_id=response.user.id,
                    email=response.user.email,
                    access_token=response.session.access_token if response.session else None,
                    refresh_token=response.session.refresh_token if response.session else None
                )
            else:
                return AuthResult(success=False, error="Verification failed")
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to verify code: {error_msg}")
            return AuthResult(success=False, error=error_msg)
    
    async def refresh_session(self, refresh_token: str) -> AuthResult:
        """刷新会话"""
        if not self._client:
            return AuthResult(success=False, error="Supabase client not initialized")
        
        try:
            response = self._client.auth.refresh_session(refresh_token)
            
            if response.session:
                return AuthResult(
                    success=True,
                    user_id=response.user.id if response.user else None,
                    email=response.user.email if response.user else None,
                    access_token=response.session.access_token,
                    refresh_token=response.session.refresh_token
                )
            else:
                return AuthResult(success=False, error="Session refresh failed")
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to refresh session: {error_msg}")
            return AuthResult(success=False, error=error_msg)
    
    async def logout(self) -> bool:
        """登出"""
        if not self._client:
            return False
        
        try:
            self._client.auth.sign_out()
            logger.info("User logged out")
            return True
        except Exception as e:
            logger.error(f"Failed to logout: {e}")
            return False
    
    async def get_user(self, access_token: str) -> Optional[UserInfo]:
        """获取用户信息"""
        if not self._client:
            return None
        
        try:
            response = self._client.auth.get_user(access_token)
            
            if response.user:
                return UserInfo(
                    user_id=response.user.id,
                    email=response.user.email,
                    name=response.user.user_metadata.get("name"),
                    avatar=response.user.user_metadata.get("avatar_url"),
                    provider=self.name
                )
            return None
            
        except Exception as e:
            logger.error(f"Failed to get user: {e}")
            return None
