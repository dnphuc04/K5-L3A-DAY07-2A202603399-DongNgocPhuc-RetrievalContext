# Kiểm kê đầu ra Day 6 cho Day 7

> **Ghi chép lịch sử:** các mục lỗi kết nối và thứ tự triển khai dưới đây mô tả lần kiểm kê đầu. Kết nối/adapter/benchmark/agent/test sau đó đã hoàn tất; trạng thái cuối ở [bản nộp](../SUBMISSION_FINAL.md) và [audit đã kết nối](../artifacts/day6_audit.json).

Ngày kiểm tra: 2026-11-14. Kết quả máy đọc được: `artifacts/day6_audit.json`.

## Có thể dùng lại

- Repo Day 6 nằm cạnh repo Day 7: `../K5-L3A-DAY06-DongNgocPhuc-2A202603399-DataIngestionEngineering`.
- PDF báo cáo thực tập: 84 trang theo manifest; file hiện có và SHA-256 khớp manifest. Corpus gồm 33 trang vật lý được chọn, đủ ngưỡng 30 trang của phần cơ bản. Chưa thực hiện đánh giá lại chất lượng từng trang trong lần kiểm kê này.
- Snapshot C: 65 chunk, ID duy nhất, text không rỗng, đủ trường nguồn/trang/metadata; tập trang khớp allowlist. B và C dùng cùng nội dung theo kết quả Day 6; C khác ở khả năng filter khi truy xuất.
- Embedding đã ghi nhận: `text-embedding-3-small`, 1536 chiều, không prefix; pgvector, bảng `lab_chunks`, cosine exact search. Giữ nguyên embedding và snapshot C cho cả Dense/BM25/Hybrid.
- Adapter Day 6 có sẵn trong `starter/src/embeddings.py` và `store.py`. Adapter store hiện chỉ hỗ trợ filter `chapter`; cần đổi tên `chunk_id → id`, `document_id → source_id` ở ranh giới Day 7.
- Dev có 15 câu có đáp án; cả 15 evidence đều nằm trong chunk C đúng nguồn/trang sau chuẩn hóa khoảng trắng. Đây là kiểm tra tự động, chưa thay thế đối chiếu ngữ nghĩa với PDF.
- Có cấu hình database và API key trong môi trường Day 6; audit chỉ kiểm tra sự hiện diện, không in giá trị. Chưa xác minh hiệu lực API key hay quyền model trả lời/tool calling.

## Cần bổ sung hoặc xác minh

| Hạng mục | Kết quả kiểm tra | Việc tiếp theo |
|---|---|---|
| Database hiện tại | Kết nối timeout; chưa đọc được bảng | Kiểm tra Docker/database đang chạy và đường kết nối, sau đó chạy lại audit read-only |
| Vector trong database | Day 6 có biên bản 65 dòng C và self-query; trạng thái hiện tại chưa xác minh | Đối chiếu toàn bộ snapshot C và vector_dims=1536 khi kết nối được |
| Câu thiếu evidence | Dev 0, test 0 | Bổ sung ít nhất 2 dev và 2 test, ghi cách kiểm tra thiếu thông tin trong corpus |
| Test độc lập Day 7 | Test Day 6 có 5 câu và đã có kết quả/audit | Giữ test cũ làm tài liệu lịch sử; tạo test Day 7 mới gồm ít nhất 5 câu có đáp án + 2 câu thiếu evidence trước tuning |
| Benchmark dev | Có thể dùng lại 15 câu; nhãn cũ có AI hỗ trợ | Chuyển schema, đối chiếu PDF, thêm 2 câu thiếu evidence; không đưa gold vào agent |
| Retrieval | Day 6 là các cấu hình dense/chunk/filter | Bổ sung BM25 và Hybrid RRF; A/B/C không được tính thành ba phương pháp Day 7 |
| Agent | Day 7 mới có protocol và vòng lặp mẫu | Kết nối model thật, tool retrieval, context, citation, abstention, giới hạn lượt và lỗi |
| Thí nghiệm | Kết quả Day 6 không thay thế benchmark Day 7 | Baseline + ít nhất 2 cấu hình cải thiện trên dev, phân tích ít nhất 2 lỗi, chốt trước test |
| Trace và chấm | Chưa có trace agent Day 7 | Lưu tool/query/ranking/context/answer/citation/time/token/cost/error, bổ sung nhãn context/answer/citation/abstention |
| Quyền chia sẻ | Manifest chưa xác minh quyền công bố PDF | Giữ dữ liệu trong máy, cung cấp cách truy cập hợp lệ; kiểm tra quyền trước khi công bố hoặc dùng dịch vụ ngoài |

Việc tạo test mới là lựa chọn bảo thủ để giữ đánh giá Day 7 độc lập sau khi Day 6 đã công bố kết quả. Chỉ việc từng chạy test Day 6 không tự chứng minh đã tuning bằng test.

Kiểm tra thêm bằng `docker ps -a`: Docker CLI có sẵn nhưng không kết nối được Docker Engine (named pipe không tồn tại); đồng thời có cảnh báo không đọc được Docker config. Chưa thể kết luận tình trạng volume hoặc container. Không thay đổi cấu hình Docker trong bước kiểm kê này.

## Thứ tự triển khai tiếp

1. Khôi phục kết nối database và chạy lại audit; không ingest lại hay thay đổi bảng trước khi xác định trạng thái hiện tại.
2. Viết adapter/export schema Day 7 cho snapshot C, giữ nguyên ID và trang PDF; giữ PDF và secret ở Day 6, không sao chép vào Git.
3. Chuẩn bị benchmark dev 17 câu và test mới 7 câu; tách gold khỏi đầu vào model, lưu hash trước thí nghiệm.
4. Triển khai Dense/BM25/Hybrid và agent thật; chạy dev, chọn cấu hình, sau đó đánh giá test và hoàn thiện báo cáo.

## Tái lập kiểm kê

Từ root Day 7, dùng Python đã có `psycopg` và `python-dotenv` (có sẵn trong venv Day 6):

```powershell
& '..\K5-L3A-DAY06-DongNgocPhuc-2A202603399-DataIngestionEngineering\starter\.venv\Scripts\python.exe' scripts/audit_day6.py --day6-root '..\K5-L3A-DAY06-DongNgocPhuc-2A202603399-DataIngestionEngineering' --output artifacts/day6_audit.json
```

Script chỉ đọc Day 6 và database trong transaction read-only; không gọi API model, không in secret, không ghi vào repo Day 6. Đọc test chỉ để đếm/schema; không xuất câu hỏi hoặc gold test vào kết quả kiểm kê.
