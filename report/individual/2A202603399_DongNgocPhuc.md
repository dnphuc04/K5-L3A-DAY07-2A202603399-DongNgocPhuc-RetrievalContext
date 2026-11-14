# Báo cáo cá nhân Day 7 — Agentic RAG

**Họ tên:** Đồng Ngọc Phúc · **Mã học viên:** 2A202603399 · **Lớp:** K5-L3A.  
**Ngày tổng hợp:** 14/11/2026 · **Phạm vi:** phần cơ bản, không yêu cầu bonus nâng cao.

## 1. Mục tiêu và kết quả

Xây agent gọi retrieval thật trên vector store Day 6, trả lời có nguồn và nhận biết thiếu evidence. Đã so sánh Dense/BM25/Hybrid trên cùng corpus, thử thêm hai cấu hình, chấm 85 kết quả dev rồi chốt BM25 trước test. Dense baseline và BM25 được chạy một lần báo cáo trên cùng 7 câu test; mỗi cấu hình trả lời đủ 5 câu có đáp án, từ chối đúng 2 câu thiếu bằng chứng, không lỗi hệ thống. Code/config/benchmark trước và sau test giữ nguyên hash.

Nhãn được ghi sau khi đối chiếu từng câu trả lời, context và citation với nguồn gốc. Điểm đầy đủ trên test nhỏ này không chứng minh hệ thống đúng với mọi tài liệu. Bằng chứng chi tiết và các hạn chế được giữ thay vì suy điểm từ mock hoặc citation ID.

## 2. Dữ liệu, embedding và benchmark

### Dữ liệu Day 6

- Tài liệu gốc: “Báo cáo thực tập doanh nghiệp - Đồng Ngọc Phúc”, PDF 84 trang; SHA-256 `052352bcb0abf94da5a523bba2710b143df11f89bc1a5801f6810e26df7e48a8`.
- Corpus đã chọn: 33 trang vật lý, 65 chunk C, paragraph tối đa 1000 ký tự. Mỗi chunk giữ ID, document/source, trang và metadata chapter/start/end. Tập trang khớp allowlist; không OCR nội dung ảnh hoặc index mọi trang PDF.
- Nguồn do người dùng cung cấp cho lab; ngày 14/11/2026 người dùng đã cho phép nộp đầy đủ bằng chứng, ghi tại `submission_permission.json`. PDF/vector/cache có trong `data/submission/day6_handoff.zip`, không có credential. Cách truy cập và restore ở [DATA_ACCESS](../../docs/DATA_ACCESS.md); vẫn cần người chấm nhận được bộ nộp/quyền repo.
- Vector store PostgreSQL 16 + pgvector, bảng `lab_chunks`, strategy C, cosine **exact search**. Có 65 dòng khớp snapshot; vector hữu hạn/khác zero, cùng 1536 chiều; self-query score 1.0. [Audit](../../artifacts/day6_audit.json).
- Embedding `text-embedding-3-small`, 1536 chiều, không prefix query/document; giữ index Day 6, không tạo document embedding mới để làm đẹp điểm. API không trả commit revision embedding; ghi đúng model ID/thông số thay vì tự bịa revision. Adapter gốc được giữ nguyên trong gói dữ liệu.
- Agent model snapshot `gpt-4.1-mini-2025-04-14`, temperature 0, Chat Completions tool calling + structured output. Model trả lỗi thật nếu key/model không truy cập được; không fallback giả.

### Benchmark và cách chấm

| Split | Có đáp án | Thiếu bằng chứng | Tổng |
|---|---|---|---|
| Dev | 15 | 2 | 17 |
| Test mới | 5 | 2 | 7 |
| Tổng | 20 | 4 | 24 |

15 câu có đáp án dev dùng lại từ Day 6; thêm hai câu hỏi cấu hình BCrypt/JWT không có con số trong corpus. Test Day 7 được tạo mới, khác nội dung cần trả lời của dev/test Day 6, trước triển khai retrieval Day 7. Có giao thoa chủ đề/trang vì cùng tài liệu; người tạo câu hỏi có đọc corpus và test cũ, nên không tuyên bố test do tác giả độc lập tạo hoặc blind với người viết benchmark.

