"""
视频分析工具 - 使用 Gemini 2.5 Flash 分析视频内容
"""
import asyncio
import base64
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import httpx

from config import RabbitAPI


@dataclass
class VideoAnalyzeRequest:
    """视频分析请求参数"""
    # 必填参数
    prompt: str
    video_path: str


class VideoAnalyzer:
    """视频分析器"""

    def __init__(self):
        self.api_key = RabbitAPI.API_KEY
        self.model = "gemini-2.5-flash"
        self.max_size_mb = 10
        self.base_url = "https://api.tu-zi.com"

        if not RabbitAPI.is_configured():
            raise RuntimeError("RabbitAPI Key 未配置，请在 .env 文件中设置 RABBIT_API_KEY")

    def _validate_video(self, video_path: str) -> Path:
        """验证视频文件

        Args:
            video_path: 视频文件路径

        Returns:
            Path 对象

        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 格式或大小不符合要求
        """
        path = Path(video_path)

        # 检查文件是否存在
        if not path.exists():
            raise FileNotFoundError(f"❌ 视频文件不存在: {video_path}")

        # 检查文件扩展名
        if path.suffix.lower() != ".mp4":
            raise ValueError(f"❌ 只支持 MP4 格式的视频，当前格式: {path.suffix}")

        # 检查文件大小
        file_size_mb = path.stat().st_size / (1024 * 1024)
        if file_size_mb > self.max_size_mb:
            raise ValueError(
                f"❌ 视频文件过大: {file_size_mb:.2f}MB，"
                f"最大支持 {self.max_size_mb}MB"
            )

        return path

    def _load_video_base64(self, video_path: Path) -> str:
        """加载视频并转换为 base64

        Args:
            video_path: 视频文件 Path 对象

        Returns:
            base64 编码的视频数据
        """
        with open(video_path, "rb") as f:
            video_data = f.read()
        return base64.b64encode(video_data).decode("utf-8")

    async def analyze(self, request: VideoAnalyzeRequest) -> str:
        """分析视频内容

        Args:
            request: 视频分析请求

        Returns:
            AI 分析结果的文本内容
        """
        # 验证视频文件
        video_path = self._validate_video(request.video_path)

        file_size_mb = video_path.stat().st_size / (1024 * 1024)
        print(f"📹 视频文件: {video_path.name}")
        print(f"📊 文件大小: {file_size_mb:.2f}MB")
        print(f"🔍 正在分析...")

        # 加载视频
        video_b64 = self._load_video_base64(video_path)

        # 构建请求
        url = f"{self.base_url}/v1beta/models/{self.model}:generateContent"

        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": request.prompt
                        },
                        {
                            "inline_data": {
                                "mime_type": "video/mp4",
                                "data": video_b64
                            }
                        }
                    ]
                }
            ]
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # 发送请求
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(url, headers=headers, json=payload)

            if response.status_code != 200:
                raise RuntimeError(
                    f"❌ API 请求失败: {response.status_code}\n"
                    f"响应: {response.text}"
                )

            result = response.json()

            # 提取分析结果
            if "candidates" in result and len(result["candidates"]) > 0:
                content = result["candidates"][0]["content"]["parts"][0]["text"]
                print(f"✅ 分析完成！")
                return content
            else:
                raise RuntimeError(f"❌ 响应格式异常: {result}")


# ==================== 便捷函数 ====================

async def analyze_video(
    prompt: str,
    video_path: str
) -> str:
    """分析视频内容（便捷函数）

    Args:
        prompt: 分析提示词
        video_path: 视频文件路径

    Returns:
        AI 分析结果的文本内容
    """
    request = VideoAnalyzeRequest(
        prompt=prompt,
        video_path=video_path
    )

    analyzer = VideoAnalyzer()
    return await analyzer.analyze(request)
