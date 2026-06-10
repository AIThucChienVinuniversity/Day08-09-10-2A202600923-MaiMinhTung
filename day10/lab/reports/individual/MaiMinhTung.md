# Báo Cáo Cá Nhân — Lab Day 10: Data Pipeline & Observability

**Họ và tên:** Mai Minh Tùng
**MSSV:** 2A202600923
**Vai trò:** Ingestion, Cleaning, Embedding và Monitoring
**Ngày nộp:** 10/06/2026

---

## 1. Tôi phụ trách phần nào?

Trong bài lab Day 10, tôi thực hiện toàn bộ pipeline dữ liệu do làm việc cá nhân. Các phần tôi phụ trách bao gồm ingest dữ liệu từ file CSV raw, xây dựng và kiểm tra cleaning rules, chạy expectation suite, embedding dữ liệu vào ChromaDB và triển khai cơ chế monitoring freshness.

**File / module chính:**

* `etl_pipeline.py`
* `transform/cleaning_rules.py`
* `quality/expectations.py`
* `monitoring/freshness_check.py`

Do làm việc một mình nên không có sự phân chia công việc giữa các thành viên. Tôi chịu trách nhiệm từ khâu ingest dữ liệu đến đánh giá retrieval và hoàn thiện các tài liệu mô tả hệ thống.

**Bằng chứng:**

Các artifact được sinh ra trong quá trình thực hiện gồm:

* `artifacts/logs/run_final-clean.log`
* `artifacts/manifests/manifest_final-clean.json`
* `artifacts/eval/grading_run.jsonl`

---

## 2. Một quyết định kỹ thuật

Quyết định kỹ thuật quan trọng nhất tôi lựa chọn là sử dụng cơ chế **idempotent embedding** dựa trên `chunk_id`.

Thay vì mỗi lần chạy pipeline lại thêm vector mới vào ChromaDB, hệ thống sử dụng:

```text
upsert(chunk_id)
```

để cập nhật vector hiện có. Ngoài ra pipeline còn thực hiện bước prune các `chunk_id` không còn xuất hiện trong cleaned dataset. Điều này giúp đảm bảo collection luôn phản ánh đúng snapshot dữ liệu hiện tại.

Ưu điểm của cách tiếp cận này là có thể rerun pipeline nhiều lần mà không sinh duplicate vector. Trong quá trình chạy thử nghiệm, log ghi nhận:

```text
embed_prune_removed=1
embed_upsert count=6
```

cho thấy vector stale đã được loại bỏ trước khi publish dữ liệu mới.

---

## 3. Một lỗi hoặc anomaly đã xử lý

Anomaly đáng chú ý nhất là phiên bản policy hoàn tiền cũ vẫn tồn tại trong dữ liệu.

Khi chạy:

```bash
python etl_pipeline.py run \
    --run-id inject-bad \
    --no-refund-fix \
    --skip-validate
```

expectation suite phát hiện lỗi:

```text
refund_no_stale_14d_window FAIL
violations=1
```

Điều này chứng minh dữ liệu vẫn chứa policy cũ với cửa sổ hoàn tiền 14 ngày làm việc thay vì 7 ngày làm việc.

Để khắc phục, tôi chạy lại pipeline chuẩn với rule sửa refund window được bật. Sau khi xử lý, expectation suite báo:

```text
refund_no_stale_14d_window OK
violations=0
```

và retrieval không còn trả về nội dung stale.

---

## 4. Bằng chứng trước / sau

### Run inject-bad

```text
run_id=inject-bad
refund_no_stale_14d_window FAIL
violations=1
```

### Run final-clean

```text
run_id=final-clean
refund_no_stale_14d_window OK
violations=0
```

Kết quả grading cuối cùng:

```text
MERIT_CHECK[gq_d10_01] OK
MERIT_CHECK[gq_d10_02] OK
MERIT_CHECK[gq_d10_03] OK
```

Đặc biệt với câu hỏi HR leave version, hệ thống truy xuất đúng tài liệu:

```text
top1_doc_id = hr_leave_policy
top1_doc_matches = true
```

chứng minh dữ liệu stale đã được loại bỏ khỏi pipeline.

---

## 5. Cải tiến tiếp theo

Nếu có thêm thời gian, tôi muốn tích hợp framework Great Expectations và xây dựng dashboard monitoring tự động. Thay vì chỉ ghi log ra file, hệ thống có thể gửi cảnh báo khi freshness vượt SLA hoặc khi expectation fail. Điều này giúp pipeline tiến gần hơn tới môi trường production thực tế.
