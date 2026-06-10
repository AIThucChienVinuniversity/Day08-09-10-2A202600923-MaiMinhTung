# Quality report — Lab Day 10

**Sinh viên:** Mai Minh Tùng – 2A202600923
**run_id:** final-clean
**Ngày:** 10/06/2026

---

## 1. Tóm tắt số liệu

| Chỉ số             | Trước (inject-bad) | Sau (final-clean) | Ghi chú                              |
| ------------------ | ------------------ | ----------------- | ------------------------------------ |
| raw_records        | 10                 | 10                | Không thay đổi                       |
| cleaned_records    | 6                  | 6                 | Sau cleaning                         |
| quarantine_records | 4                  | 4                 | Record lỗi bị tách riêng             |
| Expectation halt?  | Có                 | Không             | Refund expectation fail ở inject-bad |

---

## 2. Before / after retrieval

### Câu hỏi then chốt: refund window (`gq_d10_01`)

**Trước (inject-bad):**

* Dữ liệu stale chứa policy hoàn tiền **14 ngày làm việc** vẫn tồn tại.
* Expectation `refund_no_stale_14d_window` thất bại.
* Pipeline chỉ tiếp tục nhờ sử dụng `--skip-validate`.

**Sau (final-clean):**

* Chunk stale được sửa hoặc loại bỏ.
* Kết quả grading:

```text
MERIT_CHECK[gq_d10_01] OK
```

* `contains_expected = true`
* `hits_forbidden = false`

---

### Merit: HR leave version (`gq_d10_03`)

**Trước:**

* Có nguy cơ retrieval trả về policy cũ với **10 ngày phép năm**.

**Sau:**

* Kết quả grading:

```text
MERIT_CHECK[gq_d10_03] OK
```

* `contains_expected = true`
* `hits_forbidden = false`
* `top1_doc_matches = true`

Điều này chứng minh hệ thống đã ưu tiên đúng phiên bản hiện hành của tài liệu HR.

---

## 3. Freshness & monitor

Kết quả freshness check:

```text
FAIL
```

Chi tiết:

* `latest_exported_at`: 2026-04-10T08:00:00
* `age_hours`: khoảng 1459 giờ
* `sla_hours`: 24 giờ

Giải thích:

Pipeline hoạt động đúng khi phát hiện dữ liệu đã vượt quá SLA quy định. Trong môi trường thực tế, trường hợp này cần kích hoạt cảnh báo để yêu cầu ingest lại dữ liệu từ hệ nguồn.

---

## 4. Corruption inject (Sprint 3)

Kỹ thuật inject được sử dụng:

```bash
python etl_pipeline.py run \
    --run-id inject-bad \
    --no-refund-fix \
    --skip-validate
```

Mục tiêu:

* Giữ lại policy refund cũ (14 ngày).
* Quan sát expectation thất bại.
* Đánh giá tác động của dữ liệu lỗi lên retrieval.

Kết quả:

* Expectation `refund_no_stale_14d_window` phát hiện vi phạm.
* Pipeline ghi nhận cảnh báo nhưng vẫn tiếp tục để phục vụ mục đích thực nghiệm.

---

## 5. Hạn chế & việc chưa làm

* Expectation suite vẫn còn đơn giản và chưa bao phủ mọi trường hợp dữ liệu bất thường.
* Freshness monitoring mới dừng ở mức SLA theo thời gian export.
* Chưa tích hợp hệ thống cảnh báo tự động (email, Slack).
* Chưa áp dụng framework chuyên dụng như Great Expectations hoặc Airflow.
* Bộ dữ liệu thử nghiệm còn nhỏ, chưa phản ánh đầy đủ quy mô production.
