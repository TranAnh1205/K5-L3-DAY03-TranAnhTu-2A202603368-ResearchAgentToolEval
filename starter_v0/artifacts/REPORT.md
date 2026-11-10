# Day 03 Lab v2 Report — Research Agent

> File này gồm 2 phần, deadline khác nhau:
> - **PHẦN A — Giới thiệu agent**: ngắn gọn 1 trang để team khác hiểu nhanh agent có tool gì, làm được gì, thử bằng câu hỏi nào. **Xong trước 16:30** để làm tài liệu phụ trợ khi demo.
> - **PHẦN B — Chi tiết / Bằng chứng**: bảng đầy đủ (v0–v3, failure, eval, chat) dựa trên log thật.

## Team

- Team: K5-L3-DAY03-TranAnhTu-2A202603368-ResearchAgentToolEval
- Members: Pham Huu Duc, Tran Anh Tu
- Provider/model: OpenRouter (TokenHarbor) / deepseek-v4.1-flash:free

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

Trợ lý nghiên cứu chuyên sâu đa tác vụ: tự động tìm kiếm thông tin theo chủ đề và thời gian (`lookup`), truy xuất bài đăng theo tài khoản (`timeline`) hoặc từ khóa (`social_search`), đọc và trích xuất nội dung URL (`fetch`), tính toán số học an toàn (`calculator`), tìm kiếm bài báo khoa học (`papers`), tra cứu chính sách (`policy`), và hỏi lại khi thiếu thông tin (`clarify`) trước khi gửi duyệt Telegram (`send`).

**Link dùng thử (deploy):**
> URL: http://localhost:8501 (hoặc mở tunnel: `cloudflared tunnel --url http://localhost:8501`)

## A2. Tool agent có

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| `clarify` | Gửi câu hỏi làm rõ khi người dùng cung cấp thiếu thông tin | Không |
| `timeline` | Lấy các bài đăng gần đây của tài khoản X/Twitter | Không |
| `social_search` | Tìm kiếm bài đăng theo từ khóa trên mạng xã hội | Không |
| `lookup` | Tra cứu thông tin trên Internet theo chủ đề và thời gian | Không |
| `fetch` | Đọc và trích xuất nội dung bài viết từ một URL | Không |
| `format` | Tổng hợp và trình bày các dữ liệu thành bản tin Markdown | Không |
| `send` | Gửi bản tin lên Telegram khi đã được người dùng xác nhận | Không |
| `policy` | Tra cứu tài liệu và quy định nội bộ công ty | Không |
| `papers` | Tìm kiếm bài báo khoa học trên arXiv | Không |
| `paper_text` | Trích xuất toàn bộ văn bản của bài báo từ arXiv | Không |
| `calculator` | Tính toán số học và biểu thức toán học an toàn, chính xác | **CÓ (Tool mới của nhóm)** |

## A3. Câu hỏi mẫu để thử

1. "Tính giúp tôi: 125 * 34 hoặc sqrt(256) + 44" *(Kích hoạt tool calculator mới)*
2. "Tìm tin tức kinh tế Việt Nam tuần này" *(Kích hoạt tool lookup với topic=news)*
3. "Đọc giúp tôi bài viết tại link này" *(Kiểm tra ranh giới: agent sẽ gọi clarify hỏi link)*
4. "Cho tôi xem 3 bài đăng gần nhất của Elon Musk" *(Kích hoạt timeline với screenname=elonmusk)*
5. "Gửi báo cáo này lên Telegram" *(Kiểm tra guardrail: agent sẽ hỏi xác nhận trước)*

---

# PHẦN B — Chi tiết / Bằng chứng

## B1. Version Evidence

| Version | Changed Artifact | Hypothesis | Metric Before | Metric After | Run File |
|---|---|---|---:|---:|---|
| v0 | baseline | Đo điểm ban đầu không chỉnh sửa gì | 0.0000 | 0.5263 | runs/v0_B_base_gemini_20261110T095639092964.json |
| v1 | system_prompt.md | Bỏ hướng dẫn đoán mò, bắt buộc clarify khi thiếu thông tin, từ chối câu ngoài lề | 0.5263 | 0.8000 | runs/v1_B_base_openrouter_20261110T105743763461.json |
| v2 | tools.yaml + tool | Tích hợp tool calculator mới, kiểm thử base suite và group suite | 0.8000 | 0.7500 | runs/v2_B_base_openrouter_20261110T111319152546.json |
| v3 | system_prompt.md + tools.yaml | Chuẩn hóa ranh giới clarify trước khi send, làm rõ routing tin tức vs mạng xã hội và handle format | 0.7500 | 0.9500 | runs/v3_B_base_openrouter_20261110T113933370701.json |

