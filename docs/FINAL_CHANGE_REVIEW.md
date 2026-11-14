# Nội dung bản nộp chờ duyệt trước commit

**Chưa stage, commit hoặc push.** Mốc so sánh: `c0a294c42af6ae798ac97e242f0a539206a159b3`.

## Nội dung thay đổi

1. Thêm phần nâng cao vòng 1 (`advanced/`): nguồn NASA 297 trang, index/render,
   benchmark, agent đọc ảnh và evidence dev/test. Giữ kết quả test cũ 23/30.
2. Thêm vòng 2 (`advanced_v2/`): dùng lỗi cũ làm dev, chốt test mới độc lập trước
   thử nghiệm; so sánh hai cấu hình, chọn GPT-5.2 trên dev, test mới 29/30,
   0 lỗi hệ thống. Có trace, nhãn/citation, snapshot, hash và chi phí từng câu.
3. Thêm demo HTML phần cơ bản: chunking A/B/C, ranh giới chunk cùng trang,
   leaderboard và rank Dense/BM25/Hybrid, phát lại câu trả lời/citation.
   Giữ demo nâng cao riêng, kèm builder/template/hướng dẫn.
4. Bổ sung báo cáo, chỉ dẫn nộp cuối và thông tin phương pháp đánh giá. Giữ
   nguyên predictor cơ bản, câu hỏi/gold, raw traces và điểm số đã công bố;
   cập nhật caption/mô tả và các hash tham chiếu liên quan, có snapshot đối chiếu.
5. Bảo toàn newline/byte các file có receipt; thêm audit, validation và inventory.

## File đã tracked có sửa so với commit gốc

- `.gitattributes`
- `README.md`
- `artifacts/benchmark_validation.json`
- `artifacts/privacy_review.json`
- `benchmarks/README.md`
- `benchmarks/freeze.json`
- `configs/pipeline_freeze.json`
- `docs/AGENT_DEV_REVIEW.md`
- `docs/DEV_SELECTION.md`
- `docs/RETRIEVAL.md`
- `docs/SUBMISSION_CHECKLIST.md`
- `docs/TEST_RESULTS.md`
- `report/individual/2A202603399_DongNgocPhuc.md`
- `results/RUN_HISTORY.md`
- `results/agent_dev_dense_wide/graded_summary.json`
- `results/agent_dev_dense_wide/reviews.json`
- `results/agent_dev_dense_wide_quotes/graded_summary.json`
- `results/agent_dev_dense_wide_quotes/reviews.json`
- `results/agent_dev_v1/graded_summary.json`
- `results/agent_dev_v1/reviews.json`
- `results/agent_test_v1/evaluation_receipt.json`
- `results/agent_test_v1/graded_summary.json`
- `results/agent_test_v1/reviews.json`
- `results/dev_comparison.json`
- `scripts/select_pipeline.py`
- `scripts/validate_benchmark.py`

## File mới chưa tracked

Danh sách đầy đủ, kích thước và SHA-256 theo từng file ở
[final_change_inventory.json](../artifacts/final_change_inventory.json).
Phân bố theo thư mục:

- `(root files)`: 4 file
- `advanced`: 207 file
- `advanced_v2`: 150 file
- `artifacts`: 4 file
- `assets`: 1 file
- `docs`: 3 file
- `scripts`: 2 file

## Commit message đề xuất

Xem [nguyên văn message](PROPOSED_COMMIT_MESSAGE.txt).

## Kiểm tra và giới hạn bàn giao

- 62 kiểm thử offline đạt; preflight cơ bản, vòng 1 và vòng 2 đều đạt.
- Demo đã kiểm tra logic JavaScript/dữ liệu; chưa kiểm tra ảnh giao diện qua trình
  duyệt tích hợp vì `file://` bị chặn. Mở `demo.html` để duyệt trực quan trước nộp.
- Source/gold/raw trace/nhãn và kết quả lịch sử giữ nguyên theo integrity check;
  không chạy lại model hoặc sửa pipeline theo test khi đóng gói.
- ZIP cuối nằm cục bộ trong `data/local/`, không thuộc nội dung commit; ZIP có
  manifest SHA-256 toàn bộ payload và bản demo mới.
- Không đưa `.git`, `.env`, credential, venv/cache/scratch, PDF/ảnh render NASA
  vào ZIP. Gói Day 6 được cho phép nằm trong `data/submission/day6_handoff.zip`.
- README gốc/báo cáo vòng đầu vẫn là hồ sơ lịch sử. Đọc
  [SUBMISSION_FINAL.md](../SUBMISSION_FINAL.md) và
  [advanced_v2/README.md](../advanced_v2/README.md) để xem kết quả mới nhất.
- Quyền người chấm truy cập và thao tác nộp link chưa được xác nhận.

Người dùng cần duyệt nội dung thay đổi và message trước mọi commit. Tài liệu này
không phải xác nhận đã duyệt; chưa có thao tác stage/commit/push.
