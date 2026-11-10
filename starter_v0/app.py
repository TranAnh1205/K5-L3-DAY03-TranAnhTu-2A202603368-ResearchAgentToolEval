"""Streamlit UI for Day 03 Research Agent.

Run with:
    streamlit run app.py
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

from chat import (
    assistant_tool_message,
    execute_tool_call,
    json_text,
    now_iso,
    safe_slug,
    tool_results_message,
    trim_history,
    write_transcript,
)
from env_loader import load_lab_env
from providers import make_provider
from tools import TOOL_FUNCTIONS, load_tool_declarations, to_openai_tools
from versioning import build_artifact_version

ROOT = Path(__file__).resolve().parent
ARTIFACTS_DIR = ROOT / "artifacts"
load_lab_env(ROOT)

st.set_page_config(
    page_title="AI Research Agent — Day 03",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for clean presentation
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }
    .subtitle {
        color: #666;
        margin-bottom: 1.5rem;
    }
    .tool-badge {
        display: inline-block;
        padding: 0.2rem 0.6rem;
        border-radius: 12px;
        background-color: #f0f2f6;
        font-size: 0.85rem;
        margin: 0.2rem;
    }
    .clarify-box {
        background-color: #fff3cd;
        border-left: 5px solid #ffeeba;
        padding: 1rem;
        border-radius: 4px;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)


# ---------------- Sidebar Configuration ----------------
with st.sidebar:
    st.header("⚙️ Cấu hình Agent")

    provider_name = st.selectbox(
        "Provider",
        options=["gemini", "openrouter", "openai", "anthropic", "ollama"],
        index=0,
        help="Chọn nhà cung cấp mô hình LLM",
    )

    default_models = {
        "gemini": "gemini-3.8-flash",
        "openrouter": "openai/gpt-4o-mini",
        "openai": "gpt-4o-mini",
        "anthropic": "claude-3-5-haiku-latest",
        "ollama": "qwen2.5:7b",
    }
    model_name = st.text_input("Tên Model (tùy chọn)", value=default_models.get(provider_name, ""))

    version_label = st.selectbox("Phiên bản Artifact", options=["v3", "v2", "v1", "v0"], index=0)

    st.divider()

    # API Key check / override
    st.subheader("🔑 Trạng thái API Keys")
    key_vars = {
        "gemini": "GEMINI_API_KEY",
        "openrouter": "OPENROUTER_API_KEY",
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
    }
    target_var = key_vars.get(provider_name)
    if target_var:
        current_key = os.getenv(target_var, "")
        if current_key:
            st.success(f"{target_var}: Đã nạp ({current_key[:6]}...)")
        else:
            st.warning(f"{target_var}: Chưa thiết lập trong .env")
        override_key = st.text_input(f"Nhập đè {target_var} (nếu cần)", type="password")
        if override_key:
            os.environ[target_var] = override_key

    st.divider()

    # Tools list
    st.subheader("🛠️ Danh sách Tools")
    declarations_path = ARTIFACTS_DIR / "tools.yaml"
    declarations = load_tool_declarations(declarations_path) if declarations_path.exists() else []
    for tool_item in declarations:
        st.markdown(f"- **`{tool_item['name']}`**: {tool_item.get('description', '')[:60]}...")

    st.divider()
    if st.button("🗑️ Xóa lịch sử chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.transcript = None
        st.rerun()


# ---------------- Session State Initialization ----------------
if "messages" not in st.session_state:
    st.session_state.messages = []

if "transcript" not in st.session_state:
    st.session_state.transcript = None


# Load artifacts
prompt_path = ARTIFACTS_DIR / "system_prompt.md"
system_prompt = prompt_path.read_text(encoding="utf-8") if prompt_path.exists() else ""
openai_tools = to_openai_tools(declarations)


# ---------------- Main Interface ----------------
st.markdown('<div class="main-title">🤖 AI Research Agent — Lab Showdown</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Tìm kiếm web, khai thác mạng xã hội, tra cứu arXiv, tra cứu chính sách công ty và gửi Telegram có guardrail.</div>',
    unsafe_allow_html=True,
)

tab_chat, tab_tools, tab_docs = st.tabs(["💬 Trò chuyện (Chat Live)", "🔬 Thử nghiệm Tool (Direct Playground)", "📋 Xem Artifacts"])

# ---------------- TAB 1: Chat Live ----------------
with tab_chat:
    # Quick prompt buttons
    st.caption("Gợi ý câu hỏi nhanh:")
    col1, col2, col3, col4 = st.columns(4)
    quick_query = None
    if col1.button("📰 Tin AI mới nhất"):
        quick_query = "Tìm và tổng hợp tin tức AI mới nhất trong tuần qua, định dạng theo sections."
    if col2.button("🔍 Tweet về GPT-5"):
        quick_query = "Tìm các tweet nổi bật về GPT-5 trên X/Twitter."
    if col3.button("📄 arXiv LLM Reasoning"):
        quick_query = "Tìm 2 bài báo mới nhất trên arXiv về LLM reasoning và tóm tắt."
    if col4.button("📜 Chính sách trích dẫn"):
        quick_query = "Chính sách của công ty về việc sử dụng nguồn từ bài đăng mạng xã hội (Tier 3) là gì?"

    # Display message history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if "tool_events" in msg and msg["tool_events"]:
                with st.expander(f"🛠️ Đã gọi {len(msg['tool_events'])} tools", expanded=False):
                    for event in msg["tool_events"]:
                        st.markdown(f"**Tool:** `{event['tool']}`")
                        st.json({"args": event.get("args"), "result": event.get("result")})
            st.markdown(msg["content"])

    # Chat Input
    user_input = st.chat_input("Nhập yêu cầu nghiên cứu của bạn...")
    prompt_to_run = quick_query or user_input

    if prompt_to_run:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt_to_run})
        with st.chat_message("user"):
            st.markdown(prompt_to_run)

        # Prepare agent execution
        try:
            provider = make_provider(provider_name)
        except Exception as exc:
            st.error(f"Lỗi khởi tạo provider `{provider_name}`: {exc}")
            st.stop()

        with st.chat_message("assistant"):
            status_container = st.status("🧠 Agent đang phân tích và tìm kiếm...", expanded=True)
            
            # Format message history
            history = trim_history(
                [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages if m["role"] in {"user", "assistant"}],
                window=5,
            )
            working_messages = [{"role": "system", "content": system_prompt}, *history]
            all_tool_events: list[dict[str, Any]] = []
            final_text = ""
            max_rounds = 4

            for round_idx in range(1, max_rounds + 1):
                status_container.write(f"🔄 **Vòng {round_idx}**: Gọi mô hình LLM...")
                try:
                    response = provider.complete(
                        working_messages,
                        openai_tools,
                        model=model_name or None,
                        temperature=0.0,
                    )
                except Exception as exc:
                    status_container.update(label="❌ Lỗi gọi Provider", state="error")
                    st.error(f"API Error ({type(exc).__name__}): {exc}")
                    final_text = f"Đã xảy ra lỗi khi gọi provider {provider_name}: {exc}"
                    break

                calls = response.tool_calls
                if not calls:
                    status_container.write("✅ Agent đã có câu trả lời hoàn chỉnh.")
                    final_text = response.text or ""
                    break

                # Execute calls
                working_messages.append(assistant_tool_message(response.text, calls))
                non_clarify = []
                paused_for_clarify = False

                for call in calls:
                    status_container.write(f"🔧 **Thực thi tool**: `{call.name}` với args: `{json.dumps(call.args, ensure_ascii=False)}`")
                    event = execute_tool_call(call)
                    all_tool_events.append(event)

                    result = event.get("result", {})
                    if isinstance(result, dict) and result.get("awaiting_user"):
                        status_container.update(label="⚠️ Cần người dùng làm rõ", state="complete")
                        question = result.get("question") or call.args.get("question") or "Vui lòng cung cấp thêm thông tin."
                        final_text = question
                        paused_for_clarify = True
                        break

                    non_clarify.append(event)

                if paused_for_clarify:
                    break

                working_messages.append(tool_results_message(non_clarify))
            else:
                final_text = f"Agent đã dừng sau {max_rounds} vòng thực thi tools."

            status_container.update(label="✨ Hoàn thành", state="complete", expanded=False)

            # Display final text
            st.markdown(final_text)

            # Save assistant message to state
            st.session_state.messages.append({
                "role": "assistant",
                "content": final_text,
                "tool_events": all_tool_events,
            })

            # Save transcript
            transcript_record = {
                "transcript_id": f"{version_label}_{provider_name}_{now_iso().replace(':', '')}",
                "version": version_label,
                "provider": provider_name,
                "model": model_name or default_models.get(provider_name),
                "created_at": now_iso(),
                "turns": st.session_state.messages,
            }
            transcripts_dir = ROOT / "transcripts"
            transcript_path = transcripts_dir / f"{transcript_record['transcript_id']}.transcript.json"
            write_transcript(transcript_path, transcript_record)


# ---------------- TAB 2: Direct Tool Playground ----------------
with tab_tools:
    st.subheader("🔬 Chạy thử trực tiếp từng Tool (Offline / Trực tiếp không qua Model)")
    st.caption("Dùng để demo tính năng hoặc test trực tiếp API key mà không lo tốn credit LLM hay bị rate limit.")

    selected_tool = st.selectbox("Chọn Tool để thử nghiệm", options=list(TOOL_FUNCTIONS.keys()))

    if selected_tool == "clarify":
        q = st.text_input("Câu hỏi:", value="Bạn muốn tìm tweet của ai?")
        rtype = st.selectbox("Kiểu câu hỏi:", ["text", "yes_no", "choice"])
        opts = st.text_input("Options (phân cách bằng dấu phẩy):", value="sama, elonmusk")
        if st.button("Chạy `clarify`"):
            res = TOOL_FUNCTIONS["clarify"](question=q, response_type=rtype, options=[o.strip() for o in opts.split(",") if o.strip()])
            st.json(res)

    elif selected_tool == "lookup":
        q = st.text_input("Query tìm kiếm web:", value="DeepSeek AI news")
        topic = st.selectbox("Topic:", ["general", "news"])
        timeframe = st.selectbox("Timeframe:", ["day", "week", "month", "year"])
        max_r = st.slider("Số lượng kết quả:", 1, 10, 3)
        if st.button("Chạy `lookup` (Tavily)"):
            with st.spinner("Đang tìm kiếm..."):
                res = TOOL_FUNCTIONS["lookup"](query=q, topic=topic, timeframe=timeframe, max_results=max_r)
                st.json(res)

    elif selected_tool == "fetch":
        url = st.text_input("URL cần đọc:", value="https://techcrunch.com")
        if st.button("Chạy `fetch` (Firecrawl)"):
            with st.spinner("Đang scrape nội dung..."):
                res = TOOL_FUNCTIONS["fetch"](url=url)
                st.json(res)

    elif selected_tool == "papers":
        q = st.text_input("Từ khóa arXiv:", value="LLM chain of thought reasoning")
        max_r = st.slider("Số lượng papers:", 1, 10, 3)
        sort_by = st.selectbox("Sắp xếp:", ["relevance", "lastUpdatedDate", "submittedDate"])
        if st.button("Chạy `papers` (arXiv)"):
            with st.spinner("Đang truy vấn arXiv..."):
                res = TOOL_FUNCTIONS["papers"](query=q, max_results=max_r, sort_by=sort_by)
                st.json(res)

    elif selected_tool == "policy":
        q = st.text_input("Từ khóa chính sách:", value="data privacy external publishing")
        area = st.selectbox("Policy Area:", ["all", "ai_research", "source_citation", "data_privacy", "external_publishing", "tool_usage"])
        top_k = st.slider("Số lượng:", 1, 5, 2)
        if st.button("Chạy `policy`"):
            res = TOOL_FUNCTIONS["policy"](query=q, policy_area=area, top_k=top_k)
            st.json(res)

    elif selected_tool == "send":
        st.warning("⚠️ Guardrail: Chỉ thực sự gửi khi confirmed=True!")
        txt = st.text_area("Nội dung gửi Telegram:", value="Test tin nhắn từ UI agent.")
        conf = st.checkbox("Xác nhận gửi thật (confirmed=True)?", value=False)
        if st.button("Chạy `send`"):
            res = TOOL_FUNCTIONS["send"](text=txt, confirmed=conf)
            st.json(res)

    elif selected_tool == "format":
        sample_items = [
            {"title": "OpenAI ra mắt mô hình mới", "url": "https://openai.com", "source": "openai.com", "section": "Mô hình"},
            {"title": "DeepSeek công bố nghiên cứu", "url": "https://deepseek.com", "source": "deepseek.com", "section": "Nghiên cứu"},
        ]
        template = st.selectbox("Template:", ["sections", "brief", "bullets", "thread", "daily_ai_vn"])
        headline = st.text_input("Headline:", value="Bản tin công nghệ hôm nay")
        if st.button("Chạy `format`"):
            res = TOOL_FUNCTIONS["format"](items=sample_items, template=template, headline=headline)
            st.markdown("### Kết quả Markdown:")
            st.markdown(res.get("markdown", ""))
            st.json(res)


# ---------------- TAB 3: Artifacts ----------------
with tab_docs:
    st.subheader("📋 System Prompt & Tools Declaration")
    col_p, col_t = st.columns(2)
    with col_p:
        st.markdown("#### `system_prompt.md`")
        st.code(system_prompt, language="markdown")
    with col_t:
        st.markdown("#### `tools.yaml`")
        st.code(declarations_path.read_text(encoding="utf-8") if declarations_path.exists() else "", language="yaml")
