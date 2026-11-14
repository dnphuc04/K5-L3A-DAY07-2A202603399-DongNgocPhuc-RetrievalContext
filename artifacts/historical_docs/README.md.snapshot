# Day 7 — Agentic RAG · Đồng Ngọc Phúc

**K5-L3A · Mã học viên 2A202603399.** Agent phần cơ bản dùng model thật để gọi Dense/BM25/Hybrid trên cùng dữ liệu Day 6, trả lời có citation hoặc từ chối khi thiếu evidence. Đã chọn BM25 trên dev, sau đó đánh giá Dense/BM25 trên test; không tuning theo test.

**Phần nâng cao:** dùng NASA Systems Engineering Handbook Rev.2 **297 trang**, index/render toàn bộ tài liệu; pipeline tìm kiếm và vision, benchmark riêng 18 dev/30 test. Kết quả **17/18 dev, 23/30 test (76,666…%)**, chưa đạt 90%, **chưa đủ điều kiện 15 điểm bonus**. Xem [code, báo cáo, bằng chứng và cách chạy nâng cao](advanced/README.md). Phần cơ bản giữ nguyên predictor và kết quả đã chạy.

**Phạm vi chia sẻ:** người dùng đã cho phép nộp đầy đủ bằng chứng, được ghi tại [submission_permission.json](submission_permission.json). Bộ nộp gồm benchmark/gold, trace/nhãn, cấu hình, báo cáo và gói Day 6 đã kiểm tra không có credential. `.env`, API key, private key, `.git` và thư mục scratch vẫn bị loại. Xem [rà soát quyền riêng tư](docs/PRIVACY_REVIEW.md).

## Bài nộp và kết quả

- [Báo cáo cá nhân](report/individual/2A202603399_DongNgocPhuc.md).
- [So sánh dev](docs/DEV_SELECTION.md), [kết quả test](docs/TEST_RESULTS.md), [checklist nộp bài](docs/SUBMISSION_CHECKLIST.md).
- [Dữ liệu riêng và khôi phục](docs/DATA_ACCESS.md), [pipeline chọn](configs/selected_pipeline.json), [hash chốt](configs/pipeline_freeze.json).
- Đề gốc: [GUIDE](GUIDE.md), [BENCHMARK](BENCHMARK.md), [RUBRIC](RUBRIC.md), [SUBMISSION](SUBMISSION.md).

| Cấu hình | Split | Hit@1 | Hit@3 | Context đủ evidence | Grounded | Citation hỗ trợ | Từ chối đúng |
|---|---|---|---|---|---|---|---|
| Dense baseline | dev | 10/15 | 14/15 | 14/15 | 27/30 | 15/16 | 2/2 |
| BM25 chọn | dev | 15/15 | 15/15 | 15/15 | 30/30 | 16/16 | 2/2 |
| Hybrid RRF | dev | 13/15 | 15/15 | 15/15 | 30/30 | 16/16 | 2/2 |
| Dense k6/context lớn | dev | 10/15 | 14/15 | 15/15 | 26/30 | 16/18 | 2/2 |
| Dense k6 + quote guard | dev | 10/15 | 14/15 | 15/15 | 25/30 | 14/14 | 2/2 |
| Dense baseline | test | 4/5 | 5/5 | 5/5 | 10/10 | 5/5 | 2/2 |
| BM25 chọn | test | 5/5 | 5/5 | 5/5 | 10/10 | 5/5 | 2/2 |

Nhãn được đối chiếu từng câu trả lời và citation với nguồn gốc. Benchmark phần cơ bản nhỏ, một tài liệu; không suy rộng điểm này sang tài liệu khác. Chi tiết n/N, phần trăm, thời gian/token/lỗi và hai thử nghiệm không cải thiện có trong báo cáo. Kết quả phần nâng cao được báo riêng.

## Chuẩn bị

