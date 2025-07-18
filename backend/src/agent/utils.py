# LangGraph 实用工具函数集合
#
# 这个文件包含了支持整个AI研究工作流的辅助函数
# 
# 主要功能模块：
# 1. 消息处理：从对话历史中提取研究主题
# 2. URL管理：将长URL转换为短URL，节省令牌
# 3. 引用处理：提取和插入引用信息
# 4. 文本处理：在指定位置插入引用标记
#
# 设计原则：
# - 单一职责：每个函数只负责一个特定任务
# - 可重用性：函数可以在多个地方安全使用
# - 错误处理：包含适当的异常处理逻辑
# - 性能优化：考虑处理大量数据时的效率

from typing import Any, Dict, List
from langchain_core.messages import AnyMessage, AIMessage, HumanMessage


def get_research_topic(messages: List[AnyMessage]) -> str:
    """
    从消息历史中提取研究主题
    
    这个函数负责将用户的对话转换为清晰的研究主题描述。
    支持单轮对话和多轮对话两种情况。
    
    处理逻辑：
    1. 如果只有一条消息：直接使用该消息内容作为研究主题
    2. 如果有多条消息：将对话历史组织成结构化的格式
    
    使用场景：
    - 在提示词中提供给AI明确的研究背景
    - 帮助AI理解当前的研究上下文
    - 支持多轮对话的上下文保持
    
    Args:
        messages: 消息列表，包含用户和AI的对话历史
        
    Returns:
        str: 格式化的研究主题字符串
        
    示例：
        单轮对话：
        Input: [HumanMessage("分析苹果公司的财报")]
        Output: "分析苹果公司的财报"
        
        多轮对话：
        Input: [
            HumanMessage("苹果公司怎么样？"),
            AIMessage("苹果公司是..."),
            HumanMessage("它的股价如何？")
        ]
        Output: "User: 苹果公司怎么样？\nAssistant: 苹果公司是...\nUser: 它的股价如何？"
    """
    # 单轮对话：直接返回最后一条消息的内容
    if len(messages) == 1:
        research_topic = messages[-1].content
    else:
        # 多轮对话：构建完整的对话历史
        research_topic = ""
        for message in messages:
            if isinstance(message, HumanMessage):
                research_topic += f"User: {message.content}\n"
            elif isinstance(message, AIMessage):
                research_topic += f"Assistant: {message.content}\n"
    
    return research_topic


def resolve_urls(urls_to_resolve: List[Any], id: int) -> Dict[str, str]:
    """
    URL解析和缩短功能
    
    将Google搜索返回的长URL转换为短URL格式，主要目的：
    1. 节省令牌消耗：长URL会占用大量的AI模型令牌
    2. 提高处理速度：短URL减少了文本处理的复杂性
    3. 确保唯一性：每个URL都有唯一的短标识符
    4. 便于管理：短URL更容易在系统中传递和存储
    
    URL映射规则：
    - 原始URL → https://vertexaisearch.cloud.google.com/id/{task_id}-{index}
    - 确保每个原始URL只映射一次，避免重复
    - 使用任务ID确保不同搜索任务之间的URL不冲突
    
    Args:
        urls_to_resolve: Google搜索返回的URL对象列表，每个对象包含web.uri属性
        id: 搜索任务的唯一标识符，用于确保URL的全局唯一性
        
    Returns:
        Dict[str, str]: URL映射字典，{原始URL: 短URL}
        
    使用场景：
    - 在web_research节点中处理搜索结果
    - 在引用系统中管理URL引用
    - 在最终答案中替换URL为原始格式
    
    示例：
        Input: 
        - urls_to_resolve = [obj1.web.uri="https://example.com/very/long/url", ...]
        - id = 5
        
        Output:
        {
            "https://example.com/very/long/url": "https://vertexaisearch.cloud.google.com/id/5-0",
            "https://another.example.com/url": "https://vertexaisearch.cloud.google.com/id/5-1"
        }
    """
    # 短URL的统一前缀
    prefix = f"https://vertexaisearch.cloud.google.com/id/"
    
    # 提取所有原始URL
    urls = [site.web.uri for site in urls_to_resolve]

    # 创建URL映射字典
    # 使用字典确保每个原始URL只映射一次，即使它在列表中出现多次
    resolved_map = {}
    for idx, url in enumerate(urls):
        if url not in resolved_map:
            # 生成唯一的短URL：前缀 + 任务ID + 索引
            resolved_map[url] = f"{prefix}{id}-{idx}"

    return resolved_map


