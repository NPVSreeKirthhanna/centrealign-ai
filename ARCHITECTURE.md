# Architecture and design notes

## Execution loop

The LLM-enabled path sends the user goal plus a fixed list of tools to a chat-completions model. Each model tool call is executed in `ToolBox`, and the structured observation is appended back to the conversation. The loop stops after a final answer, approval gate, or 12 model turns. Completion is determined from successful `verify_payable` evidence, not from the text of the final answer.

The no-key fallback runs a constrained plan for the demo workflow: infer vendor, search newest-first, read the selected source document, extract required fields, check for an existing payable, create when safe, retry a retryable write failure once, and verify. This fallback is not presented as a general reasoning system; it is a reliable path to demo without credentials.

## Reliability invariants

1. No create without a source invoice ID in the index.
2. Extracted vendor and invoice number must agree with source-index metadata.
3. Invoice number is unique; existing exact records are reused; conflicting records are blocked.
4. Invalid dates, negative amounts, and missing fields are rejected.
5. Values above the configured threshold are not written without approval.
6. Transient errors can be retried once; validation errors are not retried.
7. Reported completion requires read-back verification of vendor, amount, due date, and open status.

## Threat-model notes

- Tool set is allowlisted; no shell, arbitrary network, payment, or data-export tool is exposed.
- Document text is untrusted and may contain prompt injection attempts.
- Demo uses fictional data and a local database. API-enabled mode sends the current task/tool context to the configured model provider; users must not supply confidential data.
- This is a prototype, not a secure multi-user production service. It has no identity system, audit retention guarantees, or tenant isolation.
