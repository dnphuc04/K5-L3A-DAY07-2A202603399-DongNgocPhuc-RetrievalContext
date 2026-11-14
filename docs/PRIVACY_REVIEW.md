# Phạm vi nộp bằng chứng và rà soát secret

Ngày 14/11/2026, người dùng đã cho phép nộp đầy đủ các file làm bằng chứng. Quyền này được ghi ở [submission_permission.json](../submission_permission.json). Bộ nộp hiện bao gồm code, báo cáo, benchmark/gold, trace/context/answer/citation/nhãn, cấu hình, audit và gói PDF/chunk/vector Day 6.

## Các file được nộp

- `src/`, `scripts/`, `tests/`, dependency và hướng dẫn chạy.
- `benchmarks/`, `configs/`, `results/`, `artifacts/`, tài liệu `docs/` và báo cáo cá nhân.
- `data/submission/day6_handoff.zip`: gói dữ liệu đã kiểm tra, chứa PDF/65 chunk/vector/cache và manifest hash; không có credential. Bản gốc local giữ nguyên.
- `.env.example` chỉ có placeholder. Không cần API key của tác giả để kiểm tra trace/nhãn; người chạy API dùng key riêng.

Gói source-only cũ vẫn có thể dùng để xem code nhưng không phải bộ nộp đầy đủ. Bộ đầy đủ có `SUBMISSION_MANIFEST.json` liệt kê/hash mọi file, không có `.git`.

## Luôn loại khỏi bộ nộp

`.env` thật, API key, token/DSN thực, private key, `.aws/.ssh/.docker`, `.git`, venv và thư mục scratch `data/local/`, `tmp/` vẫn bị chặn. Chỉ ZIP bàn giao đã chỉ định trong `data/submission/` được mở ngoại lệ; không dùng `git add -f data/local` để đưa các bản nháp/cache/gói cũ vào repo.

## Quét và giới hạn

Script `scripts/audit_submission_privacy.py` quét file Git sẽ nhận, index/lịch sử nhánh, toàn bộ refs cục bộ, file evidence và nội dung từng member ZIP. Kiểm tra mẫu OpenAI/GitHub/AWS/private key/DSN và khớp chính xác credential đang cấu hình (giữ trong bộ nhớ, không in giá trị). Báo cáo `artifacts/privacy_review.json`; chi tiết cục bộ ở `data/local/privacy_review.full.json` được ignore.

Quét không phát hiện mẫu/credential đã biết không chứng minh không có mọi loại secret. Không OCR screenshot/PDF. PDF/trích đoạn được nộp theo quyền người dùng vừa cấp, không phải vì scanner tự xác nhận quyền tác giả.

## Lịch sử Git

Nhánh main/remote-tracking refs và index được kiểm tra tách khỏi snapshots. `refs/codex/...` cục bộ có evidence riêng; không tự xóa/viết lại các refs thuộc cơ chế snapshot của ứng dụng. Không gửi nguyên `.git`, bundle mọi ref, `push --mirror` hay refspec `refs/codex/...`; chỉ nộp các file đã xét theo manifest. Chưa tự commit/push/upload/cấp quyền người chấm.

## Chạy lại trước khi gửi

```powershell
& $python scripts/audit_submission_privacy.py --day6-root $day6
& $python scripts/audit_submission_privacy.py --day6-root $day6 --export-full data/local/submission_complete.zip
& $python scripts/check_submission.py
```

Chọn ZIP output mới nếu đã tồn tại. Export đầy đủ yêu cầu quyền đã ghi nhận và bị chặn khi có secret hoặc file ngoài phạm vi. Bộ kết quả/code đã chốt giữ nguyên byte; thay đổi ở đây chỉ là phạm vi đóng gói/bàn giao, không thay pipeline theo test. Sau sửa file cần quét/tạo gói mới.
