"""
Brevo (Sendinblue) 邮件验证码认证

免费版：300封/天，不需要验证域名
开发模式：使用固定验证码 123456
"""
import random
import string
import time
import logging
import uuid
import requests
from typing import Dict, Optional, Tuple

from .provider import AuthProvider, AuthResult, UserInfo
from config import DEV_MODE, DEV_VERIFICATION_CODE

logger = logging.getLogger(__name__)


class BrevoAuthProvider(AuthProvider):
    """Brevo 邮件验证码认证"""
    
    # 验证码存储: {email: {"code": "123456", "expires": timestamp}}
    _codes: Dict[str, dict] = {}
    
    # 用户存储: {email: {"user_id": "xxx", "created_at": timestamp}}
    _users: Dict[str, dict] = {}
    
    # 已登录用户的 token: {access_token: {"user_id": "xxx", "email": "xxx"}}
    _tokens: Dict[str, dict] = {}
    
    def __init__(self, api_key: str, sender_email: str, sender_name: str = "咔咔记账"):
        """
        初始化 Brevo 客户端
        
        Args:
            api_key: Brevo API Key
            sender_email: 发件人邮箱（你的注册邮箱）
            sender_name: 发件人名称
        """
        self._api_key = api_key
        self._sender_email = sender_email
        self._sender_name = sender_name
        self._api_url = "https://api.brevo.com/v3/smtp/email"
        logger.info("Brevo client initialized")
    
    @property
    def name(self) -> str:
        return "brevo"
    
    def _generate_code(self, length: int = 6) -> str:
        """生成数字验证码"""
        return ''.join(random.choices(string.digits, k=length))
    
    def _generate_token(self) -> str:
        """生成访问令牌"""
        return str(uuid.uuid4())
    
    async def send_code(self, email: str) -> Tuple[bool, Optional[str]]:
        """发送邮箱验证码"""
        try:
            # 🔧 开发模式：使用固定验证码
            if DEV_MODE:
                code = DEV_VERIFICATION_CODE
                expires = time.time() + 3600  # 1小时有效期（开发模式延长时间）

                # 存储验证码
                self._codes[email] = {
                    "code": code,
                    "expires": expires
                }

                logger.info(f"🔧 DEV MODE: Verification code for {email} is {code}")
                return True, None

            # 生成 6 位数字验证码
            code = self._generate_code(6)
            expires = time.time() + 300  # 5 分钟有效期
            
            # 存储验证码
            self._codes[email] = {
                "code": code,
                "expires": expires
            }
            
            # 发送邮件
            headers = {
                "accept": "application/json",
                "api-key": self._api_key,
                "content-type": "application/json"
            }
            
            payload = {
                "sender": {
                    "name": self._sender_name,
                    "email": self._sender_email
                },
                "to": [{"email": email}],
                "subject": "登录验证码 - 咔咔记账",
                "htmlContent": f"""
                <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 400px; margin: 0 auto; padding: 30px; background: #f5f5f5;">
                    <div style="background: white; padding: 30px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                        <h2 style="color: #1a1a1a; margin: 0 0 20px 0; font-size: 20px;">登录验证码</h2>
                        <p style="color: #666; margin: 0 0 20px 0; font-size: 14px;">您的验证码是：</p>
                        <div style="background: #f0f7ff; padding: 20px; border-radius: 8px; text-align: center; margin: 0 0 20px 0;">
                            <span style="font-size: 36px; font-weight: bold; color: #3B82F6; letter-spacing: 8px;">{code}</span>
                        </div>
                        <p style="color: #999; font-size: 12px; margin: 0;">验证码有效期 5 分钟，请勿泄露给他人。</p>
                    </div>
                </div>
                """
            }
            
            response = requests.post(self._api_url, json=payload, headers=headers, timeout=10)
            
            if response.status_code in [200, 201]:
                logger.info(f"Verification code sent to {email}")
                return True, None
            else:
                error_msg = response.json().get("message", f"HTTP {response.status_code}")
                logger.error(f"Failed to send code: {error_msg}")
                return False, error_msg
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to send code: {error_msg}")
            return False, error_msg
    
    async def verify_code(self, email: str, code: str) -> AuthResult:
        """验证邮箱验证码"""
        # 🔧 开发模式：自动接受固定验证码
        if DEV_MODE and code == DEV_VERIFICATION_CODE:
            # 直接通过验证，不检查存储的验证码
            logger.info(f"🔧 DEV MODE: Auto-accepting verification code for {email}")

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

        # 正常模式：检查验证码是否存在
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
        """刷新会话"""
        return AuthResult(success=False, error="Please login again")
    
    async def logout(self) -> bool:
        """登出"""
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
