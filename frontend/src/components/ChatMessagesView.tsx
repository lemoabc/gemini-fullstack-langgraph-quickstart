// 聊天消息视图组件
//
// 这是应用的主要对话界面，负责：
// 1. 显示用户和AI之间的完整对话历史
// 2. 渲染不同类型的消息（用户消息、AI回答）
// 3. 实时显示AI的执行进展
// 4. 处理消息的复制功能
// 5. 管理滚动和布局
//
// 组件架构：
// - ChatMessagesView: 主容器组件
// - HumanMessageBubble: 用户消息气泡
// - AiMessageBubble: AI消息气泡（包含活动时间线）
// - InputForm: 输入表单组件
//
// 设计特点：
// - 响应式布局适配不同屏幕尺寸
// - Markdown渲染支持富文本显示
// - 实时活动展示与历史记录管理
// - 优雅的加载状态处理

import type React from "react";
import type { Message } from "@langchain/langgraph-sdk";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Loader2, Copy, CopyCheck } from "lucide-react";
import { InputForm } from "@/components/InputForm";
import { Button } from "@/components/ui/button";
import { useState, ReactNode } from "react";
import ReactMarkdown from "react-markdown";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import {
  ActivityTimeline,
  ProcessedEvent,
} from "@/components/ActivityTimeline";

// ========== Markdown 渲染组件 ==========

// Markdown组件的通用属性类型
type MdComponentProps = {
  className?: string;    // 自定义CSS类名
  children?: ReactNode;  // 子节点内容
  [key: string]: any;    // 其他属性（如href等）
};

/**
 * 自定义Markdown渲染组件
 * 
 * 这些组件定制了markdown内容的显示样式，确保：
 * 1. 与应用的设计系统保持一致
 * 2. 提供良好的可读性和视觉层次
 * 3. 支持引用链接的特殊处理
 * 4. 适配深色主题
 */
const mdComponents = {
  // 标题组件：不同级别的标题有不同的样式
  h1: ({ className, children, ...props }: MdComponentProps) => (
    <h1 className={cn("text-2xl font-bold mt-4 mb-2", className)} {...props}>
      {children}
    </h1>
  ),
  h2: ({ className, children, ...props }: MdComponentProps) => (
    <h2 className={cn("text-xl font-bold mt-3 mb-2", className)} {...props}>
      {children}
    </h2>
  ),
  h3: ({ className, children, ...props }: MdComponentProps) => (
    <h3 className={cn("text-lg font-bold mt-3 mb-1", className)} {...props}>
      {children}
    </h3>
  ),
  
  // 段落组件：标准文本段落
  p: ({ className, children, ...props }: MdComponentProps) => (
    <p className={cn("mb-3 leading-7", className)} {...props}>
      {children}
    </p>
  ),
  
  // 链接组件：特殊设计用于显示引用链接
  // 使用Badge组件包装，使引用链接更突出
  a: ({ className, children, href, ...props }: MdComponentProps) => (
    <Badge className="text-xs mx-0.5">
      <a
        className={cn("text-blue-400 hover:text-blue-300 text-xs", className)}
        href={href}
        target="_blank"           // 在新窗口打开
        rel="noopener noreferrer" // 安全属性
        {...props}
      >
        {children}
      </a>
    </Badge>
  ),
  
  // 列表组件：有序和无序列表
  ul: ({ className, children, ...props }: MdComponentProps) => (
    <ul className={cn("list-disc pl-6 mb-3", className)} {...props}>
      {children}
    </ul>
  ),
  ol: ({ className, children, ...props }: MdComponentProps) => (
    <ol className={cn("list-decimal pl-6 mb-3", className)} {...props}>
      {children}
    </ol>
  ),
  li: ({ className, children, ...props }: MdComponentProps) => (
    <li className={cn("mb-1", className)} {...props}>
      {children}
    </li>
  ),
  
  // 引用块组件：用于显示重要信息或引用
  blockquote: ({ className, children, ...props }: MdComponentProps) => (
    <blockquote
      className={cn(
        "border-l-4 border-neutral-600 pl-4 italic my-3 text-sm",
        className
      )}
      {...props}
    >
      {children}
    </blockquote>
  ),
  
  // 代码组件：行内代码和代码块
  code: ({ className, children, ...props }: MdComponentProps) => (
    <code
      className={cn(
        "bg-neutral-900 rounded px-1 py-0.5 font-mono text-xs",
        className
      )}
      {...props}
    >
      {children}
    </code>
  ),
  pre: ({ className, children, ...props }: MdComponentProps) => (
    <pre
      className={cn(
        "bg-neutral-900 p-3 rounded-lg overflow-x-auto font-mono text-xs my-3",
        className
      )}
      {...props}
    >
      {children}
    </pre>
  ),
  
  // 分隔线组件
  hr: ({ className, ...props }: MdComponentProps) => (
    <hr className={cn("border-neutral-600 my-4", className)} {...props} />
  ),
  
  // 表格组件：用于显示结构化数据
  table: ({ className, children, ...props }: MdComponentProps) => (
    <div className="my-3 overflow-x-auto">
      <table className={cn("border-collapse w-full", className)} {...props}>
        {children}
      </table>
    </div>
  ),
  th: ({ className, children, ...props }: MdComponentProps) => (
    <th
      className={cn(
        "border border-neutral-600 px-3 py-2 text-left font-bold",
        className
      )}
      {...props}
    >
      {children}
    </th>
  ),
  td: ({ className, children, ...props }: MdComponentProps) => (
    <td
      className={cn("border border-neutral-600 px-3 py-2", className)}
      {...props}
    >
      {children}
    </td>
  ),
};

