# LangGraph 工作流核心定义
# 
# 这个文件是整个AI研究代理的"大脑"，定义了AI如何一步步地：
# 1. 理解用户问题并生成搜索查询
# 2. 并行执行网络搜索收集信息  
# 3. 反思分析信息完整性
# 4. 决定是否需要更多研究
# 5. 最终整合所有信息生成答案
#
# 类比：就像一个资深研究员的标准作业流程(SOP)

import os

# 导入我们自定义的工具和数据结构
from agent.tools_and_schemas import SearchQueryList, Reflection
from dotenv import load_dotenv

# LangChain和LangGraph的核心组件
from langchain_core.messages import AIMessage
from langgraph.types import Send
from langgraph.graph import StateGraph
from langgraph.graph import START, END
from langchain_core.runnables import RunnableConfig

# Google AI客户端，用于调用Gemini模型和搜索功能
from google.genai import Client

# 导入我们定义的状态类型和配置
from agent.state import (
    OverallState,           # 整体状态：贯穿整个工作流的信息容器
    QueryGenerationState,   # 查询生成状态：存储生成的搜索关键词
    ReflectionState,        # 反思状态：存储分析结果和后续查询
    WebSearchState,         # 网络搜索状态：单个搜索任务的状态
)
from agent.configuration import Configuration

# 导入所有的提示词模板
from agent.prompts import (
    get_current_date,                # 获取当前日期的工具函数
    query_writer_instructions,       # 查询生成的提示词
    web_searcher_instructions,       # 网络搜索的提示词
    reflection_instructions,         # 反思分析的提示词
    answer_instructions,             # 最终答案生成的提示词
)

# Google Gemini模型的LangChain集成
from langchain_google_genai import ChatGoogleGenerativeAI

# 导入实用工具函数
from agent.utils import (
    get_citations,           # 提取引用信息
    get_research_topic,      # 从消息中提取研究主题
    insert_citation_markers, # 在文本中插入引用标记
    resolve_urls,           # 将长URL转换为短URL
)

# 加载环境变量（如API密钥）
load_dotenv()

# 检查必需的API密钥
if os.getenv("GEMINI_API_KEY") is None:
    raise ValueError("GEMINI_API_KEY is not set")

# 创建Google AI客户端，用于Google搜索API
# 注意：这里使用原生的Google客户端而不是LangChain客户端，
# 因为原生客户端能返回更详细的引用元数据
genai_client = Client(api_key=os.getenv("GEMINI_API_KEY"))


# ========== LangGraph 节点定义 ==========
# 每个节点都是工作流中的一个步骤，负责特定的任务

def generate_query(state: OverallState, config: RunnableConfig) -> QueryGenerationState:
    """
    节点1: 查询生成器
    
    作用：根据用户的问题生成优化的搜索查询关键词
    
    工作原理：
    1. 分析用户问题的核心意图
    2. 考虑时效性（如"最新"、"2024年"等）
    3. 将复杂问题分解为多个具体的搜索查询
    4. 确保查询的多样性，覆盖问题的不同方面
    
    类比：就像一个资深图书管理员，知道如何将你的问题转换为
         最有效的搜索关键词来找到相关信息
    
    Args:
        state: 当前的整体状态，包含用户的问题
        config: 运行时配置，包含模型选择等参数
        
    Returns:
        包含生成的搜索查询列表的状态更新
    """
    # 从配置中获取可自定义的参数
    configurable = Configuration.from_runnable_config(config)

    # 检查是否有自定义的初始搜索查询数量，如果没有则使用配置的默认值
    if state.get("initial_search_query_count") is None:
        state["initial_search_query_count"] = configurable.number_of_initial_queries

    # 初始化 Gemini 2.0 Flash 模型
    # 这个模型专门用于查询生成，速度快且效果好
    llm = ChatGoogleGenerativeAI(
        model=configurable.query_generator_model,  # 默认使用 gemini-2.0-flash
        temperature=1.0,    # 较高的温度确保查询的多样性
        max_retries=2,      # 网络错误时的重试次数
        api_key=os.getenv("GEMINI_API_KEY"),
    )
    
    # 使用结构化输出，确保AI返回的是我们期望的JSON格式
    # 这样可以避免解析错误，提高系统稳定性
    structured_llm = llm.with_structured_output(SearchQueryList)

    # 构建给AI的提示词
    current_date = get_current_date()  # 获取当前日期，确保搜索的时效性
    formatted_prompt = query_writer_instructions.format(
        current_date=current_date,
        research_topic=get_research_topic(state["messages"]),  # 从对话历史中提取研究主题
        number_queries=state["initial_search_query_count"],    # 要生成的查询数量
    )
    
    # 调用AI生成搜索查询
    result = structured_llm.invoke(formatted_prompt)
    
    # 返回状态更新：将生成的查询添加到状态中
    return {"search_query": result.query}


