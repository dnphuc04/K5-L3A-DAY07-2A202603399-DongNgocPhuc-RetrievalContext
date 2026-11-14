# Chấm dev, thử cải thiện và chốt pipeline

Ngày: 2026-11-14. Phạm vi: dev 17 câu, không đánh giá test.

## Phương pháp chấm

Đã đọc từng câu trả lời của cả 5 cấu hình: **85 kết quả**, bao gồm câu trả lời, mọi nguồn được cite và hành vi từ chối. Có 80 đơn vị citation (mỗi ID nguồn phân biệt trong một câu trả lời tính một lần; nếu ID gắn nhiều claim thì đọc tất cả claim đó). Nguồn nguyên văn được đối chiếu lại với PDF đúng trang; kiểm tra khớp văn bản không thay thế việc đọc xem nguồn hỗ trợ claim.

Nhãn nằm trong `reviews.json` của từng run, có lý do từng câu và từng citation, hash gắn với trace. Mỗi nhãn dựa trên đối chiếu trực tiếp câu trả lời và citation với tài liệu gốc. `scripts/grade_dev.py` chỉ tổng hợp nhãn đã ghi, không suy nhãn từ ID hay gold matching.

Quy tắc giữ nhất quán: sai citation hỗ trợ điều kiện chính chấm grounded 0 dù nội dung đúng; thiếu một điều kiện quan trọng chấm 1; đúng và đủ evidence/citation chấm 2. Câu có đáp án bị từ chối chấm 0. q11 hỏi các loại dữ liệu không được gửi AI: đủ cả bốn loại được chấm đầy đủ; lời khuyên dùng dữ liệu giả là ngữ cảnh bổ sung, không phải loại dữ liệu đang được hỏi. Multi-citation được chấp nhận khi các nguồn hỗ trợ các phần tương ứng của cùng claim, có lý do cho từng nguồn.

## So sánh đầy đủ

Tất cả dùng cùng corpus C 65 chunk/33 trang, model `gpt-4.1-mini-2025-04-14`, câu hỏi/filter/gold dev và thứ tự tiêu chí đã chốt. Không lỗi hệ thống trong các run so sánh.

| Cấu hình | Grade 0/1/2 | Grounded /30; mean /2 | Hit@1 | Hit@3 | Context đủ evidence | Citation hỗ trợ | Từ chối đúng | Từ chối nhầm |
|---|---|---|---|---|---|---|---|---|
| Dense baseline, k3/4000 ký tự | 1/1/13 | 27/30; 1.800 | 10/15 (66.7%) | 14/15 (93.3%) | 14/15 (93.3%) | 15/16 (93.75%) | 2/2 (100%) | 0/15 |
| BM25, k3/4000 | 0/0/15 | 30/30; 2.000 | 15/15 (100%) | 15/15 (100%) | 15/15 (100%) | 16/16 (100%) | 2/2 (100%) | 0/15 |
| Hybrid RRF, k3/4000 | 0/0/15 | 30/30; 2.000 | 13/15 (86.7%) | 15/15 (100%) | 15/15 (100%) | 16/16 (100%) | 2/2 (100%) | 0/15 |
| Cải thiện 1: Dense k6/7000 | 2/0/13 | 26/30; 1.733 | 10/15 (66.7%) | 14/15 (93.3%) | 15/15 (100%) | 16/18 (88.89%) | 2/2 (100%) | 0/15 |
| Cải thiện 2: Dense k6/7000 + quote guard | 2/1/12 | 25/30; 1.667 | 10/15 (66.7%) | 14/15 (93.3%) | 15/15 (100%) | 14/14 (100%) | 2/2 (100%) | 2/15 (13.33%) |

Hit@1/3 luôn lấy cùng cutoff từ **lần tìm đầu với query gốc**, kể cả k6; context được chấm trên context cuối sau tất cả lượt tìm. Mẫu số retrieval/context là 15 câu có đáp án, không gồm 2 câu thiếu bằng chứng. Context grade baseline: 14 câu mức 2, 1 câu mức 1; bốn cấu hình còn lại: 15 câu mức 2. Lỗi, nếu có, phải báo riêng và không được coi là từ chối đúng.

Mỗi cấu hình đều gọi retrieval ở 17/17 câu thành công. Citation coverage trên câu đã trả lời: 15/15 ở bốn cấu hình đầu, 13/13 ở quote guard. Coverage cao hoặc citation validity cao không bù được từ chối nhầm và thiếu nội dung.

| Cấu hình | Model calls | Lượt search: 1 / 2 | Median end-to-end | Chat input / output tokens | Embedding mới: requests / tokens |
|---|---|---|---|---|---|
| Dense baseline | 36 | 15 / 2 | 3069.81 ms | 38,304 / 2,552 | 2 / 30 |
| BM25 | 35 | 16 / 1 | 2762.79 ms | 37,679 / 2,470 | 0 / 0 |
| Hybrid | 35 | 16 / 1 | 2926.89 ms | 37,098 / 2,517 | 1 / 29 |
| Dense wide | 36 | 15 / 2 | 2845.76 ms | 57,253 / 2,520 | 2 / 37 |
| Dense wide + quotes | 36 | 15 / 2 | 3663.61 ms | 62,676 / 4,815 | 1 / 13 |