def insert_citation_markers(text, citations_list):
    """
    在文本中插入引用标记
    
    这个函数负责在AI生成的文本中的正确位置插入引用链接。
    采用从后向前插入的策略，确保插入过程不会影响其他位置的索引。
    
    引用插入原理：
    1. 按照结束位置从大到小排序（倒序）
    2. 从文本末尾开始插入引用标记
    3. 这样可以避免前面的插入影响后面位置的索引
    
    Args:
        text (str): 原始文本，由AI生成的搜索结果摘要
        citations_list (list): 引用信息列表，每个元素包含：
            - start_index: 引用文本的开始位置
            - end_index: 引用文本的结束位置
            - segments: 引用的来源信息列表
    
    Returns:
        str: 插入引用标记后的文本
        
    插入格式：
        在指定位置插入格式为 " [来源标题](短URL)" 的引用链接
        
    工作流程：
        1. 对引用列表按end_index降序排序
        2. 为每个引用构建标记字符串
        3. 在指定位置插入标记
        
    示例：
        Input:
        - text: "苹果公司Q3营收增长了15%。特斯拉销量也在上升。"
        - citations_list: [
            {
                "start_index": 0,
                "end_index": 12,
                "segments": [{"label": "Apple财报", "short_url": "https://..."}]
            }
        ]
        
        Output: "苹果公司Q3营收增长了15% [Apple财报](https://...)。特斯拉销量也在上升。"
    """
    # 对引用列表进行排序
    # 1. 主要按end_index降序排列（从后往前处理）
    # 2. 如果end_index相同，按start_index降序排列
    # 这样可以确保插入操作不会影响后续位置的索引
    sorted_citations = sorted(
        citations_list, 
        key=lambda c: (c["end_index"], c["start_index"]), 
        reverse=True
    )

    modified_text = text
    
    # 逐个插入引用标记
    for citation_info in sorted_citations:
        # 获取插入位置（原始文本中的结束位置）
        end_idx = citation_info["end_index"]
        
        # 构建引用标记字符串
        marker_to_insert = ""
        for segment in citation_info["segments"]:
            # 每个来源都生成一个markdown格式的链接
            marker_to_insert += f" [{segment['label']}]({segment['short_url']})"
        
        # 在指定位置插入引用标记
        # 由于我们从后往前处理，end_idx位置仍然有效
        modified_text = (
            modified_text[:end_idx] + marker_to_insert + modified_text[end_idx:]
        )

    return modified_text


