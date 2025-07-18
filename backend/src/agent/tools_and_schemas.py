# LangGraph 数据模型和工具定义
#
# 这个文件定义了系统中使用的数据结构和模式
# 
# 核心作用：
# 1. 确保AI输出的数据格式正确和一致
# 2. 提供类型安全和自动验证
# 3. 支持结构化输出，避免解析错误
# 4. 便于调试和系统集成
#
# 设计理念：
# - 使用Pydantic进行数据验证和序列化
# - 每个模型对应AI的一种输出格式
# - 包含详细的字段描述，帮助AI理解期望的输出

from typing import List
from pydantic import BaseModel, Field


class SearchQueryList(BaseModel):
    """
    搜索查询列表数据模型
    
    这个模型定义了"查询生成"节点的输出格式。
    当AI生成搜索查询时，必须按照这个结构返回数据。
    
    使用场景：
    - 在generate_query节点中，AI使用structured_output输出这种格式
    - 确保返回的查询列表格式正确，包含查询内容和生成理由
    
    设计优势：
    1. 类型安全：确保query字段是字符串列表
    2. 自动验证：Pydantic会自动验证数据格式
    3. 错误处理：格式错误时会给出明确的错误信息
    4. 文档化：Field描述帮助AI理解每个字段的用途
    """
    
    # 搜索查询列表
    # List[str] 确保这是一个字符串列表
    # description 提供给AI的字段说明，帮助AI理解期望的内容
    query: List[str] = Field(
        description="用于网络研究的搜索查询列表。每个查询应该针对研究主题的特定方面，确保查询的多样性和针对性。"
    )
    
    # 查询生成的理由
    # 解释为什么选择这些查询，这有助于：
    # 1. 调试：理解AI的思考过程
    # 2. 质量控制：评估查询的合理性
    # 3. 透明性：让用户了解搜索策略
    rationale: str = Field(
        description="简要解释为什么这些查询与研究主题相关，以及它们如何帮助收集全面的信息。"
    )


class Reflection(BaseModel):
    """
    反思分析结果数据模型
    
    这个模型定义了"反思分析"节点的输出格式。
    当AI分析已收集信息的完整性时，必须按照这个结构返回分析结果。
    
    使用场景：
    - 在reflection节点中，AI评估信息完整性并输出这种格式
    - 系统根据is_sufficient字段决定是否继续搜索
    - 如果需要继续搜索，使用follow_up_queries生成新的搜索任务
    
    工作流程：
    1. AI分析当前收集的所有信息
    2. 判断是否足够回答用户问题
    3. 如果不够，识别具体的知识缺口
    4. 生成针对性的补充搜索查询
    
    决策影响：
    - is_sufficient=True → 进入最终答案生成
    - is_sufficient=False → 继续网络搜索
    """
    
    # 信息充分性判断
    # 这是最关键的决策字段，直接影响工作流的下一步
    # True: 信息已足够，可以生成最终答案
    # False: 信息不足，需要继续搜索
    is_sufficient: bool = Field(
        description="判断已收集的信息摘要是否足够回答用户的问题。如果能够提供全面、准确的答案，则返回True；如果还需要更多信息，则返回False。"
    )
    
    # 知识缺口描述
    # 当信息不充分时，具体说明缺少什么信息
    # 这有助于：
    # 1. 生成针对性的补充查询
    # 2. 调试信息收集过程
    # 3. 提高搜索的精准度
    knowledge_gap: str = Field(
        description="描述当前信息中缺失或需要澄清的内容。如果信息充分，则为空字符串。应该具体指出缺少的信息类型、时间范围或特定方面。"
    )
    
    # 后续查询列表
    # 针对知识缺口生成的补充搜索查询
    # 设计要求：
    # 1. 查询应该针对具体的知识缺口
    # 2. 自包含：每个查询都应该能独立执行
    # 3. 多样性：避免与已有查询重复
    follow_up_queries: List[str] = Field(
        description="用于填补知识缺口的后续搜索查询列表。如果信息充分，则为空列表。每个查询应该针对特定的缺失信息，并且自包含，包含必要的上下文。"
    )


# ========== 数据模型设计原则 ==========
#
# 1. 简洁性：只包含必要的字段，避免复杂性
#    - SearchQueryList: 查询列表 + 理由
#    - Reflection: 判断 + 缺口 + 后续查询
#
# 2. 自描述：通过Field描述清楚每个字段的用途
#    - 帮助AI理解期望的输出内容
#    - 便于代码维护和调试
#
# 3. 类型安全：使用明确的Python类型注解
#    - List[str] 确保是字符串列表
#    - bool 确保是布尔值
#    - str 确保是字符串
#
# 4. 验证友好：Pydantic提供自动验证
#    - 数据类型错误时自动报错
#    - 缺少必需字段时给出明确提示
#
# 5. 扩展性：易于添加新字段而不影响现有功能
#    - 可以添加置信度、优先级等字段
#    - 支持版本化和向后兼容
#
# 6. 集成性：与LangGraph的structured_output无缝集成
#    - 自动序列化为JSON
#    - 支持复杂的嵌套结构
#
# ========== 使用示例 ==========
#
# 在LangGraph节点中使用：
#
# ```python
# # 查询生成节点
# structured_llm = llm.with_structured_output(SearchQueryList)
# result = structured_llm.invoke(prompt)
# # result.query 是查询列表
# # result.rationale 是生成理由
#
# # 反思分析节点  
# structured_llm = llm.with_structured_output(Reflection)
# result = structured_llm.invoke(prompt)
# # result.is_sufficient 用于路由决策
# # result.follow_up_queries 用于继续搜索
# ```
#
# 这种设计确保了AI输出的数据质量和系统的稳定性
