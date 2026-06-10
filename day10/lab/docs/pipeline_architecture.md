# Kiến trúc pipeline — Lab Day 10

**Nhóm:** Mai Minh Tùng – 2A202600923
**Cập nhật:** 10/06/2026

---

## 1. Sơ đồ luồng

```text
                ┌──────────────────────────────┐
                │ policy_export_dirty.csv      │
                │ data/docs/*.txt              │
                └──────────────┬───────────────┘
                               │
                               ▼
                      ┌────────────────┐
                      │ Ingest         │
                      │ load_raw_csv() │
                      └────────┬───────┘
                               │
                               ▼
                      ┌────────────────┐
                      │ Transform      │
                      │ clean_rows()   │
                      └───────┬────────┘
                              │
               ┌──────────────┴──────────────┐
               │                             │
               ▼                             ▼
     ┌──────────────────┐         ┌──────────────────┐
     │ Cleaned Dataset  │         │ Quarantine       │
     │ cleaned_*.csv    │         │ quarantine_*.csv │
     └────────┬─────────┘         └──────────────────┘
              │
              ▼
     ┌──────────────────┐
     │ Expectations     │
     │ run_expectations │
     └────────┬─────────┘
              │
              ▼
     ┌──────────────────┐
     │ Embed            │
     │ ChromaDB         │
     │ upsert(chunk_id) │
     └────────┬─────────┘
              │
              ▼
     ┌──────────────────┐
     │ Serving          │
     │ Day 08 / Day 09  │
     │ Retrieval        │
     └────────┬─────────┘
              │
              ▼
     ┌──────────────────┐
     │ Monitoring       │
     │ Manifest         │
     │ Freshness Check  │
     │ run_id           │
     └──────────────────┘
```

Freshness được kiểm tra dựa trên trường `latest_exported_at` trong manifest. Mỗi lần chạy pipeline đều sinh `run_id` để phục vụ truy vết và debug.

---

## 2. Ranh giới trách nhiệm

| Thành phần | Input            | Output                      | Owner         |
| ---------- | ---------------- | --------------------------- | ------------- |
| Ingest     | CSV export, docs | Raw records                 | Mai Minh Tùng |
| Transform  | Raw records      | Cleaned records, quarantine | Mai Minh Tùng |
| Quality    | Cleaned records  | Expectation results         | Mai Minh Tùng |
| Embed      | Cleaned dataset  | ChromaDB collection         | Mai Minh Tùng |
| Monitor    | Manifest, logs   | Freshness status, alerts    | Mai Minh Tùng |

---

## 3. Idempotency & rerun

Pipeline sử dụng cơ chế `upsert` theo `chunk_id` khi embed vào ChromaDB.

Khi rerun:

* Nếu `chunk_id` đã tồn tại, vector sẽ được cập nhật thay vì tạo mới.
* Các `chunk_id` không còn xuất hiện trong cleaned dataset sẽ bị xoá khỏi collection thông qua cơ chế prune.

Do đó, chạy pipeline nhiều lần không tạo duplicate vector trong ChromaDB.

---

## 4. Liên hệ Day 09

Pipeline Day 10 đóng vai trò cung cấp dữ liệu sạch và cập nhật cho hệ thống retrieval ở Day 09.

Sau khi hoàn thành ETL, cleaned dataset được embed vào ChromaDB và trở thành knowledge base cho retrieval worker trong kiến trúc supervisor–worker.

Nhờ đó, Day 09 có thể truy xuất đúng phiên bản policy mới nhất thay vì các chunk stale hoặc dữ liệu lỗi.

---

## 5. Rủi ro đã biết

* Dữ liệu export từ hệ nguồn có thể chứa duplicate hoặc thiếu trường bắt buộc.
* Tài liệu stale vẫn có thể xuất hiện nếu không thực hiện prune vector.
* Freshness SLA có thể bị vi phạm nếu nguồn dữ liệu không được cập nhật đúng hạn.
* Các expectation chưa bao phủ hết mọi trường hợp dữ liệu bất thường.
* ChromaDB có thể chứa dữ liệu không đồng nhất nếu bypass bước validation.
