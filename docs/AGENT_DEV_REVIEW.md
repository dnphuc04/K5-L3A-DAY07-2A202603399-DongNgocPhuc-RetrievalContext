# Đọc trace agent dev - lần chạy đầu

Ghi chú cập nhật: đây là bản rà soát ban đầu. Việc chấm đầy đủ và hai vòng thử cải thiện đã hoàn tất; kết quả cuối cùng và pipeline được chốt nằm trong `docs/DEV_SELECTION.md`, nhãn chính thức ở `reviews.json` của từng run.

Phạm vi: `results/agent_dev_v1`, không chạy test. Cùng model/prompt/giới hạn cho Dense, BM25, Hybrid; 17 câu mỗi cấu hình. Việc rà soát đối chiếu từng câu trả lời và citation với nguồn, kèm lý do cho mỗi nhãn.

## Kết quả chạy thật hoàn tất

Model: `gpt-4.1-mini-2025-04-14`; top-k 3, tối đa 2 lượt tìm, context 4000 ký tự. Toàn bộ 51 lần chạy hoàn tất, không lỗi hệ thống. Các file benchmark và chính sách đã chốt vẫn giữ nguyên hash.

| Cấu hình | Trả lời có citation | Từ chối | Tool use | Context Evidence Rate strict | Median end-to-end |
|---|---|---|---|---|---|
| Dense | 15/17 | 2/17 | 17/17 | 14/15 (93.3%) | 3069.81 ms |
| BM25 | 15/17 | 2/17 | 17/17 | 15/15 (100%) | 2762.79 ms |
| Hybrid RRF | 15/17 | 2/17 | 17/17 | 15/15 (100%) | 2926.89 ms |

Hai câu bị từ chối của mỗi cấu hình đúng là hai câu thiếu evidence; thông báo xuất ra không thêm suy đoán. Không có câu có đáp án bị từ chối. Nhưng số `answered` không phải số câu đạt grounded-answer grade 2: lỗi Dense q08/q13 bên dưới chứng minh cần chấm nội dung/citation riêng.

Usage trong run chính: Dense 36 model calls, 38,304 input + 2,552 output tokens; BM25 35 calls, 37,679 + 2,470 tokens; Hybrid 35 calls, 37,098 + 2,517 tokens. Tổng 106 model calls, 120,620 chat tokens. Các query tìm tiếp tạo thêm 3 embedding API requests, 59 prompt tokens. Smoke runs có usage riêng trong từng thư mục, không nằm trong tổng này. Tiền API chưa đối chiếu billing nên để null.

Đường dẫn: `summary.json` (vận hành), `traces.json` (request/tool/context/answer/usage), `context_checks.json` (kiểm tra evidence tự động), `review_packet.json` (phiếu để tiếp tục chấm đầy đủ). Chưa chọn hoặc freeze pipeline cuối, chưa đánh giá test.

## Hai lỗi Dense cần xử lý ở vòng cải thiện

### q08 - citation trỏ đúng chủ đề nhưng sai bằng chứng

Model trả đúng chuỗi `Authorization: Bearer <token>` nhưng chọn citation chunk `4cdf6c2880c5d93d02231203e4dde8870ef2a59a705fdd468d096240013801a0` trang 26. Đoạn này chỉ định nghĩa JWT/chữ ký và không chứa header/format được hỏi. Chunk trang 27 chứa evidence đã có trong context nhưng model không cite nó.

Nhãn rà soát cho citation này: **không hỗ trợ**. ID thuộc context chưa đủ để chấm citation hợp lệ. Theo thang grounded answer, câu đúng về nội dung nhưng thiếu nguồn hỗ trợ cho khẳng định không được chấm đủ điểm.

Giả thuyết: model chọn chunk gần chủ đề/top-rank thay vì đối chiếu khẳng định với nguyên văn evidence. Hướng thử tiếp trên dev: yêu cầu trích quote hỗ trợ từng claim và kiểm tra quote thật sự thuộc chunk; vẫn phải đọc ý nghĩa vì quote khớp chưa đảm bảo claim được hỗ trợ. Chưa sửa prompt hoặc chạy lại cấu hình theo lỗi này trong lần benchmark đầu.

### q13 - bỏ mất điều kiện quyết định

Câu hỏi hỏi cách chọn kết quả khi nhiều lần học **bằng điểm**. Dense trả lời chọn điểm cao nhất và giữ lịch sử nhưng không nêu quy tắc chọn năm học/học kỳ mới hơn. Top-1 là caption hình trang 56; context chứa mô tả tổng hợp trang 49 nhưng thiếu đoạn quy tắc chi tiết.

Nhãn rà soát câu trả lời: **đúng một phần**, chưa giải quyết điều kiện chính. Đây là lỗi retrieval/context dẫn tới câu trả lời thiếu, đồng thời model không nhận ra cần tìm tiếp.

Giả thuyết: đoạn caption ngắn có độ tương đồng cao, trong khi model chấp nhận đoạn mô tả chung. Retrieval Hybrid đã từng lấy được đoạn chi tiết trong top-3; cần đối chiếu câu trả lời Hybrid trong trace agent để biết model có sử dụng đầy đủ không. Một cấu hình khác có thể ưu tiên paragraph đầy đủ hoặc tìm lại theo điều kiện thiếu, nhưng phải đo riêng trên dev.

## Câu thiếu bằng chứng

Đối chiếu agent BM25 đã chạy xong: q08 cite đúng chunk trang 27 chứa `Authorization`/`Bearer`; q13 trả đủ quy tắc năm học/học kỳ mới hơn và cite đúng đoạn trang 56. Hybrid cũng cite đúng trang 27 ở q08 và trả đủ quy tắc phân xử ở q13 với nguồn trang 56. Đây là kiểm tra có mục tiêu cho các lỗi cụ thể, chưa phải chấm toàn bộ các câu trả lời của mỗi cấu hình.

Dense đã từ chối cả câu cost factor BCrypt và thời lượng JWT; trace có 2 lượt tìm cho mỗi câu. Câu xuất ra là thông báo thiếu bằng chứng trong dữ liệu truy xuất, không phỏng đoán số mặc định. Những ví dụ này kiểm tra khả năng nhận ra thiếu chi tiết dù có nhiều đoạn cùng chủ đề; không dùng điểm similarity làm ngưỡng bảo đảm answerability.

## Cách đọc kết quả

`summary.json` của runner chỉ thống kê vận hành: answered/abstain/error, tool use, số lượt, token và thời gian. Không coi số answered là số câu đúng, không coi mọi abstain là đúng, không coi citation coverage là citation support.

`scripts/inspect_agent_dev.py` tạo `context_checks.json` (strict gold-span metrics ngoại tuyến) và `review_packet.json` (phiếu có placeholder null cho nhãn ngữ nghĩa). Phiếu không được đưa lại vào model/runner. Cần tiếp tục chấm từng claim/citation theo tài liệu gốc trước khi công bố điểm grounded answer/citation hoặc chọn cấu hình cuối.
