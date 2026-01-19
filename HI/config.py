"""
配置模块 - 包含应用配置和主题定义
"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# ============================================================
# API 配置
# ============================================================
API_BASE = os.getenv("API_BASE", "http://35.78.253.89:5003")
API_TIMEOUT = int(os.getenv("API_TIMEOUT", "5"))  # 请求超时时间（秒），缩短以避免长时间卡顿


# ============================================================
# Supabase 认证配置
# ============================================================
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")


# ============================================================
# Resend 邮件配置
# ============================================================
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
RESEND_FROM_EMAIL = os.getenv("RESEND_FROM_EMAIL", "咔咔记账 <onboarding@resend.dev>")


# ============================================================
# Brevo 邮件配置（推荐）
# 免费版：300封/天，不需要验证域名
# 获取 API Key: https://app.brevo.com/settings/keys/api
# ============================================================
BREVO_API_KEY = os.getenv("BREVO_API_KEY", "")
BREVO_SENDER_EMAIL = os.getenv("BREVO_SENDER_EMAIL", "")


# ============================================================
# 主题 - 颜色定义
# ============================================================
class Theme:
    """深色主题配色方案"""
    # 背景色
    BG_PRIMARY = "#0A0E1A"      # 主背景
    BG_CARD = "#1A2332"         # 卡片背景
    BG_ELEVATED = "#1F2937"     # 提升层背景
    NAV_BG = "#0F172A"          # 导航栏背景
    
    # 强调色
    ACCENT = "#3B82F6"          # 主强调色
    ACCENT_LIGHT = "#60A5FA"    # 浅强调色
    
    # 文字色
    TEXT_PRIMARY = "#FFFFFF"    # 主文字
    TEXT_SECONDARY = "#94A3B8"  # 次要文字
    TEXT_TERTIARY = "#64748B"   # 辅助文字
    
    # 状态色
    SUCCESS = "#10B981"         # 成功/盈利（绿色）
    DANGER = "#EF4444"          # 危险/亏损（红色）
    
    # 边框
    BORDER = "#1F2937"
    
    # 渐变色
    CARD_GRADIENT = ["#1A2744", "#0F1829"]


# ============================================================
# 设计令牌 - 尺寸常量
# ============================================================
class Spacing:
    """间距常量"""
    XS = 4
    SM = 8
    MD = 12
    LG = 16
    XL = 20
    XXL = 24


class FontSize:
    """字体大小"""
    XS = 9
    SM = 10
    MD = 11
    BASE = 12
    LG = 14
    XL = 16
    XXL = 20
    TITLE = 24
    HERO = 28


class BorderRadius:
    """圆角大小"""
    SM = 6
    MD = 10
    LG = 12
    XL = 16
    XXL = 20


# ============================================================
# 窗口配置
# ============================================================
class Window:
    """窗口尺寸"""
    WIDTH = 393
    HEIGHT = 852
