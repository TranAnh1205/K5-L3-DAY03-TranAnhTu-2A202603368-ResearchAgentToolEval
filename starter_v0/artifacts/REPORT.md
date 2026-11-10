# Day 03 Lab v2 Report — Research Agent

> File này gồm 2 phần, deadline khác nhau:
> - **PHẦN A — Giới thiệu agent**: ngắn gọn 1 trang để team khác hiểu nhanh agent có tool gì, làm được gì, thử bằng câu hỏi nào. **Xong trước 16:30** để làm tài liệu phụ trợ khi demo. Có thể làm thành poster HTML/SVG (`artifacts/poster.html` / `poster.svg`) để show cho team cùng zone.
> - **PHẦN B — Chi tiết / Bằng chứng**: bảng đầy đủ (v0–v3, failure, eval, chat) dựa trên log thật. **Có thể hoàn thiện sau buổi debate để nộp bài.**

## Team

- Team:
- Members:
- Provider/model:

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

Multi-source AI Research Agent: Trợ lý nghiên cứu chuyên sâu đa nguồn — tự động tìm kiếm tin tức trên web theo chủ đề & mốc thời gian, khai thác bài đăng/thảo luận trên mạng xã hội X (Twitter), tra cứu và đọc toàn văn các bài báo khoa học học thuật trên arXiv, tra cứu cẩm nang chính sách nội bộ với cơ chế chống Prompt Injection, tổng hợp thành bản tin định dạng đẹp mắt (Markdown/Thread/Sections) và gửi lên Telegram sau khi người dùng xác nhận.

**Link dùng thử (deploy):**

> Mở local UI: `streamlit run app.py` (hoặc `python server.py --port 8501`).
> Expose link Cloudflare Tunnel: `cloudflared tunnel --url http://localhost:8501`
>
> URL: http://localhost:8501 (hoặc link tunnel `https://*.trycloudflare.com`)

## A2. Tool agent có

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| `clarify` | Hỏi lại người dùng khi thiếu thông tin bắt buộc (handle, URL) hoặc xin xác nhận trước khi thực hiện hành động ghi | không |
| `lookup` | Tìm kiếm web & tin tức chung hoặc thời sự (Tavily) theo từ khóa, chủ đề (general/news) và mốc thời gian | không |
| `timeline` | Lấy các bài đăng gần nhất từ dòng thời gian của một tài khoản Twitter/X công khai cụ thể | không |
| `social_search` | Tìm kiếm các bài đăng nổi bật (Top) hoặc mới nhất (Latest) trên Twitter/X theo từ khóa hoặc hashtag | không |
| `fetch` | Đọc và trích xuất nội dung văn bản markdown sạch từ một URL cụ thể thông qua Firecrawl | không |
| `format` | Định dạng danh sách kết quả nghiên cứu thành bản tin tổng hợp theo nhiều template (brief, sections, bullets, thread) | không |
| `policy` | Tra cứu tài liệu chính sách nội bộ công ty (phân tách nội dung tin cậy và cách ly câu lệnh injection vào untrusted_text) | không |
| `send` | Gửi bản tin đã hoàn thiện lên kênh Telegram (bắt buộc có xác nhận rõ ràng `confirmed=True`) | không |
| `papers` | Tìm kiếm bài báo nghiên cứu khoa học trên arXiv theo từ khóa và sắp xếp theo độ liên quan/thời gian | **có (extension)** |
| `paper_text` | Tải tệp PDF và trích xuất nội dung văn bản của bài báo arXiv phục vụ việc tóm tắt chuyên sâu | **có (extension)** |

## A3. Câu hỏi mẫu để thử

1. **Tổng hợp tin tức AI trong tuần:**  
   *"Tìm và tổng hợp cho tôi các tin tức nổi bật về trí tuệ nhân tạo trong tuần qua, trình bày theo dạng sections."*
2. **Khai thác mạng xã hội X (Twitter):**  
   *"Tìm các bài đăng nổi bật nhất gần đây về GPT-5 trên Twitter."*
3. **Thử nghiệm ranh giới Clarify (thiếu dữ kiện):**  
   *"Xem bài đăng mới nhất của tài khoản này."* (Agent sẽ không đoán mò mà gọi `clarify` để hỏi lại handle).
4. **Tra cứu bài báo khoa học arXiv:**  
   *"Tìm 2 bài báo mới nhất trên arXiv về đề tài LLM reasoning và tóm tắt những đóng góp chính."*
5. **Thử nghiệm Guardrail bảo vệ gửi tin Telegram:**  
   *"Gửi bản tin vừa tóm tắt lên Telegram ngay lập tức."* (Agent sẽ từ chối gửi ngay và gửi câu hỏi xác nhận yes/no trước).

---

# PHẦN B — Chi tiết / Bằng chứng

## B1. Version Evidence

Fill from `artifacts/version_log.csv` and `runs/*.json`.

