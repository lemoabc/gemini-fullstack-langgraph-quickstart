// AI 执行过程可视化时间线组件
//
// 这个组件负责实时显示LangGraph AI代理的执行进展，让用户能够：
// 1. 看到AI当前正在执行的步骤
// 2. 了解整个研究过程的进展
// 3. 查看每个步骤的详细信息
// 4. 体验AI"思考"的透明度
//
// 设计理念：
// - 时间线形式：直观展示步骤的顺序和进展
// - 实时更新：随着LangGraph执行动态更新
// - 可折叠：避免占用过多界面空间
// - 状态指示：通过图标和动画显示不同的执行状态
//
// 关键特性：
// - 支持加载状态的动画效果
// - 不同步骤类型有对应的图标
// - 自动折叠历史记录，突出当前进展

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
} from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Loader2,        // 加载动画图标
  Activity,       // 通用活动图标
  Info,          // 信息图标
  Search,        // 搜索图标
  TextSearch,    // 文本搜索图标
  Brain,         // 大脑图标（用于反思）
  Pen,           // 笔图标（用于写作）
  ChevronDown,   // 向下箭头
  ChevronUp,     // 向上箭头
} from "lucide-react";
import { useEffect, useState } from "react";

// 处理过的事件数据结构
export interface ProcessedEvent {
  title: string;    // 事件标题，如"生成搜索查询"
  data: any;        // 事件相关数据，可以是字符串、数组等
}

// 组件属性接口
interface ActivityTimelineProps {
  processedEvents: ProcessedEvent[];  // 要显示的事件列表
  isLoading: boolean;                 // 是否正在加载中
}

