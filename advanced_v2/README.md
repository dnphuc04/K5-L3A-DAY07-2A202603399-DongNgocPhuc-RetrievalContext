# Báo cáo bổ sung phần nâng cao — vòng 2

**Đồng Ngọc Phúc · Mã học viên 2A202603399 · K5-L3A.**

**Kết quả test mới độc lập: 29/30 = 96,666…%, đạt ngưỡng ≥90% (cần ít nhất 27/30). Không lỗi hệ thống.** Test cũ vẫn là 23/30, không sửa trace, nhãn hoặc điểm cũ. [Metrics](results/test_reasoned/graded_summary.json), [nhãn từng câu/citation](results/test_reasoned/reviews.json), [phiếu đối chiếu đầy đủ](results/test_reasoned/review_packet.json).

## Tài liệu, nguồn và index

Tôi tiếp tục dùng **NASA Systems Engineering Handbook, NASA/SP-2016-6105 Rev 2 (2016), 297 trang PDF**; [PDF gốc NASA](https://www.nasa.gov/wp-content/uploads/2018/09/nasa_systems_engineering_handbook_0.pdf), SHA-256 `8eeb4887a4dc57a23049da7dd2ed556833cf98e214b240468d987873164ff688`.

Index toàn bộ **297/297 trang**, 810.640 ký tự text, không lỗi dừng extraction; cảnh báo font/chữ xoay ở 44 trang vẫn được ghi nhận. Đã render toàn bộ 297 trang, không chỉ trang benchmark. Vòng hai tái sử dụng đúng index/source hash, thêm tìm heading và crop ảnh gốc, không thêm gold vào index. [Manifest](../advanced/source.json), [coverage](../advanced/coverage_check.json).

Citation dùng ID trang PDF vật lý, locator hàng/nhánh/trục/đoạn và nhãn nguồn. Từ PDF trang 11 trở đi, số trang in bằng số trang PDF trừ 10; phần đầu dùng số La Mã. PDF/PNG/crop chỉ giữ local. Bộ nộp có URL, hash và code tái tạo; giữ credit INCOSE ở Figure 2.5-1. [Quyền dùng nội dung NASA và ngoại lệ bên thứ ba](https://www.nasa.gov/nasa-brand-center/images-and-media/); không phát hành lại toàn bộ PDF/ảnh hoặc ngụ ý NASA xác nhận sản phẩm.

## Tách phát triển và đánh giá mới

Tôi chuyển 30 câu test cũ sang **dev vòng hai**, có ID mới và `previous_id` trong gold. Đây là dữ liệu đã biết kết quả, không còn là holdout. Baseline lịch sử trên các câu đó là 23/30; số liệu lịch sử được tham chiếu, không gọi lại API để thay kết quả.

**Test mới 30 câu được chốt trước mọi thử nghiệm vòng hai.** Câu mới hỏi các sự kiện khác với cả dev và test cũ: sáu bảng khác, các quan hệ sơ đồ khác, các encoding/giá trị chart chưa được hỏi, bốn cặp evidence mới và sáu chi tiết thiếu khác. Có trùng trang/hình, không chỉ đổi cách diễn đạt cùng đáp án. [Freeze](benchmarks/freeze.json), [đối chiếu độc lập từng câu](benchmarks/independence_review.json), [inputs](benchmarks/test.inputs.json), [gold/evidence](benchmarks/test.gold.json).

| Nhóm chính | Dev vòng 2 | Test mới |
|---|---:|---:|
| Bảng | 6 | 6 |
| Ảnh/sơ đồ | 5 | 5 |
| Biểu đồ | 5 | 5 |
| Multi-hop | 4 | 4 |
| Text | 4 | 4 |
| Thiếu evidence | 6 | 6 |
| Tổng | 30 | 30 |

Mỗi câu chỉ thuộc một nhóm chính. Gold ghi đáp án/điều kiện/đơn vị, trang, vùng tham khảo và locator; câu thiếu có kiểm tra toàn corpus và phần liên quan. Chỉ `id/question` đi vào runner. Gold không gửi vào search, agent hoặc verifier. Việc chấm diễn ra offline sau khi nhận câu trả lời, bằng đối chiếu trang gốc; không dùng LLM judge để tự gán điểm.

## Cải thiện và lựa chọn trên dev

[Phân tích phát triển](DEVELOPMENT.md), [policy chọn](selection_policy.json), [so sánh](dev_comparison.json), [pipeline freeze](pipeline_freeze.json).

| Cấu hình trên cùng 30 câu dev | Đạt | Lỗi hệ thống |
|---|---:|---:|
| Baseline lịch sử vòng 1, nay là dev | 23/30 | 2 |
| GPT-4.1 extractive, giữ điều kiện nguồn và có zoom/repair | 14/30 | 14 |
| **GPT-5.2 reasoning medium** | **29/30** | **0** |

Thay đổi tổng quát từ lỗi cũ: giữ tiếng Anh gần nguồn để tránh mất AND/OR và điều kiện; ưu tiên heading khớp nguyên cụm; truy theo đầu mũi tên; cho phép phóng vùng ảnh; kiểm tra lại draft với nguồn; cho một lượt sửa giao thức có lưu raw response, không retry HTTP. Không âm thầm chọn đối tượng JSON đầu tiên khi có những câu trả lời khác nhau.

GPT-4.1 thường gửi tọa độ pixel cho tool crop đòi tọa độ chuẩn hóa; lỗi vẫn tính không đạt, không bỏ lượt chạy kém. GPT-5.2 sửa được các lỗi nội dung/điều kiện cũ. Câu dev còn không đạt là 08: đích đường nối đúng nhưng citation nói có nhãn Yes được in, trong khi nhánh đó không in nhãn. Câu này vẫn bị chấm không đạt.

Cấu hình chọn: `gpt-5.2-2025-12-11`, reasoning `medium`, BM25 top 7 trên toàn corpus, tối đa 8 tool, ảnh full-page 2.000 pixel; crop từ ảnh trang ở mức cạnh dài 3.000 pixel. Tool `search/view_pages/view_region/submit_answer`; kiểm tra draft trên các trang đã xem. [Code](pipeline.py), [config](configs/reasoned.json). Không sửa predictor sau khi chạy test mới.

## Test mới: kết quả và lỗi còn lại

| Nhóm | Đạt / Tổng |
|---|---:|
| Bảng | 6/6 |
| Ảnh/sơ đồ | 4/5 |
| Biểu đồ | 5/5 |
| Multi-hop | 4/4 |
| Text | 4/4 |
| Thiếu evidence | 6/6 |
| **Toàn bộ** | **29/30 = 96,666…%** |

Đã đọc và ghi nhãn từng câu, từng citation, kèm lý do và hash trace. Chấm đúng và đủ phần được hỏi; paraphrase trung thành được chấp nhận, nhưng quote đúng không bù cho điều kiện thiếu trong claim. Lỗi hệ thống không loại khỏi mẫu số.

**ADV2-TEST-09 không đạt:** câu trả lời nêu đúng hai đích end user/Product Integration và trích nguyên annotation có “recursive loop”, nhưng chưa phân biệt rõ Product Integration là tuyến đệ quy. Đây là nhãn nghiêm ngặt về tính đầy đủ, không phải citation trỏ sai trang. Giữ nguyên lỗi này, không chỉnh pipeline sau test.

**ADV2-TEST-27 đạt theo hành vi từ chối:** status máy là `answered`, nhưng câu trả lời nói “None”/không có vendor bắt buộc, không đoán hãng; thông tin trích từ Preface và generic tool/database là đúng. Theo cùng cách chấm đã dùng trên dev, đánh giá hành vi theo nội dung, không chỉ enum. Vì vậy có **5 output `abstain` và 1 từ chối về nghĩa**, tổng 6/6 câu thiếu evidence được xử lý đúng.

[Context checks](context_checks.json) ghi đủ trang gold được tìm/xem cho **24/24 câu có đáp án**; đây chỉ là proxy coverage theo trang, không thay thế chấm semantic. Các file `results/test_reasoned/ADV2-TEST-xx.json` chứa retrieval/context, full-page/crop locator và hash, tool call, draft/final, usage, thời gian và lỗi. Ảnh có thể render lại từ PDF đúng hash; base64 và credential không được ghi vào trace.

Test có **0/30 lỗi hệ thống**, 162 model call, 15 lần zoom, 0 lần sửa JSON; median **19,03 giây/câu**, tổng latency theo câu **709,68 giây**, wall time **359,72 giây** với 2 worker. Usage: 1.685.685 prompt token, 30.755 completion token, trong đó 18.050 reasoning token đã nằm trong completion, không cộng hai lần.

[Ước tính chi phí](cost_estimate.json): test khoảng **3,035380 USD**; cả vòng hai gồm smoke, hai dev và test khoảng **8,306367 USD**, chưa đối chiếu hóa đơn, chưa gồm compute/storage. Bao gồm call trả output lỗi, không bỏ chi phí thử nghiệm thất bại. Rate dẫn từ [GPT-5.2](https://developers.openai.com/api/docs/models/gpt-5.2) và [GPT-4.1](https://developers.openai.com/api/docs/models/gpt-4.1), ngày 14/11/2026.

## Cách chạy và kiểm tra

Cần cả repository vì vòng hai tham chiếu các artifact lịch sử đã chốt. Python 3.11+, `pdftoppm` trên PATH; môi trường đã kiểm chứng là Python 3.12.14, pypdf 6.21.4, python-dotenv 1.2.4, Poppler 26.07.0. Không cần PostgreSQL cho phần nâng cao.

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r advanced_v2/requirements.txt
$python = '.\.venv\Scripts\python.exe'
& $python -m advanced_v2.prepare --download
& $python -m unittest advanced_v2.test_contract -v
& $python -m advanced_v2.check_submission
```

`prepare` kiểm tra đúng PDF/index hash, không ghi lại manifest/freeze lịch sử. Với newline khác Windows, chỉ chấp nhận chuyển newline khi byte sau chuyển khớp đúng hash cũ; không tự cho phép extraction khác. Dùng venv mới không cài thêm fontTools để tái tạo đúng extraction đã chốt.

Đặt key riêng vào biến môi trường `OPENAI_API_KEY` hoặc dotenv local bị Git ignore. Không ghi key trên command line hoặc trong repo. Khi cần replay có phí:

```powershell
& $python -m advanced_v2.run --split dev --config reasoned --env-file .env --output-root data/local/advanced_v2/replay_01
& $python -m advanced_v2.run --split test --env-file .env --output-root data/local/advanced_v2/replay_01
```

Chỉ gửi câu hỏi và text/ảnh NASA đã tìm, không gửi gold hoặc PDF nguyên bản. Output replay không thay kết quả đã báo cáo. Test không nhận subset/config override; thư mục báo cáo không được ghi đè. Không chọn lượt replay điểm cao hơn để thay lượt test. Provider có thể cho kết quả khác dù dùng snapshot; truy cập model tương lai không được bảo đảm.

Đọc phiếu/kết quả và kiểm tra hash không cần gọi API. Có thể chấm lại nhãn đã ghi bằng `python -m advanced_v2.grade test_reasoned`; không phải chạy benchmark lại. Kết quả kiểm tra cuối nằm ở [submission_check](submission_check.json), [receipt](evaluation_receipt.json) ghi hash hồ sơ đã hoàn thiện. [Rà soát absence bổ sung](absence_review.json) ghi các trang liên quan đã đọc; hit keyword không tự chứng minh thiếu evidence.

## Checklist nộp và giới hạn

- [x] Một tài liệu thực tế 297 trang, có text/bảng/sơ đồ/chart, nguồn và quyền/cách truy cập.
- [x] Index toàn bộ tài liệu; giữ cảnh báo, page ID, ảnh/region và kiểm tra render toàn bộ trang.
- [x] Dev ≥15+3; test mới 24+6 và đủ các nhóm, tách inputs/gold, chốt trước thử nghiệm.
- [x] Thử/chấm đủ cấu hình dev, chọn/freeze trước test; code dùng test khớp dev đã chọn.
- [x] Chạy toàn bộ 30 test một lượt, giữ trace/time/cost/error và nhãn/lý do từng câu/citation.
- [x] **29/30 ≥90%, không làm tròn để qua ngưỡng.**
- [x] Hồ sơ test cũ giữ nguyên byte, vẫn 23/30; không đổi test cũ thành điểm holdout mới.
- [x] Code, hướng dẫn, dữ liệu đánh giá, evidence và báo cáo đầy đủ; credential không thuộc hồ sơ.

Giới hạn: một tài liệu; nhóm chart lấy từ hai biểu đồ, chưa kiểm chứng nhiều tài liệu hoặc độ biến thiên nhiều lần; cảnh báo native extraction vẫn tồn tại; vision có thể đọc sai nhãn/quan hệ; thời gian và chi phí tăng; không có người chấm bên ngoài xác nhận nhãn này. Kết quả cũ 23/30 và mới 29/30 thuộc hai bộ test khác nhau, không phải ước lượng cải thiện trực tiếp trên cùng holdout. So sánh trực tiếp chỉ hợp lệ trên dev cùng câu hỏi. Điểm rubric cuối cùng thuộc người chấm; hồ sơ này chứng minh ngưỡng và các yêu cầu kỹ thuật đã thực hiện.
