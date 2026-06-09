#!/bin/bash
# 数据分析Agent001 启动脚本
# 自动清理旧进程，固定在 8501 端口启动

# 杀掉所有旧的 streamlit 进程
pkill -f "streamlit run app.py" 2>/dev/null
sleep 1

# 启动
cd "$(dirname "$0")"
python3 -m streamlit run app.py --server.headless true --server.port 8501
