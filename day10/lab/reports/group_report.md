# Báo Cáo Nhóm — Lab Day 10: Data Pipeline & Data Observability

**Tên nhóm:** Cá nhân – Mai Minh Tùng
**Thành viên:**

| Tên                         | Vai trò (Day 10)                       | Email           |
| --------------------------- | -------------------------------------- | --------------- |
| Mai Minh Tùng (2A202600923) | Ingestion, Cleaning, Embed, Monitoring | [email của bạn] |

**Ngày nộp:** 10/06/2026
**Repo:** [link GitHub của bạn]

---

## 1. Pipeline tổng quan

Trong bài lab này, tôi xây dựng một pipeline dữ liệu phục vụ hệ thống RAG cho trợ lý nội bộ CS + IT Helpdesk. Dữ liệu đầu vào được lấy từ file CSV mô phỏng export từ hệ thống nguồn (`policy_export_dirty.csv`) kết hợp với tập tài liệu nội bộ trong `data/docs/`.

Pipeline bao gồm các bước ingest, cleaning, validation, embedding và monitoring. Mỗi lần chạy pipeline đều được gắn `run_id` nhằm phục vụ truy vết và debugging. Các artifact như log, manifest, quarantine và evaluation được lưu lại để làm bằng chứng.

Pipeline chuẩn được chạy với `run_id=final-clean`, trong khi kịch bản inject dữ liệu lỗi được chạy với `run_id=inject-bad`.

**Lệnh chạy end-to-end:**

```bash
python etl_pipeline.py run --run-id final-clean
python grading_run.py
python instructor_quick_check.py
```

---

## 2. Cleaning & expectation

Pipeline sử dụng nhiều cleaning rules nhằm đảm bảo dữ liệu đầu vào đạt chất lượng trước khi embed vào ChromaDB. Các record lỗi sẽ được chuyển vào quarantine thay vì bị xoá trực tiếp.

### 2a. Bảng metric_impact

| Rule / Expectation     | Trước                     | Sau                     | Chứng cứ        |
| ---------------------- | ------------------------- | ----------------------- | --------------- |
| Refund stale detection | 1 violation               | 0 violation             | expectation log |
| HR stale detection     | nguy cơ xuất hiện 10 ngày | top1 đúng 12 ngày       | grading JSONL   |
| Vector prune           | vector cũ tồn tại         | `embed_prune_removed=1` | run log         |

Các expectation quan trọng được thiết lập ở chế độ halt, bao gồm:

* `refund_no_stale_14d_window`
* `effective_date_iso_yyyy_mm_dd`
* `hr_leave_no_stale_10d_annual`
* `no_empty_doc_id`

Một ví dụ expectation fail xảy ra khi inject dữ liệu lỗi:

```text
expectation[refund_no_stale_14d_window] FAIL (halt) :: violations=1
```

---

## 3. Before / after ảnh hưởng retrieval

Kịch bản inject được thực hiện bằng cách giữ lại policy refund cũ (14 ngày) và bỏ qua validation.

```bash
python etl_pipeline.py run \
    --run-id inject-bad \
    --no-refund-fix \
    --skip-validate
```

Sau khi inject, expectation phát hiện dữ liệu stale nhưng pipeline vẫn tiếp tục nhằm phục vụ mục đích đánh giá.

Sau khi chạy lại pipeline chuẩn (`final-clean`), grading cho kết quả:

```text
MERIT_CHECK[gq_d10_01] OK
MERIT_CHECK[gq_d10_02] OK
MERIT_CHECK[gq_d10_03] OK
```

Đặc biệt, kết quả retrieval cuối cùng cho thấy:

```json
{
    "id": "gq_d10_03",
    "top1_doc_id": "hr_leave_policy",
    "top1_doc_matches": true
}
```

Điều này chứng minh rằng dữ liệu sạch giúp hệ thống ưu tiên đúng phiên bản tài liệu hiện hành.

---

## 4. Freshness & monitoring

Pipeline sử dụng freshness SLA là 24 giờ.

Kết quả manifest cho thấy:

```text
freshness_check=FAIL
```

với nguyên nhân:

* latest_exported_at: 2026-04-10T08:00:00
* age_hours ≈ 1459 giờ

Điều này cho thấy monitoring đã hoạt động đúng khi phát hiện dữ liệu quá hạn và cần được ingest lại.

---

## 5. Liên hệ Day 09

Pipeline Day 10 đóng vai trò cung cấp dữ liệu sạch cho hệ thống retrieval của Day 09. Sau khi được validate và embed, dữ liệu được lưu vào ChromaDB và có thể được retrieval worker sử dụng để trả lời câu hỏi.

Việc bổ sung tầng quality giúp giảm nguy cơ agent sử dụng chunk stale hoặc policy lỗi.

---

## 6. Rủi ro còn lại & việc chưa làm

* Freshness monitoring chưa có cơ chế gửi cảnh báo tự động.
* Expectation suite vẫn còn đơn giản và có thể mở rộng thêm.
* Chưa tích hợp orchestration framework như Airflow hoặc Prefect.
* Bộ dữ liệu thử nghiệm còn nhỏ và chưa phản ánh đầy đủ môi trường production.