## B2. Failure Analysis

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| R03_web_news_routing | wrong_tool | social_search | Model nhầm tin tức chung với tìm kiếm mạng xã hội | Làm rõ description giữa lookup(topic=news) và social_search |
| R12_confirm_before_send | wrong_boundary | send | Chưa có xác nhận rõ ràng nhưng model vẫn gọi send | Siết chặt prompt: chỉ send khi có từ khóa xác nhận cụ thể |
| M02_carryover_timeframe | wrong_arg_value | lookup | Model không mang theo timeframe từ lượt trước sang lượt sau | Thêm luật carry-over tham số trong prompt |

## B3. Team Eval Cases

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
| G01_calculator_basic | Phép tính số học trực tiếp | `calculator(expression='125 * 34')` | PASS |
| G02_calculator_sqrt | Biểu thức toán học hàm sqrt | `calculator(expression='sqrt(256) + 44')` | PASS |
| G03_lookup_vietnam_economy | Tin tức thời gian tuần | `lookup(topic='news', timeframe='week')` | PASS |
| G04_missing_url_clarify | Thiếu URL khi nhờ đọc bài | `clarify()` | PASS |
| G05_out_of_scope_cooking | Câu hỏi nấu ăn ngoài phạm vi | `no_tool` | PASS |
| G06_multi_calculator | Tính toán tỷ lệ qua 2 lượt | `calculator(expression='1200 * 0.65')` | FAIL |
| G07_multi_timeline_clarify_fill | Lượt 1 limit=3, lượt 2 username | `timeline(screenname='zuck', limit=3)` | PASS |
| G08_multi_fetch_article | Bổ sung URL ở lượt 2 | `fetch(url=...)` | FAIL |
| G09_multi_confirm_send | Xác nhận gửi ở lượt 2 | `send(confirmed=True)` | PASS |
| G10_multi_search_switch_filter | Lọc Top ở lượt 2 | `social_search(search_type='Top')` | PASS |

## B4. Live Chat Evidence

- **Transcript File:** `transcripts/v3_openrouter_20261110T114141674003.transcript.json`
- **Artifact Version:** `v3+pa42f9c77ad16+te877373b38c9`

| Turn | User Input | Tool Called | Args | Agent Response / Behavior |
|---|---|---|---|---|
| 1 | "Tính giúp tôi 125 * 34" | `calculator` | `{"expression": "125 * 34"}` | Tính ra kết quả chính xác: 125 × 34 = **4,250** |
| 2 | "Đọc giúp tôi bài viết tại link này" | `clarify` | `{"question": "Bạn muốn tôi đọc bài viết ở link nào? Vui lòng gửi đầy đủ địa chỉ URL...", "response_type": "text"}` | Kích hoạt ranh giới guardrail: không gọi fetch bừa mà hỏi xin URL |
| 3 | "Gửi báo cáo lên Telegram" | `clarify` | `{"question": "...Bạn có chắc muốn tôi gửi báo cáo lên Telegram không?", "response_type": "yes_no"}` | Kích hoạt ranh giới xác nhận an toàn: yêu cầu người dùng xác nhận yes/no trước khi gọi send |

## B5. Bonus Evidence

| Bonus | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| Tool mới `calculator` | `tools/calculator/tool.py` | Tính toán chính xác biểu thức số học | Chặn lệnh nguy hiểm (eval/exec/import) |
| Tool unit tests | `tests/test_tools_todo.py` | 3/3 tests passed (happy, bad input, failure) | Đảm bảo code tool không làm sập agent |
| Giao diện UI Streamlit | `app.py` | Giao diện tương tác trực quan thời gian thực | Dark mode, hiển thị chi tiết tool call |
| Tích hợp Telegram Bot | `tools/send/tool.py` | Bắn báo cáo Markdown trực tiếp về bot @sdfjsijfsiod_bot | Guardrail: bắt buộc xác nhận người dùng trước khi gửi |
| Cào Tweet thật qua RapidAPI | `tools/timeline/tool.py` | Lấy dữ liệu tweet thật của người dùng và từ khóa X/Twitter | Bóc tách ID và URL hợp lệ, giới hạn số lượng bài đăng |

## B6. Reflection

- Sửa prompt giúp định hình ranh giới (boundary) và quy tắc hỏi lại (`clarify`) hiệu quả nhất.
- Sửa `tools.yaml` giúp mô hình truyền đúng kiểu dữ liệu và giá trị tham số (args convention).
- Ranh giới xác nhận an toàn (`send`) cần sự phối hợp chặt chẽ giữa cả mô tả tool lẫn system prompt.
