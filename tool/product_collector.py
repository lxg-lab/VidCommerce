"""
产品数据收集器 - 整合分析、抓取、解析，收集完整的产品数据
"""
import asyncio
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from langchain_openai import ChatOpenAI

from config import OUTPUT_DIR, RabbitAPI
from tool.fetch_client import FetchMCPClient
from tool.image_analyzer import ImageAnalyzer
from tool.url_builder import URLBuilder


@dataclass
class CollectionRequest:
    """数据收集请求参数"""
    # 必填参数
    style_image: str  # 风格图片路径

    # 可选参数
    product_count: int = 20  # 目标产品数量
    platforms: Optional[List[str]] = None  # 平台列表，默认所有平台
    skip_analysis: bool = False  # 是否跳过图片分析（用于Agent模式）
    existing_analysis: Optional[Dict] = None  # 已有的分析结果


class ProductCollector:
    """产品数据收集器 - 整合所有组件"""

    def __init__(self):
        self.api_key = RabbitAPI.API_KEY
        self.base_url = f"{RabbitAPI.BASE_URL}/v1"

        if not RabbitAPI.is_configured():
            raise RuntimeError("RabbitAPI Key 未配置，请在 .env 文件中设置 RABBIT_API_KEY")

        # 创建组件
        self.image_analyzer = ImageAnalyzer()
        self.fetch_client = FetchMCPClient()
        self.url_builder = URLBuilder()

        # 创建 LLM 用于解析产品信息
        self.llm = ChatOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            model="gemini-2.5-flash",
            temperature=0.3  # 较低温度以获得更稳定的解析结果
        )

    async def collect(self, request: CollectionRequest) -> Dict:
        """收集产品数据

        Args:
            request: 数据收集请求参数

        Returns:
            {
                "collection_time": "2026-04-03 12:34:56",
                "style_analysis": {...},
                "products": [...],
                "summary": {...},
                "output_file": "data/output/products_20260403_123456.json"
            }
        """
        print(f"\n{'='*70}")
        print(f"场景3 - 全网爆款收集")
        print(f"{'='*70}")
        print(f"风格图片: {request.style_image}")
        print(f"目标数量: {request.product_count}")
        if request.platforms:
            print(f"平台: {', '.join([URLBuilder.get_platform_name(p) for p in request.platforms])}")
        print(f"{'='*70}")

        # 1. 分析图片风格（或使用已有分析）
        if request.skip_analysis and request.existing_analysis:
            print(f"\n[1/4] 使用已有的图片分析")
            style_analysis = request.existing_analysis
            print(f"✓ 跳过分析，使用已有的分析结果")
        else:
            print(f"\n[1/4] 分析图片风格")
            from tool.image_analyzer import ImageAnalyzeRequest
            analyze_request = ImageAnalyzeRequest(
                image_path=request.style_image,
                prompt="请分析这个图片的风格特征，用于搜索相似的电商产品"
            )
            style_analysis = await self.image_analyzer.analyze(analyze_request)

        # 2. 构造搜索URL
        print(f"\n[2/4] 构造电商搜索URL")
        search_keywords = style_analysis.get("search_keywords", [])
        if not search_keywords:
            raise ValueError("分析结果中没有搜索关键词")

        # 使用第一个关键词进行搜索
        primary_keyword = search_keywords[0]
        print(f"  主要关键词: {primary_keyword}")

        platforms = request.platforms or list(URLBuilder.PLATFORMS.keys())
        search_urls = self.url_builder.build_search_urls(primary_keyword, platforms)

        for platform, url in search_urls.items():
            platform_name = URLBuilder.get_platform_name(platform)
            print(f"  {platform_name}: {url}")

        # 3. 抓取页面并解析产品信息
        print(f"\n[3/4] 抓取页面并解析产品信息")
        all_products = []

        for platform, url in search_urls.items():
            platform_name = URLBuilder.get_platform_name(platform)
            print(f"\n  --- {platform_name} ---")

            try:
                # 抓取页面
                markdown = await self.fetch_client.fetch_url(url, max_length=15000)

                # 解析产品信息
                products = await self._parse_products_from_markdown(markdown, platform)

                print(f"  ✓ 找到 {len(products)} 个产品")
                all_products.extend(products)

            except Exception as e:
                print(f"  ✗ 抓取失败: {e}")
                continue

        # 限制数量
        if len(all_products) > request.product_count:
            all_products = all_products[:request.product_count]

        # 4. 保存结果
        print(f"\n[4/4] 保存结果")
        result = {
            "collection_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "style_analysis": style_analysis,
            "products": all_products,
            "summary": {
                "total": len(all_products),
                "platforms": [URLBuilder.get_platform_name(p) for p in search_urls.keys()],
                "search_keyword": primary_keyword
            }
        }

        output_file = await self._save_to_file(result)

        print(f"\n{'='*70}")
        print(f"✓ 收集完成！共 {len(all_products)} 个产品")
        print(f"{'='*70}\n")

        result["output_file"] = output_file
        return result

    async def _parse_products_from_markdown(self, markdown: str, platform: str) -> List[Dict]:
        """从 Markdown 中解析产品信息（使用 LLM）

        Args:
            markdown: 页面 Markdown 内容
            platform: 平台名称

        Returns:
            产品列表
        """
        platform_name = URLBuilder.get_platform_name(platform)

        prompt = f"""请从以下 {platform_name} 搜索页面的 Markdown 内容中提取产品信息。

请提取以下字段（如果存在）：
1. name: 产品名称
2. price: 价格（包含货币符号）
3. image_url: 产品图片链接
4. product_url: 产品详情链接
5. sales_count: 销量（如"1万+"、"500+"）
6. shop_name: 店铺名称

请以 JSON 数组格式返回，只返回数据不要有其他内容：
[{{"name": "...", "price": "...", "image_url": "...", "product_url": "...", "sales_count": "...", "shop_name": "..."}}, ...]

如果没有找到产品信息，返回空数组：[]

Markdown 内容（前10000字符）：
{markdown[:10000]}
"""

        try:
            response = await self.llm.ainvoke(prompt)
            content = response.content.strip()

            # 移除可能的 markdown 代码块标记
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()

            products = json.loads(content)

            if not isinstance(products, list):
                return []

            # 添加 platform 字段
            for product in products:
                product["platform"] = platform_name

            return products

        except json.JSONDecodeError:
            print(f"  ⚠ 解析 JSON 失败")
            return []
        except Exception as e:
            print(f"  ⚠ 解析失败: {e}")
            return []

    async def _save_to_file(self, data: Dict) -> str:
        """保存到本地文件

        Args:
            data: 要保存的数据

        Returns:
            保存的文件路径
        """
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        file_path = OUTPUT_DIR / f"products_{timestamp}.json"

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"  ✓ 已保存: {file_path}")

        return str(file_path)


# ==================== 便捷函数 ====================

async def collect_products(
    style_image: str,
    product_count: int = 20,
    platforms: Optional[List[str]] = None,
    skip_analysis: bool = False,
    existing_analysis: Optional[Dict] = None
) -> Dict:
    """收集产品数据（便捷函数）

    Args:
        style_image: 风格图片路径
        product_count: 目标产品数量
        platforms: 平台列表
        skip_analysis: 是否跳过图片分析
        existing_analysis: 已有的分析结果

    Returns:
        收集结果
    """
    request = CollectionRequest(
        style_image=style_image,
        product_count=product_count,
        platforms=platforms,
        skip_analysis=skip_analysis,
        existing_analysis=existing_analysis
    )

    collector = ProductCollector()
    return await collector.collect(request)
