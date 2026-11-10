# Day 03 Lab v2 Report — Research Agent

Phần A giới thiệu agent để demo; Phần B ghi bằng chứng từ run và transcript thật.

## Team

- Team: **[điền tên nhóm]**
- Members: Tran Anh Tu, Pham Huu Duc, Nguyen Tran Anh Khoi, Nguyen Quang Vu, Khoa (**[điền họ tên đầy đủ/MSSV nếu cần]**).
- Provider/model: OpenAI `gpt-4o-mini`

### Tích hợp đóng góp của năm thành viên

| Thành viên | Đóng góp có trong bản hợp nhất |
|---|---|
| Tran Anh Tu (`TranAnhTu_03368`) | Nền agent, prompt, UI Streamlit, bốn tool nghiên cứu mới, eval và báo cáo chính. |
| Pham Huu Duc (`PhamHuuDuc_03380`) | Tool `calculator` dùng cho số liệu nghiên cứu, poster demo, run OpenRouter v1–v3 và transcript. Phần tính toán đã được giới hạn cú pháp và bổ sung test trước khi kích hoạt. |
| Nguyen Tran Anh Khoi (`nguyentrananhkhoi-03422`) | Bộ unit test TODO và rà soát báo cáo trên nhánh kế thừa Đức; lịch sử commit được giữ trong merge. Các test trùng mục tiêu với bản hiện tại được giữ một bản. |
| Khoa (`llkhoa`) | Sửa xử lý giới hạn kết quả ở `timeline`, `social_search`, `lookup`, `policy` và định dạng nguồn thiếu URL. |
| Nguyen Quang Vu (`nguyenquangvu-2A202603407`) | Hàm `normalize_handle` được dùng bên trong `timeline`, test cho tên tài khoản có `@`, run base và group hợp lệ, transcript. |

Ba merge commit giữ lịch sử từng nhánh. Các run dùng provider/model khác nhau là bằng chứng độc lập; không ghép thành một chuỗi tăng điểm giả định.

---

# PHẦN A — Giới thiệu agent

## A1. Agent này làm được gì

Research Agent tìm tin trên web hoặc X/Twitter, đọc URL, tìm paper, tra policy nội bộ và tổng hợp nguồn đã có. Agent còn tra Wikipedia, thảo luận Hacker News và repository GitHub. Khi thiếu tài khoản hoặc URL, agent hỏi lại; yêu cầu gửi Telegram phải được xác nhận trước.

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
| calculator | tính tỷ lệ hoặc chênh lệch từ số liệu đã tìm được | có |
| wiki | tra định nghĩa, tiểu sử và kiến thức nền trên Wikipedia | có |
| hn_search | tìm bài và thảo luận Hacker News | có |
| github_repos | tìm repository GitHub theo chủ đề, ngôn ngữ, sao hoặc ngày cập nhật | có |
| policy | tra tài liệu policy cục bộ | không |
| papers / paper_text | tìm và đọc bài arXiv | không |
| send | chuẩn bị tin nhắn Telegram; UI/CLI chỉ gửi thật sau xác nhận thủ công riêng | không |

## A3. Câu hỏi mẫu để thử

