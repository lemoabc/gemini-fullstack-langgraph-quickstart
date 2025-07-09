# Gemini 全栈 LangGraph 快速入门

本项目展示了一个全栈应用程序，它使用 React 前端和由 LangGraph 驱动的后端代理。该代理旨在通过动态生成搜索词、使用 Google 搜索查询网络、分析结果以识别知识差距，并迭代优化搜索，最终提供带有引用的、有充分依据的答案，从而对用户的查询进行全面研究。此应用程序是使用 LangGraph 和 Google 的 Gemini 模型构建研究增强型对话 AI 的示例。

<img src="./app.png" title="Gemini Fullstack LangGraph" alt="Gemini Fullstack LangGraph" width="90%">

## 功能特点

- 💬 使用 React 前端和 LangGraph 后端的全栈应用程序
- 🧠 由 LangGraph 代理提供支持，用于高级研究和对话式 AI
- 🔍 使用 Google Gemini 模型动态生成搜索查询
- 🌐 通过 Google 搜索 API 集成网络研究功能
- 🤔 反思性推理，识别知识差距并优化搜索
- 📄 生成带有引用的答案，来源于收集的资料
- 🔄 开发过程中前后端都支持热重载

## 项目结构

项目分为两个主要目录：

-   `frontend/`：包含使用 Vite 构建的 React 应用程序
-   `backend/`：包含 LangGraph/FastAPI 应用程序，包括研究代理逻辑

## 入门指南：开发和本地测试

按照以下步骤在本地运行应用程序进行开发和测试。

**1. 前提条件：**

