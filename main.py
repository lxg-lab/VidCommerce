"""
VidCommerce 主入口
支持三种场景的视频生成和数据收集
"""
import asyncio
import sys
from pathlib import Path

from config import RabbitAPI, OUTPUT_DIR
from core.scenario1_agent import generate_video_from_template
from core.scenario2_agent import mix_video_from_source
from core.scenario3_agent import Scenario3Agent


def print_banner():
    """打印欢迎横幅"""
    print("\n" + "="*70)
    print(" VidCommerce - AI 电商视频生成与数据收集系统")
    print("="*70)
    print()


def print_menu():
    """打印主菜单"""
    print("\n请选择场景：")
    print("  1. 模板视频+产品图→产品视频")
    print("  2. 爆款视频混剪")
    print("  3. 全网爆款收集")
    print("  0. 退出")
    print()


def check_input_files():
    """检查 input 目录中的文件"""
    input_dir = Path("data/input")

    # 场景1需要的文件
    scenario1_files = {
        "template.mp4": input_dir / "template.mp4",
        "product.jpg": input_dir / "product.jpg"
    }

    # 场景2需要的文件
    scenario2_files = {
        "source.mp4": input_dir / "source.mp4"
    }

    # 场景3需要的文件
    scenario3_files = {
        "watch.jpg": input_dir / "watch.jpg"
    }

    return {
        "scenario1": scenario1_files,
        "scenario2": scenario2_files,
        "scenario3": scenario3_files
    }


def print_file_status():
    """打印文件状态"""
    files = check_input_files()

    print("\n📁 文件状态:")
    print(f"\n  场景1需要: template.mp4 + product.jpg")
    for name, path in files["scenario1"].items():
        status = "✅" if path.exists() else "❌"
        print(f"    {status} {name}")

    print(f"\n  场景2需要: source.mp4")
    for name, path in files["scenario2"].items():
        status = "✅" if path.exists() else "❌"
        print(f"    {status} {name}")

    print(f"\n  场景3需要: watch.jpg")
    for name, path in files["scenario3"].items():
        status = "✅" if path.exists() else "❌"
        print(f"    {status} {name}")
    print()


async def run_scenario1():
    """场景1: 模板视频+产品图→产品视频"""
    input_dir = Path("data/input")
    template_video = input_dir / "template.mp4"
    product_image = input_dir / "product.jpg"

    if not template_video.exists():
        print(f"❌ 缺少文件: data/input/template.mp4")
        return False

    if not product_image.exists():
        print(f"❌ 缺少文件: data/input/product.jpg")
        return False

    print(f"\n使用文件:")
    print(f"  模板视频: {template_video}")
    print(f"  产品图片: {product_image}")
    print()

    try:
        result = await generate_video_from_template(
            template_video=str(template_video),
            product_image=str(product_image)
        )
        print(f"✅ 场景1完成！")
        return True
    except Exception as e:
        print(f"❌ 场景1执行失败: {e}")
        return False


async def run_scenario2():
    """场景2: 爆款视频混剪"""
    input_dir = Path("data/input")
    source_video = input_dir / "source.mp4"

    if not source_video.exists():
        print(f"❌ 缺少文件: data/input/source.mp4")
        return False

    print(f"\n使用文件:")
    print(f"  源视频: {source_video}")
    print(f"  生成数量: 2")
    print()

    try:
        result = await mix_video_from_source(
            source_video=str(source_video),
            user_prompt="生成两个不同风格的版本：一个是青春活力风格（色调更明亮、节奏更轻快），另一个是简约高级风格（色调更冷静、节奏更从容）",
            count=2
        )
        print(f"✅ 场景2完成！生成了 {len(result)} 个视频")
        return True
    except Exception as e:
        print(f"❌ 场景2执行失败: {e}")
        return False


async def run_scenario3():
    """场景3: 全网爆款收集"""
    input_dir = Path("data/input")
    style_image = input_dir / "watch.jpg"

    if not style_image.exists():
        print(f"❌ 缺少文件: data/input/watch.jpg")
        return False

    print(f"\n使用文件:")
    print(f"  风格图片: {style_image}")
    print(f"  目标数量: 5")
    print(f"  平台: 淘宝、京东")
    print()

    try:
        agent = Scenario3Agent()
        result = await agent.run(
            style_image=str(style_image),
            product_count=5,
            platforms=["taobao", "jd"]
        )
        print(f"✅ 场景3完成！")
        return True
    except Exception as e:
        print(f"❌ 场景3执行失败: {e}")
        return False


async def interactive_mode():
    """交互模式主循环"""
    print_banner()

    if not RabbitAPI.is_configured():
        print("❌ 错误: RabbitAPI Key 未配置")
        print("   请在 .env 文件中设置 RABBIT_API_KEY")
        sys.exit(1)

    # 确保目录存在
    Path("data/input").mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    while True:
        print_file_status()
        print_menu()
        choice = input("请输入选项: ").strip()

        if choice == "0":
            print("\n👋 再见！")
            break
        elif choice == "1":
            await run_scenario1()
        elif choice == "2":
            await run_scenario2()
        elif choice == "3":
            await run_scenario3()
        else:
            print("❌ 无效的选择，请重试")

        input("\n按回车继续...")


def main():
    """主函数"""
    asyncio.run(interactive_mode())


if __name__ == "__main__":
    main()
