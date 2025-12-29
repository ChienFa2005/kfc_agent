"""
KFC 優惠券推薦 AI - Streamlit 前端
整合 FSM Agent 進行對話式推薦
"""

import json
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st

from agent import KFCAgent
from scraper import should_update_coupons, scrape_and_parse, load_coupons_from_cache


# ---------- Page Config ----------
st.set_page_config(
    page_title="KFC 優惠券推薦 AI",
    page_icon="🍗",
    layout="wide"
)

st.title("🍗 KFC 優惠券推薦小幫手")
st.caption("AI 對話式推薦 - 告訴我人數和想吃的，我來幫你找最適合的優惠券！")


# ---------- Load Coupons ----------
@st.cache_resource(show_spinner=False)
def initialize_agent():
    """初始化 Agent 和優惠券資料"""
    # 檢查是否需要更新
    need_update, reason = should_update_coupons()

    if need_update:
        try:
            coupons = scrape_and_parse(force_update=True)
        except Exception as e:
            st.warning(f"⚠️ 更新失敗：{e}，使用快取資料")
            coupons = load_coupons_from_cache()
    else:
        coupons = load_coupons_from_cache()

    if not coupons:
        st.error("❌ 無法載入優惠券資料")
        st.stop()

    # 建立 Agent
    agent = KFCAgent(coupons)
    return agent, coupons, reason


# ---------- Sidebar Info ----------
with st.sidebar:
    st.header("📊 系統資訊")

    agent, coupons, cache_reason = initialize_agent()

    st.metric("優惠券數量", len(coupons))
    st.info(f"💾 {cache_reason}")

    st.divider()

    st.header("🎯 使用說明")
    st.markdown("""
    **對話流程：**
    1. 告訴我人數（例如：「3個人」）
    2. 告訴我想吃什麼（例如：「炸雞」「漢堡」）
    3. 說「好了」或「ok」開始查詢
    4. 查看推薦結果

    **提示：**
    - 可以分次輸入資訊
    - 不知道吃什麼？說「不知道」看菜單
    - 想重來？說「重來」
    """)

    if st.button("🔄 重置對話", use_container_width=True):
        if "agent" in st.session_state:
            st.session_state.agent.reset()
        st.session_state.messages = []
        st.rerun()


# ---------- Initialize Chat State ----------
if "agent" not in st.session_state:
    st.session_state.agent = agent

if "messages" not in st.session_state:
    st.session_state.messages = []
    # 顯示歡迎訊息
    welcome_msg = st.session_state.agent.process("")
    st.session_state.messages.append({
        "role": "assistant",
        "content": welcome_msg
    })


# ---------- Helper Functions ----------
def render_coupon_card(coupon: Dict[str, Any]):
    """渲染優惠券卡片"""
    with st.container():
        cols = st.columns([1, 3])

        # 圖片
        with cols[0]:
            if coupon.get("img"):
                st.image(coupon["img"], use_container_width=True)

        # 資訊
        with cols[1]:
            st.markdown(f"### {coupon.get('name', '未命名')}")

            # 代號和價格
            code = coupon.get('code') or coupon.get('id')
            fcode = coupon.get('fcode', '')
            st.markdown(f"**🎫 代號：** `{code}` / `{fcode}`")
            st.markdown(f"**💰 優惠價：** :red[**${coupon.get('price', 0)} 元**]")

            # 內容
            st.markdown(f"**📦 內容：** {coupon.get('description', '')}")

            # 符合項目
            if coupon.get('matched_items'):
                matched = ', '.join(coupon['matched_items'])
                st.markdown(f"**✅ 符合：** {matched}")

            # 人數建議
            serves = coupon.get('serves', 1)
            if coupon.get('people_suitable'):
                st.markdown(f"**👥 人數：** 適合 {serves} 人 ✅")
            else:
                user_count = st.session_state.agent.context.get('num_people', '?')
                st.markdown(f"**👥 人數：** 建議 {serves} 人（你們 {user_count} 人）⚠️")

            # 分類
            if coupon.get('category'):
                st.caption(f"🏷️ {coupon['category']}")


def parse_agent_response(response: str) -> tuple[str, list]:
    """
    解析 Agent 回應，分離文字訊息和優惠券資料
    回傳：(text_message, coupons_list)
    """
    # 檢查是否包含優惠券結果（包含 "找到 X 張符合的優惠券"）
    if "找到" in response and "張符合的優惠券" in response:
        # 提取文字部分（第一行）
        lines = response.split('\n')
        text_msg = lines[0]

        # 獲取過濾後的優惠券
        filtered_coupons = st.session_state.agent.context.get("filtered_coupons", [])
        return text_msg, filtered_coupons

    return response, []


# ---------- Display Chat History ----------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

        # 如果有優惠券資料，渲染卡片
        if msg.get("coupons"):
            st.divider()
            for i, coupon in enumerate(msg["coupons"], 1):
                st.markdown(f"#### 推薦 {i}")
                render_coupon_card(coupon)
                if i < len(msg["coupons"]):
                    st.divider()


# ---------- User Input ----------
user_input = st.chat_input("告訴我人數和想吃的，或說「不知道」看菜單...")

if user_input:
    # 顯示使用者訊息
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })

    with st.chat_message("user"):
        st.markdown(user_input)

    # 處理 Agent 回應
    with st.chat_message("assistant"):
        with st.spinner("思考中..."):
            response = st.session_state.agent.process(user_input)

        # 解析回應
        text_msg, coupons = parse_agent_response(response)

        # 顯示文字訊息
        st.markdown(text_msg)

        # 如果有優惠券，渲染卡片
        if coupons:
            st.divider()
            for i, coupon in enumerate(coupons, 1):
                st.markdown(f"#### 推薦 {i}")
                render_coupon_card(coupon)
                if i < len(coupons):
                    st.divider()

        # 儲存訊息
        st.session_state.messages.append({
            "role": "assistant",
            "content": text_msg,
            "coupons": coupons
        })


# ---------- Footer ----------
st.divider()
st.caption("💡 提示：輸入「重來」可以重新開始 | 當前狀態：" + st.session_state.agent.get_state())
