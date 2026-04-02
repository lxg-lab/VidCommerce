"""
场景3 Agent 测试 - 全网爆款收集
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import RabbitAPI
from core.scenario3_agent import Scenario3Agent


async def test_scenario3_agent():
    """测试场景3 Agent - 全网爆款收集"""

    print("\n" + "="*70)
    print("场景3 Agent 测试 - 全网爆款收集")
    print("="*70)

    # 检查 API 配置
    if not RabbitAPI.is_configured():
        print("❌ 跳过测试: RabbitAPI Key 未配置")
        print("   请在 .env 文件中设置 RABBIT_API_KEY")
        return False

    # 准备测试图片路径
    test_image = "data/input/watch.jpg"

    print(f"\n测试图片路径: {test_image}")
    print(f"目标产品数量: 5")

    # 检查测试图片是否存在
    if not Path(test_image).exists():
        print(f"\n⚠️  测试图片不存在: {test_image}")
        print(f"   请在 data/input/ 目录下放置 watch.jpg 文件")
        return False

    try:
        # 创建 Agent
        agent = Scenario3Agent()

        # 执行场景3任务（收集5个产品进行测试）
        result = await agent.run(
            style_image=test_image,
            product_count=5,  # 测试时只收集5个产品
            platforms=["taobao", "jd"]  # 只使用淘宝和京东
        )

        print("\n" + "="*70)
        print("✓ 测试完成！")
        print("="*70)

        # 显示结果摘要
        output = result.get("output", "")
        print(f"\nAgent 输出:\n{output}")

        return True

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主测试函数"""

    print("\n" + "="*70)
    print("场景3 测试套件")
    print("="*70)

    # 运行 Agent 测试
    agent_success = await test_scenario3_agent()

    # 总结
    print("\n" + "="*70)
    print("测试总结")
    print("="*70)
    print(f"Agent 测试: {'✓ 通过' if agent_success else '✗ 失败'}")
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
