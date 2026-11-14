# Adapter Day 6 → Day 7

## Kết quả xác minh 2026-11-14

Container `day6_student_starter-postgres-1` đã được khởi động lại qua Docker context `desktop-linux`. Không ingest lại, không đổi bảng hoặc volume.

Audit read-only xác nhận 65 dòng strategy C khớp toàn bộ ID/text/source/page/metadata của snapshot; tất cả vector có 1536 chiều, hữu hạn và khác vector zero. Truy vấn adapter bằng một vector document có sẵn trả đúng chunk ở top-1, cosine score 1.0. Đây là kiểm tra tích hợp, không phải benchmark chất lượng query và không gọi API embedding.

Chi tiết: `artifacts/day6_audit.json`. Nếu Docker dừng, khởi động lại container hiện có rồi chạy script audit; không cần ingest.

## Export local

Từ root Day 7, dùng Python/venv Day 6:

```powershell
& '..\K5-L3A-DAY06-DongNgocPhuc-2A202603399-DataIngestionEngineering\starter\.venv\Scripts\python.exe' -m src.day6_adapter --day6-root '..\K5-L3A-DAY06-DongNgocPhuc-2A202603399-DataIngestionEngineering' --output data/local/day6
```

Đã tạo 65 chunk và 15 câu dev ở thư mục này, được Git ignore:

- `chunks.json`: schema Day 7, giữ nguyên ID, nguồn, trang PDF vật lý và metadata.
- `dev.inputs.json`: chỉ ID, question, filter; dùng làm đầu vào agent.
- `dev.gold.json`: nhãn, đáp án và evidence, chỉ dùng cho evaluation.
- `provenance.json`: SHA-256 đầu vào và quy ước resolve đường dẫn nguồn tương đối với root Day 6.

Không export test Day 6; benchmark Day 7 vẫn cần 2 câu dev thiếu evidence và test mới 7 câu. File cùng tên trong thư mục output sẽ được ghi đè khi export lại. Không commit corpus/PDF khi chưa xác minh quyền chia sẻ.

## Truy vấn vector

`src.day6_adapter.Day6VectorReader(database_url).search(query_vector, filters=None, top_k=3)` truy vấn snapshot C trong transaction read-only và trả schema Day 7 cùng score. Chỉ hỗ trợ filter `chapter` như Day 6. Query vector phải được tạo bằng `text-embedding-3-small`, 1536 chiều, không prefix. Adapter này chưa gọi embedding hoặc điều phối agent.

Nạp database URL bằng biến môi trường hoặc dotenv Day 6 ở runtime; không truyền secret qua CLI hay lưu vào output. Không có chức năng tạo schema, upsert hoặc fallback giả trong adapter.
