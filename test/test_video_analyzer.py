"""
测试 video_analyzer 工具
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tool.video_analyzer import analyze_video


async def main():
    """测试视频分析"""
    print("="*50)
    print("视频分析工具测试")
    print("="*50)

    video_path = str(PROJECT_ROOT / "data" / "output" / "test_text_only.mp4")
    prompt = "请描述这个视频的内容，画面中有什么？"

    print(f"视频: {video_path}")
    print(f"提示词: {prompt}")
    print()

    try:
        result = await analyze_video(
            prompt=prompt,
            video_path=video_path
        )

        print(f"\n{'='*50}")
        print(f"分析结果:")
        print(f"{'='*50}")
        print(result)
        print(f"{'='*50}")
        print(f"✅ 测试完成！")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
