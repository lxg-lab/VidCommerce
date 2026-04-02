"""
场景2 Agent - 使用 LangChain 实现爆款视频混剪
任务：分析爆款视频的风格，根据用户需求生成多个变体视频
"""
import asyncio
from typing import List, Optional

from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import StructuredTool
from langchain_openai import ChatOpenAI

from config import RabbitAPI


class Scenario2Agent:
    """场景2 Agent - 爆款视频混剪"""

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

    def _create_tools(
        self,
        source_video: str,
        user_prompt: str,
        count: int,
        output_dir: Optional[str] = None
    ):
        """创建 LangChain 工具 - 路径已预先绑定"""

        # 动态导入，避免循环依赖
        from tool.video_mixer import VideoMixer, VideoMixRequest

        # 共享上下文，用于存储分析结果
        shared_context = {"analysis": ""}

        # 工具1: 分析源视频风格
        def analyze_source_tool(prompt: str) -> str:
            """分析爆款视频的风格特征"""
            from tool.video_analyzer import analyze_video
            result = asyncio.run(analyze_video(prompt=prompt, video_path=source_video))
            # 保存分析结果到共享上下文
            shared_context["analysis"] = result
            return result

        # 工具2: 混剪生成变体视频（使用已有分析结果）
        def mix_variations_tool(prompt: str) -> str:
            """根据用户需求，批量生成变体视频（跳过重复分析）"""
            mixer = VideoMixer()
            request = VideoMixRequest(
                source_video=source_video,
                user_prompt=user_prompt,
                count=count,
                output_dir=output_dir
            )
            # 跳过分析，使用已有的分析结果
            result = asyncio.run(mixer.mix(
                request=request,
                skip_analysis=True,
                existing_analysis=shared_context["analysis"]
            ))
            # 返回结果摘要
            return f"成功生成 {len(result)} 个变体视频：\n" + "\n".join(result)

        return [
            StructuredTool.from_function(
                func=analyze_source_tool,
                name="analyze_source",
                description=f"""分析爆款视频的风格特征（色调、镜头、场景、节奏等）

参数：
- prompt: 分析提示词，如 "请分析这个视频的风格特征"

注意：源视频路径已预先设置为：{source_video}"""
            ),
            StructuredTool.from_function(
                func=mix_variations_tool,
                name="mix_variations",
                description=f"""根据用户需求批量生成变体视频（使用已分析的结果，避免重复分析）

参数：
- prompt: 此参数保留以兼容接口，实际使用预设的用户需求

注意：
- 源视频路径已预先设置为：{source_video}
- 用户需求：{user_prompt}
- 生成数量：{count} 个变体视频
- 会使用 analyze_source 工具的分析结果，避免重复分析
{f"- 输出目录：{output_dir}" if output_dir else ""}"""
            )
        ]

    def _create_agent(self, tools, user_prompt: str, count: int):
        """创建 LangChain Agent"""

        system_prompt = f"""你是视频混剪 Agent。任务：分析爆款视频的风格，根据用户需求生成多个变体视频。

## 工作流程
1. 调用 analyze_source 分析爆款视频的风格特征
2. 调用 mix_variations 批量生成变体视频

## 用户混剪需求
{user_prompt}

## 生成数量
{count} 个变体视频

所有路径已预先配置，你只需要关注分析风格和执行混剪任务。"""

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
        source_video: str,
        user_prompt: str,
        count: int = 2,
        output_dir: Optional[str] = None
    ) -> List[str]:
        """执行场景2任务

        Args:
            source_video: 源爆款视频路径
            user_prompt: 用户混剪需求提示词
            count: 生成数量（默认2个）
            output_dir: 输出目录（可选）

        Returns:
            生成的视频文件路径列表
        """
        print(f"\n{'='*70}")
        print(f"场景2 Agent - 爆款视频混剪")
        print(f"{'='*70}")
        print(f"源视频: {source_video}")
        print(f"用户需求: {user_prompt}")
        print(f"生成数量: {count}")
        print(f"{'='*70}\n")

        # 创建工具（路径已绑定）
        tools = self._create_tools(source_video, user_prompt, count, output_dir)

        # 创建 Agent
        agent = self._create_agent(tools, user_prompt, count)

        # 简单的用户输入
        user_input = "请分析源视频的风格，然后根据用户需求批量生成变体视频。"

        # 执行 Agent
        result = await agent.ainvoke({"input": user_input})

        print(f"\n{'='*70}")
        print(f"✓ Agent 执行完成")
        print(f"{'='*70}\n")

        output = result.get("output", "")

        # 从输出中提取视频路径
        if "成功生成" in output:
            lines = output.split("\n")
            video_paths = [line.strip() for line in lines[1:] if line.strip() and (line.startswith("/") or letter_drive_path(line))]
            return video_paths

        return []


def letter_drive_path(path: str) -> bool:
    """检查是否是 Windows 盘符路径 (如 E:\\...)"""
    return len(path) >= 2 and path[1] == ":" and path[0].isalpha()


# ==================== 便捷函数 ====================

async def mix_video_from_source(
    source_video: str,
    user_prompt: str,
    count: int = 2,
    output_dir: Optional[str] = None
) -> List[str]:
    """场景2便捷函数：从爆款视频生成多个混剪变体

    Args:
        source_video: 源爆款视频路径
        user_prompt: 用户混剪需求提示词
        count: 生成数量（默认2个）
        output_dir: 输出目录（可选）

    Returns:
        生成的视频文件路径列表
    """
    agent = Scenario2Agent()
    return await agent.run(
        source_video=source_video,
        user_prompt=user_prompt,
        count=count,
        output_dir=output_dir
    )
