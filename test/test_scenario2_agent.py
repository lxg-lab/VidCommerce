"""
场景2测试 - 爆款视频混剪
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.scenario2_agent import mix_video_from_source


# 测试配置
SOURCE_VIDEO = str(PROJECT_ROOT / "data" / "output" / "template_video.mp4")


async def test_agent():
    """测试 Agent 模式 - 生成2个混剪视频"""
    print(f"\n{'='*70}")
    print(f"  场景2测试 - 爆款视频混剪（Agent 模式）")
    print(f"{'='*70}\n")

    # 检查源视频是否存在
    if not Path(SOURCE_VIDEO).exists():
        print(f"❌ 源视频不存在: {SOURCE_VIDEO}")
        print(f"   请先运行 test_generate_template.py 生成模板视频\n")
        return

    print(f"源视频: {SOURCE_VIDEO}")
    print(f"用户需求: 生成两个不同风格的版本，一个更青春活力，一个更简约高级")
    print(f"生成数量: 2 个\n")

    try:
        result = await mix_video_from_source(
            source_video=SOURCE_VIDEO,
            user_prompt="生成两个不同风格的版本：一个是青春活力风格（色调更明亮、节奏更轻快），另一个是简约高级风格（色调更冷静、节奏更从容）",
            count=2
        )

        print(f"\n{'='*70}")
        if len(result) == 2:
            print(f"  ✓ 测试通过！")
            print(f"{'='*70}")
            print(f"\n生成的视频:")
            for i, path in enumerate(result, 1):
                print(f"  {i}. {path}")
        else:
            print(f"  ✗ 测试失败：期望生成2个视频，实际生成{len(result)}个")
            print(f"{'='*70}")

    except Exception as e:
        print(f"\n{'='*70}")
        print(f"  ✗ 测试失败: {e}")
        print(f"{'='*70}")
        import traceback
        traceback.print_exc()


async def main():
    """主函数"""
    # 检查源视频
    if not Path(SOURCE_VIDEO).exists():
        print(f"\n{'='*70}")
        print(f"  ⚠ 提示")
        print(f"{'='*70}")
        print(f"  源视频不存在: {SOURCE_VIDEO}")
        print(f"  请先运行以下命令生成模板视频：")
        print(f"  poetry run python test/test_generate_template.py")
        print(f"{'='*70}\n")

        create = input("是否现在生成模板视频？(y/n): ").strip().lower()
        if create == 'y':
            from test.test_generate_template import main as gen_main
            await gen_main()
            print("\n模板视频已生成，现在开始测试场景2...\n")
            await test_agent()
    else:
        await test_agent()


if __name__ == "__main__":
    asyncio.run(main())
