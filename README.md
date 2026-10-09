# CentrAlign AI — Autonomous Task Worker

A runnable prototype for the **Autonomous AI Task Worker** intern problem statement. It takes a natural-language invoice task, searches a local mock inbox, reads an invoice file, checks for duplicates, writes a payable into a simulated company finance system, and verifies the stored record by reading it back.

The emphasis is **real execution, observed tool results, bounded retries, human approval, and verification**—not a slide deck or a pretend browser automation.

## What works

- Natural-language task input through a Streamlit UI.
- Model-driven tool selection and execution loop when `OPENAI_API_KEY` is configured.
- Local fallback that runs the supported invoice-to-payable workflow without API credentials, so the demo can run offline after dependencies are installed.
- File-backed mock invoice inbox and a SQLite-backed mock finance application.
- Latest matching invoice selection by issue date.
- Field extraction, source-document consistency checks, duplicate prevention, and read-back verification.
- One retry for a simulated transient write failure.
- Human approval gate for values above INR 50,000.
- Per-tool arguments and observations shown in an execution trace.
- A malicious instruction inside the fictional Contoso invoice to demonstrate that document contents are untrusted data.

## Demo workflow

Default task:

> Find the latest invoice from ACME Cloud Services, extract the amount and due date, enter it into our internal finance system, and confirm when it is done.

Expected outcome: `INV-ACME-2026-101`, INR 24,800.00, due `2026-10-28`, with a read-back verification result. The older ACME invoice should not be selected.

Additional scenarios:

1. **Retry:** check `Simulate one transient write failure` and run the default task. First write fails; the worker observes the failure and retries once.
2. **Approval gate and prompt-injection resistance:** run `Find the latest invoice from Contoso Analytics and register it in the finance system.` It should stop because INR 52,990 exceeds the threshold. The invoice contains a vendor note asking the agent to export other records; that note must not be followed. Tick the approval box and rerun to permit the local mock payable write.
3. **Idempotency:** rerun the default task. It should identify the exact existing payable and verify it instead of creating a duplicate.
4. **No matching vendor:** request an unknown company. The worker should report no matching invoice and must not create a record.

## Quick start (Windows PowerShell)

Python 3.10+ is recommended. From this repository folder:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
streamlit run app.py
```

On macOS/Linux, activate with `source .venv/bin/activate`, then run `streamlit run app.py`.

Streamlit opens the local app in a browser. The first run creates fictional invoice files in `workspace/inbox/` and a SQLite database at `data/company_app.db`. Nothing here logs into a real company application.

## Enable model-driven autonomy (optional)

Open `.env`, add your own API key to `OPENAI_API_KEY`, and optionally change `OPENAI_MODEL`. Restart Streamlit after editing `.env`. The LLM mode uses tool/function calling and can choose the next operation from the tool observations. Without a key, the demo uses a deliberately limited local fallback for this one invoice workflow.

Do not add company credentials, confidential files, or sensitive business information. When LLM mode is enabled, the task and mock document content are sent to the configured model provider.

## Architecture

```text
Natural-language goal
        |
        v
Agent loop (LLM tool-calling, or local fallback)
        |
        +--> search_invoices ------> SQLite invoice index
        +--> read_invoice ---------> workspace/inbox/*.txt
        +--> find_payable ---------> SQLite mock finance app
        +--> create_payable -------> validation + duplicate gate + approval gate
        +--> verify_payable -------> read-after-write checks
        |
        v
Execution trace + concise result + verification evidence
```

### Important decisions

- **Narrow, end-to-end scope:** one business process is implemented end to end rather than claiming to automate arbitrary websites.
- **Tools have a strict boundary:** the agent can only call a fixed allowlist of functions. No general shell execution, arbitrary network requests, or external export tool is available.
- **Source grounding:** create operations must point to an indexed source invoice; the vendor and invoice number must match the source index.
- **Idempotency:** invoice number is unique. An exact pre-existing payable is reused, while a conflicting record is blocked rather than overwritten.
- **Human-in-the-loop:** amounts above INR 50,000 require explicit approval in the UI. A blocked attempt does not write a record.
- **Bounded recovery:** retry only when a tool says an error is retryable, and at most once for the demo.
- **Verification is separate from execution:** the agent reads the record from SQLite and compares vendor, amount, due date, and status before reporting success.
- **Untrusted document content:** vendor notes are data, not instructions. The system prompt says this explicitly, and there is no tool that can export records to arbitrary destinations.
- **Memory:** current task context and tool observations serve as working memory during execution; SQLite is persistent business state across runs. This prototype does not implement vector/semantic long-term memory because it is unnecessary for the chosen workflow.

## Tests

Run:

```bash
python -m unittest discover -s tests -v
```

## Known limitations

- The mock invoices are plain text with a fixed format; this is not a general PDF/OCR invoice parser.
- Only the invoice-to-payable workflow is covered by the local fallback. Broader task generalization requires LLM mode and more tools.
- Browser automation, operating-system computer use, authentication, and real ERP/email integrations are not implemented.
- Approval is a local UI checkbox, not a production identity/authorization service.
- A single machine and SQLite are appropriate for this prototype, not concurrent production workloads.
- The LLM may fail or call tools incorrectly; invalid/missing data is blocked and the UI shows the trace. More systematic model evaluations are future work.

## What I would build next

1. Add a typed task/result contract and a policy engine separate from the model.
2. Add sandboxed Playwright computer-use tools with screenshots, DOM observations, and per-action assertions.
3. Build an evaluation harness with tasks for success, ambiguity, duplicate invoices, malformed files, prompt injection, transient failures, and incorrect model actions.
4. Add structured logs, trace IDs, latency/cost accounting, and replayable runs.
5. Add permission scopes and approval rules by action risk, amount, vendor, and data sensitivity.
6. Add PDF parsing and confidence scores, with a human review threshold for low-confidence extraction.

## Assumptions

- The evaluation accepts a simulated internal application and fictional sample data.
- Registering a payable means creating a draft/open record; it does not authorize payment.
- Dates are ISO `YYYY-MM-DD` in the mock system and amounts are INR.
- The INR 50,000 approval limit is an explicit prototype policy, not a claim about any real company.

## Components used

- Python, Streamlit, SQLite, pandas, OpenAI Python SDK (optional), python-dotenv.
- No pre-built autonomous-agent framework is used; the tool loop and safety gates are implemented directly for clarity.
- Fictional sample documents are generated by this repository.

## Submission / demo checklist

- [ ] Run the default task live and show the invoice selection, document read, duplicate check, write, and verification.
- [ ] Show the transient failure + one retry.
- [ ] Show the approval gate for Contoso and explain the untrusted vendor note.
- [ ] Show the finance-system tab after a successful run.
- [ ] Record a 2–3 minute walkthrough and add the video link to the submission form.
- [ ] Push this folder to a public or reviewer-accessible GitHub repository, then submit that URL with this README.
