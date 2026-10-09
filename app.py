from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from worker import AutonomousWorker, get_payables, reset_demo_data

ROOT = Path(__file__).resolve().parent
DEFAULT_TASK = "Find the latest invoice from ACME Cloud Services, extract the amount and due date, enter it into our internal finance system, and confirm when it is done."

st.set_page_config(page_title="CentrAlign AI | Autonomous Task Worker", page_icon="⚙️", layout="wide")
st.markdown("""
<style>
.block-container {padding-top: 1.4rem; padding-bottom: 2rem; max-width: 1200px;}
.hero {padding: 1.25rem 1.4rem; border: 1px solid rgba(128,128,128,.3); border-radius: 16px; margin-bottom: 1rem;}
.small-muted {font-size: .9rem; opacity: .78;}
.trace-card {border: 1px solid rgba(128,128,128,.25); border-radius: 10px; padding: .8rem 1rem; margin: .35rem 0;}
</style>
""", unsafe_allow_html=True)

st.title("Autonomous AI Task Worker")
st.caption("CentrAlign AI · Prototype · Local mock company environment")
with st.container(border=True):
    st.markdown("**The task:** Give the worker an outcome, not a list of clicks. It selects tools, observes results, handles a retry, and verifies the finance-system record before reporting success.")
    st.markdown('<span class="small-muted">Safety boundary: fictional invoices + local SQLite only. No real company credentials or external business systems.</span>', unsafe_allow_html=True)

col_a, col_b, col_c = st.columns(3)
with col_a:
    st.metric("Execution engine", "Local fallback")
with col_b:
    st.metric("Model", "Disabled")
with col_c:
    st.metric("Approval threshold", "INR 50,000")
st.info("LLM mode is disabled in this app. Tasks use the local invoice-to-payable fallback; OPENAI_API_KEY is not used.")

worker_tab, finance_tab, design_tab = st.tabs(["Run a task", "Mock finance system", "Design notes"])
with worker_tab:
    task = st.text_area("Natural-language task", value=DEFAULT_TASK, height=105, help="Be explicit about the outcome and vendor. The agent decides the steps.")
    c1, c2 = st.columns(2)
    with c1:
        simulate_failure = st.checkbox("Simulate one transient write failure", value=False, help="The first write will fail once; the worker should observe the error and retry once.")
    with c2:
        approve_high_value = st.checkbox("Approve writes above INR 50,000 for this run", value=False, help="Human approval gate for high-value payables. The default is to stop without writing.")
    run = st.button("Run autonomous worker", type="primary", use_container_width=True)
    if run:
        worker = AutonomousWorker(
            base_dir=ROOT,
            approval_granted=approve_high_value,
            fail_next_write=simulate_failure,
            use_llm=False,
        )
        result = worker.run(task)
        st.session_state["last_result"] = {
            "status": result.status,
            "summary": result.summary,
            "task": result.task,
            "events": result.events,
            "evidence": result.evidence,
            "mode": result.mode,
            "pending_approval": result.pending_approval,
            "raw_final": result.raw_final,
        }

    result = st.session_state.get("last_result")
    if result:
        st.divider()
        st.subheader("Outcome")
        status = result["status"]
        if status == "completed":
            st.success(result["summary"])
        elif status == "needs_approval":
            st.warning(result["summary"])
            st.markdown("Tick **Approve writes above INR 50,000 for this run** and run the same task again to proceed. No record was created in this run.")
            if result.get("pending_approval"):
                st.json(result["pending_approval"])
        elif status in ("blocked", "failed"):
            st.error(result["summary"])
        else:
            st.info(result["summary"])
        st.caption(f"Execution mode: {result['mode']} · Final status: {status}")
        if result.get("evidence"):
            with st.expander("Verification evidence", expanded=(status == "completed")):
                st.json(result["evidence"])
        st.subheader(f"Execution trace ({len(result['events'])} tool calls)")
        if not result["events"]:
            st.caption("No tools were executed; the worker requested more detail or could not start.")
        for idx, event in enumerate(result["events"], start=1):
            icon = "✓" if event["ok"] else "!"
            title = f"{idx}. {event['tool']} · {event['time']} · {'success' if event['ok'] else 'observed failure / gate'}"
            with st.expander(title, expanded=(not event["ok"])):
                st.markdown("**Arguments**")
                st.json(event["arguments"])
                st.markdown("**Observation returned to the agent**")
                st.json(event["observation"])
        if result.get("raw_final"):
            with st.expander("LLM final message"):
                st.write(result["raw_final"])

with finance_tab:
    st.subheader("Mock Accounts Payable")
    st.caption("These records live in data/company_app.db. They are fictional and can be reset at any time.")
    payables = get_payables(ROOT)
    if payables:
        df = pd.DataFrame(payables)
        df["amount"] = df["amount"].map(lambda v: f"{v:,.2f}")
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No payable records yet. Run a task in the first tab to create one.")
    if st.button("Reset demo finance records", help="Deletes demo payables and re-seeds the fictional invoice inbox."):
        reset_demo_data(ROOT)
        st.session_state.pop("last_result", None)
        st.success("Demo database reset.")
        st.rerun()

with design_tab:
    st.subheader("Architecture at a glance")
    st.markdown("""
    1. **Goal intake** — user provides the intended outcome in natural language.
    2. **Agent loop** — this app uses a narrow local fallback for the invoice-to-payable demo workflow. LLM mode is disabled.
    3. **Tools** — invoice search, file read, duplicate check, payable create, read-back verification, and payable listing.
    4. **State and memory** — the agent carries the task, previous tool observations, and invoice ID/fields in its context; SQLite stores business records between runs.
    5. **Reliability** — schema/date/amount checks, source-document matching, duplicate prevention, one retry on a transient write error, a high-value approval gate, and post-write verification.
    6. **Evidence** — every tool call and observation is shown in the execution trace; completion depends on a successful verification result, not the LLM's wording.

    **Deliberate scope limit:** this prototype uses text-based fictional invoices and a local mock finance system instead of automating a real browser or ERP. The goal is to prove a real end-to-end task with explicit safety boundaries, not to claim universal computer use.
    """)
    st.subheader("Useful demo tasks")
    st.code('Find the latest invoice from ACME Cloud Services, extract the amount and due date, enter it into our internal finance system, and confirm when it is done.')
    st.code('Find the latest invoice from Contoso Analytics and register it in the finance system.')
    st.caption("Contoso's mock invoice contains a malicious instruction in its vendor note. The agent must treat it as untrusted document text. Its INR 52,990 amount also triggers the approval gate.")

st.divider()
st.caption("Prototype notes: no real credentials, no live external integrations, and no payment execution. Invoice creation only writes to the local mock database.")
