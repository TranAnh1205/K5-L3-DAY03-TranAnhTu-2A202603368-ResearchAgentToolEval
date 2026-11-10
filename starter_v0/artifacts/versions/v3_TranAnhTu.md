# V3 của Tran Anh Tu

Commit gốc `69aa92a` có tác giả `AnhTu <atus011205@gmail.com>` và thêm các file v3 dưới đây cùng UI Streamlit. Commit `a971327`, cũng có tác giả `AnhTu`, cập nhật UI sau đó. Tài liệu này ghi rõ phần đóng góp của Tú mà không sửa các snapshot hoặc run đã dùng để chấm điểm.

| File | Vai trò | SHA-256 của file v3 gốc |
|---|---|---|
| `artifacts/versions/v3_system_prompt.md` | Prompt tại vòng tối ưu v3 | `ac5991968b0b4bf935742b4023645676be98ab73715092b32f4b185cf24d4165` |
| `artifacts/versions/v3_tools.yaml` | Khai báo và mô tả tool tại v3 | `f5534f4b0cf88ee9d3c57dea8d6ee8519cf08491583d71e40a5789b0bfedd27e` |
| `runs/v3_B_base_openai_20261110T110948519400.json` | Base eval OpenAI: 20/20 PASS, 0 provider error | `161b779f96ba4493ca8f10e1832a52d75fd7ec826b856d41ca151896c83d6fb9` |

Hai hash snapshot trên trùng `prompt_hash` và `tools_hash` trong run v3. UI của Tú là `app.py`; file này tiếp tục được cập nhật sau v3, nên không dùng hash hiện tại làm hash của v3.

Run OpenRouter v3 của Pham Huu Duc là thử nghiệm riêng trên nhánh của Đức, không phải run OpenAI v3 của Tú.
