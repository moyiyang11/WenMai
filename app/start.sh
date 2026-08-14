#!/usr/bin/env bash
# ============================================================
#  一键启动：AI 小说风格蒸馏与 Skill 导出系统 (Git Bash / macOS / Linux)
#  首次运行自动建 venv、装依赖；后端 8000，前端 5173。
#  Ctrl+C 同时停止两个服务。
# ============================================================
set -e
cd "$(dirname "$0")"

# Windows 的 venv 可执行文件在 Scripts/，*nix 在 bin/
if [ -f "backend/.venv/Scripts/python.exe" ]; then
  PY="backend/.venv/Scripts/python.exe"
elif [ -f "backend/.venv/bin/python" ]; then
  PY="backend/.venv/bin/python"
else
  PY=""
fi

echo "[1/3] 检查后端虚拟环境..."
if [ -z "$PY" ]; then
  echo "    创建 venv 并安装后端依赖（首次较慢）..."
  python -m venv backend/.venv
  if [ -f "backend/.venv/Scripts/python.exe" ]; then PY="backend/.venv/Scripts/python.exe"; else PY="backend/.venv/bin/python"; fi
  "$PY" -m pip install --upgrade pip
  "$PY" -m pip install -r backend/requirements.txt
fi
[ -f backend/.env ] || cp backend/.env.example backend/.env

echo "[2/3] 检查前端依赖..."
if [ ! -d frontend/node_modules ]; then
  echo "    安装前端依赖（首次较慢）..."
  (cd frontend && npm install)
fi

echo "[3/3] 启动服务..."
# 转成绝对路径，后台启动
PY_ABS="$(cd "$(dirname "$PY")" && pwd)/$(basename "$PY")"

( cd backend && "$PY_ABS" -m uvicorn main:app --reload --port 8000 ) &
BACK_PID=$!
( cd frontend && npm run dev ) &
FRONT_PID=$!

echo ""
echo "  后端: http://127.0.0.1:8000/docs   (pid $BACK_PID)"
echo "  前端: http://127.0.0.1:5173        (pid $FRONT_PID)"
echo "  按 Ctrl+C 停止全部。"

trap "echo '正在停止...'; kill $BACK_PID $FRONT_PID 2>/dev/null; exit 0" INT TERM
wait
