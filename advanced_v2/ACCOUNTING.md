# Chi phí và thời gian từng câu

[per_question_costs.json](per_question_costs.json) ghi riêng 92 lượt câu hỏi mới của vòng hai: 2 smoke, 60 dev và 30 test. Mỗi dòng có hash trace, status/lỗi, latency, số call, prompt/cached/completion/reasoning token và USD ước tính. Reasoning token đã nằm trong completion, không cộng hai lần. Mỗi response ID chỉ được tính một lần.

Đây là ước tính từ usage và rate trong [cost_estimate.json](cost_estimate.json), chưa phải hóa đơn. Call sinh output lỗi và smoke vẫn được tính. Baseline lịch sử được tham chiếu, không tính tiền lại. Tổng từng câu đã được đối chiếu bằng số thập phân với tổng từng run.

Tái tổng hợp offline, không gọi API: `python -m advanced_v2.accounting`. Không chỉnh answer, nhãn, predictor hoặc benchmark khi hạch toán.