export function ActivityTimeline({
  processedEvents,
  isLoading,
}: ActivityTimelineProps) {
  // ========== 组件状态 ==========
  
  // 时间线折叠状态：true=折叠，false=展开
  const [isTimelineCollapsed, setIsTimelineCollapsed] =
    useState<boolean>(false);

  // ========== 工具函数 ==========
  
  /**
   * 根据事件标题和状态返回对应的图标
   * 
   * 图标选择逻辑：
   * - 加载中：旋转的加载器
   * - 生成查询：文本搜索图标
   * - 网络搜索：搜索图标
   * - 反思分析：大脑图标
   * - 最终答案：笔图标
   * - 默认：通用活动图标
   * 
   * @param title 事件标题
   * @param index 事件索引
   * @returns React图标组件
   */
  const getEventIcon = (title: string, index: number) => {
    // 特殊情况：第一个事件且正在加载
    if (index === 0 && isLoading && processedEvents.length === 0) {
      return <Loader2 className="h-4 w-4 text-neutral-400 animate-spin" />;
    }
    
    // 根据标题关键词匹配图标
    if (title.toLowerCase().includes("generating")) {
      return <TextSearch className="h-4 w-4 text-neutral-400" />;
    } else if (title.toLowerCase().includes("thinking")) {
      return <Loader2 className="h-4 w-4 text-neutral-400 animate-spin" />;
    } else if (title.toLowerCase().includes("reflection")) {
      return <Brain className="h-4 w-4 text-neutral-400" />;
    } else if (title.toLowerCase().includes("research")) {
      return <Search className="h-4 w-4 text-neutral-400" />;
    } else if (title.toLowerCase().includes("finalizing")) {
      return <Pen className="h-4 w-4 text-neutral-400" />;
    }
    
    // 默认图标
    return <Activity className="h-4 w-4 text-neutral-400" />;
  };

  // ========== 副作用处理 ==========
  
  // 自动折叠逻辑：当加载完成且有事件时，自动折叠时间线
  useEffect(() => {
    if (!isLoading && processedEvents.length !== 0) {
      setIsTimelineCollapsed(true);
    }
  }, [isLoading, processedEvents]);

  // ========== 渲染逻辑 ==========
  
  return (
    <Card className="border-none rounded-lg bg-neutral-700 max-h-96">
      {/* 卡片头部：包含标题和折叠控制 */}
      <CardHeader>
        <CardDescription className="flex items-center justify-between">
          <div
            className="flex items-center justify-start text-sm w-full cursor-pointer gap-2 text-neutral-100"
            onClick={() => setIsTimelineCollapsed(!isTimelineCollapsed)}
          >
            Research {/* 时间线标题 */}
            {/* 折叠状态图标 */}
            {isTimelineCollapsed ? (
              <ChevronDown className="h-4 w-4 mr-2" />  // 已折叠，显示向下箭头
            ) : (
              <ChevronUp className="h-4 w-4 mr-2" />    // 已展开，显示向上箭头
            )}
          </div>
        </CardDescription>
      </CardHeader>
      
      {/* 卡片内容：只在未折叠时显示 */}
      {!isTimelineCollapsed && (
        <ScrollArea className="max-h-96 overflow-y-auto">
          <CardContent>
            {/* 情况1：正在加载且没有事件 - 显示初始加载状态 */}
            {isLoading && processedEvents.length === 0 && (
              <div className="relative pl-8 pb-4">
                {/* 时间线连接线 */}
                <div className="absolute left-3 top-3.5 h-full w-0.5 bg-neutral-800" />
                
                {/* 事件节点 */}
                <div className="absolute left-0.5 top-2 h-5 w-5 rounded-full bg-neutral-800 flex items-center justify-center ring-4 ring-neutral-900">
                  <Loader2 className="h-3 w-3 text-neutral-400 animate-spin" />
                </div>
                
                {/* 事件内容 */}
                <div>
                  <p className="text-sm text-neutral-300 font-medium">
                    Searching...
                  </p>
                </div>
              </div>
            )}
            
            {/* 情况2：有事件要显示 */}
            {processedEvents.length > 0 ? (
              <div className="space-y-0">
                {/* 遍历显示每个事件 */}
                {processedEvents.map((eventItem, index) => (
                  <div key={index} className="relative pl-8 pb-4">
                    {/* 时间线连接线：只在非最后一个事件或正在加载时显示 */}
                    {index < processedEvents.length - 1 ||
                    (isLoading && index === processedEvents.length - 1) ? (
                      <div className="absolute left-3 top-3.5 h-full w-0.5 bg-neutral-600" />
                    ) : null}
                    
                    {/* 事件节点：圆形节点包含对应图标 */}
                    <div className="absolute left-0.5 top-2 h-6 w-6 rounded-full bg-neutral-600 flex items-center justify-center ring-4 ring-neutral-700">
                      {getEventIcon(eventItem.title, index)}
                    </div>
                    
                    {/* 事件内容 */}
                    <div>
                      {/* 事件标题 */}
                      <p className="text-sm text-neutral-200 font-medium mb-0.5">
                        {eventItem.title}
                      </p>
                      
                      {/* 事件详细数据 */}
                      <p className="text-xs text-neutral-300 leading-relaxed">
                        {/* 智能数据格式化 */}
                        {typeof eventItem.data === "string"
                          ? eventItem.data
                          : Array.isArray(eventItem.data)
                          ? (eventItem.data as string[]).join(", ")  // 数组转逗号分隔字符串
                          : JSON.stringify(eventItem.data)           // 对象转JSON字符串
                        }
                      </p>
                    </div>
                  </div>
                ))}
                
                {/* 加载中指示器：在最后一个事件下方显示 */}
                {isLoading && processedEvents.length > 0 && (
                  <div className="relative pl-8 pb-4">
                    <div className="absolute left-0.5 top-2 h-5 w-5 rounded-full bg-neutral-600 flex items-center justify-center ring-4 ring-neutral-700">
                      <Loader2 className="h-3 w-3 text-neutral-400 animate-spin" />
                    </div>
                    <div>
                      <p className="text-sm text-neutral-300 font-medium">
                        Searching...
                      </p>
                    </div>
                  </div>
                )}
              </div>
            ) : !isLoading ? ( // 情况3：没有事件且不在加载 - 显示空状态
              <div className="flex flex-col items-center justify-center h-full text-neutral-500 pt-10">
                <Info className="h-6 w-6 mb-3" />
                <p className="text-sm">No activity to display.</p>
                <p className="text-xs text-neutral-600 mt-1">
                  Timeline will update during processing.
                </p>
              </div>
            ) : null}
          </CardContent>
        </ScrollArea>
      )}
    </Card>
  );
}

// ========== 组件设计说明 ==========
//
// 1. 视觉设计原则：
//    - 时间线布局：清晰的时间顺序
//    - 图标语义：每种操作有对应的图标
//    - 状态反馈：加载动画和完成状态
//    - 空间效率：可折叠设计节省空间
//
// 2. 交互体验：
//    - 一键折叠/展开
//    - 滚动查看历史
//    - 实时更新进展
//    - 智能默认状态
//
// 3. 数据处理：
//    - 灵活的数据格式支持
//    - 智能数据展示
//    - 错误数据的降级处理
//
// 4. 性能优化：
//    - 条件渲染减少DOM节点
//    - useEffect控制重渲染
//    - 合理的状态管理
//
// 5. 可扩展性：
//    - 新的事件类型容易添加
//    - 图标映射易于修改
//    - 样式主题化支持
//
// 这个组件让AI的"思考过程"变得可视化，
// 大大提升了用户对AI工作原理的理解和信任度。
