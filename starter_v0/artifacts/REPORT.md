# Day 03 Lab v2 Report — Research Agent

Phần A giới thiệu agent để demo; Phần B ghi bằng chứng từ run và transcript thật.

## Team

- Team:
- Members:
- Provider/model: OpenAI `gpt-4o-mini`

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

Research Agent tìm tin trên web hoặc X/Twitter, đọc URL, tìm paper, tra policy nội bộ và tổng hợp nguồn đã có. Khi thiếu tài khoản hoặc URL, agent hỏi lại; yêu cầu gửi Telegram phải được xác nhận trước.

**Link dùng thử:** `http://localhost:8501` trên máy chạy lab (`python -m streamlit run app.py`). Chưa mở link công khai theo lựa chọn của người dùng.

## A2. Tool agent có

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| clarify | hỏi lại người dùng khi thiếu thông tin | không |
| timeline | lấy bài đăng gần đây của một tài khoản | không |
| social_search | tìm bài đăng theo chủ đề | không |
| lookup | tìm thông tin hoặc tin tức trên web | không |
| fetch | đọc nội dung một URL | không |
| format | trình bày nguồn đã có thành digest | không |
| dedupe_sources | gộp các nguồn trùng URL | có |
| policy | tra tài liệu policy cục bộ | không |
| papers / paper_text | tìm và đọc bài arXiv | không |
| send | gửi Telegram sau xác nhận; chưa bật trong UI demo | không |

## A3. Câu hỏi mẫu để thử

1. Tin AI hôm nay trên web có gì nổi bật?
2. Tìm các tweet phổ biến về robotics trên X.
3. Đọc và tóm tắt trang này: https://www.python.org/about/
4. Loại nguồn trùng trong `https://example.com/story?utm_source=mail` và `https://example.com/story`.

---

# PHẦN B — Chi tiết / Bằng chứng

## B1. Version Evidence

Số liệu lấy từ `artifacts/version_log.csv` và `runs/*.json`.

| Version | Changed Artifact | Hypothesis | Metric Before | Metric After | Run File |
|---|---|---|---:|---:|---|
| v0 | baseline | Đo prompt và tool declaration ban đầu bằng OpenAI `gpt-4o-mini` | — | case_accuracy 0.65 (13/20; 0 provider error) | `runs/v0_B_base_openai_20261110T103307388725.json` |
| v1 | `artifacts/system_prompt.md` | Hỏi lại khi thiếu account hoặc URL thay vì đoán sẽ sửa lỗi R10/R11 | 0.65 | 0.90 (18/20; 0 provider error) | `runs/v1_B_base_openai_20261110T104121957586.json` |
| v2 | `artifacts/system_prompt.md` | Hỏi xác nhận bằng `clarify(response_type="yes_no")` trước khi gửi sẽ sửa R12 | 0.90 | 0.85 (17/20; R12 PASS, nhưng R01/M02/M06 FAIL) | `runs/v2_B_base_openai_20261110T110731008259.json` |
| v3 | `artifacts/tools.yaml` | Mô tả rõ `timeline`, `social_search`, `lookup` và args sẽ sửa routing nhiều lượt | 0.85 | 1.00 (20/20; 0 provider error) | `runs/v3_B_base_openai_20261110T110948519400.json` |

## B2. Failure Analysis

Nguồn: `runs/v0_B_base_openai_20261110T103307388725.json`. Baseline có 20 case được đo, 13 PASS, 7 FAIL, không có provider error. `failure_type` bên dưới là nhãn của case; cột "What Failed" ghi sai lệch thực tế do bộ chấm phát hiện.

| Case ID | Failure Type | Actual Tool Calls | What Failed | Fix |
|---|---|---|---|---|
| R03_web_news_routing | wrong_tool | `lookup(query="AI news", topic="news", timeframe="day")` | Đúng tool nhưng query cần là `AI`; `observed_mismatch=wrong_arg_value` | PASS ở v3 sau khi mô tả quy ước query trong `tools.yaml` |
| R08_out_of_scope | out_of_scope | `send(text=...)` | Gọi tool cho yêu cầu giải tích phân, trong khi case mong không gọi tool | PASS ở v3; run v3 ghi không có tool call |
| R10_missing_handle | missing_info | `timeline(screenname="sama")` | Tự đoán tài khoản thay vì gọi `clarify` | Đã sửa prompt ở v1; case PASS trong run v1 |
| R11_missing_url | missing_info | `fetch(url="https://example.com/article")` | Tự bịa URL thay vì gọi `clarify` | Đã sửa prompt ở v1; case PASS trong run v1 |
| R12_confirm_before_send | wrong_boundary | `send(text="Bản tin này")` | Gọi `send` trước khi hỏi xác nhận | PASS ở v2 sau khi thêm quy tắc `clarify(response_type="yes_no")` |
| R13_parallel_web_and_tweets | wrong_tool | `lookup(query="AI news", timeframe="day")` và `social_search(query="AI")` | Gọi đủ hai tool nhưng `lookup` sai query và thiếu `topic="news"`; `observed_mismatch=wrong_arg_value` | PASS ở v3 sau khi mô tả args tin tức trong `tools.yaml` |
| R14_out_of_scope_coding | out_of_scope | `send(text=...)` | Gọi tool cho yêu cầu viết code, trong khi case mong không gọi tool | PASS ở v3; run v3 ghi không có tool call |