def continue_to_web_research(state: QueryGenerationState):
    """
    路由函数：将搜索查询分发到多个并行的网络搜索节点
    
    作用：为每个搜索查询创建一个独立的搜索任务
    
    工作原理：
    1. 遍历所有生成的搜索查询
    2. 为每个查询创建一个Send消息
    3. LangGraph会并行执行这些搜索任务
    
    类比：就像图书馆管理员同时派出多个助手去不同的书架
         查找资料，提高效率
    
    Args:
        state: 包含搜索查询列表的状态
        
    Returns:
        Send消息列表，每个消息对应一个并行的搜索任务
    """
    return [
        Send("web_research", {"search_query": search_query, "id": int(idx)})
        for idx, search_query in enumerate(state["search_query"])
    ]


def web_research(state: WebSearchState, config: RunnableConfig) -> OverallState:
    """
    节点2: 网络搜索执行器
    
    作用：使用Google搜索API执行实际的网络搜索
    
    工作原理：
    1. 接收一个搜索查询
    2. 调用Google搜索API获取相关网页
    3. 使用Gemini模型分析和总结搜索结果
    4. 提取引用信息和来源链接
    5. 将长URL转换为短URL以节省令牌
    
    类比：就像一个专业的研究助手，不仅能找到信息，
         还能立即分析内容并整理出重点
    
    Args:
        state: 包含单个搜索查询和ID的状态
        config: 运行时配置
        
    Returns:
        包含搜索结果、来源信息等的状态更新
    """
    # 获取配置参数
    configurable = Configuration.from_runnable_config(config)
    
    # 构建搜索提示词
    formatted_prompt = web_searcher_instructions.format(
        current_date=get_current_date(),
        research_topic=state["search_query"],  # 当前要搜索的具体查询
    )

    # 使用Google原生客户端进行搜索
    # 注意：这里不使用LangChain的Google搜索客户端，因为原生客户端
    # 能够返回更详细的引用元数据(grounding_metadata)
    response = genai_client.models.generate_content(
        model=configurable.query_generator_model,
        contents=formatted_prompt,
        config={
            "tools": [{"google_search": {}}],  # 启用Google搜索工具
            "temperature": 0,  # 低温度确保搜索结果的一致性
        },
    )
    
    # 处理搜索结果和引用信息
    # 1. 将复杂的URL转换为简短的ID格式，节省令牌和处理时间
    resolved_urls = resolve_urls(
        response.candidates[0].grounding_metadata.grounding_chunks, 
        state["id"]  # 使用搜索任务的ID来确保URL的唯一性
    )
    
    # 2. 提取引用信息，包括来源标题、URL等
    citations = get_citations(response, resolved_urls)
    
    # 3. 在生成的文本中插入引用标记，如 [来源标题](短URL)
    modified_text = insert_citation_markers(response.text, citations)
    
    # 4. 收集所有的信息源，用于最终的引用列表
    sources_gathered = [item for citation in citations for item in citation["segments"]]

    # 返回状态更新
    return {
        "sources_gathered": sources_gathered,        # 收集的信息源
        "search_query": [state["search_query"]],     # 当前搜索查询（保持数组格式）
        "web_research_result": [modified_text],      # 带引用的搜索结果文本
    }


