# Vòng phát triển thứ hai

Kết quả vòng đầu được giữ nguyên: `advanced/results/test_guarded`, 23/30. Snapshot byte của toàn bộ hồ sơ cũ nằm trong `legacy_snapshot.json`; runner mới kiểm tra snapshot trước và sau khi chạy. Không sửa pipeline, gold, trace hoặc nhãn cũ.

30 câu test cũ được chuyển vai trò thành dev vòng hai với ID mới và trường `previous_id` trong gold. Đây là dữ liệu phát triển đã biết kết quả, không được gọi là test mới. Benchmark mới được chốt trong `benchmarks/freeze.json` trước khi chạy thử retrieval/model vòng hai. Test mới có 24 câu có đáp án, 6 câu thiếu evidence; đủ các nhóm yêu cầu. `independence_review.json` đối chiếu từng mục tiêu trả lời với cả dev và test cũ. Có thể trùng trang/hình, không hỏi lại cùng sự kiện; nhóm chart vẫn chỉ dựa trên hai biểu đồ định lượng của tài liệu.

Các lỗi cũ dẫn tới thay đổi tổng quát:

- Mất AND/OR và điều kiện kỹ thuật khi dịch: câu trả lời giữ tiếng Anh gần nguồn, kiểm tra điều kiện ngay trong claim.
- Đọc sai đường nối: hướng dẫn truy theo đầu mũi tên; thêm tool crop vùng trang gốc để phóng nhãn và đường nối.
- Cite đoạn validation cho điều kiện verification: tăng ưu tiên heading khớp nguyên cụm trong query, bên cạnh BM25 và reference boost.
- Lỗi JSON: giữ raw response, từ chối JSON chứa những câu trả lời khác nhau; cho phép một lượt sửa giao thức có ghi trace. Không retry HTTP và không chọn âm thầm câu trả lời đầu tiên.
- Bước kiểm tra draft đối chiếu lại câu hỏi, mọi điều kiện và các trang đã xem, không dùng gold. Đây là bước của predictor; nhãn benchmark được ghi riêng sau khi đọc câu trả lời và nguồn.

Hai cấu hình đầy đủ: GPT-4.1 extractive và GPT-5.2 reasoning medium. Cùng corpus, giới hạn top 7/8 tool, ảnh 2.000 pixel và bước kiểm tra nguồn. Cấu hình được chọn bằng policy dev đã ghi trước khi mở kết quả test mới. Các lỗi format/crop vẫn tính là không đạt; không loại câu khó khỏi mẫu số.

Nguồn vẫn là NASA Systems Engineering Handbook Rev.2, 297 trang; index và coverage 297/297 của vòng đầu được tái sử dụng đúng hash, không chỉ index trang benchmark. Xem `../advanced/source.json` và `../advanced/coverage_check.json`. PDF/PNG/crop nằm local, không phát hành lại toàn bộ tài liệu; nguồn và credit INCOSE được giữ như vòng đầu.

Model/capability/rate được đối chiếu với [OpenAI GPT-5.2](https://developers.openai.com/api/docs/models/gpt-5.2) và [GPT-4.1](https://developers.openai.com/api/docs/models/gpt-4.1). Model snapshot có thể không còn khả dụng trong tương lai. Hóa đơn thực tế cần đối chiếu riêng với usage/ước tính.
