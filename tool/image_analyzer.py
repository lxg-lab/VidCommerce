"""
图片风格分析工具 - 使用 Gemini Vision 分析图片风格
提取风格标签、色调、产品类型和搜索关键词
"""
import base64
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import httpx

from config import RabbitAPI


@dataclass
class ImageAnalyzeRequest:
    """图片分析请求参数"""
    image_path: str
    prompt: str = "请分析这个图片的风格特征，用于搜索相似的电商产品"


class ImageAnalyzer:
    """图片风格分析器 - 使用 Gemini Vision"""

    def __init__(self):
        self.api_key = RabbitAPI.API_KEY
        self.base_url = RabbitAPI.BASE_URL
        self.model = "gemini-2.5-flash"

        if not RabbitAPI.is_configured():
            raise RuntimeError("RabbitAPI Key 未配置，请在 .env 文件中设置 RABBIT_API_KEY")

    def _encode_image(self, image_path: str) -> str:
        """将图片编码为 base64"""
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"图片文件不存在: {image_path}")

        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    async def analyze(self, request: ImageAnalyzeRequest) -> dict:
        """分析图片风格，提取特征和关键词

        Args:
            request: 图片分析请求参数

        Returns:
            分析结果字典:
            {
                "style_tags": ["极简", "科技", "高端"],
                "color_tone": "香槟金色",
                "product_type": "智能手表",
                "search_keywords": ["智能手表", "金属表带", "圆形表盘"],
                "description": "详细描述"
            }
        """
        print(f"\n{'='*50}")
        print(f"分析图片风格")
        print(f"{'='*50}")
        print(f"图片路径: {request.image_path}")

        # 构建分析提示词
        analyze_prompt = f"""{request.prompt}

请提供以下信息，用于在电商平台搜索相似产品：

1. **风格标签**: 3-5个风格关键词（如：极简、复古、科技、文艺、商务等）
2. **色调**: 主要颜色和色调特征（如：香槟金色、黑色、白色等）
3. **产品类型**: 这是什么类型的产品（如：智能手表、耳机、手机等）
4. **搜索关键词**: 5-10个可用于电商搜索的具体关键词（如：智能手表、金属表带、圆形表盘等）

请以 JSON 格式返回，格式如下：
{{
  "style_tags": ["标签1", "标签2", "标签3"],
  "color_tone": "色调描述",
  "product_type": "产品类型",
  "search_keywords": ["关键词1", "关键词2", "关键词3"],
  "description": "整体风格描述"
}}

只返回 JSON，不要有其他说明文字。
"""

        # 编码图片
        base64_image = self._encode_image(request.image_path)

        # 调用 Gemini Vision API
        url = f"{self.base_url}/v1/chat/completions"

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": analyze_prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            "temperature": 0.7
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # 增加超时时间，图片分析可能需要更长时间
        # 禁用代理以避免代理问题
        timeout = httpx.Timeout(120.0, connect=30.0)
        async with httpx.AsyncClient(timeout=timeout, proxy=None) as client:
            resp = await client.post(url, json=payload, headers=headers)

            if resp.status_code != 200:
                raise RuntimeError(f"API 调用失败: {resp.status_code} - {resp.text}")

            result = resp.json()
            content = result["choices"][0]["message"]["content"].strip()

        # 解析 JSON 结果
        # 移除可能的 markdown 代码块标记
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        try:
            analysis = json.loads(content)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"解析 AI 返回的 JSON 失败: {e}\n原始内容: {content}")

        print(f"\n✓ 分析完成:")
        print(f"  风格标签: {', '.join(analysis.get('style_tags', []))}")
        print(f"  色调: {analysis.get('color_tone', 'N/A')}")
        print(f"  产品类型: {analysis.get('product_type', 'N/A')}")
        print(f"  搜索关键词: {', '.join(analysis.get('search_keywords', []))}")

        return analysis


# ==================== 便捷函数 ====================

async def analyze_image_style(
    image_path: str,
    prompt: str = "请分析这个图片的风格特征，用于搜索相似的电商产品"
) -> dict:
    """分析图片风格，提取特征和关键词（便捷函数）

    Args:
        image_path: 图片文件路径
        prompt: 分析提示词

    Returns:
        分析结果字典
    """
    request = ImageAnalyzeRequest(
        image_path=image_path,
        prompt=prompt
    )

    analyzer = ImageAnalyzer()
    return await analyzer.analyze(request)
