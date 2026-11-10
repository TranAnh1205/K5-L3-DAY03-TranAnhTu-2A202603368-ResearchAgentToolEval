"""Zero-dependency Standalone Web UI server for Day 03 Research Agent.

Runs with Python standard library only (no external packages required):
    python server.py [--port 8501]
"""
from __future__ import annotations

import argparse
import json
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from chat import (
    assistant_tool_message,
    execute_tool_call,
    now_iso,
    tool_results_message,
    trim_history,
    write_transcript,
)
from env_loader import load_lab_env
from providers import make_provider
from tools import TOOL_FUNCTIONS, load_tool_declarations, to_openai_tools

ROOT = Path(__file__).resolve().parent
ARTIFACTS_DIR = ROOT / "artifacts"
load_lab_env(ROOT)

INDEX_HTML = """<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI Research Agent — Day 03 Showdown</title>
  <style>
    :root {
      --primary: #2563eb;
      --primary-hover: #1d4ed8;
      --bg: #f8fafc;
      --sidebar-bg: #ffffff;
      --chat-bg: #ffffff;
      --text: #1e293b;
      --text-muted: #64748b;
      --border: #e2e8f0;
      --user-msg: #eff6ff;
      --bot-msg: #ffffff;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: var(--bg);
      color: var(--text);
      display: flex;
      height: 100vh;
      overflow: hidden;
    }
    /* Sidebar */
    .sidebar {
      width: 320px;
      background: var(--sidebar-bg);
      border-right: 1px solid var(--border);
      display: flex;
      flex-direction: column;
      padding: 20px;
      overflow-y: auto;
    }
    .sidebar h2 { font-size: 1.2rem; margin-bottom: 12px; color: #0f172a; }
    .sidebar label { font-size: 0.85rem; font-weight: 600; color: var(--text-muted); margin-top: 12px; display: block; }
    .sidebar select, .sidebar input {
      width: 100%;
      padding: 8px 12px;
      border: 1px solid var(--border);
      border-radius: 6px;
      margin-top: 4px;
      font-size: 0.9rem;
    }
    .tool-tag {
      display: inline-block;
      background: #f1f5f9;
      color: #334155;
      font-size: 0.75rem;
      padding: 3px 8px;
      border-radius: 12px;
      margin: 2px;
      font-family: monospace;
    }
    /* Main Chat */
    .main-area {
      flex: 1;
      display: flex;
      flex-direction: column;
      height: 100vh;
    }
    header {
      background: white;
      border-bottom: 1px solid var(--border);
      padding: 16px 24px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    header h1 { font-size: 1.3rem; font-weight: 700; color: #0f172a; }
    header p { font-size: 0.85rem; color: var(--text-muted); }
    .chat-messages {
      flex: 1;
      padding: 24px;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }
    .message {
      max-width: 80%;
      padding: 14px 18px;
      border-radius: 12px;
      line-height: 1.5;
      font-size: 0.95rem;
      white-space: pre-wrap;
      word-break: break-word;
    }
    .message.user {
      align-self: flex-end;
      background: var(--primary);
      color: white;
      border-bottom-right-radius: 2px;
    }
    .message.assistant {
      align-self: flex-start;
      background: var(--bot-msg);
      border: 1px solid var(--border);
      border-bottom-left-radius: 2px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .tool-call-banner {
      background: #f8fafc;
      border: 1px dashed #cbd5e1;
      border-radius: 6px;
      padding: 8px 12px;
      margin-bottom: 8px;
      font-size: 0.82rem;
      font-family: monospace;
      color: #475569;
    }
    /* Quick queries */
    .quick-chips {
      display: flex;
      gap: 8px;
      padding: 8px 24px;
      background: #f1f5f9;
      overflow-x: auto;
    }
    .chip {
      background: white;
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 4px 12px;
      font-size: 0.8rem;
      cursor: pointer;
      white-space: nowrap;
      transition: all 0.2s;
    }
    .chip:hover {
      background: #e2e8f0;
      color: var(--primary);
    }
    /* Input Area */
    .input-area {
      background: white;
      border-top: 1px solid var(--border);
      padding: 16px 24px;
      display: flex;
      gap: 12px;
    }
    .input-area input {
      flex: 1;
      padding: 12px 16px;
      border: 1px solid var(--border);
      border-radius: 8px;
      font-size: 1rem;
      outline: none;
    }
    .input-area input:focus { border-color: var(--primary); }
    .input-area button {
      background: var(--primary);
      color: white;
      border: none;
      padding: 12px 24px;
      border-radius: 8px;
      font-weight: 600;
      cursor: pointer;
      transition: background 0.2s;
    }
    .input-area button:hover { background: var(--primary-hover); }
    .input-area button:disabled { background: #94a3b8; cursor: not-allowed; }
  </style>
</head>
<body>
  <div class="sidebar">
    <h2>⚙️ Cấu hình Agent</h2>
    <label for="provider">Provider</label>
    <select id="provider" onchange="updateDefaultModel()">
      <option value="gemini">Gemini</option>
      <option value="openrouter">OpenRouter</option>
      <option value="openai">OpenAI</option>
      <option value="anthropic">Anthropic</option>
      <option value="ollama">Ollama (Local)</option>
    </select>

    <label for="model">Model Name</label>
    <input type="text" id="model" value="gemini-3.8-flash">

    <label for="version">Artifact Version</label>
    <select id="version">
      <option value="v3">v3 (Hiện tại)</option>
      <option value="v2">v2</option>
      <option value="v1">v1</option>
      <option value="v0">v0</option>
    </select>

    <label>Bộ Tools Đang Hoạt Động</label>
    <div style="margin-top: 6px;">
      <span class="tool-tag">clarify</span>
      <span class="tool-tag">lookup</span>
      <span class="tool-tag">timeline</span>
      <span class="tool-tag">social_search</span>
      <span class="tool-tag">fetch</span>
      <span class="tool-tag">format</span>
      <span class="tool-tag">send</span>
      <span class="tool-tag">policy</span>
      <span class="tool-tag">papers (arXiv)</span>
      <span class="tool-tag">paper_text</span>
    </div>

    <button onclick="clearChat()" style="margin-top: auto; padding: 8px; background: #fee2e2; color: #b91c1c; border: 1px solid #fca5a5; border-radius: 6px; cursor: pointer; font-weight: 600;">
      🗑️ Xóa Lịch Sử Chat
    </button>
  </div>

  <div class="main-area">
    <header>
      <div>
        <h1>🤖 AI Research Agent UI</h1>
        <p>Giao diện tra cứu đa nguồn, đọc arXiv & bảo vệ ranh giới bảo mật</p>
      </div>
      <div>
        <span style="font-size: 0.85rem; color: #16a34a; font-weight: 600;">● Sẵn sàng</span>
      </div>
    </header>

    <div class="quick-chips">
      <div class="chip" onclick="sendQuick('Tổng hợp tin tức AI mới nhất trong tuần qua')">📰 Tin AI tuần qua</div>
      <div class="chip" onclick="sendQuick('Tìm các bài đăng nổi bật về GPT-5 trên X')">🔍 Tweet về GPT-5</div>
      <div class="chip" onclick="sendQuick('Tìm 2 bài báo mới nhất trên arXiv về LLM reasoning')">📄 arXiv LLM Reasoning</div>
      <div class="chip" onclick="sendQuick('Chính sách công ty về việc sử dụng nguồn từ bài đăng mạng xã hội?')">📜 Chính sách trích dẫn</div>
    </div>

    <div class="chat-messages" id="messages">
      <div class="message assistant">Xin chào! Tôi là AI Research Agent. Bạn có thể yêu cầu tôi tìm kiếm tin tức trên web, tra cứu bài đăng Twitter/X, đọc nội dung bài báo arXiv, kiểm tra chính sách công ty hoặc soạn bản tin định dạng đẹp.</div>
    </div>

    <div class="input-area">
      <input type="text" id="userInput" placeholder="Nhập câu hỏi hoặc yêu cầu nghiên cứu..." onkeydown="if(event.key==='Enter') sendMessage()">
      <button id="sendBtn" onclick="sendMessage()">Gửi</button>
    </div>
  </div>

  <script>
    let chatHistory = [];

    function updateDefaultModel() {
      const p = document.getElementById('provider').value;
      const m = document.getElementById('model');
      if (p === 'gemini') m.value = 'gemini-3.8-flash';
      else if (p === 'openrouter') m.value = 'openai/gpt-4o-mini';
      else if (p === 'openai') m.value = 'gpt-4o-mini';
      else if (p === 'anthropic') m.value = 'claude-3-5-haiku-latest';
      else if (p === 'ollama') m.value = 'qwen2.5:7b';
    }

    function sendQuick(text) {
      document.getElementById('userInput').value = text;
      sendMessage();
    }

    function clearChat() {
      chatHistory = [];
      document.getElementById('messages').innerHTML = `
        <div class="message assistant">Đã xóa lịch sử trò chuyện. Tôi có thể giúp gì cho bạn?</div>
      `;
    }

    async function sendMessage() {
      const input = document.getElementById('userInput');
      const text = input.value.trim();
      if (!text) return;

      const btn = document.getElementById('sendBtn');
      btn.disabled = true;
      input.value = '';

      const container = document.getElementById('messages');
      container.innerHTML += `<div class="message user">${escapeHtml(text)}</div>`;
      container.scrollTop = container.scrollHeight;

      chatHistory.push({ role: 'user', content: text });

      const loadingMsg = document.createElement('div');
      loadingMsg.className = 'message assistant';
      loadingMsg.innerHTML = '<em>Agent đang suy nghĩ và thực thi tools...</em>';
      container.appendChild(loadingMsg);
      container.scrollTop = container.scrollHeight;

      try {
        const resp = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            messages: chatHistory,
            provider: document.getElementById('provider').value,
            model: document.getElementById('model').value,
            version: document.getElementById('version').value
          })
        });

        const data = await resp.json();
        let toolHtml = '';
        if (data.tool_events && data.tool_events.length > 0) {
          toolHtml = data.tool_events.map(ev => 
            `<div class="tool-call-banner">🔧 Gọi <b>${ev.tool}</b>(${JSON.stringify(ev.args || {})})</div>`
          ).join('');
        }

        loadingMsg.innerHTML = toolHtml + `<div>${escapeHtml(data.assistant_text || '(Không có phản hồi text)')}</div>`;
        chatHistory.push({ role: 'assistant', content: data.assistant_text || '' });
      } catch (err) {
        loadingMsg.innerHTML = `<span style="color: #ef4444;">Lỗi kết nối: ${escapeHtml(err.message)}</span>`;
      } finally {
        btn.disabled = false;
        container.scrollTop = container.scrollHeight;
      }
    }

    function escapeHtml(string) {
      const div = document.createElement('div');
      div.innerText = string;
      return div.innerHTML;
    }
  </script>
</body>
</html>
"""