Python 3.11+, PostgreSQL 16 với pgvector, API key có quyền `gpt-4.1-mini-2025-04-14` và `text-embedding-3-small`. Dùng snapshot C Day 6: 65 chunk/33 trang trong PDF 84 trang, bảng `lab_chunks`, vector 1536 chiều, cosine exact search, query/document không prefix.

PowerShell từ root repo:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$python = '.\.venv\Scripts\python.exe'
$day6 = '..\K5-L3A-DAY06-DongNgocPhuc-2A202603399-DataIngestionEngineering'
# Hoặc dùng venv Day 6 đã có:
# $python = "$day6\starter\.venv\Scripts\python.exe"
```

Runtime đọc `OPENAI_API_KEY` và `DATABASE_URL` từ biến môi trường, hoặc fallback `<day6-root>/starter/.env`. `.env` tại root Day 7 không tự được nạp. Xem tên biến trong [.env.example](.env.example); không đặt key trên CLI/commit vào Git. Không đổi embedding hay ingest đè DB đánh giá.

Môi trường đã chạy: Python 3.12.14, PostgreSQL 16.16, pgvector 0.8.7; phiên bản package ở [environment.json](artifacts/environment.json). Có thể cài [requirements-reproduction.txt](requirements-reproduction.txt) thay `requirements.txt` để khớp đúng phiên bản đã ghi nhận.

Máy người chấm chưa có Day 6 dùng [data/submission/day6_handoff.zip](data/submission/day6_handoff.zip) có trong bộ nộp và làm theo [DATA_ACCESS](docs/DATA_ACCESS.md). Gói không có credential; giải nén/restore vector rồi đặt API key riêng của người chạy để tái lập.

## Kiểm tra offline và dữ liệu

```powershell
& $python -m unittest discover -s tests -v
& $python -c "from scripts.run_agent_test import verify_freezes; print(verify_freezes())"
& $python scripts/validate_benchmark.py --day6-root $day6
& $python scripts/check_submission.py
# Nếu container Day 6 hiện có đang dừng:
docker --context desktop-linux start day6_student_starter-postgres-1
& $python scripts/audit_day6.py --day6-root $day6 --output artifacts/day6_audit_recheck.json
& $python -m src.day6_adapter --day6-root $day6 --output data/local/day6
```

Không có model API call trong các bước kiểm tra trên. Audit DB chỉ đọc, kiểm tra vector/snapshot/self-query. Unit tests có mock chỉ kiểm tra code, không phải điểm agent. Adapter chỉ export 15 câu Day 6; **benchmark Day 7 chính thức ở `benchmarks/`: 17 dev + 7 test**. Không chạy lại `--freeze` hoặc `select_pipeline.py` để thay pipeline đã chốt.

## Chạy API thật

Chỉ chạy khi được phép gửi câu hỏi/context tới OpenAI; có phát sinh phí. Chọn output mới, không ghi đè run đã công bố.

```powershell
# Retrieval-only dev
& $python scripts/benchmark_retrieval_dev.py --day6-root $day6 --output results/retrieval_dev_reproduction
# Agent dev: Dense/BM25/Hybrid
& $python scripts/run_agent_dev.py --day6-root $day6 --output results/agent_dev_reproduction
# Hai cấu hình thử cải thiện
& $python scripts/run_agent_dev.py --day6-root $day6 --output results/agent_wide_reproduction --methods dense --top-k 6 --budget 7000
& $python scripts/run_agent_dev.py --day6-root $day6 --output results/agent_quotes_reproduction --methods dense --top-k 6 --budget 7000 --require-quotes
# Test: chỉ Dense baseline và BM25 đúng cấu hình đã chốt, đủ 7 câu
& $python scripts/run_agent_test.py --day6-root $day6 --output results/agent_test_reproduction
```

Pipeline chọn: BM25 k3, budget 4000 ký tự gồm ID/nguồn/trang, tối đa 2 search, model/prompt gốc, không quote guard. Lần đầu dùng query gốc; model quyết định query tìm tiếp. Context tích lũy ưu tiên thứ tự tìm, dedup ID, giữ cả chunk nếu vừa budget. Model xuất claim/citation, renderer gắn `[chunk-id]`; ID hợp lệ chưa chứng minh semantic support.

Test runner không có tùy chọn đổi model/top-k/prompt hoặc chọn câu, không load gold, kiểm tra hash trước/sau. Run công bố là `results/agent_test_v1`, không chọn run tốt nhất. Tái chạy có thể khác dù temperature 0; không chỉnh pipeline theo test. Nếu nghiên cứu tiếp, công bố việc đã xem test và dùng test mới phù hợp.

Các receipt hash byte gốc; `.gitattributes` tắt chuyển đổi newline tự động để clone trên Windows/Linux vẫn khớp LF/CRLF đã ghi nhận. Không format/renormalize file đã chốt hoặc chạy formatter trên toàn repo rồi sửa hash theo.

## Tổng hợp nhãn và đọc hồ sơ

```powershell
$reviewCopy = 'data/local/regrade_check' # Chọn tên mới nếu thư mục này đã có.
New-Item -ItemType Directory -Path $reviewCopy -ErrorAction Stop | Out-Null
foreach ($run in @('agent_dev_v1', 'agent_dev_dense_wide', 'agent_dev_dense_wide_quotes', 'agent_test_v1')) {
    Copy-Item -Path "results/$run" -Destination "$reviewCopy/$run" -Recurse
}
& $python scripts/grade_dev.py --run "$reviewCopy/agent_dev_v1"
& $python scripts/grade_dev.py --run "$reviewCopy/agent_dev_dense_wide"
& $python scripts/grade_dev.py --run "$reviewCopy/agent_dev_dense_wide_quotes"
& $python scripts/grade_test.py --run "$reviewCopy/agent_test_v1"
& $python scripts/estimate_costs.py
```

Grader ghi file summary nên ví dụ trên chạy trên **bản sao**, giữ nguyên byte/receipt của kết quả công bố, kể cả khi hệ điều hành viết newline khác. Grader chỉ tổng hợp `reviews.json` đã đọc/chấm, không tự suy grounding từ ID. Với trace mới, cần đọc/chấm lại và tạo nhãn gắn hash mới; không copy nhãn cũ. `grade_test.py --prepare` tạo phiếu trống và có thể ghi đè phiếu cùng tên; không dùng trên hồ sơ đã hoàn tất nếu cần giữ receipt. Giá ước tính bổ sung ở `artifacts/cost_estimate.json`, không phải hóa đơn; summary gốc có `cost_usd=null` được giữ nguyên.

| Đường dẫn | Nội dung |
|---|---|
| `src/`, `scripts/`, `tests/` | Agent/model/retrieval, runner/validator/grader/handoff, kiểm thử |
| `benchmarks/`, `configs/` | Input tách gold, benchmark freeze, giả thuyết, pipeline freeze |
| `results/agent_dev_v1/` | Ba cấu hình dev gốc và nhãn đầy đủ |
| `results/agent_dev_dense_wide/`, `results/agent_dev_dense_wide_quotes/` | Hai cải thiện và kết quả không thắng |
| `results/agent_test_v1/` | 14 trace/nhãn, summary và receipt |
| `results/retrieval_dev_v3/` | Retrieval dev hoàn chỉnh |
| `artifacts/`, `report/individual/` | Audit/cost/checklist, báo cáo cá nhân |
| `data/local/` | Corpus/cache/gói riêng, Git ignore |

Trace và benchmark trích nội dung báo cáo đã được cho phép làm bằng chứng. Repo chưa tự động commit/push hoặc cấp quyền người chấm; xem checklist để hoàn tất nộp bài. Không dùng gói source-only cũ thay bộ nộp đầy đủ.
