"""
生成视频模板 - 用于场景1 Agent 测试
生成一个高质量的商品展示风格视频作为模板（纯文字，无图片）
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tool.video_generator import generate_video


async def main():
    """生成商品展示风格视频模板"""
    print("="*70)
    print("生成视频模板（商品展示风格）")
    print("="*70)

    template_output = str(PROJECT_ROOT / "data" / "output" / "template_video.mp4")

    # 专业商品展示风格 - 纯文字生成
    prompt = """专业商品展示视频。一款时尚现代的产品优雅地展示在干净的表面上，采用电影级灯光照明。视频通过流畅的镜头运动从多个角度展示产品。温暖、专业的商业摄影风格，带有柔和的阴影和高光效果。高质量、高端的产品展示风格。"""

    print(f"\n提示词: {prompt}")
    print(f"模板输出: {template_output}")
    print(f"\n开始生成模板...")

    try:
        video_path = await generate_video(
            model="doubao-seedance-1-0-lite_480p",
            prompt=prompt,
            seconds=10,
            output_path=template_output
        )

        print(f"\n✅ 模板视频生成完成: {video_path}")
        print(f"\n这个模板展示了商品展示风格，可以用于测试场景1 Agent")

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
