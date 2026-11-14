# Bản nộp cuối — Day 7 Agentic RAG

**Đồng Ngọc Phúc · 2A202603399 · K5-L3A · 14/11/2026.**

Đây là chỉ dẫn hiện hành cho toàn bộ bản nộp. Nội dung kỹ thuật và bằng chứng đã
hoàn tất cục bộ; code/bằng chứng đã push tại `5e07c95`. Bản sửa tài liệu sau rà soát đang chờ
duyệt commit tiếp theo; quyền truy cập của người chấm và thao tác nộp link chưa
được xác nhận.

## Mở demo

Mở [demo.html](demo.html) trực tiếp bằng Chrome/Edge, không cần server, cơ sở dữ
liệu hoặc API key. Demo **phần cơ bản** gồm so sánh chunking A/B/C, xếp hạng
Dense/BM25/Hybrid theo metric, rank/score của từng chunk và phát lại câu trả lời
agent có citation. Dữ liệu đã nhúng sẵn, không gửi câu hỏi ra ngoài hay phát sinh phí.
Xem [hướng dẫn trình bày](docs/DEMO.md). Demo nâng cao được giữ riêng tại
[demo_advanced.html](demo_advanced.html).

## Phần cơ bản

- Báo cáo: [báo cáo cá nhân](report/individual/2A202603399_DongNgocPhuc.md).
- [README và lệnh chạy](README.md), [kết quả test](docs/TEST_RESULTS.md),
  [chọn pipeline trên dev](docs/DEV_SELECTION.md).
- Dùng 65 chunk C trên 33 trang nội dung trong báo cáo 84 trang; embedding thật
  1536 chiều, pgvector cosine, Dense/BM25/Hybrid RRF.
- Dev 17 câu (15 có đáp án, 2 thiếu bằng chứng), test 7 câu (5 + 2).
- Pipeline chọn BM25: retrieval dev Hit@1 và Hit@3 đều 15/15; agent test Dense và
  BM25 đều grounded 10/10 điểm, citation hỗ trợ 5/5, từ chối đúng 2/2.
- Hai cấu hình Dense thử cải thiện, kể cả kết quả không cải thiện, được giữ đầy đủ.
- [Gói dữ liệu Day 6 đã cho phép bàn giao](data/submission/day6_handoff.zip).

## Phần nâng cao — kết quả hiện hành

- [Báo cáo vòng 2 và cách tái lập](advanced_v2/README.md),
  [chỉ dẫn kết quả hiện hành](ADVANCED_V2.md).
- NASA Systems Engineering Handbook Rev.2: **297 trang**, index/render toàn bộ.
- Dùng lỗi cũ làm dev; chốt bộ test mới độc lập trước thử nghiệm và đánh giá.
- Test mới **29/30 = 96,67%**, 0 lỗi hệ thống, đạt ngưỡng ít nhất 90%.
- Test cũ **23/30** được giữ nguyên. Không thay thế điểm cũ hoặc tuning theo test mới.
- Một câu sơ đồ chưa đủ điều kiện được giữ không đạt; một câu trả lời “None”
  được chấm là từ chối về nghĩa dù status là `answered`, như đã công bố trong báo cáo.
- PDF NASA/ảnh render không nằm trong ZIP; tải lại từ URL và đối chiếu hash theo
  hướng dẫn. Một số ảnh có credit bên thứ ba; không phân phối lại nguyên tài liệu.

**Lưu ý hồ sơ lịch sử:** thư mục `advanced/` giữ nguyên vòng 1 (23/30). Các bản
README, báo cáo và checklist gốc đã chuyển vào snapshot theo
`artifacts/historical_document_map.json` để kiểm chứng receipt lịch sử. README và
báo cáo hiện hành được cập nhật kết quả vòng 2. Kiểm tra cả hai bằng
`python scripts/check_final_submission.py`; không thay đổi receipt hoặc điểm cũ.

## Kiểm tra và bàn giao

- Kết quả kiểm tra cuối: [validation](artifacts/final_submission_validation.json).
- Nội dung chờ duyệt trước commit: [bản rà soát](docs/FINAL_CHANGE_REVIEW.md),
  [commit message đề xuất](docs/PROPOSED_COMMIT_MESSAGE.txt).
- ZIP đi kèm có `SUBMISSION_MANIFEST.json` liệt kê SHA-256 từng file.
- Chỉ xuất code/tài liệu/bằng chứng được cho phép; loại `.git`, `.env`, credential,
  cache, venv và scratch. Quét pattern và credential cục bộ đã biết không thay thế
  kiểm toán bảo mật độc lập.
- Điểm và checklist là kết quả đối chiếu của bài làm, không phải điểm giảng viên
  đã xác nhận. Cần người nộp duyệt nội dung, hoàn tất commit/push nếu dùng GitHub,
  kiểm tra quyền xem của người chấm và nộp đúng kênh/hạn của lớp.
