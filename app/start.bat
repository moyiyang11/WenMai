@echo off
REM ============================================================
REM  一键启动：AI 小说风格蒸馏与 Skill 导出系统 (Windows)
REM  首次运行会自动创建 venv、安装依赖。
REM  分别弹出后端(8000) 与 前端(5173) 两个窗口。
REM ============================================================
setlocal
cd /d "%~dp0"

echo [1/3] 检查后端虚拟环境...
if not exist "backend\.venv\Scripts\python.exe" (
  echo     创建 venv 并安装后端依赖（首次较慢）...
  python -m venv backend\.venv
  backend\.venv\Scripts\python.exe -m pip install --upgrade pip
  backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
)
if not exist "backend\.env" copy "backend\.env.example" "backend\.env" >nul

echo [2/3] 检查前端依赖...
if not exist "frontend\node_modules" (
  echo     安装前端依赖（首次较慢）...
  pushd frontend & call npm install & popd
)

echo [3/3] 启动服务...
start "后端 API :8000" cmd /k "cd /d "%~dp0backend" && .venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000"
start "前端 :5173" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo.
echo   后端: http://127.0.0.1:8000/docs
echo   前端: http://127.0.0.1:5173
echo   （关闭本窗口不影响已启动的服务）
endlocal