def get_citations(response, resolved_urls_map):
    """
    从Gemini模型响应中提取引用信息
    
    这个函数处理Google Gemini模型返回的grounding_metadata，
    将其转换为系统内部使用的引用格式。
    
    处理内容：
    1. 解析grounding_metadata结构
    2. 提取文本段落的位置信息
    3. 匹配对应的网页来源
    4. 构建引用数据结构
    
    Gemini grounding_metadata结构：
    - grounding_supports: 支撑信息列表
      - segment: 文本段落信息
        - start_index: 开始位置
        - end_index: 结束位置
      - grounding_chunk_indices: 引用的来源索引列表
    - grounding_chunks: 来源详细信息
      - web.uri: 网页URL
      - web.title: 网页标题
    
    Args:
        response: Gemini模型的完整响应对象
        resolved_urls_map: URL映射字典 {原始URL: 短URL}
        
    Returns:
        list: 引用信息列表，每个元素包含：
            - start_index: 引用文本的开始位置
            - end_index: 引用文本的结束位置  
            - segments: 来源信息列表
                - label: 来源标题
                - short_url: 短URL
                - value: 原始URL
                
    错误处理：
    - 如果响应结构不完整，返回空列表
    - 如果某个来源信息缺失，跳过该来源
    - 使用try-catch确保部分错误不影响整体处理
    
    使用场景：
    - 在web_research节点中处理搜索结果
    - 为生成的文本添加可追溯的来源信息
    - 支持最终答案中的引用链接
    """
    citations = []

    # 检查响应的基本结构
    if not response or not response.candidates:
        return citations

    candidate = response.candidates[0]
    
    # 检查是否有grounding_metadata
    if (
        not hasattr(candidate, "grounding_metadata")
        or not candidate.grounding_metadata
        or not hasattr(candidate.grounding_metadata, "grounding_supports")
    ):
        return citations

    # 处理每个支撑信息
    for support in candidate.grounding_metadata.grounding_supports:
        citation = {}

        # 检查段落信息是否存在
        if not hasattr(support, "segment") or support.segment is None:
            continue  # 跳过没有段落信息的支撑

        # 提取位置信息
        start_index = (
            support.segment.start_index
            if support.segment.start_index is not None
            else 0
        )

        # end_index是必需的，用于确定引用位置
        if support.segment.end_index is None:
            continue  # 跳过没有结束位置的支撑

        # 设置引用的基本信息
        citation["start_index"] = start_index
        citation["end_index"] = support.segment.end_index

        # 处理来源信息
        citation["segments"] = []
        if (
            hasattr(support, "grounding_chunk_indices")
            and support.grounding_chunk_indices
        ):
            # 遍历每个来源索引
            for ind in support.grounding_chunk_indices:
                try:
                    # 获取来源详细信息
                    chunk = candidate.grounding_metadata.grounding_chunks[ind]
                    
                    # 查找对应的短URL
                    resolved_url = resolved_urls_map.get(chunk.web.uri, None)
                    
                    # 构建来源信息
                    citation["segments"].append(
                        {
                            "label": chunk.web.title.split(".")[:-1][0],  # 提取主标题（去掉文件扩展名）
                            "short_url": resolved_url,                    # 短URL
                            "value": chunk.web.uri,                      # 原始URL
                        }
                    )
                except (IndexError, AttributeError, NameError):
                    # 处理各种可能的错误：
                    # - IndexError: 索引超出范围
                    # - AttributeError: 对象属性不存在
                    # - NameError: 变量未定义
                    # 
                    # 在生产系统中，可以考虑记录这些错误用于调试
                    pass
        
        citations.append(citation)
    
    return citations


# ========== 工具函数设计说明 ==========
#
# 1. 模块化设计：
#    - 每个函数负责一个特定的任务
#    - 函数之间松耦合，便于测试和维护
#    - 可以独立使用和组合使用
#
# 2. 错误处理：
#    - 包含适当的边界条件检查
#    - 使用try-catch处理预期的异常
#    - 优雅降级：部分错误不影响整体功能
#
# 3. 性能考虑：
#    - URL解析使用字典避免重复处理
#    - 引用插入采用倒序避免索引错位
#    - 文本处理考虑大文档的处理效率
#
# 4. 类型安全：
#    - 使用类型注解明确参数和返回值类型
#    - 支持IDE的智能提示和类型检查
#    - 便于代码维护和重构
#
# 5. 文档完备：
#    - 每个函数都有详细的文档字符串
#    - 包含使用示例和错误处理说明
#    - 说明函数的设计思路和使用场景
#
# 这些工具函数是整个系统正常运行的重要支撑，
# 虽然不是核心的AI逻辑，但对系统的稳定性和用户体验至关重要。
