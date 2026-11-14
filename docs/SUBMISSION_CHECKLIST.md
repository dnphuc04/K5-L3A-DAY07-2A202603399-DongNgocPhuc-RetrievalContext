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

## Phần nâng cao và trạng thái bàn giao hiện hành

- [x] Tài liệu NASA 297 trang; index và render toàn bộ.
- [x] Dùng lỗi cũ làm dev, chốt test mới độc lập trước thử nghiệm; pipeline chọn trên dev.
- [x] Test mới **29/30 = 96,67%**, 0 lỗi hệ thống; có nhãn/citation/time/cost theo từng câu.
- [x] Test cũ 23/30 và toàn bộ evidence giữ nguyên. [Báo cáo hiện hành](../advanced_v2/README.md).
- [x] Quyền chia sẻ đầy đủ bằng chứng được ghi tại `submission_permission.json`.
- [x] Gói Day 6 và demo cơ bản có trong bản nộp; credential/cache/scratch bị loại.
- [x] Code và bằng chứng đã push lên `main` tại commit `5e07c95`.
- [ ] Bản sửa tài liệu sau rà soát toàn repo cần được duyệt trước commit/push tiếp theo.
- [ ] Người nộp xác nhận người chấm xem được repo và nộp link đúng kênh/hạn.
- [ ] Tác giả đọc đối chiếu nội dung trước khi ký/nộp.

[Bản nộp cuối](../SUBMISSION_FINAL.md) là chỉ dẫn hiện hành. Các mục quyền truy cập
và nộp thật không thể xác nhận chỉ từ filesystem. Kết quả đối chiếu rubric không
phải điểm giảng viên đã trao. Phần cơ bản dùng báo cáo 84 trang; yêu cầu nâng cao
trên 100 trang được đáp ứng riêng bằng tài liệu NASA 297 trang.
