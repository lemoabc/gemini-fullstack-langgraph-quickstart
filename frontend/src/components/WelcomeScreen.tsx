// 欢迎界面组件
//
// 这是应用的初始界面，用户首次访问时看到的页面，负责：
// 1. 提供友好的欢迎信息和品牌展示
// 2. 集成输入表单，引导用户开始对话
// 3. 展示技术栈信息，建立用户信任
// 4. 优雅的居中布局和响应式设计
//
// 设计理念：
// - 简洁明了：突出核心功能，减少认知负担
// - 渐进式引导：从欢迎到输入的自然流程
// - 专业感：通过技术栈展示体现专业性
// - 无障碍：良好的对比度和可读性

import { InputForm } from "./InputForm";

// 欢迎界面组件属性接口
interface WelcomeScreenProps {
  // 用户提交问题的处理函数
  // 参数：用户输入内容，努力程度设置，选择的AI模型
  handleSubmit: (
    submittedInputValue: string,
    effort: string,
    model: string
  ) => void;
  
  // 取消操作的处理函数（用于一致性，虽然在欢迎界面较少使用）
  onCancel: () => void;
  
  // 全局加载状态，控制界面的交互性
  isLoading: boolean;
}

/**
 * 欢迎界面组件
 * 
 * 作为应用的门户页面，这个组件需要：
 * 1. 营造友好的第一印象
 * 2. 清晰地传达应用的价值主张
 * 3. 提供无摩擦的开始体验
 * 4. 建立用户对AI能力的期待
 * 
 * 布局结构：
 * - 顶部：欢迎标题和副标题
 * - 中间：输入表单（核心交互区域）
 * - 底部：技术栈信息（建立信任）
 */
export const WelcomeScreen: React.FC<WelcomeScreenProps> = ({
  handleSubmit,
  onCancel,
  isLoading,
}) => (
  <div className="h-full flex flex-col items-center justify-center text-center px-4 flex-1 w-full max-w-3xl mx-auto gap-4">
    {/* 欢迎信息区域 */}
    <div>
      {/* 主标题：简洁有力的欢迎词 */}
      <h1 className="text-5xl md:text-6xl font-semibold text-neutral-100 mb-3">
        Welcome.
      </h1>
      
      {/* 副标题：友好的询问，暗示AI的服务意愿 */}
      <p className="text-xl md:text-2xl text-neutral-400">
        How can I help you today?
      </p>
    </div>
    
    {/* 输入表单区域：用户交互的核心 */}
    <div className="w-full mt-4">
      <InputForm
        onSubmit={handleSubmit}        // 传递提交处理函数
        isLoading={isLoading}          // 传递加载状态
        onCancel={onCancel}            // 传递取消处理函数
        hasHistory={false}             // 标记为初始状态，没有对话历史
      />
    </div>
    
    {/* 技术栈信息：建立专业性和可信度 */}
    <p className="text-xs text-neutral-500">
      Powered by Google Gemini and LangChain LangGraph.
    </p>
  </div>
);

// ========== 组件设计说明 ==========
//
// 1. 视觉层次：
//    - 标题使用大字号建立强烈视觉焦点
//    - 副标题提供友好的上下文
//    - 输入框是最重要的交互元素
//    - 技术信息使用小字号，不喧宾夺主
//
// 2. 响应式设计：
//    - 使用md:前缀适配桌面端
//    - max-w-3xl限制最大宽度保持可读性
//    - flex布局确保在不同屏幕上的居中效果
//
// 3. 颜色系统：
//    - neutral-100: 主标题，最高对比度
//    - neutral-400: 副标题，次要信息
//    - neutral-500: 技术信息，最低优先级
//
// 4. 用户体验：
//    - 居中布局营造专注感
//    - 适当的间距避免拥挤
//    - 渐进式信息展示，引导用户视线流
//
// 5. 功能集成：
//    - 直接集成InputForm，减少界面跳转
//    - 状态传递确保一致的用户体验
//    - 无历史标记让输入组件适配首次使用场景
//
// 这个组件虽然简单，但承担着关键的"第一印象"责任，
// 设计上力求专业、友好、易用。