-   Node.js 和 npm (或 yarn/pnpm)
-   Python 3.11+
-   **`GEMINI_API_KEY`**：后端代理需要 Google Gemini API 密钥
    1.  从 [Google AI Studio](https://ai.google.dev/) 获取 API 密钥
    2.  进入 `backend/` 目录
    3.  通过复制 `backend/.env.example` 文件创建名为 `.env` 的文件
    4.  打开 `.env` 文件，将 `YOUR_API_KEY_HERE` 替换为你的实际 Gemini API 密钥
    
    *注意：对于 Windows 用户，`setup.bat install` 命令会在文件不存在时自动创建 `.env` 文件*

**2. 安装依赖：**

**后端（使用虚拟环境）：**

```bash
# Linux/Mac OS
cd backend
python -m venv venv  # 创建虚拟环境
source venv/bin/activate  # 激活虚拟环境
pip install .  # 在虚拟环境中安装依赖
deactivate  # 退出虚拟环境

# Windows
cd backend
python -m venv venv  # 创建虚拟环境
venv\Scripts\activate  # 激活虚拟环境
pip install .  # 在虚拟环境中安装依赖
deactivate  # 退出虚拟环境
```

**前端：**

```bash
cd frontend
npm install  # 安装到 node_modules 本地目录
```

**3. 运行开发服务器：**

### Linux/Mac OS：

**后端和前端：**

```bash
make dev
```
这将运行后端和前端开发服务器。打开浏览器并导航到前端开发服务器 URL（例如 `http://localhost:5173/app`）。

_或者，您也可以分别运行后端和前端开发服务器。对于后端，在 `backend/` 目录中打开终端并运行 `langgraph dev`。后端 API 将在 `http://127.0.0.1:2024` 上可用，它还会打开一个浏览器窗口到 LangGraph UI。对于前端，在 `frontend/` 目录中打开终端并运行 `npm run dev`。前端将在 `http://localhost:5173` 上可用。_

### Windows：

对于 Windows 用户，提供了批处理脚本 `setup.bat` 以便于安装和运行应用程序：

**安装：**

```cmd
setup.bat install
```

这将：
1. 为后端创建一个 Python 虚拟环境（位于 `backend/venv` 目录），确保依赖隔离
2. 在虚拟环境中安装后端依赖，避免与全局 Python 环境冲突
3. 安装前端依赖到 `frontend/node_modules` 目录
4. 如果不存在，则在后端目录中创建 `.env` 文件
5. 提醒您向 `.env` 文件添加 Gemini API 密钥

您也可以分别安装依赖：

```cmd
setup.bat install-backend  # 创建虚拟环境并安装后端依赖
setup.bat install-frontend  # 安装前端依赖
```

*注意：安装后，请确保在运行应用程序之前编辑 `backend/.env` 文件并添加您的 Gemini API 密钥。所有依赖都安装在项目本地，不会影响全局环境。*

**运行应用程序：**

```cmd
setup.bat dev
```

这将在单独的终端窗口中启动后端和前端开发服务器。您也可以分别启动它们：

```cmd
setup.bat dev-backend
setup.bat dev-frontend
```

**如何关闭开发服务器：**

通过 `setup.bat dev` 启动后，会分别弹出前端和后端的命令行窗口。要关闭开发服务器，只需**直接关闭这两个新弹出的命令行窗口**即可：

- 关闭“Frontend”窗口 → 前端服务停止
- 关闭“Backend”窗口 → 后端服务停止

如果是分别启动的，也只需关闭对应的窗口即可。

**关于 LangSmith API Key 提示：**

如果你在运行后端时看到弹出网页提示 `It looks like your LangSmith API key is missing`，这是因为 LangGraph 默认启用了 tracing/监控功能，但你没有配置 LangSmith 的 API Key。

- 如果你**不需要** LangSmith 云端追踪（本地开发通常不需要），只需在 `backend/.env` 文件中添加：
  ```
  LANGCHAIN_TRACING_V2=false
  LANGCHAIN_ENDPOINT=
  LANGSMITH_API_KEY=
  ```
  保存后重启后端即可，之后不会再弹出提示网页。
- 如果你**需要** LangSmith 功能，请前往 [LangSmith](https://smith.langchain.com/settings) 获取 API Key，并在 `.env` 文件中填写：
  ```
  LANGSMITH_API_KEY=你的key
  ```

大多数本地开发和测试场景，直接禁用 tracing 即可。

**通过命令行快速测试（可选）：**

如果您想在不启动完整网页界面的情况下快速测试代理，可以使用命令行示例：

```cmd
setup.bat cli-example "可再生能源的最新趋势是什么？"
```

这将直接从命令行运行代理并在终端中输出响应。

**访问完整应用程序：**

使用 `setup.bat dev` 启动服务器后，打开浏览器并导航到 `http://localhost:5173/app` 以访问具有完整用户界面的 Web 应用程序。

## 后端代理工作原理（高级概述）

后端的核心是在 `backend/src/agent/graph.py` 中定义的 LangGraph 代理。它遵循以下步骤：

<img src="./agent.png" title="代理流程" alt="代理流程" width="50%">

1.  **生成初始查询：** 基于您的输入，它使用 Gemini 模型生成一组初始搜索查询。
2.  **网络研究：** 对于每个查询，它使用 Gemini 模型和 Google 搜索 API 查找相关网页。
3.  **反思和知识差距分析：** 代理分析搜索结果，以确定信息是否足够或是否存在知识差距。它使用 Gemini 模型进行这个反思过程。
4.  **迭代优化：** 如果发现差距或信息不足，它会生成后续查询并重复网络研究和反思步骤（最多达到配置的最大循环次数）。
5.  **最终答案：** 一旦研究被认为足够充分，代理就会使用 Gemini 模型将收集到的信息综合成一个连贯的答案，包括来自网络来源的引用。

## 命令行示例（可选）

对于快速的一次性问题或在不启动完整 Web 应用程序的情况下测试代理，您可以直接从命令行执行代理。脚本 `backend/examples/cli_research.py` 运行 LangGraph 代理并打印最终答案：

### Linux/Mac OS：
```bash
cd backend
python examples/cli_research.py "可再生能源的最新趋势是什么？"
```

### Windows：
```cmd
setup.bat cli-example "可再生能源的最新趋势是什么？"
```

**注意：** 这完全是可选的，与主应用程序分开。您可以根据需要使用命令行示例或完整的 Web 应用程序。


## 部署

在生产环境中，后端服务器提供优化的静态前端构建。LangGraph 需要 Redis 实例和 Postgres 数据库。Redis 用作发布-订阅代理，以支持从后台运行中流式传输实时输出。Postgres 用于存储助手、线程、运行，持久化线程状态和长期记忆，并使用"恰好一次"语义管理后台任务队列的状态。有关如何部署后端服务器的更多详细信息，请查看 [LangGraph 文档](https://langchain-ai.github.io/langgraph/concepts/deployment_options/)。以下是如何构建包含优化前端构建和后端服务器的 Docker 镜像并通过 `docker-compose` 运行它的示例。

_注意：对于 docker-compose.yml 示例，您需要 LangSmith API 密钥，您可以从 [LangSmith](https://smith.langchain.com/settings) 获取一个。_

_注意：如果您不运行 docker-compose.yml 示例或将后端服务器暴露给公共互联网，您应该在 `frontend/src/App.tsx` 文件中更新 `apiUrl` 为您的主机。目前，docker-compose 的 `apiUrl` 设置为 `http://localhost:8123`，开发环境设置为 `http://localhost:2024`。_

**1. 构建 Docker 镜像：**

   从**项目根目录**运行以下命令：
   ```bash
   docker build -t gemini-fullstack-langgraph -f Dockerfile .
   ```
**2. 运行生产服务器：**

   ```bash
   GEMINI_API_KEY=<您的gemini_api密钥> LANGSMITH_API_KEY=<您的langsmith_api密钥> docker-compose up
   ```

打开浏览器并导航到 `http://localhost:8123/app/` 以查看应用程序。API 将在 `http://localhost:8123` 上可用。

## 使用的技术

- [React](https://reactjs.org/) (配合 [Vite](https://vitejs.dev/)) - 用于前端用户界面
- [Tailwind CSS](https://tailwindcss.com/) - 用于样式设计
- [Shadcn UI](https://ui.shadcn.com/) - 用于组件
- [LangGraph](https://github.com/langchain-ai/langgraph) - 用于构建后端研究代理
- [Google Gemini](https://ai.google.dev/models/gemini) - 用于查询生成、反思和答案合成的大语言模型

## 许可证

本项目采用 Apache License 2.0 许可证。有关详细信息，请参阅 [LICENSE](LICENSE) 文件。
