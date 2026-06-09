# Báo Cáo Nhóm — Lab Day 09: Multi-Agent Orchestration

**Tên nhóm:** Cá nhân (Single-member Team)
**Thành viên:**

| Tên           | Vai trò                                                          | Email       |
| ------------- | ---------------------------------------------------------------- | ----------- |
| Mai Minh Tùng | Supervisor Owner / Worker Owner / MCP Owner / Trace & Docs Owner | ___________ |

**Ngày nộp:** 09/06/2026
**Repo:** `Lecture-Day-08-09-10/day09/lab`

---

## 1. Kiến trúc nhóm đã xây dựng

Hệ thống được xây dựng theo mô hình Supervisor-Worker với mục tiêu tăng khả năng quan sát và mở rộng của pipeline RAG. Supervisor chịu trách nhiệm phân tích truy vấn đầu vào và quyết định worker phù hợp để xử lý. Hai worker chính được triển khai là Retrieval Worker và Policy Tool Worker. Sau khi các worker hoàn thành nhiệm vụ, Synthesis Worker tổng hợp evidence và tạo câu trả lời cuối cùng.

**Hệ thống tổng quan:**

User Query → Supervisor → Retrieval Worker / Policy Tool Worker → MCP Tools (nếu cần) → Synthesis Worker → Final Answer + Trace.

**Routing logic cốt lõi:**

Supervisor sử dụng rule-based routing dựa trên keyword matching:

* SLA, P1, escalation, ticket → `retrieval_worker`
* refund, access, policy → `policy_tool_worker`
* unknown error + risk_high → `human_review`

**MCP tools đã tích hợp:**

* `search_kb`: tìm evidence bổ sung từ knowledge base.
* `get_ticket_info`: truy xuất thông tin ticket giả lập.
* `check_access_permission`: kiểm tra điều kiện cấp quyền.

Ví dụ trace:

```text id="2fb2gf"
Task: Contractor cần Admin Access Level 3...
Route: policy_tool_worker
MCP tools: ['search_kb', 'get_ticket_info']
```

---

## 2. Quyết định kỹ thuật quan trọng nhất

**Quyết định:** Sử dụng file-based fallback retrieval thay cho việc phụ thuộc hoàn toàn vào ChromaDB.

**Bối cảnh vấn đề:**

Trong quá trình kiểm thử, retrieval worker liên tục trả về 0 chunks mặc dù dữ liệu tồn tại trong thư mục `data/docs`. Điều này khiến toàn bộ pipeline không thể sinh câu trả lời grounded.

**Các phương án đã cân nhắc:**

| Phương án                       | Ưu điểm                    | Nhược điểm               |
| ------------------------------- | -------------------------- | ------------------------ |
| Sửa hoàn toàn ChromaDB indexing | Semantic retrieval tốt hơn | Tốn thời gian debug      |
| File-based fallback retrieval   | Đơn giản, ổn định          | Không tận dụng embedding |

**Phương án đã chọn và lý do:**

Tôi chọn file-based fallback retrieval vì mục tiêu chính của Day 09 là hoàn thiện multi-agent orchestration. Việc duy trì pipeline hoạt động ổn định quan trọng hơn tối ưu retrieval.

**Bằng chứng từ trace/code:**

```python id="hkwiyw"
if not chunks:
    return retrieve_file_fallback(query, top_k)
```

Sau khi áp dụng:

```text id="7g2b6u"
Retrieved: 3 chunks
Sources: ['sla_p1_2026.txt',
          'it_helpdesk_faq.txt',
          'access_control_sop.txt']
```

---

## 3. Kết quả grading questions

Do bộ `grading_questions.json` chưa được công bố trong thời điểm hoàn thành báo cáo, nhóm sử dụng `test_questions.json` để đánh giá sơ bộ.

**Tổng điểm raw ước tính:** N/A

**Câu pipeline xử lý tốt nhất:**

* ID: q01
* Lý do tốt: Retrieval worker tìm đúng tài liệu SLA và synthesis tạo câu trả lời grounded.

**Câu pipeline fail hoặc partial:**

* Không ghi nhận trường hợp fail trong 15 test questions.
* Root cause: N/A

**Câu gq07 (abstain): Nhóm xử lý thế nào?**

Synthesis worker được thiết kế để trả lời:

```text id="i4n3wa"
Không đủ thông tin trong tài liệu nội bộ để trả lời.
```

nếu không có evidence phù hợp.

**Câu gq09 (multi-hop khó nhất):**

Chưa có grading set chính thức nên chưa đánh giá được. Tuy nhiên, trace của các câu policy-access đã cho thấy nhiều worker phối hợp thành công.

---

## 4. So sánh Day 08 vs Day 09 — Điều nhóm quan sát được

**Metric thay đổi rõ nhất (có số liệu):**

* Avg confidence: 0.84
* Routing visibility: Có đầy đủ `route_reason`.
* MCP usage rate: 45%.

**Điều nhóm bất ngờ nhất khi chuyển từ single sang multi-agent:**

Khả năng debug tăng đáng kể. Chỉ cần đọc trace là có thể xác định lỗi nằm ở retrieval, policy hay synthesis.

**Trường hợp multi-agent KHÔNG giúp ích hoặc làm chậm hệ thống:**

Đối với các câu hỏi đơn giản chỉ cần một tài liệu, multi-agent không cải thiện đáng kể chất lượng câu trả lời nhưng làm tăng số lượng thành phần cần bảo trì.

---

## 5. Phân công và đánh giá nhóm

**Phân công thực tế:**

| Thành viên    | Phần đã làm                                   | Sprint     |
| ------------- | --------------------------------------------- | ---------- |
| Mai Minh Tùng | Supervisor, Workers, MCP, Evaluation, Reports | Sprint 1–4 |

**Điều nhóm làm tốt:**

Thực hiện debug theo hướng module hóa, kiểm thử độc lập từng worker trước khi tích hợp toàn pipeline.

**Điều nhóm làm chưa tốt hoặc gặp vấn đề về phối hợp:**

Do làm việc cá nhân nên khối lượng công việc lớn, việc hoàn thiện semantic retrieval chưa đạt như thiết kế ban đầu.

**Nếu làm lại, nhóm sẽ thay đổi gì trong cách tổ chức?**

Sẽ ưu tiên hoàn thiện ChromaDB indexing ngay từ đầu thay vì bổ sung fallback ở giai đoạn cuối.

---

## 6. Nếu có thêm 1 ngày, nhóm sẽ làm gì?

Nhóm sẽ triển khai semantic retrieval hoàn chỉnh với ChromaDB và embedding model thay cho file-based fallback hiện tại. Trace cho thấy pipeline orchestration đã hoạt động ổn định, do đó retrieval là thành phần có tiềm năng cải thiện chất lượng câu trả lời lớn nhất trong tương lai.

---


