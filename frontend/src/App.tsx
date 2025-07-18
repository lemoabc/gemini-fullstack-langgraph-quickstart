// React 前端主应用组件
//
// 这是整个前端应用的核心组件，负责：
// 1. 与LangGraph后端建立WebSocket连接
// 2. 管理应用的全局状态
// 3. 处理用户输入和AI响应
// 4. 实时显示AI的工作进展
// 5. 在不同界面之间进行路由切换
//
// 架构设计：
// - 使用LangGraph SDK的useStream hook进行实时通信
// - 状态管理：React useState管理组件状态
// - 事件处理：实时处理LangGraph的执行事件
// - 界面切换：根据消息状态显示不同的界面
//
// 关键概念：
// - Thread: LangGraph的执行线程，一个对话会话
// - Stream: 实时数据流，接收AI的执行进展
// - Events: LangGraph节点执行时产生的事件

import { useStream } from "@langchain/langgraph-sdk/react";
import type { Message } from "@langchain/langgraph-sdk";
import { useState, useEffect, useRef, useCallback } from "react";
import { ProcessedEvent } from "@/components/ActivityTimeline";
import { WelcomeScreen } from "@/components/WelcomeScreen";
import { ChatMessagesView } from "@/components/ChatMessagesView";
import { Button } from "@/components/ui/button";

