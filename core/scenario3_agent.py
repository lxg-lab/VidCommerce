"""
场景3 Agent - 使用 LangChain 实现全网爆款收集
任务：分析爆款风格图，搜索并收集符合风格的电商产品信息
"""
import asyncio
import json
from typing import Dict, List, Optional

from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import StructuredTool
from langchain_openai import ChatOpenAI

from config import RabbitAPI


class Scenario3Agent:
    """场景3 Agent - 全网爆款收集"""

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
        style_image: str,
        product_count: int,
        platforms: Optional[List[str]] = None
    ):
        """创建 LangChain 工具 - 路径已预先绑定"""

        # 共享上下文，用于存储分析结果
        shared_context = {"analysis": None}

        # 工具1: 分析图片风格
        def analyze_style_tool(prompt: str) -> str:
            """分析爆款风格图，提取风格特征和搜索关键词"""
            from tool.image_analyzer import analyze_image_style
            result = asyncio.run(analyze_image_style(
                image_path=style_image,
                prompt=prompt or "请分析这个图片的风格特征，用于搜索相似的电商产品"
            ))
            # 保存分析结果到共享上下文
            shared_context["analysis"] = result
            # 返回可读的摘要
            return json.dumps(result, ensure_ascii=False, indent=2)

        # 工具2: 收集产品信息（使用已有分析结果）
        def collect_products_tool(prompt: str) -> str:
            """根据分析结果搜索并收集产品信息（跳过重复分析）"""
            from tool.product_collector import collect_products
            result = asyncio.run(collect_products(
                style_image=style_image,
                product_count=product_count,
                platforms=platforms,
                skip_analysis=True,
                existing_analysis=shared_context["analysis"]
            ))
            # 返回结果摘要
            summary = result.get("summary", {})
            return f"""成功收集产品信息！

- 总数量: {summary.get('total', 0)} 个
- 平台: {', '.join(summary.get('platforms', []))}
- 搜索关键词: {summary.get('search_keyword', 'N/A')}
- 保存路径: {result.get('output_file', 'N/A')}
"""

        return [
            StructuredTool.from_function(
                func=analyze_style_tool,
                name="analyze_style",
                description="""分析爆款风格图，提取风格特征和搜索关键词

参数：
- prompt: 分析提示词，如 "请分析这个图片的风格特征"

注意：风格图片路径已预先设置"""
            ),
            StructuredTool.from_function(
                func=collect_products_tool,
                name="collect_products",
                description=f"""根据分析结果搜索并收集电商产品信息（使用已分析的结果，避免重复分析）

参数：
- prompt: 此参数保留以兼容接口，实际使用预设的分析结果

注意：
- 风格图片路径已预先设置
- 目标数量: {product_count} 个产品
- 平台: {', '.join([f"'{p}'" for p in (platforms or ['淘宝', '京东', '拼多多'])])}
- 会使用 analyze_style 工具的分析结果，避免重复分析"""
            )
        ]

    def _create_agent(self, tools, product_count: int):
        """创建 LangChain Agent"""

        platforms_str = "淘宝、京东、拼多多"

        system_prompt = f"""你是电商产品收集 Agent。任务：分析爆款风格图，搜索并收集符合风格的电商产品信息。

## 工作流程
1. 调用 analyze_style 分析爆款风格图，提取风格特征和搜索关键词
2. 调用 collect_products 搜索并收集产品信息

## 目标数量
{product_count} 个产品

## 支持的平台
{platforms_str}

所有路径已预先配置，你只需要关注分析风格和执行产品收集任务。返回结果时请用中文简洁说明。"""

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
        style_image: str,
        product_count: int = 20,
        platforms: Optional[List[str]] = None
    ) -> Dict:
        """执行场景3任务

        Args:
            style_image: 爆款风格图片路径
            product_count: 目标产品数量（默认20个）
            platforms: 平台列表（可选）

        Returns:
            收集的产品数据
        """
        print(f"\n{'='*70}")
        print(f"场景3 Agent - 全网爆款收集")
        print(f"{'='*70}")
        print(f"风格图片: {style_image}")
        print(f"目标数量: {product_count}")
        if platforms:
            print(f"平台: {', '.join(platforms)}")
        print(f"{'='*70}\n")

        # 创建工具（路径已绑定）
        tools = self._create_tools(style_image, product_count, platforms)

        # 创建 Agent
        agent = self._create_agent(tools, product_count)

        # 简单的用户输入
        user_input = "请分析风格图，然后搜索并收集符合风格的电商产品信息。"

        # 执行 Agent
        result = await agent.ainvoke({"input": user_input})

        print(f"\n{'='*70}")
        print(f"✓ Agent 执行完成")
        print(f"{'='*70}\n")

        return result


# ==================== 辅助函数 ====================

def letter_drive_path(path: str) -> bool:
    """检查是否是 Windows 盘符路径 (如 E:\\...)"""
    return len(path) >= 2 and path[1] == ":" and path[0].isalpha()
