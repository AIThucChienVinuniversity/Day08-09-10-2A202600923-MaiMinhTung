"""
graph.py — Supervisor Orchestrator
Day 09 Lab: Multi-Agent Orchestration

Kiến trúc:
    Input → Supervisor → [retrieval_worker | policy_tool_worker | human_review] → synthesis → Output

Chạy:
    python graph.py
"""

import json
import os
import re
import time
from datetime import datetime
from typing import TypedDict, Literal, Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOCS_DIR = os.path.join(BASE_DIR, "data", "docs")


# ─────────────────────────────────────────────
# 1. Shared State
# ─────────────────────────────────────────────

class AgentState(TypedDict):
    task: str

    route_reason: str
    risk_high: bool
    needs_tool: bool
    hitl_triggered: bool

    retrieved_chunks: list
    retrieved_sources: list
    policy_result: dict
    mcp_tools_used: list

    final_answer: str
    sources: list
    confidence: float

    history: list
    workers_called: list
    supervisor_route: str
    latency_ms: Optional[int]
    run_id: str
    timestamp: str


def make_initial_state(task: str) -> AgentState:
    now = datetime.now().isoformat()

    return {
        "task": task,
        "route_reason": "",
        "risk_high": False,
        "needs_tool": False,
        "hitl_triggered": False,

        "retrieved_chunks": [],
        "retrieved_sources": [],
        "policy_result": {},
        "mcp_tools_used": [],

        "final_answer": "",
        "sources": [],
        "confidence": 0.0,

        "history": [],
        "workers_called": [],
        "supervisor_route": "",
        "latency_ms": None,
        "run_id": f"run_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
        "timestamp": now,
    }


# ─────────────────────────────────────────────
# 2. Supervisor Node
# ─────────────────────────────────────────────

def supervisor_node(state: AgentState) -> AgentState:
    task = state["task"].lower()
    state["history"].append(f"[supervisor] received task: {state['task'][:100]}")

    route = "retrieval_worker"
    route_reason = "default retrieval route"
    needs_tool = False
    risk_high = False

    policy_keywords = [
        "hoàn tiền",
        "refund",
        "flash sale",
        "policy",
        "license",
        "digital product",
        "sản phẩm lỗi",
        "cấp quyền",
        "access",
        "admin access",
        "level 3",
        "contractor",
    ]

    retrieval_keywords = [
        "p1",
        "sla",
        "ticket",
        "escalation",
        "2am",
        "thông báo",
        "notify",
        "helpdesk",
    ]

    risk_keywords = [
        "emergency",
        "khẩn cấp",
        "2am",
        "admin access",
        "level 3",
        "contractor",
        "err-",
        "không rõ",
    ]

    if any(kw in task for kw in policy_keywords):
        route = "policy_tool_worker"
        route_reason = "task contains policy/access/refund keyword"
        needs_tool = True

    elif any(kw in task for kw in retrieval_keywords):
        route = "retrieval_worker"
        route_reason = "task contains SLA/P1/ticket/escalation keyword"

    if any(kw in task for kw in risk_keywords):
        risk_high = True
        route_reason += " | risk_high flagged"

    if risk_high and re.search(r"\berr-[a-z0-9_-]+", task):
        route = "human_review"
        route_reason = "unknown ERR code + risk_high → human_review"

    state["supervisor_route"] = route
    state["route_reason"] = route_reason
    state["needs_tool"] = needs_tool
    state["risk_high"] = risk_high

    state["history"].append(
        f"[supervisor] route={route}; needs_tool={needs_tool}; risk_high={risk_high}; reason={route_reason}"
    )

    return state


def route_decision(
    state: AgentState,
) -> Literal["retrieval_worker", "policy_tool_worker", "human_review"]:
    return state.get("supervisor_route", "retrieval_worker")  # type: ignore


# ─────────────────────────────────────────────
# 3. Mock MCP tools
# ─────────────────────────────────────────────

