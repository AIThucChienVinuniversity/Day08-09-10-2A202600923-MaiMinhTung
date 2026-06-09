# System Architecture — Lab Day 09

**Nhóm:** Mai Minh Tùng - 2A202600923
**Ngày:** 09/06/2026
**Version:** 1.0

---

## 1. Tổng quan kiến trúc

**Pattern đã chọn:** Supervisor-Worker

**Lý do chọn pattern này (thay vì single agent):**

Nhóm chọn kiến trúc Supervisor-Worker để tách hệ thống RAG thành nhiều thành phần có vai trò rõ ràng. Thay vì để một agent vừa retrieve, vừa kiểm tra policy, vừa tổng hợp câu trả lời, hệ thống Day 09 chia thành supervisor và các worker chuyên biệt. Cách này giúp dễ debug, dễ quan sát routing decision, dễ thêm MCP tools và dễ kiểm thử từng phần độc lập.

---

## 2. Sơ đồ Pipeline

**Sơ đồ thực tế của nhóm:**

```text
User Request
     │
     ▼
┌────────────────────┐
│    Supervisor      │
│ graph.py           │
│ route_reason       │
│ risk_high          │
│ needs_tool         │
└─────────┬──────────┘
          │
          ▼
   route_decision()
          │
 ┌────────┼──────────────────────┐
 │        │                      │
 ▼        ▼                      ▼
Retrieval Worker       Policy Tool Worker       Human Review
retrieval.py           policy_tool.py           HITL placeholder
evidence chunks        policy check + MCP       auto-approve lab mode
 │                     │
 │                     ├── MCP Server
 │                     │   ├── search_kb
 │                     │   ├── get_ticket_info
 │                     │   ├── check_access_permission
 │                     │   └── create_ticket
 │                     │
 └───────────┬─────────┘
             ▼
      Synthesis Worker
      synthesis.py
      answer + citation
             │
             ▼
      Final Answer + Trace
```

---

## 3. Vai trò từng thành phần

### Supervisor (`graph.py`)

| Thuộc tính         | Mô tả                                                                                                                                       |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------- |
| **Nhiệm vụ**       | Nhận câu hỏi đầu vào, phân tích keyword, xác định rủi ro và chọn worker phù hợp.                                                            |
| **Input**          | `task` từ user                                                                                                                              |
| **Output**         | `supervisor_route`, `route_reason`, `risk_high`, `needs_tool`                                                                               |
| **Routing logic**  | Rule-based routing dựa trên keyword: SLA/P1/ticket → retrieval; refund/access/policy → policy_tool; lỗi không rõ + risk cao → human_review. |
| **HITL condition** | Khi truy vấn có mã lỗi không rõ như `ERR-*` và đồng thời bị đánh dấu `risk_high`.                                                           |

### Retrieval Worker (`workers/retrieval.py`)

| Thuộc tính          | Mô tả                                                                                                        |
| ------------------- | ------------------------------------------------------------------------------------------------------------ |
| **Nhiệm vụ**        | Truy xuất evidence chunks từ knowledge base nội bộ.                                                          |
| **Embedding model** | Có hỗ trợ `all-MiniLM-L6-v2`, nhưng bản chạy thực tế dùng file-based fallback do ChromaDB chưa index đầy đủ. |
| **Top-k**           | 3                                                                                                            |
| **Stateless?**      | Yes                                                                                                          |

### Policy Tool Worker (`workers/policy_tool.py`)

| Thuộc tính                | Mô tả                                                                                |
| ------------------------- | ------------------------------------------------------------------------------------ |
| **Nhiệm vụ**              | Kiểm tra policy, phát hiện exception và gọi MCP tools khi cần.                       |
| **MCP tools gọi**         | `search_kb`, `get_ticket_info`                                                       |
| **Exception cases xử lý** | Flash Sale, digital product/license key, activated product, access level escalation. |

### Synthesis Worker (`workers/synthesis.py`)

| Thuộc tính             | Mô tả                                                                                    |
| ---------------------- | ---------------------------------------------------------------------------------------- |
| **LLM model**          | Có hỗ trợ OpenAI/Gemini nếu có API key; bản thực tế dùng offline fallback synthesis.     |
| **Temperature**        | 0.1 nếu dùng LLM                                                                         |
| **Grounding strategy** | Chỉ tổng hợp từ `retrieved_chunks` và `policy_result`, kèm citation theo source file.    |
| **Abstain condition**  | Nếu không có context hoặc chunks thì trả lời “Không đủ thông tin trong tài liệu nội bộ”. |

