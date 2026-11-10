from __future__ import annotations
from pathlib import Path
from typing import Any
import streamlit as st
import json
from env_loader import load_lab_env
from providers import make_provider
from tools import TOOL_FUNCTIONS, load_tool_declarations, to_openai_tools
from agent import ResearchAgent
from chat import run_model_tool_loop

ROOT = Path(__file__).parent
load_lab_env(ROOT)

st.set_page_config(
    page_title="DeepResearch Agent · VinUni Lab",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Premium Modern Theme CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    .stApp {
        background: radial-gradient(circle at 10% 20%, rgba(15, 23, 42, 0.98) 0%, rgba(10, 14, 26, 1) 90%);
        color: #f1f5f9;
    }
    
    .header-box {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.9) 100%);
        border: 1px solid rgba(56, 189, 248, 0.2);
        box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5);
        border-radius: 18px;
        padding: 24px 28px;
        margin-bottom: 24px;
        backdrop-filter: blur(12px);
    }
    
    .header-title {
        font-size: 32px;
        font-weight: 800;
        background: linear-gradient(90deg, #38bdf8 0%, #818cf8 50%, #c084fc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 6px;
    }
    
    .badge-chip {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 12px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 600;
        background: rgba(56, 189, 248, 0.12);
        color: #38bdf8;
        border: 1px solid rgba(56, 189, 248, 0.3);
    }
    
    .tool-badge {
        display: inline-block;
        padding: 3px 8px;
        border-radius: 6px;
        background: #1e293b;
        color: #38bdf8;
        font-family: 'JetBrains Mono', monospace;
        font-size: 12px;
        margin: 2px 4px 2px 0;
        border: 1px solid rgba(56, 189, 248, 0.2);
    }
    
    .stChatMessage {
        border-radius: 14px !important;
        padding: 14px 18px !important;
        margin-bottom: 12px !important;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
</style>
""", unsafe_allow_html=True)

# Load system artifacts
prompt_path = ROOT / "artifacts" / "system_prompt.md"
system_prompt = prompt_path.read_text(encoding="utf-8") if prompt_path.exists() else "You are a research assistant."

tools_path = ROOT / "artifacts" / "tools.yaml"
declared_tools = load_tool_declarations(tools_path) if tools_path.exists() else []
openai_tools = to_openai_tools(declared_tools)

# Sidebar Configuration
with st.sidebar:
    st.markdown("### ⚡ Cấu hình Trợ lý")
    
    provider_presets = {
        "TokenHarbor (DeepSeek V4.1)": ("openrouter", "deepseek-v4.1-flash:free"),
        "Google Gemini (Miễn phí)": ("gemini", "gemini-3.5-flash"),
        "OpenRouter Cloud": ("openrouter", "openai/gpt-4o-mini"),
        "Local Ollama (Offline)": ("ollama", "qwen2.5:7b"),
    }
    
    preset_choice = st.selectbox("Chọn nhà cung cấp AI", list(provider_presets.keys()), index=0)
    provider_key, default_model = provider_presets[preset_choice]
    
    model_name = st.text_input("Tên Model ID", value=default_model)
    
    st.markdown(f"<span class='badge-chip'>🟢 Trạng thái: Sẵn sàng kết nối</span>", unsafe_allow_html=True)
    st.divider()
    
    st.markdown(f"**Kho vũ khí (11 Tools):**")
    for t in declared_tools:
        name = t.get("name", "")
        is_new = "✨ Mới" if name == "calculator" else ""
        st.markdown(f"<span class='tool-badge'>{name}</span> <small style='color:#94a3b8'>{is_new}</small>", unsafe_allow_html=True)
        
    st.divider()
    if st.button("🗑️ Xóa toàn bộ đoạn chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# Main Container Header
st.markdown(f"""
<div class="header-box">
    <div style="display:flex; justify-content:space-between; align-items:center;">
        <div>
            <div class="header-title">⚡ DeepResearch Agent</div>
            <div style="color:#94a3b8; font-size:14px;">Trợ lý đa công cụ VinUni AI Thực Chiến — Tác giả: <b>Pham Huu Duc & Tran Anh Tu</b></div>
        </div>
        <div>
            <span class="badge-chip">🚀 Model: {model_name}</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Quick Prompts Pills
st.markdown("**Gợi ý thử nhanh:**")
col1, col2, col3, col4 = st.columns(4)
quick_prompt = None
if col1.button("🧮 Tính 1200 quả táo bán 35%"):
    quick_prompt = "Tôi có 1200 quả táo, bán đi 35%. Tính giúp tôi số quả táo còn lại"
if col2.button("📰 Tin tức AI mới nhất"):
    quick_prompt = "Tìm tin tức mới nhất về trí tuệ nhân tạo AI tuần này"
if col3.button("🐦 Đọc tweet của Sam Altman"):
    quick_prompt = "Cho tôi xem 3 bài đăng gần nhất của tài khoản sama"
if col4.button("📢 Bắn tin lên Telegram"):
    quick_prompt = "Gửi báo cáo tóm tắt tin tức AI hôm nay lên Telegram, tôi xác nhận gửi đi"

if "messages" not in st.session_state:
    st.session_state.messages = []

def synthesize_markdown_from_tools(events: list[dict[str, Any]]) -> str:
    parts = []
    for evt in events:
        tool_name = evt.get("tool")
        res = evt.get("result", {})
        if not isinstance(res, dict):
            continue
        if tool_name == "calculator" and "result" in res:
            parts.append(f"🧮 **Kết quả tính toán:** `{res.get('expression')}` = **{res.get('result')}**")
        elif tool_name in ["lookup", "web_search"] and "items" in res:
            items = res.get("items", [])
            if items:
                parts.append("### 📚 Kết quả tra cứu thông tin:\n")
                for item in items[:5]:
                    title = item.get("title", "Bài viết")
                    url = item.get("url", "#")
                    summary = item.get("summary", "")
                    parts.append(f"- **[{title}]({url})**\n  {summary[:240]}...\n")
        elif tool_name in ["timeline", "social_search", "get_user_tweets", "search_tweets"] and "items" in res:
            items = res.get("items", [])
            if items:
                parts.append("### 🐦 Bài đăng mạng xã hội (X/Twitter):\n")
                for item in items[:5]:
                    source = item.get("source", "@user")
                    url = item.get("url", "")
                    summary = item.get("summary", "")
                    link_str = f" · [Xem bài đăng]({url})" if url else ""
                    parts.append(f"- **{source}**{link_str}:\n  > {summary}\n")
        elif tool_name == "send":
            if res.get("status") == "sent":
                parts.append("🚀 **Đã gửi báo cáo thành công lên Telegram!** Bạn hãy mở Telegram xem nhé.")
            elif res.get("status") == "needs_confirmation":
                parts.append("⚠️ **Cần xác nhận:** Bạn có chắc chắn muốn gửi nội dung này lên Telegram không? Vui lòng xác nhận 'Có / Đồng ý'.")
        elif tool_name == "clarify":
            q = res.get("question") or (evt.get("args") or {}).get("question")
            if q:
                parts.append(f"❓ {q}")
    return "\n\n".join(parts)

# Display conversation
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if "tool_calls" in msg and msg["tool_calls"]:
            t_names = ", ".join(f"`{tc.get('tool')}`" for tc in msg["tool_calls"])
            with st.expander(f"🔍 Đã dùng công cụ: {t_names}", expanded=False):
                for tc in msg["tool_calls"]:
                    st.markdown(f"**{tc.get('tool')}** — *Tham số:* `{json.dumps(tc.get('args', {}), ensure_ascii=False)}`")
        if msg.get("content"):
            st.markdown(msg["content"])

# Handle user query
user_input = prompt = st.chat_input("Nhập câu hỏi nghiên cứu, tính toán, tra cứu tin tức...") or quick_prompt
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Agent đang phân tích câu hỏi & tìm kiếm câu trả lời..."):
            try:
                provider = make_provider(provider_key)
                
                # Build message history for the multi-round tool loop
                messages = [{"role": "system", "content": system_prompt}]
                for m in st.session_state.messages:
                    if m["role"] in ["user", "assistant"] and m.get("content"):
                        messages.append({"role": m["role"], "content": m["content"]})

                loop_res = run_model_tool_loop(
                    provider=provider,
                    messages=messages,
                    tools=openai_tools,
                    model=model_name if model_name.strip() else None,
                    max_tool_rounds=4,
                )
                
                response_text = loop_res.get("assistant_text") or ""
                tool_events = loop_res.get("tool_events") or []

                # Notify user if send tool was invoked
                for evt in tool_events:
                    if evt.get("tool") == "send":
                        res_val = evt.get("result", {})
                        if isinstance(res_val, dict) and res_val.get("status") == "sent":
                            tele_note = "🚀 **Đã gửi báo cáo thành công lên Telegram!** Hãy kiểm tra tin nhắn bot vừa nhận nhé."
                            if tele_note not in response_text:
                                response_text = f"{response_text}\n\n{tele_note}".strip() if response_text else tele_note

                # Subtle collapsible pill for tools executed (collapsed by default)
                if tool_events:
                    t_names = ", ".join(f"`{tc.get('tool')}`" for tc in tool_events)
                    with st.expander(f"🔍 Đã thực thi công cụ ({len(tool_events)} bước): {t_names}", expanded=False):
                        for res in tool_events:
                            st.markdown(f"**{res.get('tool')}** — *Tham số:* `{json.dumps(res.get('args', {}), ensure_ascii=False)}`")

                # If assistant text is empty, synthesize rich markdown from tool output
                final_text = response_text.strip()
                if not final_text and tool_events:
                    final_text = synthesize_markdown_from_tools(tool_events)

                if final_text:
                    st.markdown(final_text)
                elif not tool_events:
                    st.info("Agent không gọi công cụ nào và không phản hồi văn bản.")
                    
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": final_text,
                    "tool_calls": tool_events
                })
            except Exception as e:
                st.error(f"⚠️ Phát sinh lỗi: {str(e)}")
