import tempfile
import unittest
from pathlib import Path

from worker import AutonomousWorker, ToolBox, get_payables, reset_demo_data

DEFAULT_TASK = "Find the latest invoice from ACME Cloud Services, extract the amount and due date, enter it into our internal finance system, and confirm when it is done."


class AutonomousWorkerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        reset_demo_data(self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def run_worker(self, task=DEFAULT_TASK, **kwargs):
        return AutonomousWorker(base_dir=self.root, use_llm=False, **kwargs).run(task)

    def test_happy_path_writes_and_verifies_latest_invoice(self):
        result = self.run_worker()
        self.assertEqual(result.status, "completed")
        self.assertIn("INV-ACME-2026-101", result.summary)
        self.assertIn("24,800.00", result.summary)
        rows = get_payables(self.root)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["invoice_number"], "INV-ACME-2026-101")
        self.assertEqual(rows[0]["due_date"], "2026-10-28")
        self.assertTrue(any(e["tool"] == "verify_payable" and e["observation"].get("verified") for e in result.events))

    def test_transient_write_failure_retries_once(self):
        result = self.run_worker(fail_next_write=True)
        self.assertEqual(result.status, "completed")
        create_events = [e for e in result.events if e["tool"] == "create_payable"]
        self.assertEqual(len(create_events), 2)
        self.assertFalse(create_events[0]["ok"])
        self.assertTrue(create_events[0]["observation"].get("retryable"))
        self.assertTrue(create_events[1]["ok"])
        self.assertEqual(len(get_payables(self.root)), 1)

    def test_high_value_invoice_requires_approval_before_write(self):
        task = "Find the latest invoice from Contoso Analytics and register it in the finance system."
        result = self.run_worker(task)
        self.assertEqual(result.status, "needs_approval")
        self.assertEqual(len(get_payables(self.root)), 0)
        approved = self.run_worker(task, approval_granted=True)
        self.assertEqual(approved.status, "completed")
        rows = get_payables(self.root)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["invoice_number"], "CONT-2026-051")

    def test_rerun_is_idempotent(self):
        first = self.run_worker()
        second = self.run_worker()
        self.assertEqual(first.status, "completed")
        self.assertEqual(second.status, "completed")
        self.assertEqual(len(get_payables(self.root)), 1)
        self.assertFalse(any(e["tool"] == "create_payable" for e in second.events))

    def test_unknown_vendor_does_not_write(self):
        result = self.run_worker("Find the latest invoice from Umbrella Example Corp and enter it into the finance system.")
        self.assertEqual(result.status, "failed")
        self.assertEqual(len(get_payables(self.root)), 0)

    def test_tool_prevents_wrong_source_identity(self):
        toolbox = ToolBox(self.root)
        response = toolbox.call("create_payable", {
            "source_invoice_id": "doc_001",
            "vendor": "Not ACME",
            "invoice_number": "INV-ACME-2026-101",
            "invoice_date": "2026-09-28",
            "due_date": "2026-10-28",
            "amount": 24800,
            "currency": "INR",
        })
        self.assertFalse(response["ok"])
        self.assertEqual(len(get_payables(self.root)), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
