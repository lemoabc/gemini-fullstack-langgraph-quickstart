# FastAPI 应用入口和前端集成
#
# 这个文件是整个应用的HTTP服务入口，负责：
# 1. 创建FastAPI应用实例
# 2. 集成和服务前端静态文件
# 3. 处理前端路由和回退逻辑
# 4. 提供生产环境的完整Web服务
#
# 架构设计：
# - FastAPI作为后端API服务器
# - 静态文件服务器提供React前端
# - 路径分离：/app/* 用于前端，其他路径用于API
# - 开发/生产环境的差异化处理
#
# 集成方式：
# - 生产环境：后端直接服务前端静态文件
# - 开发环境：前后端分离，前端由Vite开发服务器提供

# mypy: disable - error - code = "no-untyped-def,misc"
import pathlib
from fastapi import FastAPI, Response
from fastapi.staticfiles import StaticFiles

# 创建FastAPI应用实例
# FastAPI是现代、快速的Python Web框架，支持：
# - 自动API文档生成
# - 类型检查和验证
# - 异步处理
# - WebSocket支持（LangGraph需要）
app = FastAPI()


def create_frontend_router(build_dir="../frontend/dist"):
    """
    创建前端路由器，用于服务React应用
    
    这个函数负责配置前端静态文件的服务逻辑，包括：
    1. 检查前端构建文件的存在性
    2. 配置静态文件服务器
    3. 处理构建缺失的错误情况
    4. 支持单页应用（SPA）的路由回退
    
    工作原理：
    - 正常情况：使用StaticFiles服务React构建产物
    - 构建缺失：返回友好的错误信息
    - HTML模式：支持客户端路由（React Router）
    
    Args:
        build_dir: React构建目录的相对路径，默认为"../frontend/dist"
                  这个路径相对于当前文件（app.py）
    
    Returns:
        StaticFiles实例或Route实例，用于处理前端请求
        
    文件结构说明：
    ```
    project/
    ├── backend/src/agent/app.py  (当前文件)
    └── frontend/dist/            (构建目录)
        ├── index.html           (入口HTML文件)
        ├── assets/              (JS、CSS等资源)
        └── ...
    ```
    """
    # 计算前端构建目录的绝对路径
    # pathlib.Path(__file__).parent = backend/src/agent/
    # parent.parent.parent = 项目根目录
    # / build_dir = frontend/dist/
    build_path = pathlib.Path(__file__).parent.parent.parent / build_dir

    # 检查构建目录和关键文件是否存在
    if not build_path.is_dir() or not (build_path / "index.html").is_file():
        # 构建不存在或不完整的处理逻辑
        print(
            f"WARN: Frontend build directory not found or incomplete at {build_path}. "
            f"Serving frontend will likely fail."
        )
        
        # 创建一个临时路由，返回构建缺失的错误信息
        # 这在开发环境或构建失败时很有用
        from starlette.routing import Route

        async def dummy_frontend(request):
            """
            临时前端处理器：当构建缺失时返回错误信息
            
            Args:
                request: Starlette请求对象
                
            Returns:
                Response: 包含错误信息的HTTP响应
            """
            return Response(
                "Frontend not built. Run 'npm run build' in the frontend directory.",
                media_type="text/plain",
                status_code=503,  # 503 Service Unavailable
            )

        # 返回通配符路由，捕获所有前端路径
        return Route("/{path:path}", endpoint=dummy_frontend)

    # 正常情况：返回静态文件服务器
    # StaticFiles特性：
    # - directory: 静态文件目录
    # - html: 启用HTML模式，支持SPA路由
    #   当请求的文件不存在时，返回index.html
    #   这样React Router可以处理客户端路由
    return StaticFiles(directory=build_path, html=True)


# ========== 应用配置和路由挂载 ==========

# 挂载前端应用到 /app 路径
# 
# 路径设计说明：
# - /app/*: 前端React应用（用户界面）
# - /docs: FastAPI自动生成的API文档
# - /openapi.json: OpenAPI规范文件
# - 其他路径: LangGraph API端点（由LangGraph自动注册）
#
# 为什么使用 /app 前缀？
# 1. 避免与LangGraph API路由冲突
# 2. 明确区分前端和API请求
# 3. 便于负载均衡和代理配置
# 4. 支持未来的多应用架构
app.mount(
    "/app",                     # 挂载路径：所有 /app/* 请求都会路由到前端
    create_frontend_router(),   # 路由器：处理前端静态文件
    name="frontend",           # 路由名称：便于调试和监控
)

# ========== 应用架构说明 ==========
#
# 1. 服务模式：
#    - 开发环境：前后端分离
#      * 前端：http://localhost:5173 (Vite dev server)
#      * 后端：http://localhost:2024 (LangGraph dev)
#    - 生产环境：前后端集成
#      * 统一服务：http://localhost:8123 (Docker)
#      * 前端：/app/* 路径
#      * 后端：其他API路径
#
# 2. 路由策略：
#    - 静态资源：直接文件服务
#    - SPA路由：回退到index.html
#    - API请求：LangGraph处理
#    - 文档：FastAPI自动生成
#
# 3. 部署优势：
#    - 单一端口：简化部署和网络配置
#    - 统一域名：避免CORS问题
#    - 缓存策略：静态资源可以被CDN缓存
#    - SSL终止：在同一个地方处理HTTPS
#
# 4. 开发体验：
#    - 热重载：开发时前后端独立重载
#    - 调试友好：清晰的错误信息
#    - 构建检查：自动检测构建状态
#
# 5. 扩展性：
#    - 多版本支持：可以同时服务多个前端版本
#    - API版本控制：通过路径前缀区分
#    - 微服务就绪：易于拆分为独立服务
#
# 这种架构提供了开发时的灵活性和生产时的高效性，
# 是现代全栈应用的最佳实践之一。
