"""
视频混剪工具 - 批量生成变体视频
基于爆款视频风格，根据用户需求生成多个变体视频
"""
import asyncio
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from langchain_openai import ChatOpenAI

from config import OUTPUT_DIR, RabbitAPI
from tool.video_analyzer import analyze_video
from tool.video_generator import generate_video


@dataclass
class VideoMixRequest:
    """视频混剪请求参数"""
    # 必填参数
    source_video: str  # 源爆款视频路径
    user_prompt: str  # 用户混剪需求提示词

    # 可选参数
    count: int = 3  # 生成数量
    model: str = "doubao-seedance-1-0-lite_480p"  # 生成模型
    seconds: int = 10  # 视频时长
    size: str = "1280x720"  # 视频尺寸
    output_dir: Optional[str] = None  # 输出目录

    def __post_init__(self):
        """参数校验"""
        if self.count < 1:
            raise ValueError(f"生成数量必须大于0，当前值: {self.count}")
        if self.count > 10:
            raise ValueError(f"生成数量不能超过10，当前值: {self.count}")


class VideoMixer:
    """视频混剪器 - 批量生成变体视频"""

    def __init__(self):
        self.api_key = RabbitAPI.API_KEY
        self.base_url = f"{RabbitAPI.BASE_URL}/v1"
        self.model = "gemini-2.5-flash"
        self.output_dir = None  # 初始化输出目录

        if not RabbitAPI.is_configured():
            raise RuntimeError("RabbitAPI Key 未配置，请在 .env 文件中设置 RABBIT_API_KEY")

        # 创建 LLM 用于生成变体提示词
        self.llm = ChatOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            model=self.model,
            temperature=0.8  # 较高温度以增加创意和多样性
        )

    def _get_output_dir(self) -> Path:
        """获取输出目录"""
        if self.output_dir:
            return Path(self.output_dir)
        return OUTPUT_DIR

    async def _analyze_source_video(self, video_path: str) -> str:
        """分析源视频风格特征

        Args:
            video_path: 源视频路径

        Returns:
            风格分析结果
        """
        print(f"\n{'='*50}")
        print(f"[1/3] 分析源视频风格")
        print(f"{'='*50}")

        analyze_prompt = """请详细分析这个视频的风格特征，包括：

1. **视觉风格**：色调、光影、构图风格
2. **镜头语言**：镜头运动方式（推拉摇移、运镜节奏）
3. **场景特征**：场景类型、氛围感
4. **节奏特点**：视频节奏快慢、转场风格
5. **核心元素**：最吸引眼球的关键元素

请用简洁准确的语言描述，为后续生成变体视频提供参考。"""

        analysis = await analyze_video(prompt=analyze_prompt, video_path=video_path)
        print(f"\n✓ 风格分析完成")
        return analysis

    async def _generate_variation_prompts(
        self,
        style_analysis: str,
        user_prompt: str,
        count: int
    ) -> List[str]:
        """基于风格分析和用户需求，生成N个变体提示词

        Args:
            style_analysis: 源视频风格分析
            user_prompt: 用户混剪需求
            count: 生成数量

        Returns:
            变体提示词列表
        """
        print(f"\n{'='*50}")
        print(f"[2/3] 生成变体方案")
        print(f"{'='*50}")
        print(f"用户需求: {user_prompt}")
        print(f"生成数量: {count}")

        prompt = f"""你是一位专业的视频创作专家。基于以下信息，生成 {count} 个不同的视频生成提示词。

## 原视频风格分析
{style_analysis}

## 用户混剪需求
{user_prompt}

## 任务要求
请生成 {count} 个风格相似但各有特色的视频生成提示词，每个提示词应该：
1. **保持核心风格**：延续原视频的核心风格元素和氛围感
2. **响应用户需求**：根据用户混剪需求进行创新和变化
3. **明确差异化**：每个变体有明确的差异化特点（场景、镜头、色调、节奏等）
4. **适合AI生成**：提示词要具体生动，适合AI视频生成模型理解

请直接以 JSON 数组格式返回，不要包含其他说明文字：
["提示词1", "提示词2", "提示词3", ...]

每个提示词应该是一段完整的中文描述，长度在50-100字之间。
"""

        try:
            # 调用 LLM 生成
            response = await self.llm.ainvoke(prompt)
            content = response.content.strip()

            # 尝试解析 JSON
            # 移除可能的 markdown 代码块标记
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()

            prompts = json.loads(content)

            if not isinstance(prompts, list):
                raise ValueError("返回的不是数组格式")

            if len(prompts) != count:
                print(f"⚠ 警告：期望生成 {count} 个提示词，实际返回 {len(prompts)} 个")

            print(f"\n✓ 生成了 {len(prompts)} 个变体方案：")
            for i, p in enumerate(prompts, 1):
                print(f"  {i}. {p[:50]}...")

            return prompts

        except json.JSONDecodeError as e:
            raise RuntimeError(f"解析 LLM 返回的 JSON 失败: {e}\n原始内容: {content}")
        except Exception as e:
            raise RuntimeError(f"生成变体提示词失败: {e}")

    async def _batch_generate_videos(
        self,
        prompts: List[str],
        request: VideoMixRequest
    ) -> List[str]:
        """批量并发生成视频

        Args:
            prompts: 变体提示词列表
            request: 混剪请求参数

        Returns:
            生成的视频路径列表
        """
        print(f"\n{'='*50}")
        print(f"[3/3] 批量生成视频")
        print(f"{'='*50}")
        print(f"并发生成 {len(prompts)} 个视频...")

        output_dir = self._get_output_dir()
        output_dir.mkdir(parents=True, exist_ok=True)

        # 创建生成任务
        tasks = []
        for i, prompt in enumerate(prompts, 1):
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            output_path = output_dir / f"mix_{timestamp}_{i}.mp4"

            task = generate_video(
                model=request.model,
                prompt=prompt,
                seconds=request.seconds,
                size=request.size,
                output_path=str(output_path)
            )
            tasks.append(task)

        # 并发执行
        print(f"\n开始并发生成...\n")
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理结果
        success_videos = []
        for i, result in enumerate(results, 1):
            if isinstance(result, Exception):
                print(f"\n❌ 视频 {i} 生成失败: {result}")
            else:
                success_videos.append(result)
                print(f"\n✓ 视频 {i} 生成成功: {result}")

        return success_videos

    async def mix(self, request: VideoMixRequest, skip_analysis: bool = False, existing_analysis: str = "") -> List[str]:
        """执行混剪，生成多个变体视频

        Args:
            request: 视频混剪请求参数
            skip_analysis: 是否跳过视频分析（用于Agent模式，Agent已分析过）
            existing_analysis: 已有的视频分析结果（当skip_analysis=True时使用）

        Returns:
            生成的视频文件路径列表
        """
        print(f"\n{'='*70}")
        print(f"场景2 - 爆款视频混剪")
        print(f"{'='*70}")
        print(f"源视频: {request.source_video}")
        print(f"用户需求: {request.user_prompt}")
        print(f"生成数量: {request.count}")
        print(f"模型: {request.model}")
        print(f"{'='*70}")

        # 绑定输出目录
        self.output_dir = request.output_dir

        # 1. 分析源视频风格（或使用已有分析）
        if skip_analysis and existing_analysis:
            print(f"\n[1/3] 使用已有视频分析")
            style_analysis = existing_analysis
            print(f"✓ 跳过分析，使用Agent提供的分析结果")
        else:
            style_analysis = await self._analyze_source_video(request.source_video)

        # 2. 生成变体提示词
        variation_prompts = await self._generate_variation_prompts(
            style_analysis=style_analysis,
            user_prompt=request.user_prompt,
            count=request.count
        )

        # 3. 批量生成视频
        video_paths = await self._batch_generate_videos(
            prompts=variation_prompts,
            request=request
        )

        print(f"\n{'='*70}")
        print(f"✓ 混剪完成！成功生成 {len(video_paths)}/{request.count} 个视频")
        print(f"{'='*70}\n")

        return video_paths


# ==================== 便捷函数 ====================

async def mix_video(
    source_video: str,
    user_prompt: str,
    count: int = 2,
    model: str = "doubao-seedance-1-0-lite_480p",
    seconds: int = 10,
    size: str = "1280x720",
    output_dir: Optional[str] = None
) -> List[str]:
    """一键混剪视频（便捷函数）

    Args:
        source_video: 源爆款视频路径
        user_prompt: 用户混剪需求提示词
        count: 生成数量（默认2个，最多10个）
        model: 视频生成模型
        seconds: 视频时长
        size: 视频尺寸
        output_dir: 输出目录（可选）

    Returns:
        生成的视频文件路径列表
    """
    request = VideoMixRequest(
        source_video=source_video,
        user_prompt=user_prompt,
        count=count,
        model=model,
        seconds=seconds,
        size=size,
        output_dir=output_dir
    )

    mixer = VideoMixer()
    return await mixer.mix(request)
