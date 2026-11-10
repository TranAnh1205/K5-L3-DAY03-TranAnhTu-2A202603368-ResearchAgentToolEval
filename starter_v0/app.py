"""Local Streamlit demo for the Research Agent lab."""

from __future__ import annotations

import os
from pathlib import Path

import streamlit as st

from chat import execute_tool_call, run_model_tool_loop, trim_history
from env_loader import load_lab_env
from providers.base import ToolCall
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import build_artifact_version


ROOT = Path(__file__).resolve().parent
PROMPT_PATH = ROOT / "artifacts" / "system_prompt.md"
TOOLS_PATH = ROOT / "artifacts" / "tools.yaml"
load_lab_env(ROOT)

st.set_page_config(
    page_title="Research Agent | Day 03",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
    :root { color-scheme: dark; }
    html, body, [class*="css"], [data-testid="stApp"] { font-family: 'DM Sans', sans-serif; }
    [data-testid="stAppViewContainer"] {
        background: radial-gradient(circle at 70% 0%, #15384b 0, transparent 38%),
                    radial-gradient(circle at 4% 55%, #17283d 0, transparent 36%), #0b1523;
        color: #edf5f8;
    }
    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stSidebar"] { background: #101e2c; border-right: 1px solid #294051; }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color: #bfd0d9; }
    .block-container { max-width: 980px; padding-top: 2.5rem; padding-bottom: 7rem; }
    h1, h2, h3 { font-family: 'Space Grotesk', sans-serif; letter-spacing: -.035em; }
    .hero {
        padding: 2.2rem 2.4rem; border: 1px solid #3b6270; border-radius: 24px;
        background: linear-gradient(125deg, #163f50 0%, #102b3b 55%, #13283a 100%);
        box-shadow: 0 18px 55px #030a124d; margin-bottom: 1.5rem;
    }
    .eyebrow { color: #7ee5d0; font-size: .76rem; font-weight: 700; letter-spacing: .19em; text-transform: uppercase; }
    .hero h1 { color: #fff; font-size: clamp(2.2rem, 5vw, 3.5rem); margin: .55rem 0 .45rem; line-height: 1.08; }
    .hero p { color: #c1d7df; font-size: 1.05rem; max-width: 640px; margin: 0; line-height: 1.6; }
    .section-label { color: #91b6c4; font-size: .77rem; font-weight: 700; text-transform: uppercase; letter-spacing: .13em; margin: 1.3rem 0 .6rem; }
    .hint { color: #a9bec9; font-size: .89rem; margin-top: .65rem; }
    .status-ok { color: #8ee5c1; font-weight: 700; }
    .status-warn { color: #ffd38a; font-weight: 700; }
    [data-testid="stButton"] button {
        border: 1px solid #3b5c6c; background: #152b3a; color: #e8f4f5;
        border-radius: 12px; min-height: 3.3rem; text-align: left; white-space: normal;
    }
    [data-testid="stButton"] button:hover { border-color: #78d9c7; color: #fff; background: #1c3c49; }
    [data-testid="stChatMessage"] { background: #132435; border: 1px solid #294457; border-radius: 16px; margin: .7rem 0; }
    [data-testid="stChatMessage"] p { line-height: 1.65; }
    [data-testid="stChatInput"] { border-color: #557c89; }
    [data-testid="stExpander"] { border: 1px solid #2c4859; border-radius: 12px; }
    @media (max-width: 640px) { .hero { padding: 1.5rem; } .block-container { padding-top: 1.2rem; } }
    </style>
    """,
    unsafe_allow_html=True,
)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "history" not in st.session_state:
    st.session_state.history = []
if "pending_send" not in st.session_state:
    st.session_state.pending_send = None

artifact = build_artifact_version("demo", PROMPT_PATH, TOOLS_PATH)
declarations = load_tool_declarations(TOOLS_PATH)
tool_names = [tool["name"] for tool in declarations]
tool_requirements = {
    "timeline": ("RAPIDAPI_KEY",),
    "social_search": ("RAPIDAPI_KEY",),
    "lookup": ("TAVILY_API_KEY",),
    "fetch": ("FIRECRAWL_API_KEY",),
    "send": ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"),
}
with st.sidebar:
    st.markdown("### 🔎 Research Agent")
    st.caption("DAY 03 · LOCAL DEMO")
    st.divider()
    st.markdown("**Trạng thái**")
    if os.getenv("OPENAI_API_KEY"):
        st.markdown('<span class="status-ok">● OpenAI API key đã cấu hình</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-warn">● Thiếu OpenAI API key</span>', unsafe_allow_html=True)
    model = st.text_input("Model", value="gpt-4o-mini", help="Tên model OpenAI dùng cho cuộc trò chuyện.")
    st.caption(f"Phiên bản: `{artifact.artifact_version}`")
    st.divider()
    st.markdown("**Có thể thử**")
    st.caption("Tin tức trên web · X/Twitter · Đọc URL · arXiv · Policy · Gộp nguồn · Telegram")
    with st.expander(f"{len(tool_names)} công cụ đã khai báo"):
        st.caption("Dấu ✓ nghĩa là đã có cấu hình cần thiết; quyền API và quota được kiểm tra khi chạy.")
        for name in tool_names:
            missing = [key for key in tool_requirements.get(name, ()) if not os.getenv(key)]
            st.caption(f"{'⚠️' if missing else '✓'} `{name}`" + (f" · thiếu {', '.join(missing)}" if missing else ""))
    st.info("Telegram luôn cần bạn xác nhận bằng nút trước khi gửi thật.", icon="🔒")
    if st.button("↺  Bắt đầu cuộc trò chuyện mới", use_container_width=True):
        st.session_state.messages = []
        st.session_state.history = []
        st.session_state.pending_send = None
        st.rerun()

st.markdown(
    """
    <div class="hero">
      <div class="eyebrow">Research workspace · Day 03</div>
      <h1>Hỏi. Tìm nguồn. Hiểu nhanh.</h1>
      <p>Trợ lý nghiên cứu dùng công cụ để tìm tin, đọc trang web và sắp xếp nguồn. Hãy đặt một câu hỏi để bắt đầu.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if not os.getenv("OPENAI_API_KEY"):
    st.error("Thiếu OPENAI_API_KEY trong starter_v0/.env. Thêm key rồi tải lại trang.")
    st.stop()

examples = [
    ("📰", "Tin AI hôm nay trên web có gì nổi bật?"),
    ("𝕏", "Tìm các tweet phổ biến về robotics trên X."),
    ("🔗", "Đọc và tóm tắt trang https://www.python.org/about/"),
    ("◈", "Loại nguồn trùng trong https://example.com/story?utm_source=mail và https://example.com/story"),
]
selected_example = None
if not st.session_state.messages:
    st.markdown('<div class="section-label">Bắt đầu với một câu hỏi mẫu</div>', unsafe_allow_html=True)
    left, right = st.columns(2)
    for index, (icon, prompt) in enumerate(examples):
        column = left if index % 2 == 0 else right
        with column:
            if st.button(f"{icon}  {prompt}", key=f"example_{index}", use_container_width=True):
                selected_example = prompt
    st.markdown('<div class="hint">Bạn cũng có thể nhập câu hỏi riêng ở ô bên dưới.</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="section-label">Cuộc trò chuyện</div>', unsafe_allow_html=True)


def show_tool_events(events: list[dict]) -> None:
    if not events:
        return
    names = ", ".join(event.get("tool", "tool") for event in events)
    with st.expander(f"🔧 {len(events)} công cụ đã gọi · {names}"):
        for number, event in enumerate(events, start=1):
            name = event.get("tool", "tool")
            result = event.get("result", {})
            st.markdown(f"**{number}. `{name}`**")
            if isinstance(result, dict) and result.get("error"):
                st.error(f"{result['error']}: {result.get('message', 'Có lỗi khi chạy công cụ.')}")
            st.caption("Tham số")
            st.json(event.get("args", {}))
            st.caption("Kết quả")
            st.json(result)
            if number < len(events):
                st.divider()


for item in st.session_state.messages:
    with st.chat_message(item["role"]):
        st.markdown(item["content"])
        show_tool_events(item.get("tool_events", []))

if st.session_state.pending_send is not None:
    pending_text = st.session_state.pending_send["text"]
    st.warning("Telegram đang chờ xác nhận. Chỉ nút bên dưới mới có thể gửi tin nhắn.")
    st.text_area("Nội dung sẽ gửi", value=pending_text, height=160, disabled=True)
    can_send = bool(pending_text.strip()) and all(os.getenv(key) for key in tool_requirements["send"])
    if not can_send:
        st.caption("Cần nội dung và TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID trong .env để gửi.")
    confirm_col, cancel_col = st.columns(2)
    with confirm_col:
        if st.button("Xác nhận và gửi Telegram", disabled=not can_send, use_container_width=True):
            event = execute_tool_call(ToolCall(name="send", args={"text": pending_text, "confirmed": True}))
            success = event["result"].get("status") == "sent"
            answer = "Đã gửi Telegram." if success else f"Gửi Telegram thất bại: {event['result'].get('message', 'Lỗi không xác định.')}"
            st.session_state.messages.append({"role": "assistant", "content": answer, "tool_events": [event]})
            st.session_state.history.extend([
                {"role": "user", "content": "Tôi đã xác nhận gửi bằng nút trong UI."},
                {"role": "assistant", "content": answer},
            ])
            st.session_state.pending_send = None
            st.rerun()
    with cancel_col:
        if st.button("Hủy gửi", use_container_width=True):
            st.session_state.messages.append({"role": "assistant", "content": "Đã hủy gửi Telegram."})
            st.session_state.pending_send = None
            st.rerun()

typed_text = st.chat_input("Đặt câu hỏi nghiên cứu của bạn...", disabled=st.session_state.pending_send is not None)
user_text = selected_example or typed_text
if user_text:
    st.session_state.messages.append({"role": "user", "content": user_text})
    with st.chat_message("user"):
        st.markdown(user_text)

    with st.chat_message("assistant"):
        with st.spinner("Đang tìm và kiểm tra nguồn..."):
            try:
                prompt = PROMPT_PATH.read_text(encoding="utf-8")
                provider = make_provider("openai")
                context = [
                    {"role": "system", "content": prompt},
                    *trim_history(st.session_state.history, 5),
                    {"role": "user", "content": user_text},
                ]
                result = run_model_tool_loop(
                    provider=provider,
                    messages=context,
                    tools=to_openai_tools(declarations),
                    model=model.strip() or None,
                    max_tool_rounds=4,
                )
                answer = result["assistant_text"] or "Không có câu trả lời. Hãy thử diễn đạt lại yêu cầu."
                st.markdown(answer)
                show_tool_events(result["tool_events"])
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer,
                    "tool_events": result["tool_events"],
                })
                st.session_state.history.extend([
                    {"role": "user", "content": user_text},
                    {"role": "assistant", "content": answer},
                ])
                if result["status"] == "waiting_for_send_confirmation":
                    st.session_state.pending_send = result["pending_send"]
                    st.rerun()
            except Exception as exc:
                st.error(f"Không chạy được agent: {type(exc).__name__}: {exc}")
