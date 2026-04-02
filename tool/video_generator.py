"""
视频生成模块 - 使用兔子AI API（异步版本）
支持文字生成、图片+文字生成两种模式
"""
import asyncio
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import httpx

from config import RabbitAPI, OUTPUT_DIR


@dataclass
class VideoGenerateRequest:
    """视频生成请求参数"""
    # 必填参数
    model: str

    prompt: str
    image_path: Optional[str] = None

    # 视频参数
    seconds: int = 10
    size: str = "1280x720"

    # 输出参数
    output_path: Optional[str] = None

    def __post_init__(self):
        """参数校验"""

        # 校证模型参数
        valid_models = [
            "sora-2", "sora-2-pro",
            "doubao-seedance-1-0-lite_480p",
            "doubao-seedance-1-0-pro_720p",
        ]
        if self.model not in valid_models:
            raise ValueError(f"不支持的模型: {self.model}，可选: {valid_models}")

        # 校准时长
        valid_seconds = [4, 8, 10, 12, 15, 25]
        if self.seconds not in valid_seconds:
            raise ValueError(f"不支持的时长: {self.seconds}秒，可选: {valid_seconds}")


class VideoGenerator:
    """异步视频生成器"""

    def __init__(self):
        self.base_url = RabbitAPI.BASE_URL
        self.api_key = RabbitAPI.API_KEY
        self._client: Optional[httpx.AsyncClient] = None

        if not RabbitAPI.is_configured():
            raise RuntimeError("RabbitAPI Key 未配置，请在 .env 文件中设置 RABBIT_API_KEY")

    async def _get_client(self) -> httpx.AsyncClient:
        """获取或创建 HTTP 客户端"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=300.0,
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
        return self._client

    async def close(self):
        """关闭客户端"""
        if self._client:
            await self._client.aclose()
            self._client = None

    def _get_headers(self) -> dict:
        """获取请求头"""
        return RabbitAPI.get_headers()

    async def _submit_task(self, request: VideoGenerateRequest) -> str:
        """提交视频生成任务，返回任务ID"""
        client = await self._get_client()
        url = f"{self.base_url}/v1/videos"

        # 构建表单数据
        data = {
            "model": request.model,
            "prompt": request.prompt,
            "seconds": str(request.seconds),
            "size": request.size
        }

        # 兔子API必须使用 multipart/form-data
        if request.image_path:
            # 有图片：添加文件
            image_path = Path(request.image_path)
            if not image_path.exists():
                raise FileNotFoundError(f"图片文件不存在: {request.image_path}")

            with open(image_path, "rb") as f:
                files = {
                    "input_reference": (image_path.name, f, "image/jpeg")
                }
                resp = await client.post(url, data=data, files=files)
        else:
            # 无图片：必须传空的 files 字段才能让 httpx 设置 multipart/form-data
            files = {"_": ("", "", "application/octet-stream")}
            resp = await client.post(url, data=data, files=files)

        if resp.status_code != 200:
            raise RuntimeError(f"任务提交失败: {resp.status_code} - {resp.text}")

        result = resp.json()
        task_id = result.get("id")

        if not task_id:
            raise RuntimeError(f"响应中未找到任务ID: {result}")

        return task_id

    async def _get_status(self, task_id: str) -> dict:
        """查询任务状态"""
        client = await self._get_client()
        url = f"{self.base_url}/v1/videos/{task_id}"
        resp = await client.get(url)

        if resp.status_code != 200:
            raise RuntimeError(f"状态查询失败: {resp.status_code} - {resp.text}")

        return resp.json()

    async def _wait_completion(self, task_id: str, timeout: int = 300) -> dict:
        """等待任务完成

        Args:
            task_id: 任务ID
            timeout: 超时时间（秒），默认5分钟

        Returns:
            任务完成后的结果数据
        """
        start_time = time.time()

        print(f"    等待任务完成...")

        while True:
            if time.time() - start_time > timeout:
                raise TimeoutError(f"任务超时（{timeout}秒）: {task_id}")

            status_data = await self._get_status(task_id)
            status = status_data.get("status")
            progress = status_data.get("progress", 0)
            elapsed = int(time.time() - start_time)

            # 打印进度
            print(f"    状态: {status:12} | 进度: {progress:3}% | 已等待: {elapsed}秒", end="\r")

            if status == "completed":
                print(f"\n    ✓ 任务完成！")
                return status_data
            elif status == "succeeded":
                print(f"\n    ✓ 任务完成！")
                return status_data
            elif status == "failed":
                error = status_data.get("error", status_data.get("message", "未知错误"))
                print(f"\n    ✗ 任务失败: {error}")
                raise RuntimeError(f"任务失败: {error}")

            await asyncio.sleep(5)

    async def _download_video(self, task_id: str, save_path: str) -> str:
        """下载视频

        Args:
            task_id: 任务ID
            save_path: 保存路径

        Returns:
            实际保存的文件路径
        """
        client = await self._get_client()
        url = f"{self.base_url}/v1/videos/{task_id}/content"
        resp = await client.get(url, timeout=60.0)

        if resp.status_code != 200:
            raise RuntimeError(f"视频下载失败: {resp.status_code} - {resp.text}")

        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)

        with open(save_path, "wb") as f:
            f.write(resp.content)

        file_size = len(resp.content) / (1024 * 1024)
        print(f"    ✓ 视频已保存: {save_path} ({file_size:.2f} MB)")

        return str(save_path)

    async def generate(self, request: VideoGenerateRequest) -> str:
        """生成视频

        Args:
            request: 视频生成请求参数

        Returns:
            生成的视频文件路径
        """
        print(f"\n{'='*50}")
        print(f"开始生成视频")
        print(f"{'='*50}")
        print(f"  模型: {request.model}")
        print(f"  时长: {request.seconds}秒")
        print(f"  尺寸: {request.size}")
        if request.prompt:
            print(f"  提示词: {request.prompt}")
        if request.image_path:
            print(f"  图片: {request.image_path}")

        # 1. 提交任务
        print(f"\n  [1/3] 提交任务...")
        task_id = await self._submit_task(request)
        print(f"    ✓ 任务ID: {task_id}")

        # 2. 等待完成
        print(f"\n  [2/3] 等待生成...")
        result = await self._wait_completion(task_id)

        # 3. 下载视频
        print(f"\n  [3/3] 下载视频...")

        # 确定输出路径
        if request.output_path:
            output_path = request.output_path
        else:
            # 使用默认路径：data/output/video_{timestamp}.mp4
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            output_path = OUTPUT_DIR / f"video_{timestamp}.mp4"

        video_path = await self._download_video(task_id, output_path)

        print(f"\n{'='*50}")
        print(f"✓ 视频生成完成！")
        print(f"{'='*50}\n")

        return video_path


# ==================== 便捷函数 ====================

async def generate_video(
    model: str,
    prompt: str = "",
    image_path: Optional[str] = None,
    seconds: int = 10,
    size: str = "1280x720",
    output_path: Optional[str] = None
) -> str:
    """一键生成视频（便捷函数）

    Args:
        model: 模型名称（如 sora-2, doubao-seedance-1-0-lite_480p）
        prompt: 文字提示词
        image_path: 图片路径（可选）
        seconds: 视频时长（秒）
        size: 视频尺寸
        output_path: 输出路径（可选）

    Returns:
        生成的视频文件路径
    """
    request = VideoGenerateRequest(
        model=model,
        prompt=prompt,
        image_path=image_path,
        seconds=seconds,
        size=size,
        output_path=output_path
    )

    generator = VideoGenerator()
    try:
        return await generator.generate(request)
    finally:
        await generator.close()
