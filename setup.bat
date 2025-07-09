@echo off
setlocal

:: Change directory to the script's location to ensure all paths are relative to the script.
pushd "%~dp0"

echo Gemini Fullstack LangGraph Quickstart
echo ===================================

IF "%1"=="" GOTO help
IF "%1"=="help" GOTO help
IF "%1"=="install" GOTO install
IF "%1"=="install-backend" GOTO install-backend
IF "%1"=="install-frontend" GOTO install-frontend
IF "%1"=="dev-frontend" GOTO dev-frontend
IF "%1"=="dev-backend" GOTO dev-backend
IF "%1"=="dev" GOTO dev
IF "%1"=="cli-example" GOTO cli-example
GOTO help

:help
echo Available commands:
echo   setup.bat install           - Install all dependencies (frontend and backend)
echo   setup.bat install-backend   - Install only backend dependencies
echo   setup.bat install-frontend  - Install only frontend dependencies
echo   setup.bat dev-frontend      - Starts the frontend development server (Vite)
echo   setup.bat dev-backend       - Starts the backend development server (Uvicorn with reload)
echo   setup.bat dev               - Starts both frontend and backend development servers
echo   setup.bat cli-example       - Run CLI example (requires an argument)
exit /b

:install
echo "Installing all dependencies..."
echo.

echo "--- Running Backend Installation ---"
call "%~f0" install-backend
if ERRORLEVEL 1 (
    echo Backend installation failed. Aborting.
    exit /b 1
)
echo "--- Backend Installation Complete ---"

echo.

echo "--- Running Frontend Installation ---"
call "%~f0" install-frontend
if ERRORLEVEL 1 (
    echo Frontend installation failed. Aborting.
    exit /b 1
)
echo "--- Frontend Installation Complete ---"

echo.
echo "All dependencies installed successfully!"
exit /b

:install-backend
echo Installing backend dependencies...
pushd backend
if not exist .env (
    echo Creating .env file from .env.example...
    copy .env.example .env
    echo IMPORTANT: Please edit the .env file and add your Gemini API key.
)

:: 检查是否已安装虚拟环境
if not exist venv (
    echo Creating virtual environment for backend...
    python -m venv venv
    if ERRORLEVEL 1 (
        echo Failed to create virtual environment. Please ensure Python 3.11+ is installed.
        exit /b 1
    )
)

:: 激活虚拟环境并安装依赖
echo Activating virtual environment and installing dependencies...
call .\venv\Scripts\activate.bat
pip install .
call .\venv\Scripts\deactivate.bat
popd
echo Backend dependencies installed.
exit /b

:install-frontend
echo Installing frontend dependencies...
pushd frontend
:: 检查 package.json 是否存在
if not exist package.json (
    echo package.json not found in frontend directory!
    popd
    exit /b 1
)
:: 安装依赖
npm install
popd
echo Frontend dependencies installed.
exit /b

:dev-frontend
echo Starting frontend development server...
pushd frontend
npm run dev
popd
exit /b

:dev-backend
echo Starting backend development server...
pushd backend
:: 检查虚拟环境是否存在
if not exist venv (
    echo Virtual environment not found. Please run 'setup.bat install-backend' first.
    exit /b 1
)
:: 激活虚拟环境并运行服务器
call venv\Scripts\activate
langgraph dev
call deactivate
popd
exit /b

:dev
echo Starting both frontend and backend development servers...
start "Frontend" cmd /k "setup.bat dev-frontend"
start "Backend" cmd /k "setup.bat dev-backend"
popd
exit /b

:cli-example
if "%2"=="" (
    echo Please provide a query for the CLI example:
    echo   setup.bat cli-example "What are the latest trends in renewable energy?"
    exit /b
)
pushd backend
:: 检查虚拟环境是否存在
if not exist venv (
    echo Virtual environment not found. Please run 'setup.bat install-backend' first.
    exit /b 1
)
:: 激活虚拟环境并运行示例
call venv\Scripts\activate
python examples\cli_research.py %2
call deactivate
popd
exit /b
