# Routing Decisions Log — Lab Day 09

**Nhóm:** Mai Minh Tùng - 2A202600923
**Ngày:** 09/06/2026

> **Hướng dẫn:** Ghi lại ít nhất **3 quyết định routing** thực tế từ trace của nhóm.
> Không ghi giả định — phải từ trace thật (`artifacts/traces/`).

---

## Routing Decision #1

**Task đầu vào:**

> SLA xử lý ticket P1 là bao lâu?

**Worker được chọn:** `retrieval_worker`
**Route reason (từ trace):** `task contains SLA/P1/ticket/escalation keyword`
**MCP tools được gọi:** Không có
**Workers called sequence:** `retrieval_worker → synthesis_worker`

**Kết quả thực tế:**

* final_answer (ngắn): Ticket P1 yêu cầu phản hồi ban đầu trong vòng 15 phút và phải được xử lý trong 4 giờ.
* confidence: `0.85`
* Correct routing? **Yes**

**Nhận xét:** Routing này phù hợp vì câu hỏi chỉ yêu cầu truy xuất thông tin từ tài liệu SLA, không cần kiểm tra policy hay gọi MCP tools.

---

## Routing Decision #2

**Task đầu vào:**

> Sản phẩm kỹ thuật số (license key) có được hoàn tiền không?

**Worker được chọn:** `policy_tool_worker`
**Route reason (từ trace):** `task contains policy/access/refund keyword`
**MCP tools được gọi:** `search_kb`
**Workers called sequence:** `policy_tool_worker → synthesis_worker`

**Kết quả thực tế:**

* final_answer (ngắn): License key thuộc nhóm sản phẩm kỹ thuật số và không được hoàn tiền theo chính sách hiện hành.
* confidence: `0.90`
* Correct routing? **Yes**

**Nhận xét:** Supervisor đã nhận diện đúng đây là câu hỏi liên quan đến chính sách hoàn tiền và chuyển sang policy worker để xử lý các ngoại lệ nghiệp vụ.

---

## Routing Decision #3

**Task đầu vào:**

> Contractor cần Admin Access (Level 3) để khắc phục sự cố P1 đang diễn ra.

**Worker được chọn:** `policy_tool_worker`
**Route reason (từ trace):** `task contains policy/access/refund keyword | risk_high flagged`
**MCP tools được gọi:** `search_kb`, `get_ticket_info`
**Workers called sequence:** `policy_tool_worker → synthesis_worker`

**Kết quả thực tế:**

* final_answer (ngắn): Contractor muốn được cấp quyền Level 3 phải tuân thủ quy trình phê duyệt đầy đủ; không tồn tại emergency bypass cho Level 3.
* confidence: `0.80`
* Correct routing? **Yes**

**Nhận xét:** Đây là trường hợp kết hợp giữa policy và yếu tố rủi ro cao. Việc đánh dấu `risk_high` giúp tăng độ an toàn của hệ thống.

---

## Routing Decision #4 (tuỳ chọn — bonus)

**Task đầu vào:**

> ERR-403-AUTH là lỗi gì và cách xử lý?

**Worker được chọn:** `retrieval_worker`
**Route reason:** `retrieval route selected based on error troubleshooting context`

**Nhận xét: Đây là trường hợp routing khó nhất trong lab. Tại sao?**

Mã lỗi có thể yêu cầu tra cứu tài liệu kỹ thuật hoặc kích hoạt Human-in-the-Loop nếu liên quan đến thao tác nguy hiểm. Việc xác định đúng mức độ rủi ro của truy vấn là thách thức lớn trong thiết kế supervisor.

---

# Tổng kết

## Routing Distribution

| Worker             | Số câu được route | % tổng |
| ------------------ | ----------------- | ------ |
| retrieval_worker   | 8                 | 53%    |
| policy_tool_worker | 7                 | 47%    |
| human_review       | 0                 | 0%     |

## Routing Accuracy

> Trong số 15 câu nhóm đã chạy, supervisor đã route phù hợp cho tất cả các trường hợp.

* Câu route đúng: **15 / 15**
* Câu route sai (đã sửa bằng cách nào?): **0**
* Câu trigger HITL: **0**

## Lesson Learned về Routing

> Quyết định kỹ thuật quan trọng nhất được đưa ra trong phần routing logic.

1. Sử dụng **keyword-based routing kết hợp risk flag** thay vì gọi LLM classifier cho mọi truy vấn để giảm chi phí và tăng tính ổn định.
2. Thiết kế **worker chuyên biệt** giúp việc kiểm thử, mở rộng và debug trở nên dễ dàng hơn so với kiến trúc single-agent.

## Route Reason Quality

> Nhìn lại các `route_reason` trong trace — chúng có đủ thông tin để debug không?

Các `route_reason` hiện tại đã giúp xác định được lý do supervisor chọn worker tương ứng. Tuy nhiên, nhóm đề xuất cải tiến bằng cách bổ sung:

* Danh sách keyword cụ thể kích hoạt route.
* Điểm rủi ro (risk score).
* Danh sách candidate workers trước khi supervisor đưa ra quyết định cuối cùng.

Những cải tiến này sẽ giúp quá trình phân tích trace minh bạch và dễ bảo trì hơn trong các hệ thống multi-agent quy mô lớn.
