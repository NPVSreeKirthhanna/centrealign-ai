# 2–3 minute demo script

## 0:00–0:20 — Set up the problem
"This is a narrow autonomous worker. I'm giving it the business outcome rather than step-by-step instructions. It can inspect files, write to a mock finance system, and verify the write."

## 0:20–1:00 — Happy path
Run the default ACME task. Expand the trace and narrate: search results are newest-first; it reads the selected file; checks for duplicates; writes the payable; reads it back and checks amount/vendor/due date/status. Open the Mock finance system tab to show the actual record.

## 1:00–1:30 — Reliability
Reset demo records, tick "Simulate one transient write failure", and run the default task. Show that the first write returns a retryable error, the worker retries once, and verification is only successful after the record exists.

## 1:30–2:10 — Safety and human approval
Run the Contoso task. Explain that the amount crosses the demo's INR 50,000 approval threshold, so the first attempt stops without writing. Point out the malicious vendor note asks to export other records; document text is untrusted and the worker has no export tool. Approve and rerun only to demonstrate the gated mock write.

## 2:10–2:40 — Engineering choices
Explain source-document checks, unique invoice numbers, duplicate prevention, fixed tool allowlist, traceability, and the separate read-back verification. Close with current limitations: text invoices, SQLite, mock app, and no arbitrary browser/desktop automation yet.