export default function App() {
  // ========== 状态管理 ==========
  
  // 当前活动时间线事件：实时显示AI正在执行的步骤
  const [processedEventsTimeline, setProcessedEventsTimeline] = useState<
    ProcessedEvent[]
  >([]);
  
  // 历史活动记录：每个AI回答对应的完整执行过程
  // key: 消息ID, value: 该消息对应的执行事件列表
  const [historicalActivities, setHistoricalActivities] = useState<
    Record<string, ProcessedEvent[]>
  >({});
  
  // 滚动区域引用：用于自动滚动到最新消息
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  
  // 最终答案生成完成标志：标记AI是否已完成当前回答
  const hasFinalizeEventOccurredRef = useRef(false);
  
  // 错误状态：记录连接或执行过程中的错误
  const [error, setError] = useState<string | null>(null);
  
  // ========== LangGraph 连接和事件处理 ==========
  
  // 使用LangGraph SDK的useStream hook建立连接
  const thread = useStream<{
    messages: Message[];                  // 对话消息列表
    initial_search_query_count: number;  // 初始搜索查询数量
    max_research_loops: number;          // 最大研究循环次数
    reasoning_model: string;             // 推理模型名称
  }>({
    // API地址配置：开发环境和生产环境使用不同的地址
    apiUrl: import.meta.env.DEV
      ? "http://localhost:2024"    // 开发环境：LangGraph开发服务器
      : "http://localhost:8123",   // 生产环境：Docker容器内的地址
    
    // LangGraph代理ID：对应后端定义的图名称
    assistantId: "agent",
    
    // 消息字段名：告诉SDK在状态的哪个字段中查找消息
    messagesKey: "messages",
    
    // 实时事件处理器：当LangGraph执行节点时会触发此回调
    onUpdateEvent: (event: any) => {
      let processedEvent: ProcessedEvent | null = null;
      
      // 根据事件类型处理不同的节点执行事件
      if (event.generate_query) {
        // 查询生成节点事件
        processedEvent = {
          title: "Generating Search Queries",
          data: event.generate_query?.search_query?.join(", ") || "",
        };
      } else if (event.web_research) {
        // 网络搜索节点事件
        const sources = event.web_research.sources_gathered || [];
        const numSources = sources.length;
        
        // 提取信息源的标签，显示搜索结果概览
        const uniqueLabels = [
          ...new Set(sources.map((s: any) => s.label).filter(Boolean)),
        ];
        const exampleLabels = uniqueLabels.slice(0, 3).join(", ");
        
        processedEvent = {
          title: "Web Research",
          data: `Gathered ${numSources} sources. Related to: ${
            exampleLabels || "N/A"
          }.`,
        };
      } else if (event.reflection) {
        // 反思分析节点事件
        processedEvent = {
          title: "Reflection",
          data: "Analysing Web Research Results",
        };
      } else if (event.finalize_answer) {
        // 最终答案生成节点事件
        processedEvent = {
          title: "Finalizing Answer",
          data: "Composing and presenting the final answer.",
        };
        
        // 标记最终答案生成已开始
        hasFinalizeEventOccurredRef.current = true;
      }
      
      // 如果处理了有效事件，添加到时间线中
      if (processedEvent) {
        setProcessedEventsTimeline((prevEvents) => [
          ...prevEvents,
          processedEvent!,
        ]);
      }
    },
    
    // 错误处理器：处理连接或执行错误
    onError: (error: any) => {
      setError(error.message);
    },
  });

  // ========== 副作用和事件处理 ==========
  
  // 自动滚动到最新消息
  useEffect(() => {
    if (scrollAreaRef.current) {
      // 查找Radix UI滚动组件的视口元素
      const scrollViewport = scrollAreaRef.current.querySelector(
        "[data-radix-scroll-area-viewport]"
      );
      if (scrollViewport) {
        // 滚动到底部显示最新消息
        scrollViewport.scrollTop = scrollViewport.scrollHeight;
      }
    }
  }, [thread.messages]); // 依赖消息列表，消息更新时触发滚动

  // 保存历史活动记录
  useEffect(() => {
    // 检查是否满足保存条件：
    // 1. 最终答案生成已完成
    // 2. 不再加载中
    // 3. 有消息存在
    if (
      hasFinalizeEventOccurredRef.current &&
      !thread.isLoading &&
      thread.messages.length > 0
    ) {
      const lastMessage = thread.messages[thread.messages.length - 1];
      
      // 确保最后一条消息是AI消息且有ID
      if (lastMessage && lastMessage.type === "ai" && lastMessage.id) {
        // 将当前的活动事件列表保存到历史记录中
        setHistoricalActivities((prev) => ({
          ...prev,
          [lastMessage.id!]: [...processedEventsTimeline],
        }));
      }
      
      // 重置最终答案标志，准备下一轮对话
      hasFinalizeEventOccurredRef.current = false;
    }
  }, [thread.messages, thread.isLoading, processedEventsTimeline]);

  // ========== 事件处理函数 ==========
  
  // 处理用户提交新问题
  const handleSubmit = useCallback(
    (submittedInputValue: string, effort: string, model: string) => {
      // 验证输入
      if (!submittedInputValue.trim()) return;
      
      // 重置状态，准备新的对话轮次
      setProcessedEventsTimeline([]);
      hasFinalizeEventOccurredRef.current = false;

      // 根据用户选择的"努力程度"映射为LangGraph配置参数
      let initial_search_query_count = 0;
      let max_research_loops = 0;
      
      switch (effort) {
        case "low":
          // 低努力程度：快速搜索，适合简单问题
          initial_search_query_count = 1;
          max_research_loops = 1;
          break;
        case "medium":
          // 中等努力程度：标准搜索，平衡速度和质量
          initial_search_query_count = 3;
          max_research_loops = 3;
          break;
        case "high":
          // 高努力程度：深度搜索，适合复杂问题
          initial_search_query_count = 5;
          max_research_loops = 10;
          break;
      }

      // 构建新的消息列表
      const newMessages: Message[] = [
        ...(thread.messages || []),
        {
          type: "human",
          content: submittedInputValue,
          id: Date.now().toString(), // 使用时间戳作为简单的ID
        },
      ];
      
      // 提交到LangGraph执行
      thread.submit({
        messages: newMessages,
        initial_search_query_count: initial_search_query_count,
        max_research_loops: max_research_loops,
        reasoning_model: model,
      });
    },
    [thread] // 依赖thread对象
  );

  // 处理取消操作
  const handleCancel = useCallback(() => {
    // 停止当前执行
    thread.stop();
    
    // 刷新页面重置所有状态
    // 注意：这是一个简单的重置方式，生产环境中可以考虑更优雅的状态重置
    window.location.reload();
  }, [thread]);

  // ========== 渲染逻辑 ==========
  
  return (
    <div className="flex h-screen bg-neutral-800 text-neutral-100 font-sans antialiased">
      <main className="h-full w-full max-w-4xl mx-auto">
        {/* 条件渲染：根据应用状态显示不同界面 */}
        
        {/* 情况1: 初始状态 - 显示欢迎界面 */}
        {thread.messages.length === 0 ? (
          <WelcomeScreen
            handleSubmit={handleSubmit}      // 传递提交处理函数
            isLoading={thread.isLoading}     // 传递加载状态
            onCancel={handleCancel}          // 传递取消处理函数
          />
        ) : 
        /* 情况2: 错误状态 - 显示错误信息 */
        error ? (
          <div className="flex flex-col items-center justify-center h-full">
            <div className="flex flex-col items-center justify-center gap-4">
              <h1 className="text-2xl text-red-400 font-bold">Error</h1>
              <p className="text-red-400">{JSON.stringify(error)}</p>

              <Button
                variant="destructive"
                onClick={() => window.location.reload()}
              >
                Retry
              </Button>
            </div>
          </div>
        ) : (
        /* 情况3: 正常对话状态 - 显示聊天界面 */
          <ChatMessagesView
            messages={thread.messages}                    // 对话消息列表
            isLoading={thread.isLoading}                  // 整体加载状态
            scrollAreaRef={scrollAreaRef}                 // 滚动区域引用
            onSubmit={handleSubmit}                       // 提交处理函数
            onCancel={handleCancel}                       // 取消处理函数
            liveActivityEvents={processedEventsTimeline}  // 当前活动事件
            historicalActivities={historicalActivities}  // 历史活动记录
          />
        )}
      </main>
    </div>
  );
}

// ========== 组件设计说明 ==========
//
// 1. 状态管理策略：
//    - 使用React的useState管理本地状态
//    - 通过useRef管理不需要触发重渲染的状态
//    - 状态更新采用函数式更新确保一致性
//
// 2. 实时通信架构：
//    - LangGraph SDK提供WebSocket连接
//    - 事件驱动的更新机制
//    - 自动重连和错误处理
//
// 3. 用户体验优化：
//    - 实时显示AI的执行进展
//    - 自动滚动到最新消息
//    - 错误状态的友好显示
//    - 加载状态的明确指示
//
// 4. 组件通信：
//    - 通过props向下传递数据和回调
//    - 使用useCallback优化回调函数性能
//    - 避免不必要的重渲染
//
// 5. 扩展性设计：
//    - 配置参数可以轻松调整
//    - 新的事件类型容易添加
//    - 界面状态易于扩展
//
// 这个组件是整个前端的"大脑"，协调所有子组件的工作，
// 确保用户获得流畅、直观的AI研究体验。
