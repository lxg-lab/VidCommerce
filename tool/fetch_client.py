"""
网页抓取工具 - 抓取电商页面并转换为 Markdown
使用 httpx + markdownify 实现
"""
import httpx
from markdownify import markdownify as md


class FetchMCPClient:
    """网页抓取客户端 - 抓取网页并转为 Markdown"""

    def __init__(self):
        self.timeout = 30.0
        # 模拟浏览器的 User-Agent
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }

    async def fetch_url(self, url: str, max_length: int = 10000) -> str:
        """抓取URL并返回Markdown内容

        Args:
            url: 要抓取的URL
            max_length: 最大内容长度（字符数）

        Returns:
            Markdown格式的页面内容
        """
        print(f"\n  正在抓取: {url}")

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(
                    url,
                    headers=self.headers,
                    follow_redirects=True,
                )

                if resp.status_code != 200:
                    raise RuntimeError(f"HTTP {resp.status_code}: {url}")

                html = resp.text

            # 转换为 Markdown
            markdown = md(html)

            # 截断到最大长度
            if len(markdown) > max_length:
                markdown = markdown[:max_length]
                print(f"  ⚠ 内容已截断到 {max_length} 字符")

            print(f"  ✓ 抓取成功，内容长度: {len(markdown)} 字符")

            return markdown

        except httpx.TimeoutException:
            raise RuntimeError(f"请求超时: {url}")
        except httpx.RequestError as e:
            raise RuntimeError(f"请求失败: {e}")
        except Exception as e:
            raise RuntimeError(f"抓取页面时出错: {e}")


# ==================== 便捷函数 ====================

async def fetch_webpage(url: str, max_length: int = 10000) -> str:
    """抓取网页并转为 Markdown（便捷函数）

    Args:
        url: 要抓取的URL
        max_length: 最大内容长度

    Returns:
        Markdown格式的页面内容
    """
    client = FetchMCPClient()
    return await client.fetch_url(url, max_length)
