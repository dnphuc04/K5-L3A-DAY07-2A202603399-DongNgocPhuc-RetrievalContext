# Rà soát toàn repo — bản hiện hành

Rà soát sau commit `5e07c95`, ngày 14/11/2026. Bản sửa tài liệu này chưa commit/push.

## Các lỗi phát hiện và cách sửa

1. README trình bày kết quả nâng cao vòng 1 (23/30) như kết quả cuối, gây hiểu sai
   rằng chưa đạt ngưỡng. Đã đưa vòng 2 **29/30 = 96,67%** và link bằng chứng lên đầu.
2. Báo cáo cá nhân/checklist mới có vòng 1 hoặc còn câu “không làm nâng cao”. Đã
   bổ sung vòng 2, benchmark mới, pipeline, kết quả theo nhóm và giới hạn chấm.
3. Ghi chép retrieval/dev nói “chưa chạy test/chưa chọn pipeline” mà không ghi rõ
   thời điểm. Đã đánh dấu là ghi chép giai đoạn và dẫn tới kết quả cuối.
4. Một số chỉ dẫn bàn giao còn ghi “chưa commit/push” sau khi đã push `5e07c95`.
   Đã phân biệt commit đã push với bản sửa hiện đang chờ duyệt.
5. Receipt vòng 1 khóa cả README/báo cáo/checklist. Để cho phép cập nhật tài liệu
   mà không viết lại lịch sử, lưu nguyên byte ba tài liệu gốc trong
   `artifacts/historical_docs/`, đối chiếu hash bằng
   `artifacts/historical_document_map.json`. Preflight vòng 1 được chạy trong
   thư mục tạm với đúng snapshot tài liệu gốc; preflight hiện hành kiểm tra tài
   liệu và evidence hiện hành riêng. Không sửa predictor, benchmark, nhãn hoặc điểm cũ.

## Cách kiểm tra

```powershell
python scripts/check_final_submission.py
python -m unittest discover -s tests -v
python -m unittest advanced.test_agent advanced.test_contract advanced_v2.test_contract -v
```

`python -m advanced.check_submission` là preflight lịch sử kỳ vọng README vòng 1
tại đường dẫn cũ; sau khi tài liệu hiện hành được cập nhật, dùng lệnh kiểm tra toàn
repo ở trên để phục dựng snapshot và chạy đúng preflight gốc, không thay hash kỳ vọng.

Kết quả chi tiết của đợt rà soát nằm ở `artifacts/repo_audit.json`. Các file
validation/inventory/receipt của lần nộp trước vẫn là hồ sơ theo thời điểm được ghi;
không đọc trạng thái “chưa commit” trong các record lịch sử như trạng thái Git hiện tại.

## Phạm vi bảo đảm

Kiểm tra tự động có thể xác nhận cú pháp, hash, tính đầy đủ, link và số liệu nội bộ.
Demo được kiểm tra logic JavaScript và dữ liệu; browser tích hợp chặn `file://`
nên chưa xác nhận bố cục bằng ảnh. Không chạy lại benchmark trả phí, không thay
điểm bằng lượt chạy mới, không tuyên bố kiểm toán bảo mật hay người chấm độc lập.
Điểm rubric và quyền truy cập của giảng viên vẫn cần xác nhận bên ngoài repo.
