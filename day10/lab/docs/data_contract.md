# Data contract — Lab Day 10

> Bắt đầu từ `contracts/data_contract.yaml` — mở rộng và đồng bộ file này.

---

## 1. Nguồn dữ liệu (source map)

| Nguồn | Phương thức ingest | Failure mode chính | Metric / alert |
|-------|-------------------|-------------------|----------------|
| `data/raw/policy_export_dirty.csv` | Batch CSV export từ hệ nguồn DB/API giả lập | duplicate record, sai `doc_id`, thiếu ngày, ngày không đúng ISO, stale version | `raw_records`, `cleaned_records`, `quarantine_records`, expectation fail |
| `data/docs/*.txt` | Local document corpus dùng cho RAG / Helpdesk KB | tài liệu cũ còn trong index, version policy xung đột | `hits_forbidden`, `top1_doc_id`, `contains_expected` |
| ChromaDB collection `day10_kb` | Embed cleaned chunks sau khi validate | vector cũ chưa bị xoá, chunk stale vẫn xuất hiện trong top-k | `embed_prune_removed`, `embed_upsert count`, grading JSONL |

---

## 2. Schema cleaned

| Cột | Kiểu | Bắt buộc | Ghi chú |
|-----|------|----------|---------|
| chunk_id | string | Có | Khóa duy nhất cho mỗi chunk, dùng để upsert idempotent vào Chroma |
| doc_id | string | Có | Mã tài liệu thuộc allowlist, ví dụ `policy_refund_v4`, `sla_p1_2026`, `hr_leave_policy` |
| chunk_text | string | Có | Nội dung chunk sau khi làm sạch, dùng để embed |
| effective_date | date | Có | Ngày hiệu lực chuẩn ISO `YYYY-MM-DD` |
| exported_at | datetime | Có | Thời điểm export từ hệ nguồn, dùng để kiểm tra freshness |
| source | string | Không | Nguồn sinh record nếu có |
| version | string | Không | Phiên bản policy nếu có |

---

## 3. Quy tắc quarantine vs drop

Record không hợp lệ không bị xoá âm thầm. Pipeline tách dữ liệu thành hai nhóm:

- `cleaned`: record hợp lệ, được validate và embed vào ChromaDB.
- `quarantine`: record có lỗi như thiếu `doc_id`, `doc_id` không thuộc allowlist, ngày không đúng định dạng ISO, duplicate, stale HR version hoặc chunk không đạt rule chất lượng.

Các record trong quarantine cần được Data Owner hoặc Policy Owner kiểm tra trước khi merge lại. Chỉ khi lỗi được sửa ở source hoặc mapping rule được cập nhật thì record mới được chạy lại qua pipeline.

---

## 4. Phiên bản & canonical

Source of truth cho refund policy là:

- `doc_id`: `policy_refund_v4`
- rule hiện hành: khách hàng có **7 ngày làm việc** để yêu cầu hoàn tiền
- chunk stale chứa **14 ngày làm việc** phải bị sửa hoặc bị chặn bằng expectation `refund_no_stale_14d_window`

Source of truth cho HR leave policy là:

- `doc_id`: `hr_leave_policy`
- rule hiện hành năm 2026: nhân viên dưới 3 năm kinh nghiệm có **12 ngày phép năm**
- bản cũ chứa **10 ngày phép năm** không được xuất hiện trong top-k retrieval