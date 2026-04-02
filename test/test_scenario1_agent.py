"""
测试场景1 Agent - 视频模板+产品图→短视频
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.scenario1_agent import Scenario1Agent


async def main():
    """测试场景1 Agent"""
    print("="*70)
    print("场景1 Agent 测试")
    print("="*70)

    # 测试参数
    template_video = str(PROJECT_ROOT / "data" / "output" / "template_video.mp4")
    product_image = str(PROJECT_ROOT / "data" / "input" / "watch.jpg")
    output_path = str(PROJECT_ROOT / "data" / "output" / "agent_generated.mp4")

    print(f"\n输入参数:")
    print(f"  模板视频: {template_video}")
    print(f"  产品图片: {product_image}")
    print(f"  输出路径: {output_path}")

    # 检查文件是否存在
    if not Path(template_video).exists():
        print(f"\n❌ 模板视频不存在: {template_video}")
        return

    if not Path(product_image).exists():
        print(f"\n❌ 产品图片不存在: {product_image}")
        return

    print(f"\n开始执行...")

    try:
        agent = Scenario1Agent()
        result = await agent.run(
            template_video=template_video,
            product_image=product_image,
            output_path=output_path
        )

        print(f"\n{'='*70}")
        print(f"最终结果: {result}")
        print(f"{'='*70}")

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
