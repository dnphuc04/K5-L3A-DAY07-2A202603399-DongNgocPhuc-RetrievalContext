# Demo HTML phần cơ bản

Mở `demo.html` ở root bằng Chrome hoặc Edge. HTML chứa sẵn dữ liệu, chạy offline,
không cần server, PostgreSQL hay API key. Có nút chế độ trình chiếu để ẩn thanh bên.

Luồng trình bày đề xuất:

1. **Tổng quan & xếp hạng:** đổi metric Hit@1 / Hit@3 / context để xem xếp hạng
   Dense, BM25, Hybrid. Các phương pháp bằng điểm được đồng hạng.
2. **So sánh chunking:** A fixed 500/50; B theo cấu trúc max 1000; C giống B + filter
   chương. Chọn cùng trang để xem ranh giới, số ký tự và nội dung chunk; chọn câu
   dev để xem rank Dense của A/B/C. Không gọi C là cách chia khác B.
3. **Rank truy xuất:** chọn q13 để minh họa Dense bỏ lỡ quy tắc bằng điểm, BM25 tìm
   đúng ở rank 1, Hybrid khôi phục evidence trong top 3. Score giữa các cách có thang
   khác nhau nên không so trực tiếp.
4. **Trả lời & citation:** chọn dev/test và retriever, bấm mã citation trong câu trả
   lời để mở đoạn nguồn. Chọn câu thiếu bằng chứng để trình bày khả năng từ chối.

Nguồn số liệu: Day 6 `starter/results/chunks/{A,B,C}.jsonl`,
`starter/results/dev/traces.jsonl`, `artifacts/experiment_log.csv`;
Day 7 `results/retrieval_dev_v3`, `results/agent_dev_v1`, `results/agent_test_v1`
và `benchmarks/dev.gold.json`. Kết quả strict và kết quả rà soát được tách riêng.
Đây là bản phát lại thực nghiệm; không có ô nhập câu hỏi tùy ý hoặc lời hứa chạy live.

Tái tạo HTML từ dữ liệu gốc bằng Python:

```powershell
python scripts/build_demo.py --day6-root '..\K5-L3A-DAY06-DongNgocPhuc-2A202603399-DataIngestionEngineering'
```

Template ở `assets/demo-basic.template.html`. Dữ liệu được nhúng chỉ từ các trường
đầu ra cần trình chiếu, không đọc `.env`, chuỗi kết nối hay header xác thực.
File HTML chứa trích đoạn báo cáo trong phạm vi bằng chứng đã được cho phép chia sẻ.
Không thay đổi benchmark, pipeline, kết quả hoặc receipt đã chốt. Bản demo nâng cao
trước đó được giữ riêng tại `demo_advanced.html`.
