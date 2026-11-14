# Đánh giá test - Dense baseline và BM25 đã chốt

Ngày chạy/chấm: 2026-11-14. Run chính thức: `results/agent_test_v1`.

## Tính độc lập và cấu hình

Pipeline được chọn bằng dev và chốt trước khi chạy test: `configs/selected_pipeline.json`, `configs/pipeline_freeze.json`. Runner test xác minh toàn bộ hash code, cấu hình, bằng chứng lựa chọn và benchmark cả trước/sau chạy; đều khớp. Không chỉnh prompt, retrieval, context hoặc ngưỡng theo test, không chọn lại pipeline, không chạy nhiều lần rồi chọn kết quả tốt nhất.

Chạy đủ 7 câu test với hai cấu hình cố định: Dense baseline và BM25 được chọn. Cùng corpus C 65 chunk/33 trang, model `gpt-4.1-mini-2025-04-14`, top-k 3, budget 4000 ký tự, tối đa 2 lượt search, schema claim/citation gốc, không quote guard. Query đầu là câu hỏi gốc; query tìm tiếp do model chọn và được lưu. Không đưa gold, đáp án hay ghi chú evidence vào agent/retriever. Mọi file test/gold giữ nguyên hash.

## Bảng kết quả

| Chỉ số | Dense baseline | BM25 đã chốt |
|---|---|---|
| Chạy thành công / thử | 7/7 (100%) | 7/7 (100%) |
| Hit@1, query gốc | 4/5 (80%) | 5/5 (100%) |
| Evidence Hit@3, query gốc | 5/5 (100%) | 5/5 (100%) |
| Context Evidence Rate strict/reviewed | 5/5 (100%) | 5/5 (100%) |
| Context grade 0 / 1 / 2 | 0 / 0 / 5 | 0 / 0 / 5 |
| Grounded answer grade 0 / 1 / 2 | 0 / 0 / 5 | 0 / 0 / 5 |
| Điểm grounded | 10/10; mean 2.0/2 | 10/10; mean 2.0/2 |
| Citation trong context và hỗ trợ claim | 5/5 (100%) | 5/5 (100%) |
| Câu trả lời có citation | 5/5 (100%) | 5/5 (100%) |
| Từ chối đúng câu thiếu evidence | 2/2 (100%) | 2/2 (100%) |
| Từ chối nhầm câu có đáp án | 0/5 (0%) | 0/5 (0%) |
| Tool use / câu thành công | 7/7 (100%) | 7/7 (100%) |
| Lỗi hệ thống | 0 | 0 |
| Search 1 lượt / 2 lượt | 5 / 2 | 5 / 2 |
| Model calls | 16 | 16 |
| Median end-to-end | 3884.70 ms | 2657.85 ms |
| Chat input / output tokens | 18,230 / 779 | 18,850 / 823 |
| Embedding mới: request / prompt tokens | 9 / 423 | 0 / 0 |

Citation tính theo ID nguồn phân biệt trong một câu trả lời, như phần dev; nếu cùng ID gắn nhiều claim thì đọc đầy đủ tất cả claim đó. Hai câu thiếu evidence không nằm trong mẫu số retrieval/context/grounded answer. Câu không có citation do từ chối không được cộng vào citation validity; không che giấu từ chối nhầm bằng tỷ lệ coverage.

## Chấm từng câu

Đã đọc cả câu trả lời, context cuối, từng citation và nguồn gốc cho **cả hai cấu hình**. Các nhãn dưới đây dựa trên đối chiếu câu trả lời, context và citation với tài liệu gốc. File `reviews.json` ghi riêng từng cấu hình/query, lý do context, lý do từng citation và hash trace; `review_packet.json` chứa đủ answer/context/gold/nguồn/nhãn để kiểm tra lại.

