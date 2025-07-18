# LangGraph 配置管理系统
#
# 这个文件定义了整个AI研究代理的可配置参数
# 
# 配置管理的重要性：
# 1. 灵活性：不同场景可以使用不同的模型和参数
# 2. 可扩展性：新增配置项不影响现有代码
# 3. 环境适配：开发、测试、生产环境可以有不同配置
# 4. 用户定制：前端可以动态传递配置参数
# 5. 成本控制：根据需求选择合适的模型，平衡性能和成本
#
# 设计原则：
# - 使用Pydantic确保配置的类型安全
# - 提供合理的默认值，开箱即用
# - 支持环境变量和运行时配置
# - 包含详细的元数据说明

import os
from pydantic import BaseModel, Field
from typing import Any, Optional

from langchain_core.runnables import RunnableConfig


class Configuration(BaseModel):
    """
    LangGraph 代理的核心配置类
    
    这个类定义了整个AI研究工作流的所有可配置参数。
    所有参数都有合理的默认值，同时支持动态配置。
    
    配置来源优先级：
    1. 运行时传入的参数（最高优先级）
    2. 环境变量
    3. 配置文件中的默认值（最低优先级）
    
    使用场景：
    - 前端用户可以选择不同的"努力程度"影响搜索深度
    - 开发者可以通过环境变量调整模型选择
    - 不同部署环境可以有不同的默认配置
    """

    # ========== AI 模型配置 ==========
    
    query_generator_model: str = Field(
        default="gemini-2.0-flash",
        metadata={
            "description": "用于生成搜索查询的语言模型名称。推荐使用快速、高效的模型，因为查询生成是高频操作。"
        },
    )
    """
    查询生成模型配置
    
    作用：负责将用户问题转换为有效的搜索查询
    要求：速度快、理解能力强、创造性适中
    
    模型选择建议：
    - gemini-2.0-flash: 速度快，适合实时查询生成
    - gemini-1.5-pro: 理解更深入，但速度较慢
    - 可以根据成本和延迟要求调整
    
    影响：这个模型的质量直接影响搜索的准确性和相关性
    """

    reflection_model: str = Field(
        default="gemini-2.5-flash",
        metadata={
            "description": "用于反思分析的语言模型名称。需要强的分析和判断能力，用于评估信息完整性。"
        },
    )
    """
    反思分析模型配置
    
    作用：分析已收集信息的完整性，决定是否需要继续搜索
    要求：强的逻辑分析能力、批判性思维、准确的判断力
    
    模型选择建议：
    - gemini-2.5-flash: 平衡性能和速度
    - gemini-2.5-pro: 最强分析能力，适合复杂判断
    - claude-3-sonnet: 擅长逻辑分析和批判思维
    
    影响：决定了AI何时停止搜索，影响信息收集的充分性
    """

    answer_model: str = Field(
        default="gemini-2.5-pro",
        metadata={
            "description": "用于生成最终答案的语言模型名称。应选择推理能力最强的模型。"
        },
    )
    """
    答案生成模型配置
    
    作用：整合所有信息，生成最终的研究报告
    要求：最强的推理能力、综合分析能力、文档写作能力
    
    模型选择建议：
    - gemini-2.5-pro: 当前最强的推理模型（默认）
    - claude-3-opus: 优秀的写作和分析能力
    - gpt-4-turbo: 强大的综合能力
    
    影响：直接决定最终答案的质量和深度
    """

    # ========== 搜索行为配置 ==========
    
    number_of_initial_queries: int = Field(
        default=3,
        metadata={"description": "初始搜索阶段生成的搜索查询数量。更多查询可以获得更全面的信息，但会增加处理时间。"},
    )
    """
    初始查询数量配置
    
    作用：控制第一轮搜索的广度
    
    取值建议：
    - 1-2: 快速模式，适合简单问题
    - 3-5: 标准模式，平衡速度和质量（默认3）
    - 5+: 深度模式，适合复杂研究问题
    
    前端映射：
    - 低努力程度: 1个查询
    - 中等努力程度: 3个查询  
    - 高努力程度: 5个查询
    
    影响：查询数量越多，初始信息收集越全面，但执行时间越长
    """

    max_research_loops: int = Field(
        default=2,
        metadata={"description": "允许的最大研究循环次数。防止无限循环，同时确保充分的信息收集。"},
    )
    """
    最大研究循环次数配置
    
    作用：控制反思和补充搜索的循环次数，防止无限循环
    
    循环过程：
    初始搜索 → 反思分析 → 补充搜索 → 反思分析 → ... → 最终答案
    
    取值建议：
    - 1: 快速模式，只做一轮反思
    - 2-3: 标准模式，适合大多数问题（默认2）
    - 5+: 深度模式，适合需要多角度验证的复杂问题
    
    前端映射：
    - 低努力程度: 1个循环
    - 中等努力程度: 3个循环
    - 高努力程度: 10个循环
    
    安全机制：即使AI认为信息不足，达到最大循环次数也会强制结束
    """

    @classmethod
    def from_runnable_config(
        cls, config: Optional[RunnableConfig] = None
    ) -> "Configuration":
        """
        从LangGraph运行时配置创建Configuration实例
        
        这是配置系统的核心方法，负责整合多个配置来源：
        1. 运行时传入的参数（config["configurable"]）
        2. 环境变量（os.environ）
        3. 类定义的默认值
        
        配置优先级：
        运行时参数 > 环境变量 > 默认值
        
        Args:
            config: LangGraph的运行时配置，包含用户传入的参数
            
        Returns:
            Configuration: 完整的配置实例
            
        使用示例：
        ```python
        # 在LangGraph节点中
        def my_node(state, config):
            cfg = Configuration.from_runnable_config(config)
            model_name = cfg.query_generator_model
            max_loops = cfg.max_research_loops
        ```
        
        配置传递流程：
        前端 → LangGraph API → RunnableConfig → Configuration
        """
        
        # 提取运行时可配置参数
        # 这些参数通常来自前端用户的设置
        configurable = (
            config["configurable"] if config and "configurable" in config else {}
        )

        # 获取原始配置值
        # 为每个配置字段尝试从环境变量或运行时配置中获取值
        raw_values: dict[str, Any] = {
            name: os.environ.get(name.upper(), configurable.get(name))
            for name in cls.model_fields.keys()
        }

        # 过滤掉空值
        # None值会使用类定义中的默认值
        values = {k: v for k, v in raw_values.items() if v is not None}

        # 创建配置实例
        # Pydantic会自动验证类型和应用默认值
        return cls(**values)


