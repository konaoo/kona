"""
Resend 邮件验证码认证

使用 Resend 发送验证码邮件，本地存储验证码进行验证
用户数据存储在 Supabase
"""
import random
import string
import time
import logging
import uuid
from typing import Dict, Optional, Tuple

from .provider import AuthProvider, AuthResult, UserInfo

logger = logging.getLogger(__name__)


class ResendAuthProvider(AuthProvider):
    """Resend 邮件验证码认证"""
    
    # 验证码存储: {email: {"code": "123456", "expires": timestamp}}
    _codes: Dict[str, dict] = {}
    
    # 用户存储: {email: {"user_id": "xxx", "created_at": timestamp}}
    _users: Dict[str, dict] = {}
    
    # 已登录用户的 token: {access_token: {"user_id": "xxx", "email": "xxx"}}
    _tokens: Dict[str, dict] = {}
    
    def __init__(self, api_key: str, from_email: str = "咔咔记账 <onboarding@resend.dev>"):
        """
        初始化 Resend 客户端
        
        Args:
            api_key: Resend API Key
            from_email: 发件人邮箱（免费账户使用 onboarding@resend.dev）
        """
        self._api_key = api_key
        self._from_email = from_email
        self._client = None
        self._init_client()
    
    def _init_client(self):
        """初始化 Resend 客户端"""
        try:
            import resend
            resend.api_key = self._api_key
            self._client = resend
            logger.info("Resend client initialized")
        except ImportError:
            logger.error("resend not installed. Run: pip install resend")
        except Exception as e:
            logger.error(f"Failed to init Resend client: {e}")
    
    @property
    def name(self) -> str:
        return "resend"
    
    def _generate_code(self, length: int = 6) -> str:
        """生成数字验证码"""
        return ''.join(random.choices(string.digits, k=length))
    
    def _generate_token(self) -> str:
        """生成访问令牌"""
        return str(uuid.uuid4())
    
    async def send_code(self, email: str) -> Tuple[bool, Optional[str]]:
        """发送邮箱验证码"""
        if not self._client:
            return False, "Resend client not initialized"
        
        try:
            # 生成 6 位数字验证码
            code = self._generate_code(6)
            expires = time.time() + 300  # 5 分钟有效期
            
            # 存储验证码
            self._codes[email] = {
                "code": code,
                "expires": expires
            }
            
            # 发送邮件
            params = {
                "from": self._from_email,
                "to": [email],
                "subject": "登录验证码 - 咔咔记账",
                "html": f"""
                <div style="font-family: sans-serif; max-width: 400px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #1a1a1a; margin-bottom: 20px;">登录验证码</h2>
                    <p style="color: #666; margin-bottom: 20px;">您的验证码是：</p>
                    <p style="font-size: 32px; font-weight: bold; color: #3B82F6; letter-spacing: 4px; margin: 20px 0;">
                        {code}
                    </p>
                    <p style="color: #999; font-size: 14px;">验证码有效期 5 分钟，请勿泄露给他人。</p>
                </div>
                """
            }
            
            self._client.Emails.send(params)
            logger.info(f"Verification code sent to {email}")
            return True, None
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to send code: {error_msg}")
            return False, error_msg
    
    async def verify_code(self, email: str, code: str) -> AuthResult:
        """验证邮箱验证码"""
        # 检查验证码是否存在
        stored = self._codes.get(email)
        if not stored:
            return AuthResult(success=False, error="请先获取验证码")
        
        # 检查是否过期
        if time.time() > stored["expires"]:
            del self._codes[email]
            return AuthResult(success=False, error="验证码已过期，请重新获取")
        
        # 验证码匹配
        if stored["code"] != code:
            return AuthResult(success=False, error="验证码错误")
        
        # 验证成功，删除验证码
        del self._codes[email]
        
        # 获取或创建用户
        user = self._users.get(email)
        if not user:
            user = {
                "user_id": str(uuid.uuid4()),
                "email": email,
                "created_at": time.time()
            }
            self._users[email] = user
            logger.info(f"New user created: {user['user_id']}")
        
        # 生成访问令牌
        access_token = self._generate_token()
        refresh_token = self._generate_token()
        
        self._tokens[access_token] = {
            "user_id": user["user_id"],
            "email": email,
            "expires": time.time() + 86400 * 7  # 7 天有效期
        }
        
        logger.info(f"User logged in: {user['user_id']}")
        
        return AuthResult(
            success=True,
            user_id=user["user_id"],
            email=email,
            access_token=access_token,
            refresh_token=refresh_token
        )
    
    async def refresh_session(self, refresh_token: str) -> AuthResult:
        """刷新会话（简单实现，直接返回新 token）"""
        # 这里简单处理，实际应该验证 refresh_token
        return AuthResult(success=False, error="Please login again")
    
    async def logout(self) -> bool:
        """登出"""
        # 简单实现，实际应该清除指定 token
        return True
    
    async def get_user(self, access_token: str) -> Optional[UserInfo]:
        """获取用户信息"""
        token_data = self._tokens.get(access_token)
        if not token_data:
            return None
        
        if time.time() > token_data.get("expires", 0):
            del self._tokens[access_token]
            return None
        
        return UserInfo(
            user_id=token_data["user_id"],
            email=token_data["email"],
            name=None,
            avatar=None,
            provider=self.name
        )
