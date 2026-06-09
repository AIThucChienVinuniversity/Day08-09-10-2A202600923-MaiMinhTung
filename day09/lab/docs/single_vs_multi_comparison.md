# Single Agent vs Multi-Agent Comparison — Lab Day 09

**Nhóm:** Mai Minh Tùng - 2A202600923
**Ngày:** 09/06/2026

> **Lưu ý:** Day 08 không lưu trace và nhóm không chạy lại `eval.py` trong thời gian thực hiện báo cáo. Vì vậy, các số liệu của Day 08 được ghi là **N/A**.

---

## 1. Metrics Comparison

| Metric                | Day 08 (Single Agent) | Day 09 (Multi-Agent) | Delta    | Ghi chú                                          |
| --------------------- | --------------------- | -------------------- | -------- | ------------------------------------------------ |
| Avg confidence        | N/A                   | 0.84                 | N/A      | Day 09 lấy từ `eval_trace.py`                    |
| Avg latency (ms)      | N/A                   | 0                    | N/A      | Thời gian quá nhỏ nên hiển thị 0 ms              |
| Abstain rate (%)      | N/A                   | 0%                   | N/A      | Không có câu nào abstain trong 15 test questions |
| Multi-hop accuracy    | N/A                   | 100% (3/3)           | N/A      | Các câu policy + access đều route đúng           |
| Routing visibility    | ✗ Không có            | ✓ Có route_reason    | N/A      |                                                  |
| Debug time (estimate) | ~30 phút              | ~10 phút             | -20 phút |                                                  |
| MCP integration       | ✗                     | ✓                    | N/A      | Day 09 hỗ trợ MCP                                |

---

## 2. Phân tích theo loại câu hỏi

### 2.1 Câu hỏi đơn giản (single-document)

| Nhận xét    | Day 08           | Day 09                             |
| ----------- | ---------------- | ---------------------------------- |
| Accuracy    | N/A              | 100%                               |
| Latency     | N/A              | ≈ 0 ms                             |
| Observation | Không có số liệu | Retrieval worker hoạt động ổn định |

**Kết luận:** Multi-agent không mang lại cải thiện đáng kể về độ chính xác đối với các câu hỏi đơn giản, nhưng cung cấp thêm khả năng quan sát và debug.

---

### 2.2 Câu hỏi multi-hop (cross-document)

| Nhận xét         | Day 08                            | Day 09                                         |
| ---------------- | --------------------------------- | ---------------------------------------------- |
| Accuracy         | N/A                               | 100%                                           |
| Routing visible? | ✗                                 | ✓                                              |
| Observation      | Không biết pipeline xử lý thế nào | Có thể quan sát route_reason và workers_called |

**Kết luận:**

Multi-agent thể hiện ưu thế rõ ràng ở các câu hỏi yêu cầu kết hợp nhiều nguồn thông tin. Trace giúp dễ dàng xác định worker nào chịu trách nhiệm cho từng bước xử lý.

---

### 2.3 Câu hỏi cần abstain

| Nhận xét            | Day 08           | Day 09                                    |
| ------------------- | ---------------- | ----------------------------------------- |
| Abstain rate        | N/A              | 0%                                        |
| Hallucination cases | N/A              | 0                                         |
| Observation         | Không có số liệu | Supervisor và policy worker xử lý ổn định |

**Kết luận:**

Day 09 cung cấp cơ chế Human-in-the-Loop và route_reason giúp giảm nguy cơ hallucination trong các tình huống thực tế.

---

## 3. Debuggability Analysis

### Day 08 — Debug workflow

```
Khi answer sai → phải đọc toàn bộ RAG pipeline code → tìm lỗi ở indexing/retrieval/generation
Không có trace → không biết bắt đầu từ đâu
Thời gian ước tính: khoảng 30 phút
```

### Day 09 — Debug workflow

```
Khi answer sai → đọc trace → xem supervisor_route + route_reason
  → Nếu route sai → sửa supervisor routing logic
  → Nếu retrieval sai → test retrieval_worker độc lập
  → Nếu synthesis sai → test synthesis_worker độc lập
Thời gian ước tính: khoảng 10 phút
```

**Câu cụ thể đã debug trong lab:**

Trong quá trình thực hiện, retrieval worker trả về 0 chunks do ChromaDB chưa được index. Trace giúp xác định lỗi nằm ở retrieval thay vì synthesis. Sau đó nhóm bổ sung file-based fallback retrieval để khắc phục.

---

## 4. Extensibility Analysis

| Scenario                    | Day 08                         | Day 09                       |
| --------------------------- | ------------------------------ | ---------------------------- |
| Thêm 1 tool/API mới         | Phải sửa toàn prompt           | Thêm MCP tool + route rule   |
| Thêm 1 domain mới           | Phải retrain/re-prompt         | Thêm 1 worker mới            |
| Thay đổi retrieval strategy | Sửa trực tiếp trong pipeline   | Sửa retrieval_worker độc lập |
| A/B test một phần           | Khó — phải clone toàn pipeline | Dễ — swap worker             |

**Nhận xét:**

Kiến trúc multi-agent có tính module hóa cao hơn, giúp mở rộng và bảo trì dễ dàng hơn trong môi trường doanh nghiệp.

---

## 5. Cost & Latency Trade-off

| Scenario      | Day 08 calls | Day 09 calls     |
| ------------- | ------------ | ---------------- |
| Simple query  | 1 LLM call   | 1 LLM call       |
| Complex query | 1 LLM call   | 1–2 worker calls |
| MCP tool call | N/A          | 1–2 MCP calls    |

**Nhận xét về cost-benefit:**

Mặc dù multi-agent làm tăng số lượng bước xử lý, chi phí bổ sung được đánh đổi bằng khả năng debug, mở rộng và tích hợp công cụ vượt trội.

---

## 6. Kết luận

> **Multi-agent tốt hơn single agent ở điểm nào?**

1. Có trace đầy đủ giúp dễ debug và phân tích lỗi.
2. Dễ mở rộng thông qua worker mới hoặc MCP tools.

> **Multi-agent kém hơn hoặc không khác biệt ở điểm nào?**

1. Đối với các câu hỏi đơn giản, độ chính xác không cải thiện đáng kể nhưng kiến trúc phức tạp hơn.

> **Khi nào KHÔNG nên dùng multi-agent?**

Không nên sử dụng multi-agent cho các ứng dụng nhỏ, domain hẹp hoặc chatbot chỉ thực hiện một nhiệm vụ đơn giản vì chi phí thiết kế và bảo trì có thể lớn hơn lợi ích mang lại.

> **Nếu tiếp tục phát triển hệ thống này, nhóm sẽ thêm gì?**

* Thay rule-based routing bằng LLM-based router.
* Tích hợp MCP HTTP server thật.
* Bổ sung Human-in-the-Loop với giao diện phê duyệt thực tế.
* Thêm evaluation tự động dựa trên LLM-as-Judge.
