# LangGraph 状态管理定义
#
# 这个文件定义了在整个AI研究工作流中需要传递和保存的所有状态信息
# 
# 核心概念：
# - 状态(State)就像是一个"信息容器"，在不同的处理步骤之间传递数据
# - 每个节点可以读取状态、修改状态、添加新信息
# - LangGraph会自动管理状态的合并和传递
#
# 类比：就像一份不断更新的工作文档，每个同事处理后都会添加新内容，
#      最终形成完整的项目报告

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TypedDict

# LangGraph的状态管理工具
from langgraph.graph import add_messages
from typing_extensions import Annotated

import operator


class OverallState(TypedDict):
    """
    整体状态：贯穿整个研究工作流的主要状态容器
    
    这是最重要的状态类型，包含了从开始到结束的所有信息。
    每个节点都可以读取和更新这个状态。
    
    类比：就像一个项目文件夹，里面包含了项目的所有资料：
    - 客户需求（用户消息）
    - 搜索计划（搜索查询）  
    - 调研结果（网络搜索结果）
    - 资料来源（信息源）
    - 项目进度（循环计数）等
    """
    
    # 对话历史：用户问题和AI回答的完整记录
    # Annotated[list, add_messages] 表示这是一个消息列表，
    # LangGraph会自动将新消息添加到现有列表中
    messages: Annotated[list, add_messages]
    
    # 搜索查询列表：所有生成的搜索关键词
    # operator.add 表示新的查询会追加到现有列表中
    search_query: Annotated[list, operator.add]
    
    # 网络搜索结果：每次搜索返回的文本内容
    # 每个元素是一次搜索的完整结果（包含引用标记）
    web_research_result: Annotated[list, operator.add]
    
    # 收集的信息源：所有引用的来源信息
    # 包含标题、URL、短链接等详细信息
    sources_gathered: Annotated[list, operator.add]
    
    # 初始搜索查询数量：第一轮要生成多少个搜索查询
    # 这个值可以由用户在前端设置（低/中/高努力程度）
    initial_search_query_count: int
    
    # 最大研究循环次数：防止无限循环的安全限制
    # 如果达到这个次数，即使AI认为信息不够也会强制结束
    max_research_loops: int
    
    # 当前研究循环计数：已经进行了多少轮反思和补充搜索
    # 用于跟踪进度和判断是否达到最大限制
    research_loop_count: int
    
    # 推理模型：用于反思和答案生成的AI模型名称
    # 可以在运行时动态指定，支持不同的模型选择
    reasoning_model: str


class ReflectionState(TypedDict):
    """
    反思状态：AI分析当前信息完整性后的状态
    
    这个状态专门用于"反思"节点，包含AI对已收集信息的分析结果。
    
    工作流程：
    1. AI分析所有搜索结果
    2. 判断信息是否充分回答用户问题  
    3. 如果不充分，识别具体的知识缺口
    4. 生成针对性的补充搜索查询
    
    类比：就像项目经理审查团队提交的资料，判断是否达到客户要求，
         如果不够就明确指出还需要补充哪些方面的信息
    """
    
    # 信息是否充分：AI判断当前收集的信息是否足够回答用户问题
    # True = 可以生成最终答案，False = 需要继续搜索
    is_sufficient: bool
    
    # 知识缺口描述：如果信息不充分，具体缺少什么信息
    # 例如："缺少最新的市场数据"、"需要更多技术细节"等
    knowledge_gap: str
    
    # 后续查询列表：为填补知识缺口而生成的新搜索查询
    # 这些查询会被发送到网络搜索节点继续研究
    follow_up_queries: Annotated[list, operator.add]
    
    # 研究循环计数：更新后的循环次数
    research_loop_count: int
    
    # 已运行查询数量：到目前为止总共执行了多少个搜索查询
    # 用于为新查询分配唯一ID
    number_of_ran_queries: int


class Query(TypedDict):
    """
    单个搜索查询的结构
    
    不只是简单的搜索词，还包含生成该查询的理由，
    这有助于调试和理解AI的思考过程。
    """
    
    # 实际的搜索查询字符串
    query: str
    
    # 生成这个查询的理由：为什么AI认为这个查询有助于回答用户问题
    rationale: str


class QueryGenerationState(TypedDict):
    """
    查询生成状态：查询生成节点的输出状态
    
    这个状态专门用于存储查询生成节点的结果。
    包含多个Query对象，每个都有查询内容和生成理由。
    """
    
    # 生成的搜索查询列表，每个元素包含查询和理由
    search_query: list[Query]


class WebSearchState(TypedDict):
    """
    网络搜索状态：单个搜索任务的状态
    
    这个状态用于并行的网络搜索任务。由于LangGraph支持并行执行，
    每个搜索查询都会创建一个独立的WebSearchState实例。
    
    设计要点：
    - 只包含执行单次搜索所需的最少信息
    - 每个并行任务都有唯一的ID
    - 搜索完成后结果会合并回OverallState
    """
    
    # 要搜索的查询字符串
    search_query: str
    
    # 搜索任务的唯一标识符
    # 用于区分不同的并行搜索任务，确保URL解析的唯一性
    id: str


@dataclass(kw_only=True)
class SearchStateOutput:
    """
    搜索输出状态（数据类形式）
    
    这是一个辅助数据结构，使用dataclass而不是TypedDict。
    目前看起来是为未来扩展预留的，可能用于更复杂的输出格式。
    
    注意：在当前实现中，这个类似乎没有被直接使用，
         主要的状态管理都通过上面的TypedDict类完成。
    """
    
    # 最终的研究报告内容
    # field(default=None) 表示这个字段是可选的，默认值为None
    running_summary: str = field(default=None)


# ========== 状态设计原则说明 ==========
#
# 1. 类型安全：使用TypedDict确保状态字段的类型正确
#
# 2. 自动合并：通过Annotated和operator.add，LangGraph会自动合并来自
#    不同节点的状态更新，例如：
#    - 新的搜索查询会追加到search_query列表
#    - 新的搜索结果会追加到web_research_result列表
#
# 3. 模块化设计：不同的状态类型对应不同的处理阶段：
#    - OverallState: 全局状态，贯穿整个流程
#    - ReflectionState: 反思阶段的专用状态  
#    - QueryGenerationState: 查询生成的专用状态
#    - WebSearchState: 并行搜索的专用状态
#
# 4. 可扩展性：新增状态字段或状态类型都很容易，不会影响现有功能
#
# 5. 调试友好：状态结构清晰，便于调试和监控工作流执行过程
