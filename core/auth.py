"""
Flask 认证中间件

提供 JWT token 验证和用户认证装饰器
"""
import jwt
import logging
from functools import wraps
from datetime import datetime, timedelta
from flask import request, jsonify, g
from typing import Optional, Tuple

import config

logger = logging.getLogger(__name__)

# JWT 配置
JWT_SECRET = getattr(config, 'JWT_SECRET', 'your-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRY_HOURS = 24 * 7  # 7 天


def generate_token(user_id: str, email: str) -> str:
    """
    生成 JWT token
    
    Args:
        user_id: 用户 ID
        email: 用户邮箱
        
    Returns:
        JWT token 字符串
    """
    payload = {
        'user_id': user_id,
        'email': email,
        'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRY_HOURS),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> Tuple[bool, Optional[dict]]:
    """
    验证 JWT token
    
    Args:
        token: JWT token 字符串
        
    Returns:
        (是否有效, 用户信息 dict 或 None)
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return True, payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token expired")
        return False, None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        return False, None


def login_required(f):
    """
    登录验证装饰器
    
    使用方式：
        @app.route('/api/protected')
        @login_required
        def protected_route():
            user_id = g.user_id  # 从 g 对象获取用户信息
            email = g.email
            ...
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # 获取 Authorization header
        auth_header = request.headers.get('Authorization', '')
        
        if not auth_header:
            return jsonify({'error': 'Missing Authorization header'}), 401
        
        # 解析 Bearer token
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return jsonify({'error': 'Invalid Authorization header format'}), 401
        
        token = parts[1]
        
        # 验证 token
        valid, payload = verify_token(token)
        if not valid:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        # 将用户信息存入 Flask g 对象
        g.user_id = payload.get('user_id')
        g.email = payload.get('email')
        
        return f(*args, **kwargs)
    
    return decorated


def optional_auth(f):
    """
    可选认证装饰器
    
    如果提供了 token 则验证，否则 user_id 为 None
    用于兼容旧数据（user_id 为空的数据）
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        
        g.user_id = None
        g.email = None
        
        if auth_header:
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() == 'bearer':
                token = parts[1]
                valid, payload = verify_token(token)
                if valid:
                    g.user_id = payload.get('user_id')
                    g.email = payload.get('email')
        
        return f(*args, **kwargs)
    
    return decorated


# ============================================================
# 用户管理
# ============================================================

def get_or_create_user(db, user_id: str, email: str) -> bool:
    """
    获取或创建用户记录
    
    Args:
        db: DatabaseManager 实例
        user_id: 用户 ID
        email: 用户邮箱
        
    Returns:
        是否成功
    """
    conn = db.get_connection()
    cursor = conn.cursor()
    
    try:
        # 检查用户是否存在
        cursor.execute('SELECT id FROM users WHERE id = ?', (user_id,))
        if cursor.fetchone():
            # 更新最后登录时间
            cursor.execute(
                'UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?',
                (user_id,)
            )
        else:
            # 创建新用户
            cursor.execute(
                'INSERT INTO users (id, email) VALUES (?, ?)',
                (user_id, email)
            )
        
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Failed to get/create user: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()