| Query ID | Nội dung cần có | Nguồn | Dense: answer/context | BM25: answer/context | Kết luận citation/hành vi |
|---|---|---|---|---|---|
| d7-test-a01 | Content-Type: application/json | PDF trang 18 | 2 / 2 | 2 / 2 | Đúng tên/giá trị header; cite đúng đoạn JSON |
| d7-test-a02 | Không cấp mọi quyền sau đăng nhập; authentication kiểm tra danh tính, authorization kiểm tra quyền | Trang 25 | 2 / 2 | 2 / 2 | Đủ cả ba ý, mọi claim có nguồn hỗ trợ |
| d7-test-a03 | Long cho khóa; BigDecimal cho điểm/tín chỉ; enum chuỗi | Trang 49 | 2 / 2 | 2 / 2 | Đủ các nhóm kiểu dữ liệu, đúng đoạn thiết kế Entity |
| d7-test-a04 | PUT /api/me/timetables/{id}/name | Bảng 2.5-1, trang 52 | 2 / 2 | 2 / 2 | Đúng phương thức và đường dẫn cùng hàng đổi tên phương án |
| d7-test-a05 | Prompt chi tiết không tự cấp công cụ/quyền đọc file | Trang 33 | 2 / 2 | 2 / 2 | Câu phủ định và hai điều kiện có evidence; Dense lấy nguồn đúng ở rank 2, BM25 rank 1 |
| d7-test-u01 | Không suy đoán giới hạn MB của Excel | Không có fact trong corpus đã index | Không áp dụng | Không áp dụng | Cả hai tìm 2 lượt rồi từ chối, không đoán mặc định Spring Boot |
| d7-test-u02 | Không suy đoán số người dùng đồng thời đã đo | Không có fact trong corpus đã index | Không áp dụng | Không áp dụng | Cả hai tìm 2 lượt rồi từ chối, không suy từ kiểm thử chức năng |

Năm nguồn citation phân biệt được kiểm tra lại bằng PDF gốc đúng trang và khớp nội dung chunk (`cited_source_checks.json`). Đối với bảng endpoint, đã đối chiếu quan hệ hàng/cột khi kiểm tra gold bằng trang PDF; citation chunk giữ bảng và trang gốc. Câu thiếu evidence dựa trên rà soát toàn bộ corpus 33 trang đã chốt, không dựa riêng vào việc top-k không tìm thấy. Thông báo cuối của cả hai là: “Không đủ bằng chứng trong dữ liệu truy xuất để trả lời câu hỏi này.”

## Diễn giải và giới hạn

Trong run này không có lỗi câu trả lời/citation trên test; không tạo lỗi giả để phân tích. Chênh lệch retrieval duy nhất là câu a05: Dense top-1 chưa chứa câu kết luận về prompt/công cụ/quyền, nhưng đoạn đúng nằm ở rank 2 nên context/câu trả lời vẫn đầy đủ. Các lỗi dev và hai thí nghiệm không cải thiện vẫn giữ trong `docs/DEV_SELECTION.md`.

BM25 và Dense ngang nhau về chất lượng trả lời của bộ test nhỏ này. Median BM25 thấp hơn trong run hiện tại, nhưng Dense phải gọi embedding mới cho 7 câu gốc và 2 query tìm tiếp; không coi đây là so sánh cold-cache/cost tuyệt đối hoặc bằng chứng thống kê. BM25 có nhiều chat tokens hơn một chút trong test. Tổng run: 32 model calls, 38,682 chat tokens và 423 embedding prompt tokens; tiền API chưa đối chiếu billing nên `cost_usd=null`.

Test chỉ có 5 câu có đáp án và 2 câu thiếu evidence từ một báo cáo; nhiều câu gần từ ngữ tài liệu. Điểm đầy đủ không chứng minh tổng quát hóa, độ an toàn với prompt injection, hoặc khả năng xử lý tài liệu khác. Benchmark/tác vụ và nhãn có AI hỗ trợ, không phải blind independent evaluation. Đây là phần cơ bản; không dùng kết quả này để yêu cầu bonus nâng cao.

## Hồ sơ và tái lập

- `config.json`: cấu hình test, hash runner/input, freeze verification trước chạy.
- `traces.json`: toàn bộ 14 trace, request model không có key/header, tool args/query/results/context, answer/citation, thời gian, usage và lỗi.
- `summary.json`: vận hành và freeze verification sau chạy.
- `reviews.json`, `review_packet.json`: nhãn từng câu/citation có lý do, không gửi vào model.
- `graded_summary.json`: tổng hợp nhãn và retrieval/context metrics.
- `cited_source_checks.json`: đối chiếu nguồn với PDF.
- `evaluation_receipt.json`: hash hồ sơ đánh giá, code runner/grader và freeze tham chiếu.

Từ root Day 7, dùng venv Day 6 hoặc Python có `requirements.txt`:

```powershell
& '..\K5-L3A-DAY06-DongNgocPhuc-2A202603399-DataIngestionEngineering\starter\.venv\Scripts\python.exe' scripts/run_agent_test.py --day6-root '..\K5-L3A-DAY06-DongNgocPhuc-2A202603399-DataIngestionEngineering' --output results/agent_test_reproduction
```

Runner bắt buộc cấu hình đã chốt, toàn bộ test và thư mục output mới. Tái chạy có thể khác do provider dù temperature 0; giữ kết quả run đầu và không chọn lại pipeline theo điểm test. Lệnh này gọi API thật và chỉ dùng trong phạm vi dữ liệu đã được cho phép. Không commit secret hoặc công bố PDF/trace khi chưa xác minh quyền chia sẻ.
