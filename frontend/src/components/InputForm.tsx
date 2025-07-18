// 输入表单组件
//
// 这是用户与AI交互的核心输入界面，负责：
// 1. 接收用户的问题和查询
// 2. 配置AI研究的参数（努力程度、模型选择）
// 3. 处理表单提交和验证
// 4. 提供丰富的交互功能（快捷键、状态控制等）
// 5. 适配不同的使用场景（初次使用、对话中）
//
// 设计特点：
// - 多参数配置：不仅是简单输入，还包含研究配置
// - 智能交互：支持快捷键、自动调整高度等
// - 状态感知：根据加载状态和历史状态调整界面
// - 用户友好：清晰的视觉反馈和操作指引

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { SquarePen, Brain, Send, StopCircle, Zap, Cpu } from "lucide-react";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

// 输入表单组件属性接口
interface InputFormProps {
  // 提交处理函数：包含用户输入、努力程度和模型选择
  onSubmit: (inputValue: string, effort: string, model: string) => void;
  
  // 取消操作处理函数：用于停止正在进行的AI处理
  onCancel: () => void;
  
  // 加载状态：控制提交/取消按钮的显示和表单的交互性
  isLoading: boolean;
  
  // 历史状态：是否已有对话历史，影响布局和功能显示
  hasHistory: boolean;
}

/**
 * 输入表单组件
 * 
 * 这个组件是整个应用交互的核心，设计考虑：
 * 1. 多维度配置：问题内容 + 研究深度 + AI模型
 * 2. 智能输入：自适应高度、快捷键支持
 * 3. 状态管理：加载状态、历史状态的视觉反馈
 * 4. 用户体验：流畅的动画过渡、清晰的操作反馈
 */