// ========== 消息气泡组件 ==========

// 用户消息气泡组件属性
interface HumanMessageBubbleProps {
  message: Message;                    // 消息对象
  mdComponents: typeof mdComponents;   // Markdown渲染组件
}

/**
 * 用户消息气泡组件
 * 
 * 显示用户发送的消息，特点：
 * - 右对齐布局
 * - 深色背景区分于AI消息
 * - 支持Markdown渲染
 * - 圆角气泡样式
 */
const HumanMessageBubble: React.FC<HumanMessageBubbleProps> = ({
  message,
  mdComponents,
}) => {
  return (
    <div
      className={`text-white rounded-3xl break-words min-h-7 bg-neutral-700 max-w-[100%] sm:max-w-[90%] px-4 pt-3 rounded-br-lg`}
    >
      <ReactMarkdown components={mdComponents}>
        {/* 处理不同类型的消息内容 */}
        {typeof message.content === "string"
          ? message.content
          : JSON.stringify(message.content)  // 非字符串内容转为JSON显示
        }
      </ReactMarkdown>
    </div>
  );
};

// AI消息气泡组件属性
interface AiMessageBubbleProps {
  message: Message;                              // 消息对象
  historicalActivity: ProcessedEvent[] | undefined;  // 历史活动记录
  liveActivity: ProcessedEvent[] | undefined;        // 实时活动事件
  isLastMessage: boolean;                        // 是否为最后一条消息
  isOverallLoading: boolean;                     // 整体是否在加载中
  mdComponents: typeof mdComponents;             // Markdown渲染组件
  handleCopy: (text: string, messageId: string) => void;  // 复制处理函数
  copiedMessageId: string | null;               // 当前复制的消息ID
}

/**
 * AI消息气泡组件
 * 
 * 显示AI生成的回答，特点：
 * - 左对齐布局
 * - 包含活动时间线显示AI执行过程
 * - 支持复制功能
 * - 丰富的Markdown渲染
 * - 智能的加载状态处理
 */
const AiMessageBubble: React.FC<AiMessageBubbleProps> = ({
  message,
  historicalActivity,
  liveActivity,
  isLastMessage,
  isOverallLoading,
  mdComponents,
  handleCopy,
  copiedMessageId,
}) => {
  // 决定要显示的活动事件和是否为实时状态
  const activityForThisBubble =
    isLastMessage && isOverallLoading ? liveActivity : historicalActivity;
  const isLiveActivityForThisBubble = isLastMessage && isOverallLoading;

  return (
    <div className={`relative break-words flex flex-col`}>
      {/* AI执行过程时间线：只在有活动事件时显示 */}
      {activityForThisBubble && activityForThisBubble.length > 0 && (
        <div className="mb-3 border-b border-neutral-700 pb-3 text-xs">
          <ActivityTimeline
            processedEvents={activityForThisBubble}
            isLoading={isLiveActivityForThisBubble}
          />
        </div>
      )}
      
      {/* AI消息内容 */}
      <ReactMarkdown components={mdComponents}>
        {typeof message.content === "string"
          ? message.content
          : JSON.stringify(message.content)
        }
      </ReactMarkdown>
      
      {/* 复制按钮：只在有内容时显示 */}
      <Button
        variant="default"
        className={`cursor-pointer bg-neutral-700 border-neutral-600 text-neutral-300 self-end ${
          message.content.length > 0 ? "visible" : "hidden"
        }`}
        onClick={() =>
          handleCopy(
            typeof message.content === "string"
              ? message.content
              : JSON.stringify(message.content),
            message.id!
          )
        }
      >
        {/* 动态显示复制状态 */}
        {copiedMessageId === message.id ? "Copied" : "Copy"}
        {copiedMessageId === message.id ? <CopyCheck /> : <Copy />}
      </Button>
    </div>
  );
};

// ========== 主组件 ==========

// 聊天消息视图组件属性
interface ChatMessagesViewProps {
  messages: Message[];                                      // 消息列表
  isLoading: boolean;                                       // 是否加载中
  scrollAreaRef: React.RefObject<HTMLDivElement | null>;   // 滚动区域引用
  onSubmit: (inputValue: string, effort: string, model: string) => void;  // 提交处理
  onCancel: () => void;                                     // 取消处理
  liveActivityEvents: ProcessedEvent[];                     // 实时活动事件
  historicalActivities: Record<string, ProcessedEvent[]>;  // 历史活动记录
}