1. Tin AI hôm nay trên web có gì nổi bật?
2. Tìm các tweet phổ biến về robotics trên X.
3. Đọc và tóm tắt trang này: https://www.python.org/about/
4. Loại nguồn trùng trong `https://example.com/story?utm_source=mail` và `https://example.com/story`.
5. Tìm paper arXiv về transformer và đọc paper phù hợp.
6. Tra Wikipedia tiếng Việt: trí tuệ nhân tạo là gì?
7. Tìm bài mới nhất về Python trên Hacker News.
8. Tìm 3 repository GitHub về research agent viết bằng Python, ưu tiên nhiều sao.
9. Theo hai nguồn đã tìm, số lượt dùng tăng từ 800 lên 1000; tính tỷ lệ tăng.

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
| v4_6 | `artifacts/system_prompt.md` + `artifacts/tools.yaml`; thêm chốt gửi trong code | Kết nối đủ 11 tool, sửa prompt nhiều bước và mô tả policy mà không làm hồi quy routing base | 1.00 (v3-tool) | base 1.00 (20/20), group 1.00 (10/10), extension 1.00 (10/10); 0 provider error | `runs/v4_6_B_base_openai_20261110T210304240055.json`, `runs/v4_6_B_group_openai_20261110T210415181532.json`, `runs/v4_6_B_extension_openai_20261110T210342056688.json` |
| v5 | Thêm `wiki`, `hn_search`, `github_repos` vào code, prompt và declaration | Bốn tool tự viết sẽ mở rộng nguồn nghiên cứu mà vẫn giữ routing cũ; eval nhóm kiểm tra cả bốn tool | base 1.00, group 1.00 (v4_6) | base 1.00 (20/20), group 1.00 (10/10), extension 1.00 (10/10); 0 provider error | `runs/v5_B_base_openai_20261110T215830021951.json`, `runs/v5_B_group_openai_20261110T215900376440.json`, `runs/v5_B_extension_openai_20261110T215935217433.json` |
| team | Ghép đóng góp năm nhánh; thêm `calculator`, chuẩn hóa handle và xử lý input | Kết hợp các thay đổi có ích sẽ giữ điểm routing và không làm hỏng ranh giới xác nhận gửi | base/group/extension 1.00 (v5) | base 20/20, group 10/10, extension 10/10; 0 provider error; 128 unit test PASS | `runs/team_B_base_openai_20261110T231205543275.json`, `runs/team_B_group_openai_20261110T231243816153.json`, `runs/team_B_extension_openai_20261110T231321811094.json` |

Các run trung gian v4–v4_5 được giữ trong `runs/` và `version_log.csv`. Một số thay đổi làm điểm base giảm xuống 18/20 hoặc 19/20; v4_6 là lần đo lại cả ba suite sau khi sửa hồi quy.

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
| G02_wiki_background | Tra kiến thức nền Wikipedia | wiki / vi | PASS |
| G03_missing_article_url | Thiếu URL | clarify / text | PASS |
| G04_hn_newest | Bài mới nhất trên Hacker News | hn_search / date | PASS |
| G05_github_python_stars | Repo Python nhiều sao trên GitHub | github_repos / Python / stars / 3 | PASS |
| G06_handle_and_limit_carryover | Giữ handle và limit | timeline / elonmusk / 3 | PASS |
| G07_switch_social_to_web | Chuyển từ X sang web | lookup / news / day | PASS |
| G08_news_timeframe_carryover | Giữ timeframe | lookup / robotics / week | PASS |
| G09_send_without_confirmation | Xác nhận trước khi gửi | clarify / yes_no | PASS |
| G10_url_later_turn | URL xuất hiện ở lượt sau | fetch | PASS |

Group run hiện tại: `runs/team_B_group_openai_20261110T231243816153.json` (10/10 PASS, 0 provider error). Bốn tool mới ban đầu có case routing (G01, G02, G04, G05); `calculator` được kiểm tra bằng unit test riêng. Base run `runs/team_B_base_openai_20261110T231205543275.json` đạt 20/20 PASS. Run v3-tool được giữ làm bằng chứng lịch sử.

## B4. Live Chat Evidence

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
|---|---|---|---|---|
| 1 | Find AI news today on the web. | `lookup(query="AI", topic="news", timeframe="day")` | `v4_6+p5c07c09c2ea9+t52d987accec3` | Tavily trả 5 nguồn; agent tóm tắt và dẫn URL |
| 2 | Summarize the latest 3 tweets from Sam Altman. | `timeline(screenname="sama", limit=3)` | cùng phiên bản | RapidAPI trả 3 tweet; agent tóm tắt và dẫn URL |
| 3 | Find the most popular tweets about robotics on X. | `social_search(query="robotics", search_type="Top", limit=5)` | cùng phiên bản | RapidAPI trả 5 tweet; agent tóm tắt và dẫn URL |