export const InputForm: React.FC<InputFormProps> = ({
  onSubmit,
  onCancel,
  isLoading,
  hasHistory,
}) => {
  // ========== 组件内部状态 ==========
  
  // 用户输入的问题内容
  const [internalInputValue, setInternalInputValue] = useState("");
  
  // 研究努力程度：决定搜索深度和循环次数
  // low: 1个查询，1个循环 - 快速回答
  // medium: 3个查询，3个循环 - 平衡质量和速度  
  // high: 5个查询，10个循环 - 深度研究
  const [effort, setEffort] = useState("medium");
  
  // AI模型选择：不同模型有不同的特点
  // gemini-2.0-flash: 速度最快，适合简单查询
  // gemini-2.5-flash: 平衡速度和质量
  // gemini-2.5-pro: 最强推理能力，适合复杂分析
  const [model, setModel] = useState("gemini-2.5-flash-preview-04-17");

  // ========== 事件处理函数 ==========
  
  /**
   * 内部提交处理：验证输入并调用外部提交函数
   * 
   * @param e 可选的表单事件对象
   */
  const handleInternalSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();  // 阻止默认表单提交行为
    
    // 验证输入：确保有内容且不全是空白字符
    if (!internalInputValue.trim()) return;
    
    // 调用外部提交函数，传递所有配置参数
    onSubmit(internalInputValue, effort, model);
    
    // 清空输入框，准备下一次输入
    setInternalInputValue("");
  };

  /**
   * 键盘快捷键处理：支持 Ctrl/Cmd + Enter 快速提交
   * 
   * @param e 键盘事件对象
   */
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // 检测快捷键组合：Enter + (Ctrl 或 Cmd)
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();  // 防止换行
      handleInternalSubmit();
    }
  };

  // 提交按钮禁用条件：无内容或正在加载中
  const isSubmitDisabled = !internalInputValue.trim() || isLoading;

  return (
    <form
      onSubmit={handleInternalSubmit}
      className={`flex flex-col gap-2 p-3 pb-4`}
    >
      {/* ========== 主输入区域 ========== */}
      <div
        className={`flex flex-row items-center justify-between text-white rounded-3xl rounded-bl-sm ${
          hasHistory ? "rounded-br-sm" : ""  // 有历史时调整圆角
        } break-words min-h-7 bg-neutral-700 px-4 pt-3 `}
      >
        {/* 文本输入区域 */}
        <Textarea
          value={internalInputValue}
          onChange={(e) => setInternalInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Who won the Euro 2024 and scored the most goals?"  // 示例问题
          className={`w-full text-neutral-100 placeholder-neutral-500 resize-none border-0 focus:outline-none focus:ring-0 outline-none focus-visible:ring-0 shadow-none
                        md:text-base  min-h-[56px] max-h-[200px]`}
          rows={1}  // 初始单行显示，会自动扩展
        />
        
        {/* 操作按钮区域 */}
        <div className="-mt-3">
          {isLoading ? (
            // 加载中：显示停止按钮
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="text-red-500 hover:text-red-400 hover:bg-red-500/10 p-2 cursor-pointer rounded-full transition-all duration-200"
              onClick={onCancel}
            >
              <StopCircle className="h-5 w-5" />
            </Button>
          ) : (
            // 非加载状态：显示提交按钮
            <Button
              type="submit"
              variant="ghost"
              className={`${
                isSubmitDisabled
                  ? "text-neutral-500"  // 禁用状态：灰色
                  : "text-blue-500 hover:text-blue-400 hover:bg-blue-500/10"  // 可用状态：蓝色
              } p-2 cursor-pointer rounded-full transition-all duration-200 text-base`}
              disabled={isSubmitDisabled}
            >
              Search
              <Send className="h-5 w-5" />
            </Button>
          )}
        </div>
      </div>
      
      {/* ========== 配置选项区域 ========== */}
      <div className="flex items-center justify-between">
        <div className="flex flex-row gap-2">
          {/* 努力程度选择 */}
          <div className="flex flex-row gap-2 bg-neutral-700 border-neutral-600 text-neutral-300 focus:ring-neutral-500 rounded-xl rounded-t-sm pl-2  max-w-[100%] sm:max-w-[90%]">
            <div className="flex flex-row items-center text-sm">
              <Brain className="h-4 w-4 mr-2" />
              Effort
            </div>
            <Select value={effort} onValueChange={setEffort}>
              <SelectTrigger className="w-[120px] bg-transparent border-none cursor-pointer">
                <SelectValue placeholder="Effort" />
              </SelectTrigger>
              <SelectContent className="bg-neutral-700 border-neutral-600 text-neutral-300 cursor-pointer">
                <SelectItem
                  value="low"
                  className="hover:bg-neutral-600 focus:bg-neutral-600 cursor-pointer"
                >
                  Low  {/* 低努力：1查询1循环，快速响应 */}
                </SelectItem>
                <SelectItem
                  value="medium"
                  className="hover:bg-neutral-600 focus:bg-neutral-600 cursor-pointer"
                >
                  Medium  {/* 中等努力：3查询3循环，平衡模式 */}
                </SelectItem>
                <SelectItem
                  value="high"
                  className="hover:bg-neutral-600 focus:bg-neutral-600 cursor-pointer"
                >
                  High  {/* 高努力：5查询10循环，深度研究 */}
                </SelectItem>
              </SelectContent>
            </Select>
          </div>
          
          {/* AI模型选择 */}
          <div className="flex flex-row gap-2 bg-neutral-700 border-neutral-600 text-neutral-300 focus:ring-neutral-500 rounded-xl rounded-t-sm pl-2  max-w-[100%] sm:max-w-[90%]">
            <div className="flex flex-row items-center text-sm ml-2">
              <Cpu className="h-4 w-4 mr-2" />
              Model
            </div>
            <Select value={model} onValueChange={setModel}>
              <SelectTrigger className="w-[150px] bg-transparent border-none cursor-pointer">
                <SelectValue placeholder="Model" />
              </SelectTrigger>
              <SelectContent className="bg-neutral-700 border-neutral-600 text-neutral-300 cursor-pointer">
                <SelectItem
                  value="gemini-2.0-flash"
                  className="hover:bg-neutral-600 focus:bg-neutral-600 cursor-pointer"
                >
                  <div className="flex items-center">
                    <Zap className="h-4 w-4 mr-2 text-yellow-400" /> 2.0 Flash
                  </div>
                  {/* 最快速度，基础推理能力 */}
                </SelectItem>
                <SelectItem
                  value="gemini-2.5-flash-preview-04-17"
                  className="hover:bg-neutral-600 focus:bg-neutral-600 cursor-pointer"
                >
                  <div className="flex items-center">
                    <Zap className="h-4 w-4 mr-2 text-orange-400" /> 2.5 Flash
                  </div>
                  {/* 速度与质量平衡，默认选择 */}
                </SelectItem>
                <SelectItem
                  value="gemini-2.5-pro-preview-05-06"
                  className="hover:bg-neutral-600 focus:bg-neutral-600 cursor-pointer"
                >
                  <div className="flex items-center">
                    <Cpu className="h-4 w-4 mr-2 text-purple-400" /> 2.5 Pro
                  </div>
                  {/* 最强推理能力，适合复杂分析 */}
                </SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
        
        {/* 新搜索按钮：只在有历史对话时显示 */}
        {hasHistory && (
          <Button
            className="bg-neutral-700 border-neutral-600 text-neutral-300 cursor-pointer rounded-xl rounded-t-sm pl-2 "
            variant="default"
            onClick={() => window.location.reload()}  // 刷新页面重置状态
          >
            <SquarePen size={16} />
            New Search
          </Button>
        )}
      </div>
    </form>
  );
};

// ========== 组件设计说明 ==========
//
// 1. 功能层次：
//    - 核心功能：问题输入和提交
//    - 配置功能：努力程度和模型选择
//    - 辅助功能：快捷键、状态反馈、历史管理
//
// 2. 交互设计：
//    - 主要交互：文本输入 + 回车提交
//    - 快捷操作：Ctrl/Cmd + Enter 快速提交
//    - 高级配置：下拉选择器自定义参数
//    - 状态控制：加载时可取消操作
//
// 3. 视觉设计：
//    - 层次清晰：主输入区域突出，配置区域次要
//    - 状态反馈：不同图标和颜色表示不同状态
//    - 响应式：适配不同屏幕尺寸
//    - 动画过渡：平滑的状态变化动画
//
// 4. 用户体验：
//    - 智能验证：自动检测空输入
//    - 操作反馈：按钮状态明确表示可用性
//    - 配置保持：用户设置在会话中保持
//    - 清晰指引：占位符文本提供示例
//
// 5. 技术实现：
//    - 受控组件：所有输入都通过state管理
//    - 事件处理：键盘事件、表单事件的统一处理
//    - 条件渲染：根据状态动态显示不同元素
//    - 性能优化：合理的re-render控制
//
// 这个组件虽然看起来简单，但实际上包含了丰富的交互逻辑
// 和用户体验优化，是现代Web应用表单设计的最佳实践。