### MCP Server (`mcp_server.py`)

| Tool                    | Input                                      | Output                                   |
| ----------------------- | ------------------------------------------ | ---------------------------------------- |
| search_kb               | query, top_k                               | chunks, sources                          |
| get_ticket_info         | ticket_id                                  | ticket details                           |
| check_access_permission | access_level, requester_role, is_emergency | can_grant, approvers, emergency_override |
| create_ticket           | priority, title, description               | mock ticket_id, url, created_at          |

---

## 4. Shared State Schema

| Field             | Type  | Mô tả                           | Ai đọc/ghi                      |
| ----------------- | ----- | ------------------------------- | ------------------------------- |
| task              | str   | Câu hỏi đầu vào                 | supervisor đọc                  |
| supervisor_route  | str   | Worker được chọn                | supervisor ghi                  |
| route_reason      | str   | Lý do route                     | supervisor ghi                  |
| risk_high         | bool  | Đánh dấu truy vấn rủi ro cao    | supervisor ghi, synthesis đọc   |
| needs_tool        | bool  | Có cần gọi MCP tool không       | supervisor ghi, policy_tool đọc |
| hitl_triggered    | bool  | Có kích hoạt human review không | human_review ghi                |
| retrieved_chunks  | list  | Evidence từ retrieval           | retrieval ghi, synthesis đọc    |
| retrieved_sources | list  | Danh sách file nguồn            | retrieval/policy_tool ghi       |
| policy_result     | dict  | Kết quả kiểm tra policy         | policy_tool ghi, synthesis đọc  |
| mcp_tools_used    | list  | Tool calls đã thực hiện         | policy_tool ghi                 |
| final_answer      | str   | Câu trả lời cuối                | synthesis ghi                   |
| confidence        | float | Mức tin cậy                     | synthesis ghi                   |
| workers_called    | list  | Chuỗi worker đã chạy            | từng worker ghi                 |
| history           | list  | Log từng bước xử lý             | tất cả component ghi            |
| latency_ms        | int   | Thời gian xử lý                 | graph ghi                       |
| run_id            | str   | ID của lần chạy                 | graph khởi tạo                  |

---

## 5. Lý do chọn Supervisor-Worker so với Single Agent (Day 08)

| Tiêu chí            | Single Agent (Day 08)    | Supervisor-Worker (Day 09)        |
| ------------------- | ------------------------ | --------------------------------- |
| Debug khi sai       | Khó — không rõ lỗi ở đâu | Dễ hơn — test từng worker độc lập |
| Thêm capability mới | Phải sửa toàn prompt     | Thêm worker/MCP tool riêng        |
| Routing visibility  | Không có                 | Có route_reason trong trace       |
| Tool integration    | Hard-code vào pipeline   | Gọi qua MCP server                |
| Observability       | Hạn chế                  | Có trace, history, workers_called |

**Nhóm điền thêm quan sát từ thực tế lab:**

Trong quá trình chạy lab, retrieval worker ban đầu trả về 0 chunks do ChromaDB chưa được index. Nhờ tách riêng worker, nhóm debug được lỗi nhanh bằng cách chạy độc lập `python lab/workers/retrieval.py`, sau đó bổ sung file-based fallback retrieval. Nếu dùng single-agent, lỗi này khó phát hiện hơn vì retrieval, policy và synthesis bị gộp chung trong một pipeline.

---

## 6. Giới hạn và điểm cần cải tiến

1. Routing hiện tại vẫn dựa trên keyword matching nên có thể sai với câu hỏi diễn đạt phức tạp hoặc không chứa keyword rõ ràng.
2. Retrieval hiện đang dùng file-based fallback, chưa tận dụng đầy đủ semantic search từ ChromaDB.
3. MCP server hiện là mock in-process, chưa phải MCP server thật qua HTTP hoặc MCP protocol chính thức.
4. Synthesis offline fallback còn đơn giản, chưa có LLM-as-Judge để đánh giá chất lượng câu trả lời.
5. Human-in-the-Loop mới là placeholder, chưa có giao diện hoặc cơ chế phê duyệt thật.