/**
 * 聊天消息视图主组件
 * 
 * 这是对话界面的核心组件，管理整个聊天体验：
 * 1. 消息列表的渲染和布局
 * 2. 不同消息类型的处理
 * 3. 加载状态的显示
 * 4. 滚动区域的管理
 * 5. 输入表单的集成
 */
export function ChatMessagesView({
  messages,
  isLoading,
  scrollAreaRef,
  onSubmit,
  onCancel,
  liveActivityEvents,
  historicalActivities,
}: ChatMessagesViewProps) {
  // ========== 组件状态 ==========
  
  // 复制状态管理：跟踪哪条消息被复制了
  const [copiedMessageId, setCopiedMessageId] = useState<string | null>(null);

  // ========== 事件处理 ==========
  
  /**
   * 处理消息复制功能
   * 
   * @param text 要复制的文本内容
   * @param messageId 消息ID，用于显示复制状态
   */
  const handleCopy = async (text: string, messageId: string) => {
    try {
      // 使用浏览器剪贴板API复制文本
      await navigator.clipboard.writeText(text);
      
      // 设置复制状态
      setCopiedMessageId(messageId);
      
      // 2秒后重置状态
      setTimeout(() => setCopiedMessageId(null), 2000);
    } catch (err) {
      console.error("Failed to copy text: ", err);
    }
  };
  
  // ========== 渲染逻辑 ==========
  
  return (
    <div className="flex flex-col h-full">
      {/* 消息滚动区域：占据大部分空间 */}
      <ScrollArea className="flex-1 overflow-y-auto" ref={scrollAreaRef}>
        <div className="p-4 md:p-6 space-y-2 max-w-4xl mx-auto pt-16">
          {/* 遍历渲染所有消息 */}
          {messages.map((message, index) => {
            const isLast = index === messages.length - 1;
            return (
              <div key={message.id || `msg-${index}`} className="space-y-3">
                <div
                  className={`flex items-start gap-3 ${
                    message.type === "human" ? "justify-end" : ""  // 用户消息右对齐
                  }`}
                >
                  {/* 根据消息类型渲染不同的气泡组件 */}
                  {message.type === "human" ? (
                    <HumanMessageBubble
                      message={message}
                      mdComponents={mdComponents}
                    />
                  ) : (
                    <AiMessageBubble
                      message={message}
                      historicalActivity={historicalActivities[message.id!]}
                      liveActivity={liveActivityEvents}
                      isLastMessage={isLast}
                      isOverallLoading={isLoading}
                      mdComponents={mdComponents}
                      handleCopy={handleCopy}
                      copiedMessageId={copiedMessageId}
                    />
                  )}
                </div>
              </div>
            );
          })}
          
          {/* 加载状态显示：当正在加载且没有AI消息在处理时 */}
          {isLoading &&
            (messages.length === 0 ||
              messages[messages.length - 1].type === "human") && (
              <div className="flex items-start gap-3 mt-3">
                <div className="relative group max-w-[85%] md:max-w-[80%] rounded-xl p-3 shadow-sm break-words bg-neutral-800 text-neutral-100 rounded-bl-none w-full min-h-[56px]">
                  {/* 根据是否有活动事件显示不同的加载内容 */}
                  {liveActivityEvents.length > 0 ? (
                    <div className="text-xs">
                      <ActivityTimeline
                        processedEvents={liveActivityEvents}
                        isLoading={true}
                      />
                    </div>
                  ) : (
                    // 基础加载指示器
                    <div className="flex items-center justify-start h-full">
                      <Loader2 className="h-5 w-5 animate-spin text-neutral-400 mr-2" />
                      <span>Processing...</span>
                    </div>
                  )}
                </div>
              </div>
            )}
        </div>
      </ScrollArea>
      
      {/* 输入表单：固定在底部 */}
      <InputForm
        onSubmit={onSubmit}
        isLoading={isLoading}
        onCancel={onCancel}
        hasHistory={messages.length > 0}  // 传递是否有对话历史
      />
    </div>
  );
}

// ========== 组件设计说明 ==========
//
// 1. 组件分离策略：
//    - 主组件负责布局和数据管理
//    - 子组件负责具体的消息渲染
//    - Markdown组件负责内容格式化
//    - 清晰的职责分工便于维护
//
// 2. 状态管理：
//    - 本地状态：复制状态等UI交互状态
//    - 传递状态：消息数据、加载状态等
//    - 状态提升：复杂状态由父组件管理
//
// 3. 用户体验：
//    - 实时活动展示增强透明度
//    - 复制功能提供便利操作
//    - 加载状态提供明确反馈
//    - 滚动管理确保最新内容可见
//
// 4. 渲染优化：
//    - 条件渲染减少不必要的DOM
//    - 合理使用key属性优化重渲染
//    - 组件拆分避免大组件重渲染
//
// 5. 可访问性：
//    - 语义化HTML结构
//    - 适当的ARIA属性
//    - 键盘导航支持
//    - 响应式设计
//
// 这个组件是用户与AI交互的主要界面，
// 设计上注重信息展示的清晰性和操作的便利性。
