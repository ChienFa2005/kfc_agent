#!/bin/bash
# KFC 優惠券推薦 AI - Web UI 啟動腳本

echo "🍗 啟動 KFC 優惠券推薦 AI (Web UI)..."
echo ""

# 檢查是否安裝 streamlit
if ! python3 -c "import streamlit" 2>/dev/null; then
    echo "📦 正在安裝 streamlit..."
    pip3 install streamlit
fi

# 啟動 Streamlit
streamlit run frontend.py