| Version | Changed Artifact | Hypothesis | Metric Before | Metric After | Run File |
|---|---|---|---:|---:|---|
| v0 | baseline |  |  |  |  |
| v1 |  |  |  |  |  |
| v2 |  |  |  |  |  |
| v3 |  |  |  |  |  |

## B2. Failure Analysis

Use actual failures from `results[*].result.failures`.

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
|  |  |  |  |  |

## B3. Team Eval Cases

List the 10 cases added to `data/eval_group.json` (5 single turn + 5 multi turn).

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
|  |  |  |  |

## B4. Live Chat Evidence

Use `transcripts/*.transcript.json`.

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
|---|---|---|---|---|
|  |  |  |  |  |

## B5. Bonus Evidence

Only fill if your team did bonus.

| Bonus | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| send (Telegram) |  |  |  |
| arXiv/company policy |  |  |  |
| UI |  |  |  |
| Tool unit tests (`tests/`) | `pytest` output (84 passed, 0 skipped) | 22 tests trong `test_tools_todo.py` (14 stub + 3 extension + 5 regression tests) | Bắt lỗi type coercion từ model (chuỗi số, boolean dạng chuỗi, limit/top_k=0) |

Tool unit tests:
- **Số test đã viết**: 22 unit tests trong `tests/test_tools_todo.py` (bao gồm toàn bộ 14 stub functions cho `clarify`, `format`, `send`, `lookup`, `fetch`, `timeline`, `social_search`, `policy`; 3 test cho tool mở rộng `papers` (arXiv); và 5 regression tests cho các bug phát hiện). Toàn bộ test suite đạt **84 passed, 0 failed, 0 skipped**.
- **Số bug tìm được & đã vá trong tool có sẵn (5 bugs)**:
  1. `tools/format/tool.py`: `_bullet()` để lại separator thừa `" - "` ở cuối dòng khi item thiếu cả `url` lẫn `source`.
  2. `tools/send/tool.py`: Khi LLM sinh arg `confirmed="false"` hoặc `confirmed="0"` dạng chuỗi, Python đánh giá chuỗi khác rỗng là truthy (`bool("false") == True`), làm bypass guardrail xác nhận gửi Telegram. Đã sửa để coerce chuỗi boolean an toàn (`confirmed.lower() in {"true", "1", "yes"}`).
  3. `tools/timeline/tool.py` & `tools/social_search/tool.py`: Khi model gửi `limit=0`, logic `int(limit or 5)` trả về 5 thay vì 0 tweet.
  4. `tools/policy/tool.py`: `hits[: max(1, int(top_k or 3))]` ép trả về 1-3 kết quả khi `top_k=0`. Đã sửa thành `max(0, k)`.
  5. `tools/lookup/tool.py`: `max_results=0` bị `0 or 5` đổi thành 5, cần parse `int` an toàn cho cả số dạng chuỗi và số 0.
- **Ví dụ lỗi mà unit test bắt được nhưng eval không bắt được**:
  - Khi model gọi `send(text="...", confirmed="false")`, eval kiểm tra hành vi model thấy gọi tool với arg `confirmed` hợp lệ nên chấm PASS. Tuy nhiên ở tầng code tool thực tế, giá trị `"false"` dạng chuỗi làm bypass điều kiện kiểm tra `if not confirmed:`, dẫn đến việc gửi API thật ngoài ý muốn. Unit test `test_regression_send_string_false_confirmed_still_blocks` đã bắt được lỗ hổng này.

## B6. Reflection

- Which fixes belonged in `system_prompt.md`?
- Which fixes belonged in `tools.yaml`?
- Which failure needed manual review instead of automatic grading?
- What would you improve next?

## B7. Small Local Model Challenge (bonus)

Only fill if your team did the local model challenge.

| Version | Model (provider) | Prompt/Tools | case_accuracy | tool_routing | argument | multiturn | Run File |
|---|---|---|---|---|---|---|---|
| v3 | (cloud) | v3 |  |  |  |  |  |
| v3-... | (ollama) | v3 |  |  |  |  |  |
| v3-... | (ollama) | v3 |  |  |  |  |  |
| v4-local |  |  |  |  |  |  |  |
| v5-local |  |  |  |  |  |  |  |

Lỗi đặc thù của model nhỏ (đếm từ run JSON):

| Failure Pattern | Count | Example Case | Fix Tried | Helped? |
|---|---|---|---|---|
| wrong / hallucinated tool |  |  |  |  |
| invalid JSON args (`_invalid_json_arguments`) |  |  |  |  |
| no tool call / answered directly |  |  |  |  |
| missed `clarify` |  |  |  |  |
| repeated / unnecessary calls |  |  |  |  |

- Cái gì giúp model nhỏ gọi tool đúng hơn nhất? Bằng chứng?
- Bản prompt tối ưu cho local chạy trên model cloud thì sao?
- Khi nào nhóm sẽ chọn model local thay vì cloud cho agent này?
