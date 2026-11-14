# Phần nâng cao — tài liệu đa phương thức 297 trang

Đã triển khai và chạy đầy đủ quy trình riêng cho phần nâng cao. **Test đạt 23/30 = 76,666…%, chưa đạt ngưỡng 90% (27/30), vì vậy chưa đủ điều kiện 15 điểm bonus.** Không sửa pipeline hoặc chạy lại để chọn kết quả tốt hơn sau khi xem test.

## Tài liệu và phạm vi index

Tài liệu là **NASA Systems Engineering Handbook, NASA/SP-2016-6105 Rev 2 (2016), 297 trang PDF**, gồm văn bản, bảng, sơ đồ quy trình và biểu đồ định lượng. Đây là tài liệu khác với báo cáo 84 trang dùng cho phần cơ bản.

- [Trang giới thiệu NASA](https://www.nasa.gov/reference/systems-engineering-handbook/), [PDF gốc](https://www.nasa.gov/wp-content/uploads/2018/09/nasa_systems_engineering_handbook_0.pdf).
- SHA-256: `8eeb4887a4dc57a23049da7dd2ed556833cf98e214b240468d987873164ff688`.
- [Manifest nguồn/index](source.json): 297/297 trang, 810.640 ký tự text, không trang rỗng text, không lỗi dừng extraction. Có cảnh báo font/chữ xoay ở 44 trang; số liệu này không có nghĩa mọi ký tự/hình đã được đọc đúng.
- [Kiểm tra render](coverage_check.json): render được **297/297 trang**, không lỗi. Toàn bộ trang có ảnh gốc để tra cứu, kể cả ngoài benchmark. Không có allowlist chỉ index trang gold.
- Số trang citation là **trang vật lý PDF**; từ trang PDF 11, số trang in bằng số trang PDF trừ 10.

Index bằng pypdf layout text theo trang, lưu ID, source URL, số trang, text và liên kết ảnh render. BM25 tìm trên toàn bộ index, tăng ưu tiên theo figure/table/section được nêu trong query. Agent có thể xem ảnh trang gốc bằng vision để đọc ô bảng, đường nối và trục/chú giải. Không coi text extraction là nguồn đúng mặc định.

Index và PDF/PNG nằm trong `data/local/advanced/`, không đưa vào Git. Bộ nộp có URL, hash, code tải lại, manifest, evidence/locator và trace. [Hướng dẫn NASA](https://www.nasa.gov/nasa-brand-center/images-and-media/) cho phép nhiều cách sử dụng giáo dục/thông tin, đồng thời nêu ngoại lệ nội dung bên thứ ba. Figure 2.5-1 ghi nguồn chuyển thể INCOSE; giữ credit này và dẫn người chấm tới bản gốc thay vì phát hành lại toàn bộ PDF/ảnh. Không ngụ ý NASA xác nhận sản phẩm.

## Benchmark đã chốt trước thử nghiệm

[Freeze benchmark](benchmarks/freeze.json), [dev inputs](benchmarks/dev.inputs.json), [dev gold](benchmarks/dev.gold.json), [test inputs](benchmarks/test.inputs.json), [test gold](benchmarks/test.gold.json).

| Nhóm chính | Dev | Test |
|---|---:|---:|
| Bảng | 4 | 6 |
| Ảnh/sơ đồ | 4 | 5 |
| Biểu đồ | 2 | 5 |
| Multi-hop | 2 | 4 |
| Text | 3 | 4 |
| Thiếu bằng chứng | 3 | 6 |
| Tổng | 18 | 30 |

Mỗi câu chỉ có một nhóm chính. Gold có đáp án, trang, vùng tham khảo chuẩn hóa, tên bảng/hình/hàng/nhánh/đoạn và điều kiện/đơn vị. Câu thiếu bằng chứng có cách kiểm tra và [kết quả quét toàn corpus](benchmarks/absence_checks.json); không dùng riêng số hit bằng 0 để kết luận thiếu. Các câu dev/test hỏi những sự kiện khác nhau, không chỉ đổi cách diễn đạt cùng đáp án.

Runner chỉ đọc `id/question` từ inputs. Gold và vùng gold chỉ dùng khi xây/chấm benchmark, không gửi vào retrieval, agent hoặc bước kiểm tra câu trả lời. Tài liệu chỉ có hai biểu đồ định lượng chính được dùng trong nhóm chart test; năm câu hỏi đọc các thông tin khác nhau trên hai hình đó. Đây là giới hạn đa dạng trực quan của benchmark, không phải năm biểu đồ độc lập.

## Pipeline và thử nghiệm dev

[Pipeline](pipeline.py) có tool `search`, `view_pages`, `submit_answer`. Lượt tìm đầu dùng nguyên câu hỏi. Các lượt sau và ID trang cần xem do model chọn trong kết quả đã tìm. Citation cuối gồm `source_id`, locator hàng/nhánh/trục/đoạn và từ/nhãn nguồn giúp tìm lại vùng gốc. Không dùng tọa độ pixel do model đoán.

Cấu hình chọn: **GPT-4.1-2025-04-14**, BM25 top 7, tối đa 8 lượt tool, ảnh cạnh dài 2.000 pixel, temperature 0, không retry. Trước khi xuất, model kiểm tra lại draft với các trang đã xem. Đây là một bước của pipeline, không phải người chấm benchmark độc lập. Guard định lượng chuyển thành từ chối nếu câu hỏi yêu cầu một đại lượng chính xác nhưng câu trả lời chỉ là thảo luận định tính. Guard không chứng minh các số đã trả lời đều đúng và có thể từ chối nhầm số viết bằng chữ.

| Cấu hình/thay đổi trên dev | Đạt / 18 |
|---|---:|
| compact: mini, bbox, top 4, 4 tool | 3/18 |
| wide: mini, ràng buộc bbox/page, top 7, 6 tool | 5/18 |
| locator: mini, source ID + tên vùng, final qua tool | 14/18 |
| precise: GPT-4.1, ưu tiên section | 14/18 |
| checked: sửa heading hai cột, kiểm tra draft với nguồn | 16/18 |
| **guarded: thêm kiểm tra yêu cầu định lượng** | **17/18** |

Đã chấm đủ 108 kết quả dev, không bỏ lượt lỗi. [So sánh đầy đủ](dev_comparison.json) và [pipeline freeze](pipeline_freeze.json) ghi quyết định trước test. Các lượt compact/wide là lỗi tích hợp thực, không phải mock. Một số câu có text đúng nhưng bbox trỏ sai vùng nên không đạt. Locator giải quyết định dạng; model lớn, tìm đúng heading và kiểm tra nguồn tiếp tục cải thiện grounding. Câu dev còn sai là ADV-DEV-10: đúng hệ số nhưng thêm giai đoạn mà nhãn mũi tên không chứng minh.

## Kết quả test một lượt

[Kết quả tổng hợp](results/test_guarded/graded_summary.json), [nhãn/lý do từng câu và citation](results/test_guarded/reviews.json), [context checks](context_checks.json). Mỗi `ADV-TEST-xx.json` lưu câu hỏi, kết quả tìm, trang/ảnh đã xem và hash, tool call, draft/final, usage, thời gian và lỗi. Ảnh không nhúng base64 vào trace; có thể render lại từ PDF đúng hash.

| Nhóm | Đạt / Tổng |
|---|---:|
| Bảng | 5/6 |
| Ảnh/sơ đồ | 4/5 |
| Biểu đồ | 5/5 |
| Multi-hop | 2/4 |
| Text | 3/4 |
| Thiếu bằng chứng | 4/6 |
| **Toàn bộ** | **23/30 (76,666…%)** |

Chấm nhị phân nghiêm ngặt trên các khẳng định trả lời: đúng một phần không đạt; quote nguồn đúng không tự sửa điều kiện thiếu/sai trong claim. Từng citation được đối chiếu trang gốc, không chấm chỉ bằng ID hoặc LLM judge. Các trường hợp sát ranh giới được ghi rõ để người chấm kiểm tra lại.

| Câu không đạt | Nguyên nhân |
|---|---|
| 02 | Claim đổi phân tích dữ liệu **và** mẫu được trả về thành **hoặc**; quote đúng nhưng claim đổi phép nối. |
| 08 | Nhánh No quay về Stakeholder Expectations, không phải Logical Decomposition. |
| 19 | Chọn đúng từ Analysis nhưng cite trang validation 136, không chứng minh điều kiện không có prototype ở trang verification 103. |
| 20 | Claim tiếng Việt thiếu điều kiện **flight-proven** của TRL 9; quote nguồn có nhưng không bù thiếu trong claim. |
| 21 | Suy thêm Demonstration thường có điều kiện ít kiểm soát hơn; nguồn chỉ phát biểu rõ controlled conditions cho Test. |
| 27, 29 | JSONDecodeError, không có kết quả hợp lệ; vẫn tính không đạt, không xem như từ chối đúng. |

Có **2 lỗi hệ thống / 30**; không loại khỏi mẫu số, không retry. Median 8,65 giây/câu; tổng latency theo câu 351,55 giây, wall time khoảng 194,06 giây với 2 worker. Tổng 150 model call, 1.195.960 prompt token và 9.598 completion token cho test, bao gồm call sinh output không parse được.

[Ước tính chi phí](cost_estimate.json): test khoảng **2,345824 USD**, toàn bộ 6 dev + test khoảng **5,385675 USD**, theo usage và giá chuẩn công khai ngày 14/11/2026, chưa đối chiếu hóa đơn, không gồm compute/storage. Không gửi embedding cho phần nâng cao. Các rate được dẫn từ [GPT-4.1](https://developers.openai.com/api/docs/models/gpt-4.1) và [GPT-4.1 mini](https://developers.openai.com/api/docs/models/gpt-4.1-mini).

## Chạy lại

Không cần PostgreSQL cho phần nâng cao. Cần Python 3.11+ và `pdftoppm` trên PATH. Môi trường đã chạy: Python 3.12.14, pypdf 6.21.4, python-dotenv 1.2.4, Poppler 26.07.0. Cài vào venv mới để tránh thêm thư viện font làm thay đổi extraction đã chốt.

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r advanced/requirements.txt
$python = '.\.venv\Scripts\python.exe'
& $python -m advanced.ingest --download
& $python -m unittest advanced.test_contract advanced.test_agent -v
& $python -m advanced.check_coverage
```

Lệnh ingest xác minh source/index hash và giữ nguyên manifest đã chốt nếu rebuild khớp; không tự cập nhật freeze khi khác. Coverage replay được ghi vào `data/local/advanced/coverage_replay.json`. PDF/index/ảnh render không cần copy từ máy tác giả nếu tải lại đúng nguồn. Model có thể bị ngừng hỗ trợ về sau; khả năng truy cập và kết quả API khi chạy lại không được bảo đảm.

Đặt `OPENAI_API_KEY` trong môi trường hoặc file dotenv cục bộ bị Git ignore, không đặt giá trị key trong lệnh/README. Ví dụ file `.env` chỉ chứa `OPENAI_API_KEY=...` với key riêng của người chạy:

```powershell
& $python -m advanced.run --split dev --config guarded --env-file .env --output-root data/local/advanced/replay_01
& $python -m advanced.run --split test --env-file .env --output-root data/local/advanced/replay_01
```

Các lệnh này gọi API có phí, chỉ gửi câu hỏi và text/ảnh NASA được truy xuất, không gửi gold. Output replay nằm ngoài kết quả báo cáo, không ghi đè. Test chỉ dùng cấu hình đã freeze, không có override model/retrieval theo test. Replay phục vụ tái lập, không chọn lượt điểm cao hơn để thay lượt đã công bố. Đọc kết quả đã lưu/chấm lại offline không cần gọi API:

```powershell
& $python -m advanced.grade test_guarded
& $python -m advanced.check_submission
```

## Checklist và giới hạn

- [x] Một tài liệu thực tế ≥100 trang; nguồn/phiên bản/hash và cách truy cập.
- [x] Index toàn bộ 297 trang; lưu cảnh báo extraction và kiểm tra render toàn tài liệu.
- [x] Dev 15+3, test 24+6, đủ số câu của từng nhóm; inputs/gold tách và freeze trước thử nghiệm.
- [x] Thử/chấm các cấu hình trên dev rồi chốt trước test; không sửa theo test.
- [x] Chạy toàn bộ 30 test, đủ trace/answer/context/citation/usage/error, nhãn và lý do từng câu.
- [x] Code, cách tái lập, chi phí, lỗi và giới hạn được ghi nhận; credential không nằm trong hồ sơ.
- [ ] **Đạt ≥90% test: chưa đạt. Không tự nhận 15 điểm bonus.**

Các giới hạn còn lại: native text có lỗi font/chữ xoay; tìm kiếm lexical có thể bỏ sót hình ít nhãn; tên vùng do model tạo cần được kiểm chứng; vision và bước kiểm tra draft vẫn đọc sai quan hệ/điều kiện; guard định lượng bảo thủ; benchmark một tài liệu, nhóm chart chỉ từ hai biểu đồ; chưa đo độ biến thiên nhiều lần. Bước tiếp theo nếu tiếp tục cải thiện là dùng các lỗi này làm dữ liệu phát triển, chốt một benchmark test mới độc lập trước lượt đánh giá tiếp theo; không sửa pipeline rồi báo lại điểm trên test hiện tại.