# ========== 配置系统设计说明 ==========
#
# 1. 层次化配置：
#    - 基础层：硬编码的合理默认值
#    - 环境层：通过环境变量覆盖默认值
#    - 运行时层：通过API调用动态传递参数
#
# 2. 类型安全：
#    - 使用Pydantic确保配置值的类型正确
#    - 自动验证和类型转换
#    - 配置错误时给出明确提示
#
# 3. 文档化：
#    - 每个配置项都有详细的metadata描述
#    - 说明配置的作用、影响和建议值
#    - 便于开发者理解和维护
#
# 4. 扩展性：
#    - 新增配置项不会影响现有代码
#    - 支持复杂的配置验证逻辑
#    - 可以添加配置分组和依赖关系
#
# 5. 环境适配：
#    - 开发环境可以使用快速模型
#    - 生产环境可以使用高质量模型
#    - 测试环境可以使用较少的循环次数
#
# ========== 配置使用模式 ==========
#
# 前端用户选择 → 映射到配置参数 → 传递给LangGraph → 影响AI行为
#
# 例如：
# 用户选择"高努力程度" → {
#     "initial_search_query_count": 5,
#     "max_research_loops": 10,
#     "reasoning_model": "gemini-2.5-pro"
# } → 更深入的研究过程
#
# 这种设计让用户可以根据需求平衡速度和质量
