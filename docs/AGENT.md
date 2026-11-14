# Agent thật trên dev

## Kiến trúc

`src/model.py` kết nối OpenAI Chat Completions bằng HTTP, dùng snapshot cấu hình mặc định `gpt-4.1-mini-2025-04-14`, temperature 0, tối đa 1200 completion tokens/request, timeout 45 giây, `store=false`. Không fallback mock, không ghi API key hoặc raw HTTP error vào trace. Model snapshot này được tài liệu chính thức đánh dấu deprecated; cần kiểm tra quyền truy cập thật trước khi chạy hàng loạt, không tự đổi model giữa các cấu hình.

`src/agent.py` thực thi tool calling thật: lần gọi đầu bắt buộc tool `search`, các lượt sau model được chọn tìm tiếp hoặc trả lời. Mỗi cấu hình sử dụng một retriever cố định Dense/BM25/Hybrid để so sánh công bằng; model quyết định lúc nào tìm tiếp và query sau. Lần tìm đầu luôn dùng câu hỏi gốc; cả query model yêu cầu và query thực thi đều được ghi lại. Filter lấy từ input đã chốt, model không được sửa filter.

Mặc định top-k=3, tối đa 2 lượt search, context budget 4000 ký tự gồm ID/nguồn/trang. Gom candidate theo thứ tự tìm, loại trùng và giữ nguyên cả chunk nếu còn budget. History model chỉ chứa context tích lũy hiện tại và danh sách query đã tìm, không cộng dồn các context cũ ngoài budget. Chính sách ưu tiên chunk cũ có thể làm thiếu evidence mới; cần đo trên dev trước khi thay đổi.

Output model dùng JSON schema nghiêm ngặt với `status` và `claims`; mỗi claim có `text` và `citations`. Renderer gắn các ID model chọn dưới dạng `[chunk-id]` sau từng claim, không tự tạo nội dung hoặc nguồn. Câu trả lời chỉ được xuất khi mỗi claim có ID hợp lệ trong context cuối và mọi citation inline khớp danh sách nguồn. Nếu model từ chối, hệ thống xuất câu từ chối cố định để tránh đưa thêm suy đoán. Citation ID hợp lệ chỉ là kiểm tra cấu trúc; nhãn semantic support phải được chấm riêng. Lỗi API/retrieval được ghi `status=error`, không tính là từ chối đúng.

Smoke test thật đã phát hiện provider có thể trả `finish_reason=stop` cùng một tool call hợp lệ; agent chấp nhận trường hợp này nhưng vẫn từ chối phản hồi bị cắt do token limit. Các smoke v1-v3 được giữ để ghi lỗi tích hợp và lần thay đổi cấu trúc citation; smoke v4 xác nhận một câu có citation và một câu thiếu evidence được từ chối. Đây đều là thử nghiệm dev trước khi chạy toàn bộ dev, không chỉnh dựa trên test.

## Bảo vệ benchmark và trace

`scripts/run_agent_dev.py` chỉ đọc `dev.inputs.json`; không load gold. Test chỉ được kiểm tra hash để bảo toàn freeze, không gửi tới model hoặc chạy truy xuất. `src/runtime.py` đối chiếu snapshot và dữ liệu DB trước khi chạy; tái sử dụng query embedding cache trong Day 7.

Trace từng câu gồm tool call/arguments, query gốc và viết lại, kết quả/ranking/score, context cuối, nội dung request model (không có header/key), phản hồi, answer/citations, số lượt gọi, latency, token usage và lỗi. Model request có chứa context báo cáo nên trace chỉ dùng local cho đến khi xác minh quyền chia sẻ. Gold và kết quả chấm nằm ngoài runner.

Runner ghi từng câu bằng file tạm rồi replace; không ghi đè thư mục run cũ. Dừng sớm nếu gặp lỗi provider để tránh lặp nhiều request không có ích. Summary ban đầu chỉ là thống kê vận hành; không tự suy điểm grounding/citation/abstention từ status hoặc citation ID.

## Chạy

Dùng venv Day 6 hoặc cài `requirements.txt`. Model dùng API key có sẵn ở môi trường hoặc dotenv Day 6; không copy key sang repo.

```powershell
# Smoke trên một câu dev
& '..\K5-L3A-DAY06-DongNgocPhuc-2A202603399-DataIngestionEngineering\starter\.venv\Scripts\python.exe' scripts/run_agent_dev.py --day6-root '..\K5-L3A-DAY06-DongNgocPhuc-2A202603399-DataIngestionEngineering' --output results/agent_smoke_new --methods bm25 --ids q01

# Toàn bộ dev, 3 cấu hình retriever, chưa chạy test
& '..\K5-L3A-DAY06-DongNgocPhuc-2A202603399-DataIngestionEngineering\starter\.venv\Scripts\python.exe' scripts/run_agent_dev.py --day6-root '..\K5-L3A-DAY06-DongNgocPhuc-2A202603399-DataIngestionEngineering' --output results/agent_dev_new
```

CLI không cung cấp tùy chọn test. Các lệnh thật gửi câu hỏi/context dev tới OpenAI Chat Completions và có thể gửi query tìm tiếp tới embeddings; phải trong phạm vi người dùng cho phép. Tiền API chưa tính khi chưa đối chiếu billing; lưu token/request thực tế thay vì bịa chi phí.

## Trạng thái sau vòng cải thiện dev

Đã chấm đầy đủ 85 kết quả của 5 cấu hình và chốt BM25 theo `configs/selected_pipeline.json`. Chi tiết điểm, lỗi, hai thử nghiệm không thắng và giới hạn nằm trong `docs/DEV_SELECTION.md`. Quote mode (`--require-quotes`) bổ sung quote nguyên văn cho từng claim và kiểm tra quote thuộc đúng chunk; schema/prompt/output cap thay đổi được ghi trong run config. Đây là tùy chọn thí nghiệm, không bật trong pipeline được chọn. Bộ test chưa chạy.

## Tài liệu API đã đối chiếu

- [Function calling](https://developers.openai.com/api/docs/guides/function-calling): strict schema, tool choice, tool result messages và tắt parallel calls.
- [Structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs): JSON schema cho câu trả lời cuối.
- [GPT-4.1 mini](https://developers.openai.com/api/docs/models/gpt-4.1-mini): snapshot, tool calling, structured outputs và trạng thái model.