[Input dev](../../benchmarks/dev.inputs.json) và [input test](../../benchmarks/test.inputs.json) chỉ có ID, câu hỏi và filter nếu có. Gold/expected answer/absence reason nằm trong file riêng, không được đưa vào model, query rewrite, filter hoặc context selection. Filter chapter lấy từ phạm vi được nêu trong câu hỏi (q01/q09 dev), không lấy từ gold. Query đầu là nguyên câu hỏi; query tìm tiếp ghi riêng trong trace.

Gold có nguồn, trang và đoạn evidence; mỗi câu hiện cần một đoạn đầy đủ trong một chunk. Gold alternatives có nghĩa OR, không phải multi-hop. Đối chiếu evidence với PDF gốc và snapshot; chuẩn hóa NFC/khoảng trắng cho phép kiểm tra strict. Citation đúng ID nhưng không hỗ trợ claim vẫn sai. Câu thiếu evidence được rà soát trên toàn bộ 33 trang index và ghi absence reason; không kết luận thiếu thông tin từ top-k rỗng hay suy giá trị mặc định thư viện.

Hit@1/3 = số câu có evidence hợp lệ trong top-1/3 của lần tìm đầu bằng query gốc / số câu có đáp án. Context Evidence Rate = số câu có đủ evidence và nguồn trong context cuối / số câu có đáp án. Context chấm 0 thiếu evidence, 1 có nhưng thiếu điều kiện/nguồn, 2 đủ. Grounded answer chấm 0 sai/không có evidence hỗ trợ hoặc từ chối nhầm, 1 đúng một phần, 2 đúng/đủ. Mọi citation được đọc để chấm hỗ trợ; một ID nguồn phân biệt trong một câu trả lời tính một đơn vị, đọc tất cả claim dùng ID đó. Hai câu thiếu evidence không nằm trong mẫu số retrieval/context/grounded.

Chi tiết policy, giới hạn và hash ở [benchmark README](../../benchmarks/README.md), [benchmark freeze](../../benchmarks/freeze.json).

## 3. Kiến trúc agent và retrieval

Luồng: câu hỏi → model gọi tool `search` → retriever cấu hình sẵn → context có nguồn → model tìm tiếp hoặc xuất claim/citation/từ chối. Một tool được dùng với ba backend để so sánh công bằng, không yêu cầu số tool cố định.

| Phương pháp | Thiết kế |
|---|---|
| Dense | Query embedding tương thích Day 6 → pgvector cosine exact trên C; filter chapter cố định theo input |
| BM25 | k1=1.5, b=0.75; IDF/độ dài trên cùng 65 chunk; NFC/casefold/Unicode word tokens, tiếng Việt tách theo âm tiết, không bỏ stopword; query terms duy nhất |
| Hybrid RRF | Dense/BM25 mỗi bên tối đa 20 candidate; hợp nhất `1/(60+rank)` trọng số bằng nhau; không cộng trực tiếp score khác thang đo |

Ranking hòa được phân xử theo ID; BM25 chỉ trả score dương. Kết quả giữ ID/text/source/page/metadata/score/rank; Hybrid lưu thêm rank/score từng thành phần cho chunk trả về. Không thêm reranker vào ba cấu hình gốc.

Mặc định top-k 3, tối đa 2 search, context 4000 **ký tự**, gồm header ID/nguồn/trang và dấu phân cách. Candidate tích lũy theo thứ tự tìm, dedup ID, giữ cả chunk nếu vừa budget, bỏ qua block quá lớn. Model chỉ nhận context tích lũy mới nhất để không nhân budget qua history. Ưu tiên chunk cũ có thể làm thiếu evidence mới; đã ghi là giới hạn.

Lần model đầu bắt buộc search; lượt sau model được chọn query mới hoặc trả lời. Hết lượt search thì không cho gọi thêm tool. Nguồn/tool là dữ liệu, không phải chỉ dẫn. Output gốc gồm status và claims; mỗi claim có text/citations, renderer gắn `[chunk-id]`. Guard kiểm tra citation thuộc context và cấu trúc; chấm semantic được làm riêng. Nếu model nói thiếu evidence, xuất thông báo cố định, không thêm suy đoán. Lỗi API/retrieval là `error`, không đổi thành từ chối đúng hoặc mock.

Trace lưu request model không có key/header, phản hồi/usage/model snapshot, tool call/args, query yêu cầu/thực thi/filter, results/ranking, context cuối, answer/citations, số lượt, latency và lỗi. Các lỗi kết nối/định dạng của run smoke được giữ ở `results/agent_smoke_*`; không dùng làm benchmark chính.