class AgentUIHandler(SimpleHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path in {"/", "/index.html"}:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(INDEX_HTML.encode("utf-8"))
        elif parsed.path == "/poster.html":
            poster_path = ARTIFACTS_DIR / "poster.html"
            if poster_path.exists():
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(poster_path.read_bytes())
            else:
                self.send_error(404, "Poster not found")
        else:
            self.send_error(404, "Not Found")

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/chat":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode("utf-8")
            payload = json.loads(body)

            messages = payload.get("messages", [])
            provider_name = payload.get("provider", "gemini")
            model_name = payload.get("model") or None
            version_label = payload.get("version", "v3")

            declarations = load_tool_declarations(ARTIFACTS_DIR / "tools.yaml")
            openai_tools = to_openai_tools(declarations)
            prompt = (ARTIFACTS_DIR / "system_prompt.md").read_text(encoding="utf-8")

            try:
                provider = make_provider(provider_name)
            except Exception as exc:
                self._send_json({"assistant_text": f"Lỗi cấu hình provider: {exc}", "tool_events": []})
                return

            working_messages = [{"role": "system", "content": prompt}, *trim_history(messages, 5)]
            all_tool_events: list[dict[str, Any]] = []
            final_text = ""

            for _ in range(4):
                try:
                    response = provider.complete(working_messages, openai_tools, model=model_name, temperature=0.0)
                except Exception as exc:
                    final_text = f"Lỗi gọi LLM ({type(exc).__name__}): {exc}"
                    break

                calls = response.tool_calls
                if not calls:
                    final_text = response.text or ""
                    break

                working_messages.append(assistant_tool_message(response.text, calls))
                non_clarify = []
                paused = False

                for call in calls:
                    event = execute_tool_call(call)
                    all_tool_events.append(event)
                    res = event.get("result", {})
                    if isinstance(res, dict) and res.get("awaiting_user"):
                        final_text = res.get("question") or call.args.get("question") or "Vui lòng cung cấp thêm thông tin."
                        paused = True
                        break
                    non_clarify.append(event)

                if paused:
                    break
                working_messages.append(tool_results_message(non_clarify))
            else:
                if not final_text:
                    final_text = "Đã dừng sau tối đa 4 vòng gọi tool."

            self._send_json({"assistant_text": final_text, "tool_events": all_tool_events})
        else:
            self.send_error(404, "Unknown endpoint")

    def _send_json(self, data: dict[str, Any]) -> None:
        res = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(res)))
        self.end_headers()
        self.wfile.write(res)


def main() -> None:
    parser = argparse.ArgumentParser(description="Standalone UI server for Research Agent.")
    parser.add_argument("--port", type=int, default=8501, help="Port to listen on (default 8501).")
    args = parser.parse_args()

    server_address = ("127.0.0.1", args.port)
    httpd = HTTPServer(server_address, AgentUIHandler)
    print(f"🚀 UI Server running at http://localhost:{args.port}")
    print(f"📄 Poster view available at http://localhost:{args.port}/poster.html")
    httpd.serve_forever()


if __name__ == "__main__":
    main()
