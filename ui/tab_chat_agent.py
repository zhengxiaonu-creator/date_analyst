"""对话式 Agent 标签页。"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from data_analyzer import AGENT_NAME
from data_analyzer.agent import DataAgent


def reset_chat_messages():
    """重置对话开场白。"""
    st.session_state.messages = [{
        "role": "assistant",
        "content": (
            f"你好！我是 **{AGENT_NAME}** 🤖\n\n"
            "数据已经加载啦。试试这些问题：\n"
            "- `概览` 或 `完整报告`\n"
            "- `统计` 或 `分类列`\n"
            "- `相关性`\n"
            "- `查找 张三`\n"
            "- `查询 地区 是 华东`\n"
            "- `找出 销售额 大于 1000 的行`\n"
            "- `按 地区 聚合 销售额`\n"
            "- `检测 销售额 异常值`\n"
            "- `画 年龄 直方图`\n"
            "- `自动图表`"
        ),
    }]


def _get_or_create_agent(df: pd.DataFrame, file_name: str = "") -> DataAgent:
    """复用会话级 Agent，在数据或 LLM 配置变化时重建。"""
    agent_key = (
        st.session_state.get("data_version", 0),
        st.session_state.get("llm_enabled", False),
        bool(st.session_state.get("llm_api_key")),
        st.session_state.get("llm_base_url", "https://api.openai.com/v1"),
        st.session_state.get("llm_model", "gpt-4o-mini"),
    )

    cached_agent = st.session_state.get("data_agent")
    if cached_agent is not None and st.session_state.get("data_agent_key") == agent_key:
        return cached_agent

    old_history = []
    if cached_agent is not None:
        old_history = cached_agent.get_conversation_history()

    agent = DataAgent()
    agent.set_dataframe(df, file_name=file_name)
    if old_history:
        agent.set_conversation_history(old_history)

    if st.session_state.get("llm_enabled") and st.session_state.get("llm_api_key"):
        agent.configure_llm(
            api_key=st.session_state["llm_api_key"],
            base_url=st.session_state.get("llm_base_url", "https://api.openai.com/v1"),
            model=st.session_state.get("llm_model", "gpt-4o-mini"),
        )

    st.session_state.data_agent = agent
    st.session_state.data_agent_key = agent_key
    return agent


def render(df: pd.DataFrame, file_name: str = ""):
    st.header("💬 对话式分析 Agent")

    if st.session_state.get("llm_enabled"):
        model = st.session_state.get("llm_model", "unknown")
        st.caption(f"🤖 LLM 已启用 · 模型: {model} · 大模型优先理解需求并调用已有分析工具")
    else:
        st.caption("💡 提示：在侧边栏启用 LLM 可获得更好的自然语言理解能力")

    if "messages" not in st.session_state:
        reset_chat_messages()

    chat_container = st.container(height=500)
    with chat_container:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"], avatar="🤖" if msg["role"] == "assistant" else "🧑"):
                st.markdown(msg["content"])

    if prompt := st.chat_input("输入你的问题或命令..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="🧑"):
            st.markdown(prompt)

        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("思考中..."):
                agent = _get_or_create_agent(df, file_name)
                reply = agent.ask(prompt)

            if any(reply.startswith(p) for p in (
                "📉 已生成直方图 →", "📦 已生成箱线图", "📊 已生成条形图 →",
                "🗺️  已生成热力图", "🔵 已生成散点图",
            )):
                st.markdown(reply)
                try:
                    path = reply.split("→", 1)[1].strip()
                    if Path(path).exists():
                        st.image(path, use_container_width=True)
                except Exception:
                    pass
            elif reply.startswith("📄 已生成"):
                st.markdown(reply)
            else:
                st.markdown(f"```\n{reply}\n```")

        st.session_state.messages.append({"role": "assistant", "content": reply})

    if st.sidebar.button("🗑️ 清空对话历史", use_container_width=True):
        reset_chat_messages()
        agent = st.session_state.get("data_agent")
        if agent is not None:
            agent.set_conversation_history([])
        st.rerun()
