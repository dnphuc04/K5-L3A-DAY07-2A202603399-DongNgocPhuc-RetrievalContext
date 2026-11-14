# Rà soát nộp bài phần cơ bản

Đối chiếu [SUBMISSION](../SUBMISSION.md), [RUBRIC](../RUBRIC.md) và [BENCHMARK](../BENCHMARK.md), ngày 2026-11-14. Các dấu hoàn thành bên dưới nói về bằng chứng **đã có cục bộ**, không tự xác nhận đã nộp hoặc giảng viên sẽ cho đủ điểm.

## Bằng chứng kỹ thuật

- [x] **Dữ liệu/Day 6:** PDF hash khớp, 33 trang/65 chunk C, OpenAI embeddings thật 1536 chiều và pgvector cosine exact; audit DB và self-query. [Audit](../artifacts/day6_audit.json), [adapter](DAY6_ADAPTER.md).
- [x] **Benchmark:** 15+2 dev, 5+2 test; câu có đáp án kèm nguồn/trang/evidence, câu thiếu có absence reason; input tách gold. [Benchmark](../benchmarks/README.md), [freeze](../benchmarks/freeze.json).
- [x] **Ba retrieval khác nhau:** Dense, BM25 và Hybrid RRF, cùng corpus/filter, score/rank/source/page/metadata. [Code](../src/retrieval.py), [retrieval dev](../results/retrieval_dev_v3/summary.json).
- [x] **Agent thật:** OpenAI snapshot, tool search, truy xuất nhiều lượt có giới hạn; context dedup/budget, claim/citation, từ chối và lỗi riêng. [Agent](../src/agent.py), [model](../src/model.py), [trace dev](../results/agent_dev_v1/traces.json).
- [x] **Đánh giá:** Hit@1/3 cùng cutoff; context evidence; chấm grounded 0/1/2, citation semantic support, coverage, abstention, false refusal và tool use. [Dev](DEV_SELECTION.md), [test](TEST_RESULTS.md).
- [x] **Hai cấu hình thử cải thiện:** Dense k6/7000 và thêm quote guard; giả thuyết, lỗi trước/sau, kết quả không cải thiện vẫn giữ. [Giả thuyết](../configs/dev_experiments.json), [bảng so sánh](../results/dev_comparison.json).
- [x] **Chọn dev trước test:** BM25 đã chốt; Dense/BM25 chạy đủ test, code/config/benchmark hash giữ nguyên trước/sau. [Pipeline freeze](../configs/pipeline_freeze.json), [test receipt](../results/agent_test_v1/evaluation_receipt.json).
- [x] **Chấm đầy đủ test:** 14 kết quả, 10 context có đáp án và mọi citation, lý do từng câu; không lấy ID hợp lệ làm bằng chứng semantic. [Nhãn](../results/agent_test_v1/reviews.json), [phiếu](../results/agent_test_v1/review_packet.json).
- [x] **Ví dụ trình bày:** một câu có nguồn, một câu thiếu và một lỗi dev có nguyên nhân trong báo cáo cá nhân.
- [x] **Tái lập dữ liệu:** gói local và script restore không chứa secret; đã thử round-trip DB riêng. [Cách bàn giao](DATA_ACCESS.md), [kết quả kiểm tra](../artifacts/handoff_verification.json).
- [x] **Chi phí/thời gian:** usage thật từng run, latency, estimate theo giá công khai với ngày/nguồn; hóa đơn thực tế vẫn chưa đối chiếu. [Ước tính](../artifacts/cost_estimate.json), [script](../scripts/estimate_costs.py). Không sửa summary gốc hoặc quyết định chọn pipeline bằng estimate bổ sung sau test.
- [x] **Báo cáo cá nhân và hướng dẫn:** [báo cáo](../report/individual/2A202603399_DongNgocPhuc.md), [README](../README.md), dependency và biến môi trường mẫu.
- [x] **Kiểm thử code/hash:** suite unittest, validation benchmark, pipeline freeze và test receipt; không gọi API benchmark lại chỉ để kiểm tra hồ sơ.
- [x] **Giữ byte khi clone:** `.gitattributes` tắt newline conversion vì hồ sơ có cả LF/CRLF và hash theo byte gốc; không renormalize run đã chốt.

## Việc còn cần trước khi nộp thật

- [x] Người dùng đã cho phép nộp đầy đủ PDF và bằng chứng ngày 14/11/2026; ghi nhận ở `submission_permission.json`.
- [x] Đưa gói dữ liệu đã quét vào `data/submission/day6_handoff.zip` và mở các file evidence cho Git/bộ nộp đầy đủ. Không có credential trong gói.
- [ ] Bàn giao bộ nộp hoặc cấp quyền người chấm; chưa kiểm chứng truy cập từ tài khoản khác.
- [ ] Commit/push code và bằng chứng được phép lên repo cá nhân; hiện có nhiều file mới/chưa commit. Không dùng `git add -f data/local`; gói được phép nằm trong `data/submission/`.
- [ ] Kiểm tra tài khoản giảng viên xem được repo và dữ liệu riêng; nộp link đúng kênh/hạn của lớp. Chưa tự push, mời người khác hoặc gửi link thay người dùng.
- [ ] Khuyến nghị tác giả đọc đối chiếu lại các nhãn AI và số liệu trước khi ký/nộp. Bài không tuyên bố đã có người chấm độc lập.

Các mục quyền truy cập/nộp thật không thể được xác nhận chỉ từ filesystem. Không đánh dấu hoàn thành giả để kết luận bài đã nộp. Không làm bonus nâng cao; PDF 84 trang và benchmark cơ bản không đáp ứng thử thách 100 trang.