Tiền API chưa đối chiếu billing nên để null, không tuyên bố chi phí tiền thấp hơn. Latency đo một lần tuần tự, dùng cache query chung; khác biệt nhỏ không chứng minh ưu thế thống kê. Input token của wide tăng do context lớn hơn; quote mode tăng output. Các con số không bao gồm smoke run trước đó; usage từng smoke đã lưu riêng.

## Lỗi, giả thuyết và kết quả trước/sau

**q13: thiếu quy tắc khi bằng điểm.** Baseline lấy caption ngắn ở rank 1 và thiếu đoạn rule (rank 6) trong context: trả chung chung, grade 1. Wide k6 đưa đủ rule vào context: nội dung trả lời đầy đủ nhưng cite caption không chứa quy tắc năm học/học kỳ, grade 0. Quote mode chọn đúng rule ở trang 56, grade 2. Giả thuyết tăng candidate depth được xác nhận ở context; giả thuyết chỉ tăng context sẽ tự sửa grounding bị bác bỏ.

**q08: citation JWT sai đoạn.** Baseline và wide trả đúng Authorization/Bearer nhưng cite định nghĩa JWT ở trang 26, grade 0. Quote mode vẫn gán đoạn header của trang 27 cho ID trang 26; quote guard chặn lại và gây từ chối nhầm, grade vẫn 0. Guard giảm xuất citation sai nhưng chưa sửa khả năng chọn nguồn; không được báo là cải thiện câu trả lời. BM25/Hybrid đã cite đúng đoạn trang 27 và đạt grade 2.

**q05: lỗi mới do quote guard.** Model ghép câu Repository của trang 22 vào quote gắn chunk trang 23; guard kiểm tra đúng và từ chối. Context có đầy đủ đáp án, nên đây là false abstention, grade 0. Cần cơ chế sửa nguồn/quote hoặc thử lại có giới hạn trong công việc tương lai; chưa thêm rồi chọn lại sau khi freeze.

**q09: quote không thay thế nội dung trả lời.** Quote mode trích đoạn đầy đủ nhưng câu trả lời chỉ nêu BigDecimal/HALF_UP/2/4 chữ số, bỏ cách dùng tổng điểm trọng số trực tiếp và tránh nhân ngược CPA đã làm tròn. Chấm 1; nguồn cho các ý thực sự được nói vẫn hợp lệ.

Các giả thuyết được ghi ở `configs/dev_experiments.json` trước khi chạy thử. Quote mode là cấu hình kết hợp prompt/schema/guard và tăng giới hạn output từ 1200 lên 2000 để chứa quote; không quy toàn bộ khác biệt cho riêng prompt. Không thay corpus, gold hoặc filter theo đáp án.

## Pipeline được chọn

**Chọn BM25 k3, budget 4000 ký tự, tối đa 2 lượt search, model/prompt gốc, không quote guard.** Theo policy đã đóng băng: BM25 và Hybrid bằng nhau về mean grounded, Context Evidence Rate, citation validity, abstention và Hit@3; BM25 thắng ở median thời gian của lần đo. Hybrid có ít chat token hơn một chút, nhưng tiền API chưa xác minh và cost nằm sau latency trong policy. Hai thử nghiệm Dense mới không thắng về chất lượng, nên không được chọn chỉ vì mới hơn.

Đây là lựa chọn trên dev nhỏ, một tài liệu, câu hỏi nhiều từ gần nội dung gốc; chưa chứng minh BM25 tốt nhất trên dữ liệu khác. Điểm hoàn hảo dev có nguy cơ lạc quan do nhãn/câu hỏi đều có AI hỗ trợ. Test giữ nguyên và chưa chạy.

File chính thức: `configs/selected_pipeline.json`; baseline đối chiếu test sau này là Dense k3/4000 với cùng model/prompt. `configs/pipeline_freeze.json` lưu timestamp và SHA-256 cấu hình, code, trace, nhãn, bảng so sánh và benchmark freeze. `scripts/select_pipeline.py` từ chối ghi đè pipeline đã chốt. Không tuning tiếp bằng test; nếu cần đổi pipeline sau này phải ghi một quyết định/version mới và xử lý độc lập test tương ứng.

## Hồ sơ và tái lập

- Ba cấu hình ban đầu: `results/agent_dev_v1/{traces,reviews,graded_summary,context_checks,summary}.json`.
- Hai cấu hình mới: cùng tên file trong `results/agent_dev_dense_wide/` và `results/agent_dev_dense_wide_quotes/`.
- Bảng máy đọc được: `results/dev_comparison.json`; nguồn PDF của từng citation đã kiểm tra trong `cited_source_checks.json` ở mỗi run.
- Tổng hợp lại nhãn bằng `scripts/grade_dev.py --run <run-directory>`; kiểm tra context bằng `scripts/inspect_agent_dev.py --run <run-directory>`. Những script này chỉ đánh giá offline, không gọi model.
- Runner dev hỗ trợ `--top-k 6 --budget 7000`, thêm `--require-quotes` cho thử nghiệm 2; không cung cấp CLI test. Lệnh tái lập cần thư mục output mới và không tự ghi đè kết quả cũ.
