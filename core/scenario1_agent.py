"""
场景1 Agent - 使用 LangChain 实现视频模板+产品图→短视频
任务：分析视频模板风格，然后用产品图生成类似风格的视频
"""
import asyncio
from typing import Optional

from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import StructuredTool
from langchain_openai import ChatOpenAI

from config import RabbitAPI
from tool.video_analyzer import analyze_video
from tool.video_generator import generate_video


class Scenario1Agent:
    """场景1 Agent - AI视频生成"""

    def __init__(self):
        self.api_key = RabbitAPI.API_KEY
        self.base_url = f"{RabbitAPI.BASE_URL}/v1"
        self.model = "gemini-2.5-flash"

        if not RabbitAPI.is_configured():
            raise RuntimeError("RabbitAPI Key 未配置，请在 .env 文件中设置 RABBIT_API_KEY")

        # 创建 LLM
        self.llm = ChatOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            model=self.model,
            temperature=0.7
        )

    def _create_tools(self, template_video: str, product_image: str, output_path: Optional[str] = None):
        """创建 LangChain 工具 - 路径已预先绑定"""

        # 工具1: 视频分析（路径已固定）
        def analyze_video_tool(prompt: str) -> str:
            """分析视频内容，提取风格特征"""
            result = asyncio.run(analyze_video(prompt=prompt, video_path=template_video))
            return result

        # 工具2: 视频生成（路径已固定）
        def generate_video_tool(prompt: str) -> str:
            """根据提示词和产品图生成视频"""
            result = asyncio.run(generate_video(
                model="doubao-seedance-1-0-lite_480p",
                prompt=prompt,
                image_path=product_image,
                seconds=10,
                size="1280x720",
                output_path=output_path or None
            ))
            return result

        return [
            StructuredTool.from_function(
                func=analyze_video_tool,
                name="analyze_template",
                description=f"""分析模板视频的风格特征（构图、光线、色调、镜头运动等）

参数：
- prompt: 分析提示词，如 "请分析这个视频的风格特征"

注意：模板视频路径已预先设置为：{template_video}"""
            ),
            StructuredTool.from_function(
                func=generate_video_tool,
                name="generate_product_video",
                description=f"""根据提示词和产品图生成视频

参数：
- prompt: 视频生成提示词，描述想要的风格和内容

注意：
- 产品图片路径已预先设置为：{product_image}
- 模型固定为 doubao-seedance-1-0-lite_480p
- 视频时长10秒，尺寸1280x720
{f"- 输出路径：{output_path}" if output_path else ""}"""
            )
        ]

    def _create_agent(self, tools):
        """创建 LangChain Agent"""

        system_prompt = """你是视频生成 Agent。任务：分析模板视频的风格，然后用产品图生成类似风格的产品视频。

## 工作流程
1. 调用 analyze_template 分析模板视频的风格
2. 根据分析结果，生成产品视频的 prompt
3. 调用 generate_product_video 生成视频

所有路径已预先配置，你只需要关注分析风格和生成合适的 prompt。"""

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}")
        ])

        agent = create_tool_calling_agent(
            llm=self.llm,
            tools=tools,
            prompt=prompt
        )

        return AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            handle_parsing_errors=True
        )

    async def run(
        self,
        template_video: str,
        product_image: str,
        output_path: Optional[str] = None
    ) -> str:
        """执行场景1任务

        Args:
            template_video: 模板视频路径
            product_image: 产品图片路径
            output_path: 输出视频路径（可选）

        Returns:
            生成的视频文件路径
        """
        print(f"\n{'='*70}")
        print(f"场景1 Agent - AI视频生成")
        print(f"{'='*70}")
        print(f"模板视频: {template_video}")
        print(f"产品图片: {product_image}")
        print(f"{'='*70}\n")

        # 创建工具（路径已绑定）
        tools = self._create_tools(template_video, product_image, output_path)

        # 创建 Agent
        agent = self._create_agent(tools)

        # 简单的用户输入
        user_input = "请分析模板视频的风格，然后生成产品视频。"

        # 执行 Agent
        result = await agent.ainvoke({"input": user_input})

        print(f"\n{'='*70}")
        print(f"✓ Agent 执行完成")
        print(f"{'='*70}\n")

        output = result.get("output", "")
        return output


# ==================== 便捷函数 ====================

async def generate_video_from_template(
    template_video: str,
    product_image: str,
    output_path: Optional[str] = None
) -> str:
    """场景1便捷函数：从模板和产品图生成视频

    Args:
        template_video: 模板视频路径
        product_image: 产品图片路径
        output_path: 输出视频路径（可选）

    Returns:
        生成的视频文件路径
    """
    agent = Scenario1Agent()
    return await agent.run(
        template_video=template_video,
        product_image=product_image,
        output_path=output_path
    )
