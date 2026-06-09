# Báo Cáo Cá Nhân — Lab Day 09: Multi-Agent Orchestration

**Họ và tên:** Mai Minh Tùng – 2A202600923
**Vai trò trong nhóm:** Supervisor Owner / Worker Owner / MCP Owner / Trace & Docs Owner
**Ngày nộp:** 09/06/2026

---

## 1. Tôi phụ trách phần nào?

Trong buổi lab Day 09, tôi làm việc cá nhân nên chịu trách nhiệm cho toàn bộ pipeline multi-agent. Tuy nhiên, phần tôi tập trung nhiều nhất là triển khai và tích hợp các worker cùng cơ chế trace của hệ thống. Tôi trực tiếp sửa và hoàn thiện các file `workers/retrieval.py`, `workers/policy_tool.py`, `workers/synthesis.py`, `mcp_server.py` và `eval_trace.py`.

**Module/file tôi chịu trách nhiệm:**

* File chính: `workers/retrieval.py`, `workers/policy_tool.py`, `workers/synthesis.py`, `mcp_server.py`, `eval_trace.py`

**Functions tôi implement:**

* `retrieve_dense()`
* `retrieve_file_fallback()`
* `analyze_policy()`
* `synthesize()`
* `_call_mcp_tool()`
* `analyze_traces()`
* `compare_single_vs_multi()`

Do làm việc độc lập nên tôi đồng thời đóng vai trò supervisor owner và trace owner. Retrieval worker tạo evidence cho policy và synthesis worker. Policy worker gọi MCP tools để kiểm tra thông tin bổ sung. Cuối cùng, synthesis worker tạo câu trả lời và eval pipeline sử dụng trace để đánh giá toàn hệ thống.

**Bằng chứng:**

Các file trên đều được chỉnh sửa trực tiếp trong quá trình debug. Trace cuối cùng cho thấy toàn bộ 15/15 test questions được xử lý thành công.

---

## 2. Tôi đã ra một quyết định kỹ thuật gì?

**Quyết định:** Sử dụng file-based fallback retrieval thay vì phụ thuộc hoàn toàn vào ChromaDB.

Ban đầu, retrieval worker được thiết kế để truy vấn ChromaDB bằng embedding. Tuy nhiên, khi chạy độc lập, hệ thống luôn trả về 0 chunks do collection chưa được index đúng cách. Tôi có hai lựa chọn: tiếp tục sửa pipeline indexing của ChromaDB hoặc xây dựng cơ chế fallback dựa trên các file `.txt` có sẵn trong thư mục `data/docs`.

Tôi quyết định triển khai file-based fallback retrieval. Cách này sử dụng keyword matching kết hợp heuristic scoring để đảm bảo retrieval worker luôn hoạt động ngay cả khi vector database chưa sẵn sàng.

**Lý do:**

Mục tiêu của buổi lab là hoàn thiện multi-agent orchestration chứ không phải tối ưu vector database. File-based fallback giúp toàn bộ pipeline tiếp tục chạy ổn định và cho phép tôi kiểm thử các worker khác.

**Trade-off đã chấp nhận:**

Độ chính xác semantic thấp hơn retrieval bằng embedding. Tuy nhiên, tính ổn định và khả năng hoàn thành bài lab được ưu tiên.

**Bằng chứng từ trace/code:**

```python
if not chunks:
    return retrieve_file_fallback(query, top_k)
```

Sau khi bổ sung fallback, retrieval worker trả về đúng sources như:

```text
Retrieved: 3 chunks
Sources: ['access_control_sop.txt',
          'it_helpdesk_faq.txt',
          'sla_p1_2026.txt']
```

---

## 3. Tôi đã sửa một lỗi gì?

**Lỗi:** Retrieval worker luôn trả về 0 chunks.

**Symptom (pipeline làm gì sai?):**

Mặc dù knowledge base đã tồn tại, mọi câu hỏi đều cho kết quả:

```text
Retrieved: 0 chunks
Sources: []
```

Điều này khiến synthesis worker không có evidence để tạo câu trả lời.

**Root cause:**

ChromaDB collection chưa được build đúng cách nên `collection.query()` không trả về dữ liệu. Lỗi nằm ở tầng retrieval chứ không phải supervisor hay synthesis.

**Cách sửa:**

Tôi bổ sung hàm `retrieve_file_fallback()` để đọc trực tiếp các file trong `data/docs`. Đồng thời sửa path bằng cách sử dụng `BASE_DIR` thay cho relative path.

**Bằng chứng trước/sau:**

Trước khi sửa:

```text
Retrieved: 0 chunks
Sources: []
```

Sau khi sửa:

```text
Retrieved: 3 chunks
[14.000] sla_p1_2026.txt ...
Sources: ['access_control_sop.txt',
          'it_helpdesk_faq.txt',
          'sla_p1_2026.txt']
```

Lỗi này ảnh hưởng trực tiếp đến toàn bộ pipeline. Sau khi khắc phục, `eval_trace.py` đạt kết quả:

```text
Done. 15 / 15 succeeded.
```

---

## 4. Tôi tự đánh giá đóng góp của mình

**Tôi làm tốt nhất ở điểm nào?**

Tôi chủ động debug từng worker độc lập thay vì sửa ngẫu nhiên trên toàn pipeline. Điều này giúp xác định nguyên nhân lỗi nhanh hơn.

**Tôi làm chưa tốt hoặc còn yếu ở điểm nào?**

Tôi chưa hoàn thành semantic retrieval bằng ChromaDB như thiết kế ban đầu. Hệ thống vẫn đang dựa vào fallback retrieval.

**Nhóm phụ thuộc vào tôi ở đâu?**

Do làm việc cá nhân, retrieval worker là thành phần quan trọng nhất. Nếu retrieval không hoạt động, policy worker và synthesis worker đều không thể tạo ra câu trả lời grounded.

**Phần tôi phụ thuộc vào thành viên khác:**

Không có, vì tôi thực hiện toàn bộ bài lab một mình.

---

## 5. Nếu có thêm 2 giờ, tôi sẽ làm gì?

Nếu có thêm thời gian, tôi sẽ hoàn thiện ChromaDB indexing và semantic retrieval. Trace cho thấy toàn bộ hệ thống đang hoạt động ổn định, nhưng retrieval vẫn dựa trên keyword fallback. Việc chuyển sang dense retrieval thực sự sẽ giúp tăng chất lượng evidence cho các câu hỏi diễn đạt phức tạp và cải thiện khả năng mở rộng của hệ thống trong tương lai.

---
