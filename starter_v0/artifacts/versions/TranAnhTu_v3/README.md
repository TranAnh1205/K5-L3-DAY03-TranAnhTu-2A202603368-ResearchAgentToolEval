# Phần v3 và UI của Tran Anh Tu

Thư mục này chứa **bản sao nội dung file thật** từ phần v3 của Tú, được commit riêng với tác giả `Tran Anh Tu`. Các file gốc vẫn ở vị trí mà bài lab dùng để chạy và chấm điểm.

| File trong thư mục này | File gốc | Vai trò |
|---|---|---|
| `system_prompt.md` | `../v3_system_prompt.md` | Prompt v3; SHA-256 `ac5991968b0b4bf935742b4023645676be98ab73715092b32f4b185cf24d4165` |
| `tools.yaml` | `../v3_tools.yaml` | Khai báo tool v3; SHA-256 `f5534f4b0cf88ee9d3c57dea8d6ee8519cf08491583d71e40a5789b0bfedd27e` |
| `eval_base.json` | `../../../runs/v3_B_base_openai_20261110T110948519400.json` | Run OpenAI v3, 20/20 PASS, 0 provider error |
| `app.py` | `../../../app.py` tại commit `69aa92a` | Mã UI Streamlit của Tú tại thời điểm v3; UI chính tiếp tục được cập nhật sau đó |

Hai file prompt và tools giữ nguyên byte, kể cả CRLF, vì run v3 lưu hash theo byte. `.gitattributes` ngăn Git đổi dòng khi commit hoặc checkout các bản sao này.