## B3. Team Eval Cases

10 case nhóm gồm 5 single turn và 5 multi turn trong `data/eval_group.json`.

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
| G01_dedupe_sources | Route tới tool mới | dedupe_sources | PASS |
| G02_social_top | Top tweet theo chủ đề | social_search / Top | PASS |
| G03_missing_article_url | Thiếu URL | clarify / text | PASS |
| G04_news_today | Tin hôm nay trên web | lookup / news / day | PASS |
| G05_out_of_scope | Ngoài phạm vi | no_tool | PASS |
| G06_handle_and_limit_carryover | Giữ handle và limit | timeline / elonmusk / 3 | PASS |
| G07_switch_social_to_web | Chuyển từ X sang web | lookup / news / day | PASS |
| G08_news_timeframe_carryover | Giữ timeframe | lookup / robotics / week | PASS |
| G09_send_without_confirmation | Xác nhận trước khi gửi | clarify / yes_no | PASS |
| G10_url_later_turn | URL xuất hiện ở lượt sau | fetch | PASS |

Group run: `runs/v3-tool_B_group_openai_20261110T111232980225.json` (10/10 PASS, 0 provider error). Sau khi thêm tool mới, base run `runs/v3-tool_B_base_openai_20261110T111340846274.json` vẫn đạt 20/20 PASS.

## B4. Live Chat Evidence

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
|---|---|---|---|---|
| 1 | Find AI news today on the web. | `lookup(query="AI", topic="news", timeframe="day")` | `v3-tool+pac5991968b0b+tb6d2f34a7e14` | Trả về 5 nguồn từ Tavily và tóm tắt |
| 2 | Summarize the latest 5 tweets for me. | Không gọi tool | cùng phiên bản | Hỏi lại tài khoản bằng câu trả lời trực tiếp; đây là khác biệt so với kỳ vọng `clarify` ở eval |
| 3 | The account is sama. | `timeline(screenname="sama", limit=5)` | cùng phiên bản | Route và args đúng, nhưng tool trả `Missing RAPIDAPI_KEY env var`; chưa lấy được tweet |

Transcript: `transcripts/v3-tool_openai_20261110T111515378687.transcript.json` (3 lượt thật). Cần bổ sung `RAPIDAPI_KEY` trong `.env` rồi thử lại nhánh X/Twitter trước demo.

## B5. Bonus Evidence

| Bonus | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| UI | `app.py` | Streamlit local mở trên `http://localhost:8501`; AppTest gọi `dedupe_sources` và trả lời không có exception | `send` chưa bật trong UI; chưa có link public |
| Tool unit tests (`tests/`) | `tests/test_tools_todo.py` | 6 test cho `dedupe_sources` PASS; toàn suite 87 PASS, 0 skipped | HTTP được mock; chưa kiểm tra RapidAPI thật vì thiếu key |

Unit test chưa phát hiện bug trong tool có sẵn. Live chat phát hiện lỗi cấu hình `RAPIDAPI_KEY` mà eval routing/args không phát hiện.

## B6. Reflection

- `system_prompt.md` phù hợp với quy tắc hỏi lại khi thiếu thông tin và xác nhận trước hành động gửi.
- `tools.yaml` phù hợp với routing web/X và quy ước `query`, `topic`, `timeframe`, `screenname`.
- R12 cần xem thủ công cả ranh giới hành động gửi. Run v2 cho thấy R12 PASS nhưng điểm tổng giảm từ 0.90 xuống 0.85, nên phải kiểm tra toàn bộ suite sau mỗi thay đổi.
- Eval chỉ chấm tool call và args: lượt chat 3 gọi đúng `timeline` nhưng thực thi thất bại do thiếu `RAPIDAPI_KEY`. Cần bổ sung key và chạy thử tool thật trước demo.

## B7. Small Local Model Challenge (bonus)

Không thực hiện bonus Small Local Model Challenge.