class MockMCPClient:
    def __init__(self, docs_dir: str = DOCS_DIR):
        self.docs_dir = docs_dir

    def search_kb(self, query: str, top_k: int = 3) -> dict:
        chunks = []
        query_words = set(query.lower().split())

        if not os.path.exists(self.docs_dir):
            return {
                "chunks": [],
                "sources": [],
                "error": f"docs_dir not found: {self.docs_dir}",
            }

        for fname in os.listdir(self.docs_dir):
            if not fname.endswith(".txt"):
                continue

            path = os.path.join(self.docs_dir, fname)

            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()

            text_lower = text.lower()
            score = sum(1 for w in query_words if w in text_lower)

            filename_hint = 0
            if "refund" in query.lower() or "hoàn tiền" in query.lower():
                filename_hint += int("refund" in fname.lower())
            if "p1" in query.lower() or "sla" in query.lower() or "ticket" in query.lower():
                filename_hint += int("sla" in fname.lower())
            if "access" in query.lower() or "cấp quyền" in query.lower():
                filename_hint += int("access" in fname.lower())

            total_score = score + filename_hint * 5

            if total_score > 0:
                chunks.append(
                    {
                        "text": text[:1200],
                        "source": fname,
                        "score": float(total_score),
                    }
                )

        chunks = sorted(chunks, key=lambda x: x["score"], reverse=True)[:top_k]

        return {
            "chunks": chunks,
            "sources": list(dict.fromkeys([c["source"] for c in chunks])),
        }

    def get_ticket_info(self, ticket_id: str) -> dict:
        mock_tickets = {
            "P1": {
                "ticket_id": "P1",
                "priority": "critical",
                "owner": "IT On-call Engineer",
                "notify": ["Incident Manager", "Helpdesk Lead", "Service Owner"],
                "expected_response": "15 minutes",
                "expected_resolution": "4 hours",
            }
        }

        return mock_tickets.get(
            ticket_id.upper(),
            {
                "ticket_id": ticket_id,
                "status": "not_found",
            },
        )


# ─────────────────────────────────────────────
# 4. Human Review
# ─────────────────────────────────────────────

def human_review_node(state: AgentState) -> AgentState:
    state["hitl_triggered"] = True
    state["workers_called"].append("human_review")
    state["history"].append("[human_review] HITL triggered")

    state["history"].append("[human_review] auto-approved in lab mode")
    state["supervisor_route"] = "retrieval_worker"
    state["route_reason"] += " | human approved → retrieval_worker"

    return state


# ─────────────────────────────────────────────
# 5. Workers
# ─────────────────────────────────────────────

def retrieval_worker_node(state: AgentState) -> AgentState:
    state["workers_called"].append("retrieval_worker")
    state["history"].append("[retrieval_worker] called")

    client = MockMCPClient()
    result = client.search_kb(state["task"], top_k=3)

    state["retrieved_chunks"] = result.get("chunks", [])
    state["retrieved_sources"] = result.get("sources", [])

    state["history"].append(
        f"[retrieval_worker] retrieved {len(state['retrieved_chunks'])} chunks"
    )

    return state


def policy_tool_worker_node(state: AgentState) -> AgentState:
    state["workers_called"].append("policy_tool_worker")
    state["history"].append("[policy_tool_worker] called")

    client = MockMCPClient()

    kb_result = client.search_kb(state["task"], top_k=3)

    mcp_call = {
        "tool": "search_kb",
        "input": {
            "query": state["task"],
            "top_k": 3,
        },
        "output": {
            "sources": kb_result.get("sources", []),
            "num_chunks": len(kb_result.get("chunks", [])),
        },
        "timestamp": datetime.now().isoformat(),
    }

    state["mcp_tools_used"].append(mcp_call)

    if not state["retrieved_chunks"]:
        state["retrieved_chunks"] = kb_result.get("chunks", [])
        state["retrieved_sources"] = kb_result.get("sources", [])

    task = state["task"].lower()

    exceptions = []
    policy_name = "general_policy"

    if "flash sale" in task:
        policy_name = "refund_policy_v4"
        exceptions.append("flash_sale_case")

    if "digital" in task or "license" in task:
        policy_name = "refund_policy_v4"
        exceptions.append("digital_or_license_product_case")

    if "access" in task or "cấp quyền" in task or "level 3" in task:
        policy_name = "access_control_sop"
        exceptions.append("temporary_admin_access_requires_approval")

    if "p1" in task or "ticket" in task:
        ticket_result = client.get_ticket_info("P1")

        state["mcp_tools_used"].append(
            {
                "tool": "get_ticket_info",
                "input": {
                    "ticket_id": "P1",
                },
                "output": ticket_result,
                "timestamp": datetime.now().isoformat(),
            }
        )

    state["policy_result"] = {
        "policy_applies": True,
        "policy_name": policy_name,
        "exceptions_found": exceptions,
        "sources": kb_result.get("sources", []),
        "summary": "Policy worker checked task against KB through mock MCP tools.",
    }

    state["history"].append(
        f"[policy_tool_worker] policy={policy_name}; exceptions={exceptions}"
    )

    return state


