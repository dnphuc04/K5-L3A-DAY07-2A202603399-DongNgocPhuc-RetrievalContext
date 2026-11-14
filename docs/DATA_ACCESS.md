# Dữ liệu Day 6 và bàn giao để tái lập

## Nguồn và phạm vi

Nguồn: “Báo cáo thực tập doanh nghiệp - Đồng Ngọc Phúc”, PDF 84 trang, SHA-256 `052352bcb0abf94da5a523bba2710b143df11f89bc1a5801f6810e26df7e48a8`. Chỉ 33 trang vật lý trong allowlist manifest được index, tạo 65 chunk C (paragraph tối đa 1000 ký tự). Không OCR ảnh; số trang giữ nguyên PDF gốc, không đánh lại từ 1 trong corpus con.

PDF được người dùng cung cấp cho lab. Ngày 14/11/2026 người dùng đã cho phép nộp đầy đủ file làm bằng chứng, gồm PDF và các trích đoạn; phạm vi được ghi tại [submission_permission.json](../submission_permission.json). Benchmark, trace và review packet vì vậy được đưa vào bộ nộp. Credential và thư mục `.git` không nằm trong quyền bàn giao này.

Repo Day 7 có đủ code/nhãn/kết quả và gói PDF/vector/cache trong `data/submission/day6_handoff.zip`, không có secret. Repo Day 6 cục bộ không có remote origin; người chấm không cần clone repo đó, dùng gói đã chuẩn bị bên dưới. Chưa tự upload/gửi hoặc cấp quyền người chấm.

## Gói cục bộ đã chuẩn bị

[data/submission/day6_handoff.zip](../data/submission/day6_handoff.zip), 6,026,295 bytes, SHA-256:

```text
3215f46debb4b1e01c3421a7c36c82401bb466e1aade31ba54bb11f2c66f063d
```

Gói có 41 file, theo allowlist, không chứa `.env`, key, DSN hoặc Docker config:

- `day6/data/manifest.json`, PDF gốc ở `day6/starter/data/bao_cao_thuc_tap.pdf`.
- Snapshot `day6/starter/results/chunks/C.jsonl`, ingestion metadata và adapter embedding gốc `day6/starter/src/embeddings.py`.
- Benchmark Day 6 gốc chỉ để kiểm kê/chuyển định dạng; benchmark đánh giá Day 7 chính thức vẫn ở repo Day 7.
- `vectors_C.json`: 65 vector thật đã lưu, 1536 chiều, đi cùng chunk/source/page/metadata; không cần tạo lại document embedding để khôi phục.
- `query_cache/`: cache query đã có để tránh phí lặp khi tái lập; không chứa gold/context. Không được dùng tên cache/hash làm filter hay đưa gold vào retriever.
- `handoff_manifest.json`: hash từng file.

Gói đã được giải nén kiểm tra hash và **khôi phục thành công vào một database tạm mới tách biệt**. Đối chiếu runtime với snapshot chốt, self-query cosine=1.0, BM25 smoke tìm đúng trang 18, kiểm tra từ chối restore đè bảng đã có. Database kiểm tra đã xóa sau xác minh; database Day 6 gốc không thay đổi. Chi tiết: [handoff_verification.json](../artifacts/handoff_verification.json). Không có API call trong kiểm tra này.

## Quy trình cho người chấm sau khi được cấp quyền

1. Nhận repo/bộ nộp Day 7, dùng `data/submission/day6_handoff.zip`; kiểm tra SHA-256 trên đây hoặc manifest bàn giao.
2. Giải nén gói vào một thư mục riêng, ví dụ `data/local/reviewer_handoff`. Đặt `$day6` vào thư mục `day6` bên trong. Không đổi nội dung snapshot/manifest/adapter.
3. Cài dependency theo README. Chuẩn bị PostgreSQL 16 có pgvector trong **database mới**, không dùng DB đang có `lab_chunks`.
4. Đặt DSN mới vào biến `DAY7_RESTORE_DATABASE_URL` cục bộ (không commit). Chạy restore, sau đó dùng cùng DSN ở `DATABASE_URL` cho runner. Điền key cá nhân vào `OPENAI_API_KEY` bằng môi trường/secret manager, không đặt vào lệnh được ghi log.

```powershell
$handoff = 'data/local/reviewer_handoff'
$day6 = "$handoff/day6"
# Trước lệnh tiếp theo: nạp DAY7_RESTORE_DATABASE_URL từ cấu hình cục bộ của bạn.
& $python scripts/restore_day6_handoff.py --handoff-root $handoff
$env:DATABASE_URL = $env:DAY7_RESTORE_DATABASE_URL
New-Item -ItemType Directory -Force data/local/query_cache | Out-Null
Copy-Item -Path "$handoff/query_cache/*" -Destination data/local/query_cache -Force
& $python scripts/validate_benchmark.py --day6-root $day6
& $python -c "from scripts.run_agent_test import verify_freezes; print(verify_freezes())"
```

Tạo trước `data/local/query_cache` nếu máy mới chưa có thư mục này. Có thể bỏ bước copy cache; lúc chạy Dense sẽ gọi embeddings thật cho query và có phí. Cache không thay document index trong pgvector. Restore từ chối bất kỳ database nào đã có bảng `lab_chunks`; không xóa/upsert đè. User DB cần quyền tạo extension/bảng phù hợp.

Sau đó chạy dev/test bằng các lệnh README với `$day6` mới và thư mục output mới. Không gửi gold vào agent, không ghi đè run công bố hoặc chọn lại pipeline bằng test. Snapshot và source hashes phải khớp bản chốt; nếu không khớp, dừng và xác minh nguồn thay vì sửa hash để chạy tiếp.

## Tạo lại gói từ máy tác giả

```powershell
& $python scripts/package_day6.py --day6-root $day6 --output data/local/day6_handoff_new.zip
```

Lệnh chỉ đọc Day 6 và DB hiện có, không gọi API, chỉ ghi ZIP mới trong Day 7. ZIP thay đổi cache hoặc timestamp có thể có hash khác; script kiểm tra corpus đóng băng và manifest hash từng file. Không tự ghi đè gói đã chuẩn bị. Gói được phép nộp hiện tại có hash ở trên; bản local gốc vẫn giữ nguyên.
