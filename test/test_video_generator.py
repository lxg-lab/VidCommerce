"""
测试 video_generator 模块的生成方式（异步版本）：
1. 文字生成
2. 图片+文字生成
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.video_generator import VideoGenerator, VideoGenerateRequest, generate_video

# 使用项目根目录构建绝对路径
TEST_IMAGE = PROJECT_ROOT / "data" / "input" / "cat.jpg"


async def test_1_text_only():
    """测试1：文字生成视频"""
    print("\n" + "="*70)
    print("【测试1】文字生成视频")
    print("="*70)

    request = VideoGenerateRequest(
        model="doubao-seedance-1-0-lite_480p",
        prompt="A cat sitting on a wooden table, cinematic lighting, professional photography",
        seconds=10,
        output_path=str(PROJECT_ROOT / "data" / "output" / "test_text_only.mp4")
    )

    generator = VideoGenerator()
    try:
        video_path = await generator.generate(request)
        print(f"✓ 测试1完成: {video_path}")
        return video_path
    finally:
        await generator.close()


async def test_2_image_and_text():
    """测试2：图片+文字生成视频"""
    print("\n" + "="*70)
    print("【测试2】图片+文字生成视频")
    print("="*70)

    request = VideoGenerateRequest(
        model="doubao-seedance-1-0-lite_480p",
        image_path=str(TEST_IMAGE),
        prompt="图像中的形象在赛跑",
        seconds=10,
        output_path=str(PROJECT_ROOT / "data" / "output" / "test_image_and_text.mp4")
    )

    generator = VideoGenerator()
    try:
        video_path = await generator.generate(request)
        print(f"✓ 测试2完成: {video_path}")
        return video_path
    finally:
        await generator.close()


async def test_3_convenience_function():
    """测试3：使用便捷函数"""
    print("\n" + "="*70)
    print("【测试3】便捷函数测试")
    print("="*70)

    video_path = await generate_video(
        model="doubao-seedance-1-0-lite_480p",
        prompt="A beautiful sunset over the ocean",
        seconds=10,
        output_path=str(PROJECT_ROOT / "data" / "output" / "test_convenience.mp4")
    )

    print(f"✓ 测试3完成: {video_path}")
    return video_path


async def test_4_concurrent():
    """测试4：并发生成多个视频"""
    print("\n" + "="*70)
    print("【测试4】并发生成视频（测试异步优势）")
    print("="*70)

    generator = VideoGenerator()

    try:
        # 同时生成3个视频
        requests = [
            VideoGenerateRequest(
                model="doubao-seedance-1-0-lite_480p",
                prompt=f"Video {i+1}: A beautiful scene",
                seconds=10,
                output_path=str(PROJECT_ROOT / "data" / "output" / f"test_concurrent_{i+1}.mp4")
            )
            for i in range(3)
        ]

        # 并发执行
        print("  并发生成3个视频...")
        results = await asyncio.gather(*[
            generator.generate(req) for req in requests
        ])

        print(f"\n✓ 测试4完成，生成了 {len(results)} 个视频")
        return results
    finally:
        await generator.close()


async def main():
    """主测试函数"""
    print("\n" + "="*70)
    print("VideoGenerator 异步生成测试")
    print("="*70)

    # 检查测试图片是否存在
    if not TEST_IMAGE.exists():
        print(f"\n✗ 测试图片不存在: {TEST_IMAGE}")
        print(f"  请先将测试图片放入 {TEST_IMAGE}")
        return

    tests = [
        ("文字生成", test_1_text_only),
        ("图片+文字生成", test_2_image_and_text),
        ("便捷函数", test_3_convenience_function),
        ("并发生成", test_4_concurrent),
    ]

    print(f"\n共有 {len(tests)} 个测试")
    print(f"使用模型: doubao-seedance-1-0-lite_480p")
    print(f"视频时长: 10秒")

    # 选择要运行的测试
    print("\n请选择测试：")
    print("  1 - 文字生成")
    print("  2 - 图片+文字生成")
    print("  3 - 便捷函数测试")
    print("  4 - 并发生成（异步优势）")
    print("  all - 运行所有测试")
    print("  q - 退出")

    choice = input("\n请输入选择: ").strip().lower()

    if choice == "q":
        print("退出测试")
        return

    try:
        if choice == "all":
            for name, test_func in tests:
                await test_func()
        elif choice == "1":
            await test_1_text_only()
        elif choice == "2":
            await test_2_image_and_text()
        elif choice == "3":
            await test_3_convenience_function()
        elif choice == "4":
            await test_4_concurrent()
        else:
            print(f"无效选择: {choice}")
            return
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return

    print("\n" + "="*70)
    print("✓ 所有测试完成！")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(main())