def synthesis_worker_node(state: AgentState) -> AgentState:
    state["workers_called"].append("synthesis_worker")
    state["history"].append("[synthesis_worker] called")

    chunks = state.get("retrieved_chunks", [])
    policy = state.get("policy_result", {})

    answer_parts = []

    if chunks:
        answer_parts.append("Dựa trên các tài liệu tìm được:")

        for i, chunk in enumerate(chunks, start=1):
            text = chunk.get("text", "").strip().replace("\n", " ")
            source = chunk.get("source", "unknown")

            short_text = text[:350]
            answer_parts.append(f"[{i}] {short_text}... (Nguồn: {source})")

    if policy:
        answer_parts.append("")
        answer_parts.append("Kết quả kiểm tra policy:")

        policy_name = policy.get("policy_name", "unknown_policy")
        exceptions = policy.get("exceptions_found", [])

        answer_parts.append(f"- Policy áp dụng: {policy_name}")

        if exceptions:
            answer_parts.append(f"- Exception/edge case: {', '.join(exceptions)}")
        else:
            answer_parts.append("- Không phát hiện exception đặc biệt.")

    if not chunks and not policy:
        answer_parts.append(
            "Không tìm thấy bằng chứng đủ rõ trong knowledge base. Cần human review."
        )
        state["confidence"] = 0.35

    else:
        base_confidence = 0.75

        if chunks:
            base_confidence += 0.1

        if policy:
            base_confidence += 0.05

        if state.get("risk_high"):
            base_confidence -= 0.1

        state["confidence"] = max(0.0, min(base_confidence, 0.95))

    state["final_answer"] = "\n".join(answer_parts)
    state["sources"] = list(
        dict.fromkeys(
            state.get("retrieved_sources", [])
            + policy.get("sources", [])
        )
    )

    state["history"].append(
        f"[synthesis_worker] answer generated; confidence={state['confidence']}"
    )

    return state


# ─────────────────────────────────────────────
# 6. Build Graph
# ─────────────────────────────────────────────

def build_graph():
    def run(state: AgentState) -> AgentState:
        start = time.time()

        state = supervisor_node(state)
        route = route_decision(state)

        if route == "human_review":
            state = human_review_node(state)
            state = retrieval_worker_node(state)

        elif route == "policy_tool_worker":
            state = policy_tool_worker_node(state)

            if not state["retrieved_chunks"]:
                state = retrieval_worker_node(state)

        else:
            state = retrieval_worker_node(state)

        state = synthesis_worker_node(state)

        state["latency_ms"] = int((time.time() - start) * 1000)
        state["history"].append(f"[graph] completed in {state['latency_ms']}ms")

        return state

    return run


_graph = build_graph()


# ─────────────────────────────────────────────
# 7. Public API
# ─────────────────────────────────────────────

def run_graph(task: str) -> AgentState:
    state = make_initial_state(task)
    return _graph(state)


def save_trace(state: AgentState, output_dir: str = None) -> str:
    if output_dir is None:
        output_dir = os.path.join(BASE_DIR, "artifacts", "traces")

    os.makedirs(output_dir, exist_ok=True)
    filename = f"{output_dir}/{state['run_id']}.json"

    trace = {
        "run_id": state["run_id"],
        "task": state["task"],
        "supervisor_route": state["supervisor_route"],
        "route_reason": state["route_reason"],
        "workers_called": state["workers_called"],
        "mcp_tools_used": state["mcp_tools_used"],
        "retrieved_sources": state["retrieved_sources"],
        "final_answer": state["final_answer"],
        "confidence": state["confidence"],
        "hitl_triggered": state["hitl_triggered"],
        "latency_ms": state["latency_ms"],
        "timestamp": state["timestamp"],
        "history": state["history"],
    }

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(trace, f, ensure_ascii=False, indent=2)

    return filename


# ─────────────────────────────────────────────
# 8. Manual Test
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("Day 09 Lab — Supervisor-Worker Graph")
    print("=" * 60)

    test_queries = [
        "SLA xử lý ticket P1 là bao lâu?",
        "Khách hàng Flash Sale yêu cầu hoàn tiền vì sản phẩm lỗi — được không?",
        "Cần cấp quyền Level 3 để khắc phục P1 khẩn cấp. Quy trình là gì?",
        "Ticket P1 lúc 2am — escalation xảy ra thế nào và ai nhận thông báo?",
        "ERR-778 không rõ khi cấp quyền admin khẩn cấp",
    ]

    for query in test_queries:
        print(f"\n▶ Query: {query}")

        result = run_graph(query)

        print(f"  Route      : {result['supervisor_route']}")
        print(f"  Reason     : {result['route_reason']}")
        print(f"  Workers    : {result['workers_called']}")
        print(f"  MCP tools  : {[x['tool'] for x in result['mcp_tools_used']]}")
        print(f"  Sources    : {result['sources']}")
        print(f"  Confidence : {result['confidence']}")
        print(f"  Latency    : {result['latency_ms']}ms")
        print(f"  Answer     : {result['final_answer'][:200]}...")

        trace_file = save_trace(result)
        print(f"  Trace saved → {trace_file}")

    print("\n✅ graph.py completed.")