## 4. So sánh dev/test và chi phí

Thời gian dưới đây là median **end-to-end agent**, không phải latency riêng retrieval. Kết quả retrieval riêng ở [retrieval_dev_v3](../../results/retrieval_dev_v3/summary.json). Mọi cấu hình dev xử lý đủ 17 câu, hai cấu hình test đủ 7 câu; các run chính không lỗi hệ thống.

| Cấu hình | Thay đổi/giả thuyết | Split | Hit@1 | Hit@3 | Context Evidence Rate | Median ms | API ước tính USD |
|---|---|---|---|---|---|---|---|
| Dense baseline | k3/4000, mốc ban đầu | dev | 10/15 (66.7%) | 14/15 (93.3%) | 14/15 (93.3%) | 3069.81 | 0.019405 |
| BM25 | lexical để bắt thuật ngữ/chi tiết chính xác | dev | 15/15 (100%) | 15/15 (100%) | 15/15 (100%) | 2762.79 | 0.017718 |
| Hybrid RRF | phối hợp semantic và lexical | dev | 13/15 (86.7%) | 15/15 (100%) | 15/15 (100%) | 2926.89 | 0.018061 |
| Cải thiện 1 | Dense k6/7000 để lấy rule bị rơi ở rank 6 | dev | 10/15 (66.7%) | 14/15 (93.3%) | 15/15 (100%) | 2845.76 | 0.026934 |
| Cải thiện 2 | k6/7000 + quote/guard cho từng claim | dev | 10/15 (66.7%) | 14/15 (93.3%) | 15/15 (100%) | 3663.61 | 0.032775 |
| Dense baseline | giữ nguyên sau chốt | test | 4/5 (80%) | 5/5 (100%) | 5/5 (100%) | 3884.70 | 0.008547 |
| BM25 đã chọn | giữ nguyên sau chốt | test | 5/5 (100%) | 5/5 (100%) | 5/5 (100%) | 2657.85 | 0.008857 |

Kể cả k6 vẫn báo Hit@3 cùng cutoff. Context grade dev baseline: 0/1/2 = 0/1/14; các cấu hình dev khác 0/0/15. Test của cả hai cấu hình 0/0/5, đã đọc đủ tất cả context năm câu có đáp án mỗi bên.

| Cấu hình/split | Tool use | Search 1/2 lượt | Model calls | Answer grade 0/1/2; mean /2 | Citation hỗ trợ | Câu có citation / câu trả lời | Từ chối đúng | Từ chối nhầm |
|---|---|---|---|---|---|---|---|---|
| Dense/dev | 17/17 | 15/2 | 36 | 1/1/13; 1.800 | 15/16 (93.75%) | 15/15 | 2/2 | 0/15 |
| BM25/dev | 17/17 | 16/1 | 35 | 0/0/15; 2.000 | 16/16 (100%) | 15/15 | 2/2 | 0/15 |
| Hybrid/dev | 17/17 | 16/1 | 35 | 0/0/15; 2.000 | 16/16 (100%) | 15/15 | 2/2 | 0/15 |
| Dense wide/dev | 17/17 | 15/2 | 36 | 2/0/13; 1.733 | 16/18 (88.89%) | 15/15 | 2/2 | 0/15 |
| Dense wide+quotes/dev | 17/17 | 15/2 | 36 | 2/1/12; 1.667 | 14/14 (100%) | 13/13 | 2/2 | 2/15 |
| Dense/test | 7/7 | 5/2 | 16 | 0/0/5; 2.000 | 5/5 (100%) | 5/5 | 2/2 | 0/5 |
| BM25/test | 7/7 | 5/2 | 16 | 0/0/5; 2.000 | 5/5 (100%) | 5/5 | 2/2 | 0/5 |

Tất cả tool use, citation coverage, abstention đúng trong bảng là 100%; false abstention 0% trừ quote mode 2/15 = 13.33%. Citation coverage cao không đồng nghĩa citation đúng hoặc trả lời đủ.

### Nguồn và phạm vi chi phí

Usage thật nằm ở summary/traces từng run. Tổng test: 32 model calls, 37,080 input + 1,602 output = 38,682 chat tokens; Dense tạo 9 request embedding/423 tokens, BM25 không gọi embedding. Dev/các cải thiện/smoke giữ số đo riêng.