def reflection(state: OverallState, config: RunnableConfig) -> ReflectionState:
    """
    节点3: 反思分析器
    
    作用：分析已收集的信息是否足够回答用户问题
    
    工作原理：
    1. 评估当前搜索结果的完整性和相关性
    2. 识别信息缺口和不平衡之处
    3. 如果信息不足，生成具体的补充搜索查询
    4. 决定是否需要继续搜索还是可以生成最终答案
    
    类比：就像一个经验丰富的研究主管，审查助手收集的资料，
         判断是否已经足够完成报告，还是需要补充特定方面的信息
    
    Args:
        state: 包含当前所有搜索结果的整体状态
        config: 运行时配置
        
    Returns:
        包含分析结果和后续行动建议的反思状态
    """
    configurable = Configuration.from_runnable_config(config)
    
    # 更新研究循环计数器
    # 这用于跟踪已经进行了多少轮搜索，防止无限循环
    state["research_loop_count"] = state.get("research_loop_count", 0) + 1
    
    # 获取推理模型，默认使用配置中的反思模型
    reasoning_model = state.get("reasoning_model", configurable.reflection_model)

    # 构建反思提示词
    current_date = get_current_date()
    formatted_prompt = reflection_instructions.format(
        current_date=current_date,
        research_topic=get_research_topic(state["messages"]),
        # 将所有搜索结果合并，用分隔符连接
        summaries="\n\n---\n\n".join(state["web_research_result"]),
    )
    
    # 初始化推理模型（通常使用更强大的模型如Gemini 2.5 Flash）
    llm = ChatGoogleGenerativeAI(
        model=reasoning_model,
        temperature=1.0,    # 适中的温度，平衡创造性和准确性
        max_retries=2,
        api_key=os.getenv("GEMINI_API_KEY"),
    )
    
    # 使用结构化输出确保返回格式正确
    result = llm.with_structured_output(Reflection).invoke(formatted_prompt)

    # 返回反思结果
    return {
        "is_sufficient": result.is_sufficient,           # 信息是否充分
        "knowledge_gap": result.knowledge_gap,           # 识别出的知识缺口
        "follow_up_queries": result.follow_up_queries,   # 建议的补充查询
        "research_loop_count": state["research_loop_count"],  # 更新循环计数
        "number_of_ran_queries": len(state["search_query"]),  # 已执行的查询数量
    }


def evaluate_research(
    state: ReflectionState,
    config: RunnableConfig,
) -> OverallState:
    """
    路由函数：决定研究流程的下一步
    
    作用：根据反思结果和配置决定是继续搜索还是生成最终答案
    
    决策逻辑：
    1. 如果AI认为信息已经充分 → 进入最终答案生成
    2. 如果达到最大研究循环次数 → 强制进入最终答案生成
    3. 否则 → 使用补充查询继续搜索
    
    类比：就像项目管理中的检查点，决定项目是否可以进入下一阶段
         还是需要继续当前阶段的工作
    
    Args:
        state: 反思状态，包含分析结果
        config: 运行时配置，包含最大循环次数限制
        
    Returns:
        字符串标识下一个节点，或者Send消息列表用于继续搜索
    """
    configurable = Configuration.from_runnable_config(config)
    
    # 获取最大研究循环次数限制
    max_research_loops = (
        state.get("max_research_loops")
        if state.get("max_research_loops") is not None
        else configurable.max_research_loops
    )
    
    # 决策逻辑
    if state["is_sufficient"] or state["research_loop_count"] >= max_research_loops:
        # 情况1: 信息充分，或者已达到最大循环次数
        return "finalize_answer"
    else:
        # 情况2: 需要继续搜索，为每个补充查询创建新的搜索任务
        return [
            Send(
                "web_research",
                {
                    "search_query": follow_up_query,
                    # 为新查询分配唯一ID，基于已有查询数量
                    "id": state["number_of_ran_queries"] + int(idx),
                },
            )
            for idx, follow_up_query in enumerate(state["follow_up_queries"])
        ]


