"""
电商URL构造器 - 根据关键词构造各电商平台的搜索URL
"""
from typing import Dict, List, Optional
from urllib.parse import quote


class URLBuilder:
    """电商URL构造器"""

    # 支持的电商平台
    PLATFORMS = {
        "taobao": "https://s.taobao.com/search?q={}",
        "jd": "https://search.jd.com/Search?keyword={}",
        "pinduoduo": "https://mobile.yangkeduo.com/search_result.html?search_key={}",
    }

    # 平台中文名称
    PLATFORM_NAMES = {
        "taobao": "淘宝",
        "jd": "京东",
        "pinduoduo": "拼多多",
    }

    @staticmethod
    def build_search_url(keyword: str, platform: str) -> str:
        """构造单个平台的搜索URL

        Args:
            keyword: 搜索关键词
            platform: 平台名称 (taobao/jd/pinduoduo)

        Returns:
            搜索URL
        """
        if platform not in URLBuilder.PLATFORMS:
            raise ValueError(f"不支持的平台: {platform}，可选: {list(URLBuilder.PLATFORMS.keys())}")

        url_template = URLBuilder.PLATFORMS[platform]
        encoded_keyword = quote(keyword)
        return url_template.format(encoded_keyword)

    @staticmethod
    def build_search_urls(
        keyword: str,
        platforms: Optional[List[str]] = None
    ) -> Dict[str, str]:
        """构造多个平台的搜索URL

        Args:
            keyword: 搜索关键词
            platforms: 平台列表，默认使用所有平台

        Returns:
            {平台名: URL} 的字典
        """
        if platforms is None:
            platforms = list(URLBuilder.PLATFORMS.keys())

        urls = {}
        for platform in platforms:
            urls[platform] = URLBuilder.build_search_url(keyword, platform)

        return urls

    @staticmethod
    def get_platform_name(platform: str) -> str:
        """获取平台中文名称"""
        return URLBuilder.PLATFORM_NAMES.get(platform, platform)


# ==================== 便捷函数 ====================

def build_urls(keyword: str, platforms: Optional[List[str]] = None) -> Dict[str, str]:
    """构造搜索URL（便捷函数）"""
    return URLBuilder.build_search_urls(keyword, platforms)