Ước tính bổ sung ngày 14/11/2026: input/cached input/output chat lần lượt 0.40/0.10/1.60 USD mỗi triệu token theo [giá GPT-4.1 mini](https://developers.openai.com/api/docs/models/gpt-4.1-mini), embedding 0.02 USD mỗi triệu token theo [giá text-embedding-3-small](https://developers.openai.com/api/docs/models/text-embedding-3-small). Công thức: `(input-cached)*0.40/1e6 + cached*0.10/1e6 + output*1.60/1e6 + embedding_mới*0.02/1e6`. Tổng các run Day 7 ghi nhận, gồm smoke và usage chuẩn bị retrieval, khoảng **0.138096 USD**. [Dự toán chi tiết](../../artifacts/cost_estimate.json), [script](../../scripts/estimate_costs.py).

Đây không phải hóa đơn: chưa tính thuế/credit/chiết khấu, máy/DB/storage, document embedding Day 6 và vector query đã cache từ trước. Summary gốc có `cost_usd=null` không bị sửa. Dự toán được bổ sung sau đánh giá, không dùng để thay quyết định pipeline đã chốt. Latency là một lần chạy tuần tự; Dense test chịu thêm network embedding, không khẳng định ưu thế thời gian/cost có ý nghĩa thống kê.

## 5. Phân tích lỗi và lựa chọn pipeline

**Lỗi dev q13 — thiếu điều kiện khi bằng điểm.** Dense baseline ưu tiên caption và không lấy đoạn rule rank 6 vào top-3: trả lời chung, grade 1. Wide k6 lấy được rule, nhưng cite caption không hỗ trợ quy tắc năm học/học kỳ: grade 0 dù nội dung đúng. Quote mode chọn đúng rule và đạt grade 2. Kết quả xác nhận tăng depth giúp context, nhưng context đủ không tự bảo đảm grounding.

**Lỗi dev q08 — đúng nội dung nhưng sai citation.** Dense baseline/wide trả `Authorization: Bearer <token>` nhưng cite đoạn định nghĩa JWT trang 26; evidence header ở trang 27. Chấm 0, citation không hỗ trợ. Quote mode phát hiện quote trang 27 gắn sai ID trang 26 rồi từ chối nhầm; không được báo là tăng chất lượng câu trả lời.

**Lỗi mới của cải thiện 2:** q05 quote ghép đoạn Repository sang sai chunk làm guard từ chối dù context đủ; q09 quote có đủ thông tin nhưng answer bỏ cách dùng tổng điểm trọng số để tính tiếp, grade 1. Quote membership không bảo đảm semantic support hay completeness. Không bỏ các kết quả giảm điểm này.

Tổng grounded dev: baseline 27/30; wide 26/30; wide+quote 25/30; BM25 và Hybrid cùng 30/30. Policy công bố trước: mean grounded → Context Evidence Rate → citation validity → đúng abstention → Hit@3 → latency → cost nếu biết → ít calls → baseline khi vẫn hòa. BM25/Hybrid hòa các chỉ số chất lượng trên dev, BM25 thắng median thời gian. Chọn BM25 k3/4000/max2, không quote guard. Thử nghiệm quote còn tăng output cap từ 1200 lên 2000 nên là cấu hình kết hợp, không phải ablation riêng prompt.

Giả thuyết và cấu hình ở [dev_experiments](../../configs/dev_experiments.json); so sánh đầy đủ ở [DEV_SELECTION](../../docs/DEV_SELECTION.md). Pipeline chốt trong [selected_pipeline](../../configs/selected_pipeline.json) và [pipeline_freeze](../../configs/pipeline_freeze.json) trước khi test. Hash được kiểm tra trước/sau test, không sửa bằng kết quả test.

## 6. Ví dụ và đánh giá test

| Ví dụ | Tool/context | Câu trả lời và nguồn | Nhãn/lý do |
|---|---|---|---|
| BM25 `d7-test-a04`, có evidence | 1 search; bảng endpoint trong context trang 52 | `PUT /api/me/timetables/{id}/name` với citation `627d6e967b4ca95990799554276fe3552f377630959c93863d817e9daeb8166c` | Answer 2, context 2, citation đúng hàng đổi tên phương án |
| BM25 `d7-test-u01`, thiếu evidence | 2 search; tìm nội dung Excel nhưng không có giới hạn MB | “Không đủ bằng chứng trong dữ liệu truy xuất để trả lời câu hỏi này.” Không citation | Từ chối đúng, không đoán mặc định thư viện |
| Dense dev `q08`, lỗi | Đủ đoạn header trang 27 trong context nhưng model cite đoạn định nghĩa trang 26 | Nội dung Authorization/Bearer với ID nguồn sai | Answer 0, context 2, citation false; giữ lỗi làm bằng chứng phân tích |

Đã chấm riêng mọi test query cho hai cấu hình: header JSON (trang 18), authentication/authorization (25), kiểu dữ liệu Entity (49), endpoint đổi tên (52), công cụ/quyền đọc file (33), thiếu giới hạn Excel và thiếu số đo tải. Cả hai có 5 answer/context mức 2 và 2 từ chối đúng; nguồn citation được đọc đối chiếu PDF. Dense chỉ Hit@1=4/5 vì câu công cụ/quyền lấy evidence rank 2; context và câu trả lời vẫn đủ. Không tạo lỗi test giả hoặc đổi pipeline để tăng điểm.

[TEST_RESULTS](../../docs/TEST_RESULTS.md) có bảng từng câu; [reviews test](../../results/agent_test_v1/reviews.json), [review packet](../../results/agent_test_v1/review_packet.json) và [graded summary](../../results/agent_test_v1/graded_summary.json) đủ truy ngược nhãn/lý do. [Evaluation receipt](../../results/agent_test_v1/evaluation_receipt.json) lưu hash kết quả và freeze tham chiếu.

## 7. Tái lập và hồ sơ nộp

Rà soát cuối: **50 unit tests đạt**, validator benchmark đạt, 99 kết quả dev/test có nhãn, link Markdown nội bộ hợp lệ, không phát hiện các mẫu key OpenAI/GitHub thông dụng trong file sẽ được Git theo dõi. Đây không phải chứng nhận privacy/security toàn diện. [Kết quả rà soát](../../artifacts/submission_check.json). Cả 44 file trong pipeline freeze/test receipt được kiểm tra giữ nguyên byte qua Git clean filters; `.gitattributes` bảo vệ LF/CRLF để không làm lệch hash khi clone.

[README](../../README.md) có lệnh cài dependency, nạp biến môi trường, audit/khôi phục dữ liệu, chạy retrieval/agent dev, hai cải thiện, test cố định và tổng hợp nhãn. Các output cũ không bị ghi đè; run mới cần thư mục mới. Không gọi API lại chỉ để chấm hồ sơ đã lưu. Tái chạy provider có thể khác dù temperature 0; không chọn lại pipeline hoặc run tốt nhất bằng test.

| Bằng chứng | Vị trí |
|---|---|
| Corpus/index/source audit | `artifacts/day6_audit.json`, gói riêng theo `docs/DATA_ACCESS.md` |
| Benchmark 24 câu, evidence và absence | `benchmarks/*.inputs.json`, `*.gold.json`, `freeze.json` |
| Ba agent dev gốc | `results/agent_dev_v1/` |
| Hai cải thiện dev | `results/agent_dev_dense_wide/`, `results/agent_dev_dense_wide_quotes/` |
| So sánh và quyết định | `results/dev_comparison.json`, `configs/selected_pipeline.json`, `configs/pipeline_freeze.json` |
| Baseline/selected test | `results/agent_test_v1/` |
| Mỗi run agent | `config.json`, `traces.json`, `reviews.json`, `review_packet.json`, `graded_summary.json`, `summary.json` |
| PDF đối chiếu citation | `cited_source_checks.json` trong các run; PDF gốc qua gói riêng |
| Lỗi/smoke và usage chuẩn bị | `results/RUN_HISTORY.md`, các thư mục smoke/retrieval v1/v2 giữ nguyên |
| Kiểm thử/handoff/nộp bài | `tests/`, `artifacts/handoff_verification.json`, `docs/SUBMISSION_CHECKLIST.md` |

Gói dữ liệu đã khôi phục thử trên DB tạm mới, so snapshot, self-query/BM25 và chặn ghi đè; không thay DB gốc, không gọi model. Gói được phép nộp trong `data/submission/`, không có credential; các bản nháp/cache rời trong `data/local/` vẫn ignore. Code/bằng chứng cần commit/push hoặc bàn giao gói hoàn chỉnh, và người chấm cần truy cập được; checklist không đánh dấu giả các việc này.

## 8. Kết luận và giới hạn

BM25 là lựa chọn phù hợp nhất theo policy/dev hiện tại; Dense và Hybrid vẫn triển khai/đánh giá đầy đủ. Truy xuất đủ evidence, trả lời đúng và chọn citation đúng là ba việc khác nhau: hai lỗi Dense và hai cải thiện không thắng thể hiện rõ điều đó. Test xác nhận hành vi tốt trên đúng 7 câu đã chốt, không chứng minh tổng quát hóa hoặc an toàn prompt injection toàn diện.

Các giới hạn chính của phần cơ bản: một corpus nhỏ, chỉ 33/84 trang, không OCR; benchmark dựa trên một tài liệu; từ vựng nhiều câu gần tài liệu; chưa đánh giá nhiều lần/độ biến thiên; context ưu tiên chunk cũ; quote guard có false abstention; model snapshot có thể không còn khả dụng về sau. Phần nâng cao được trình bày riêng bên dưới; không suy điểm từ phần cơ bản sang phần nâng cao.

## 9. Phần nâng cao vòng 1 — hồ sơ lịch sử

Tôi chọn **NASA Systems Engineering Handbook, NASA/SP-2016-6105 Rev 2 (2016), 297 trang PDF**. Tài liệu có text, bảng, sơ đồ quy trình và biểu đồ định lượng, đáp ứng yêu cầu tài liệu trên 100 trang. [Nguồn gốc NASA](https://www.nasa.gov/wp-content/uploads/2018/09/nasa_systems_engineering_handbook_0.pdf), [manifest/hash](../../advanced/source.json). PDF, index và ảnh render giữ local; bộ nộp có nguồn tải lại và code tái tạo. Giữ credit INCOSE trên Figure 2.5-1, không phát hành lại toàn bộ PDF/ảnh gốc trong repo.

Pipeline riêng index **297/297 trang**, 810.640 ký tự text; native extraction có cảnh báo font/chữ xoay ở 44 trang và không có lỗi dừng. Đã render được toàn bộ 297 trang, không chỉ trang benchmark. BM25 tìm theo trang/caption/heading, agent xem ảnh gốc bằng vision để đọc bảng và quan hệ trực quan. Citation dùng ID trang vật lý, tên hàng/nhánh/trục/đoạn và nhãn nguồn. [Code và cách chạy](../../advanced/README.md), [coverage](../../advanced/coverage_check.json).

Benchmark nâng cao được chốt trước thử nghiệm: **dev 15 có đáp án + 3 thiếu evidence; test 24 có đáp án + 6 thiếu evidence**. Các nhóm test chính có 6 bảng, 5 sơ đồ, 5 biểu đồ, 4 multi-hop và 4 text; mỗi câu chỉ thuộc một nhóm. Inputs tách gold, không đưa đáp án/vùng gold vào agent hoặc bước kiểm tra draft. Năm câu chart test đọc những thông tin khác nhau trên hai biểu đồ định lượng, nên mức đa dạng biểu đồ còn thấp.

Đã chấm 108 output dev của sáu cấu hình: compact 3/18, wide 5/18, locator 14/18, precise 14/18, checked 16/18 và guarded **17/18**. Các lỗi bbox, số trang in/PDF, tìm heading hai cột, suy diễn và từ chối được giữ trong hồ sơ. Chọn guarded trên dev, freeze trước test: GPT-4.1-2025-04-14, BM25 top 7, tối đa 8 tool, ảnh 2.000 pixel, kiểm tra draft với nguồn và guard định lượng. [So sánh](../../advanced/dev_comparison.json), [freeze](../../advanced/pipeline_freeze.json).

Test chạy toàn bộ một lượt, không chỉnh pipeline theo test. Chấm nhị phân nghiêm ngặt: đúng một phần không đạt; quote nguồn không thay cho điều kiện thiếu/sai trong claim. Đã đọc đối chiếu từng câu và citation với trang gốc, kèm lý do. **Kết quả vòng 1: 23/30 = 76,666…%, chưa đạt ngưỡng ở vòng này. Kết quả hiện hành của vòng 2 được trình bày tại mục 10.**

| Nhóm test nâng cao | Đạt / Tổng |
|---|---:|
| Bảng | 5/6 |
| Sơ đồ | 4/5 |
| Biểu đồ | 5/5 |
| Multi-hop | 2/4 |
| Text | 3/4 |
| Thiếu bằng chứng | 4/6 |

Bảy lỗi gồm: câu 02 đổi điều kiện “và” thành “hoặc”; 08 đọc sai nhánh No; 19 cite validation thay vì nguồn verification cho điều kiện không có prototype; 20 thiếu flight-proven trong claim; 21 thêm so sánh điều kiện kiểm soát chưa được nguồn chứng minh; 27 và 29 lỗi JSON. Hai lỗi hệ thống vẫn nằm trong mẫu số 30, không retry. [Nhãn/lý do từng câu và citation](../../advanced/results/test_guarded/reviews.json), [metrics](../../advanced/results/test_guarded/graded_summary.json), [context checks](../../advanced/context_checks.json).

Test có median 8,65 giây/câu, tổng latency theo câu 351,55 giây và wall time 194,06 giây với hai worker; 150 model call, 1.195.960 prompt token và 9.598 completion token. Ước tính test 2,345824 USD, toàn bộ dev/test nâng cao 5,385675 USD theo usage/giá chuẩn, chưa đối chiếu hóa đơn. [Chi phí/thời gian](../../advanced/cost_estimate.json).

Các giới hạn thực tế là lỗi font/chữ xoay, tìm kiếm lexical, khả năng vision đọc sai quan hệ/điều kiện, kiểm tra draft vẫn bỏ lọt lỗi và guard có thể từ chối số viết bằng chữ. Không lấy điểm tốt nhóm chart để che lỗi nhóm khác. Nếu tiếp tục cải thiện sau phân tích này, cần chốt một test mới độc lập trước lần đánh giá tiếp theo; không sửa pipeline rồi báo điểm lại trên 30 câu hiện tại.


## 10. Phần nâng cao vòng 2 — kết quả hiện hành

Tôi dùng các lỗi vòng 1 làm dữ liệu phát triển và chuyển 30 câu test cũ sang dev.
Trước mọi thử nghiệm vòng 2, tôi chốt bộ test mới độc lập 30 câu (24 có đáp án,
6 thiếu bằng chứng), gồm 6 bảng, 5 sơ đồ, 5 biểu đồ, 4 multi-hop và 4 text.
Gold/inputs được tách riêng, không gửi đáp án chuẩn vào agent/verifier.

Hai cấu hình thử trên dev là GPT-4.1 extractive (14/30, 14 lỗi giao thức) và
GPT-5.2 reasoning medium (29/30, 0 lỗi). Tôi chọn và freeze GPT-5.2 trước test.
Test mới được chạy đủ một lượt, đạt **29/30 = 96,67%**, 0 lỗi hệ thống, vượt
ngưỡng 90%; không điều chỉnh predictor theo test mới. Test cũ vẫn giữ **23/30**.

| Nhóm test mới | Đạt / Tổng |
|---|---:|
| Bảng | 6/6 |
| Sơ đồ | 4/5 |
| Biểu đồ | 5/5 |
| Multi-hop | 4/4 |
| Text | 4/4 |
| Thiếu bằng chứng | 6/6 |

Câu 09 thiếu phân biệt tuyến đệ quy nên vẫn không đạt. Câu 27 có status
`answered` nhưng nội dung “None” là từ chối về nghĩa; cách chấm này nhất quán
với dev và đã ghi rõ trong nhãn. Có 5 `abstain` và 1 từ chối theo nội dung.

Test dùng 162 model call, median 19,03 giây/câu, wall time 359,72 giây với 2 worker;
chi phí ước tính 3,035380 USD, chưa đối chiếu hóa đơn. Giới hạn: một tài liệu,
chưa đánh giá biến thiên nhiều lần; chart tập trung trên hai biểu đồ; không có
người chấm bên ngoài xác nhận nhãn. Không so mức tăng hai vòng như thể cùng test.

[Báo cáo chi tiết và tái lập](../../advanced_v2/README.md),
[metrics](../../advanced_v2/results/test_reasoned/graded_summary.json),
[nhãn/citation](../../advanced_v2/results/test_reasoned/reviews.json),
[freeze](../../advanced_v2/pipeline_freeze.json), [bản nộp cuối](../../SUBMISSION_FINAL.md).
