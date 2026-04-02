"""
统一配置管理
所有模块通过此文件读取配置，不要直接使用 os.getenv
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# ==================== 项目路径 ====================

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "data" / "output"

# 确保目录存在
DATA_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)


# ==================== API 配置 ====================

class RabbitAPI:
    """兔子AI API配置"""

    BASE_URL = "https://api.tu-zi.com"
    API_KEY = os.getenv("RABBIT_API_KEY", "")

    @classmethod
    def get_headers(cls) -> dict:
        """获取请求头"""
        return {
            "Authorization": f"Bearer {cls.API_KEY}"
        }

    @classmethod
    def is_configured(cls) -> bool:
        """检查是否已配置"""
        return bool(cls.API_KEY)


# ==================== 快捷访问 ====================

def get_config():
    """获取配置字典（方便调试）"""
    return {
        "rabbit_api_key": f"{RabbitAPI.API_KEY[:10]}..." if RabbitAPI.API_KEY else "",
        "base_url": RabbitAPI.BASE_URL,
    }