def finalize_answer(state: OverallState, config: RunnableConfig):
    """
    节点4: 最终答案生成器
    
    作用：整合所有收集的信息，生成结构化的最终答案
    
    工作原理：
    1. 分析所有搜索结果和收集的信息源
    2. 识别重复和相关的信息，进行去重和整理
    3. 使用强大的推理模型生成连贯、全面的答案
    4. 确保所有引用链接正确，来源清晰
    5. 生成最终的AI消息返回给用户
    
    类比：就像一个资深编辑，将研究团队收集的所有资料
         整理成一篇结构清晰、引用准确的研究报告
    
    Args:
        state: 包含所有搜索结果和信息源的整体状态
        config: 运行时配置
        
    Returns:
        包含最终AI消息和整理后信息源的状态更新
    """
    configurable = Configuration.from_runnable_config(config)
    
    # 获取答案生成模型，默认使用最强大的模型
    reasoning_model = state.get("reasoning_model") or configurable.answer_model

    # 构建最终答案生成的提示词
    current_date = get_current_date()
    formatted_prompt = answer_instructions.format(
        current_date=current_date,
        research_topic=get_research_topic(state["messages"]),
        # 合并所有搜索结果，用分隔符清晰地分开
        summaries="\n---\n\n".join(state["web_research_result"]),
    )

    # 初始化推理模型（默认使用 Gemini 2.5 Pro，最强的推理能力）
    llm = ChatGoogleGenerativeAI(
        model=reasoning_model,
        temperature=0,      # 低温度确保答案的一致性和准确性
        max_retries=2,
        api_key=os.getenv("GEMINI_API_KEY"),
    )
    
    # 生成最终答案
    result = llm.invoke(formatted_prompt)

    # 处理引用链接：将短URL替换回原始URL，并整理最终的信息源列表
    unique_sources = []
    for source in state["sources_gathered"]:
        if source["short_url"] in result.content:
            # 将答案中的短URL替换为原始URL
            result.content = result.content.replace(
                source["short_url"], source["value"]
            )
            # 添加到最终的信息源列表中
            unique_sources.append(source)

    # 返回最终结果
    return {
        "messages": [AIMessage(content=result.content)],  # 生成的AI回答
        "sources_gathered": unique_sources,               # 整理后的信息源列表
    }


# ========== LangGraph 图构建 ==========
# 这里定义了整个工作流的结构和连接关系

# 创建状态图构建器
# OverallState 是在整个工作流中传递的状态类型
# Configuration 是运行时配置的模式
builder = StateGraph(OverallState, config_schema=Configuration)

# 添加所有节点到图中
# 每个节点都是一个处理步骤
builder.add_node("generate_query", generate_query)      # 查询生成节点
builder.add_node("web_research", web_research)          # 网络搜索节点  
builder.add_node("reflection", reflection)              # 反思分析节点
builder.add_node("finalize_answer", finalize_answer)    # 最终答案节点

# 定义工作流的起始点
# START 是 LangGraph 的特殊标记，表示图的入口
builder.add_edge(START, "generate_query")

# 添加条件边：从查询生成到并行网络搜索
# continue_to_web_research 函数会为每个查询创建并行的搜索任务
builder.add_conditional_edges(
    "generate_query", 
    continue_to_web_research, 
    ["web_research"]  # 可能的目标节点
)

# 添加简单边：搜索完成后进行反思
builder.add_edge("web_research", "reflection")

# 添加条件边：根据反思结果决定下一步
# evaluate_research 函数决定是继续搜索还是生成最终答案
builder.add_conditional_edges(
    "reflection", 
    evaluate_research, 
    ["web_research", "finalize_answer"]  # 可能的目标节点
)

# 添加简单边：最终答案生成后结束流程
# END 是 LangGraph 的特殊标记，表示图的出口
builder.add_edge("finalize_answer", END)

# 编译图，创建可执行的工作流
# name 参数为图指定一个名称，用于监控和调试
graph = builder.compile(name="pro-search-agent")