Transcript mới: `transcripts/v4_6_openai_20261110T213256375363.transcript.json` (3 lượt thật, 3 tool thành công). Transcript cũ `transcripts/v3-tool_openai_20261110T111515378687.transcript.json` giữ làm bằng chứng lịch sử trước khi RapidAPI được cấp quyền.

## B5. Bonus Evidence

| Bonus | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| UI | `app.py` | Streamlit local mở trên `http://localhost:8501`; cả 15 tool khai báo được đưa vào model; AppTest luồng chờ gửi/hủy không lỗi | UI cần một lần bấm xác nhận riêng trước khi Telegram POST; chưa có link public |
| Bốn tool mới | `tools/{dedupe_sources,wiki,hn_search,github_repos}/` | Mỗi tool có `tool.py`, `TOOL.md`, registry và declaration; G01/G02/G04/G05 đều PASS | Ba nguồn live không cần API key nhưng phụ thuộc dịch vụ ngoài; GitHub có rate limit |
| Tool unit tests (`tests/`) | `tests/test_tools_todo.py`, `tests/test_chat_send_guard.py`, `tests/test_paper_tools.py`, `tests/test_rapidapi_errors.py`, `tests/test_calculator.py`, `tests/test_normalize_handle.py` | ≥3 test cho mỗi tool mới; toàn suite 128 PASS, 0 skipped; test chặn model tự xác nhận gửi, parse arXiv offline, chuẩn hóa handle và báo lỗi RapidAPI rõ ràng | HTTP của unit test được mock |
| Smoke test ba nguồn mới | `scripts/smoke_all_tools.py`, `analysis/tool_smoke_new_tools.json` | wiki, hn_search, github_repos đều completed với API thật | Mỗi lần smoke chỉ lấy 1 item để tiết kiệm quota |
| Smoke test tất cả tool | `scripts/smoke_all_tools.py`, `analysis/tool_smoke_v4_6.json`, `analysis/tool_smoke_after_rapidapi.json`, `analysis/tool_smoke_rapidapi_diagnostic.json` | 7 tool hoàn tất ở lần chạy đầu; sau khi cấp quyền, timeline và social_search cũng hoàn tất (mỗi tool trả 1 tweet trong diagnostic); send bị chặn đúng khi chưa xác nhận | `papers` gặp timeout/lỗi HTTP ở arXiv; Telegram chưa có `TELEGRAM_CHAT_ID` nên không gửi thật |

Unit test chưa phát hiện bug trong tool có sẵn. Eval đo việc chọn tool và args, không chứng minh mọi API bên ngoài chạy được. RapidAPI từng trả 403/429 trước khi ứng dụng được cấp quyền; lần chạy mới nhất đã thành công với cả timeline và social_search. arXiv search vẫn gặp timeout/lỗi HTTP. Tool `paper_text` đã đọc PDF arXiv thật; `papers` đã được kiểm tra parse Atom bằng unit test offline.

## B6. Reflection

- `system_prompt.md` phù hợp với quy tắc hỏi lại khi thiếu thông tin và xác nhận trước hành động gửi.
- `tools.yaml` phù hợp với routing web/X và quy ước `query`, `topic`, `timeframe`, `screenname`.
- R12 cần xem thủ công cả ranh giới hành động gửi. Run v2 cho thấy R12 PASS nhưng điểm tổng giảm từ 0.90 xuống 0.85, nên phải kiểm tra toàn bộ suite sau mỗi thay đổi.
- Eval chỉ chấm tool call và args: transcript cũ gọi đúng `timeline` nhưng thiếu `RAPIDAPI_KEY`. Sau khi key và quyền được bổ sung, transcript v4_6 chứng minh cả timeline và social_search trả dữ liệu thật.
- UI hiện nạp đủ 15 tool, còn lớp chặn độc lập trong `chat.py` giữ mọi lệnh `send` ở trạng thái chờ bấm xác nhận. Model tự đặt `confirmed=true` không thể gửi trực tiếp từ UI/CLI.

## B7. Small Local Model Challenge (bonus)

Không thực hiện bonus Small Local Model Challenge.
