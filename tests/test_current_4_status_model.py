"""
Current 4-Status Model Smoke Tests
===================================
Verify that the current reimbursement data model uses exactly 4 statuses
and that all records cover the expected states.
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from reimbursement_data import (
    get_default_records,
    STATUS_PENDING_RECEIPT, STATUS_PENDING_SUBMIT, STATUS_SUBMITTED, STATUS_ERROR,
    ALL_STATUSES, derive_ai_check_result, derive_sync_status,
)


class TestFourStatusModel(unittest.TestCase):
    """Verify the 4-status model is consistent."""

    def test_all_four_statuses_exist(self):
        self.assertEqual(len(ALL_STATUSES), 4)
        self.assertIn(STATUS_PENDING_RECEIPT, ALL_STATUSES)
        self.assertIn(STATUS_PENDING_SUBMIT, ALL_STATUSES)
        self.assertIn(STATUS_SUBMITTED, ALL_STATUSES)
        self.assertIn(STATUS_ERROR, ALL_STATUSES)

    def test_mock_records_cover_all_four_statuses(self):
        records = get_default_records()
        statuses = {r.get("status") for r in records}
        for s in ALL_STATUSES:
            self.assertIn(s, statuses, f"No mock record with status={s}")

    def test_each_status_has_at_least_one_record(self):
        records = get_default_records()
        for s in ALL_STATUSES:
            matching = [r for r in records if r["status"] == s]
            self.assertGreaterEqual(len(matching), 1, f"Need at least 1 record for status={s}")

    def test_derive_ai_check_result_mapping(self):
        self.assertEqual(derive_ai_check_result(STATUS_PENDING_RECEIPT), "need_supplement")
        self.assertEqual(derive_ai_check_result(STATUS_PENDING_SUBMIT), "passed")
        self.assertEqual(derive_ai_check_result(STATUS_SUBMITTED), "passed")
        self.assertEqual(derive_ai_check_result(STATUS_ERROR), "failed")

    def test_derive_sync_status_mapping(self):
        self.assertEqual(derive_sync_status(STATUS_PENDING_RECEIPT), "not_synced")
        self.assertEqual(derive_sync_status(STATUS_PENDING_SUBMIT), "not_synced")
        self.assertEqual(derive_sync_status(STATUS_SUBMITTED), "synced")
        self.assertEqual(derive_sync_status(STATUS_ERROR), "not_synced")

    def test_no_legacy_status_fields_in_records(self):
        records = get_default_records()
        for r in records:
            self.assertNotIn("ai_check_result", r,
                f"Record {r['id']} still has legacy 'ai_check_result' field")
            self.assertNotIn("sync_status", r,
                f"Record {r['id']} still has legacy 'sync_status' field")

    def test_status_label_lookup(self):
        from reimbursement_data import get_status_label
        for s in ALL_STATUSES:
            label = get_status_label(s)
            self.assertIsInstance(label, str)
            self.assertTrue(len(label) > 0, f"Empty label for status={s}")

    def test_cta_action_for_each_status(self):
        from reimbursement_data import get_cta_action
        for s in ALL_STATUSES:
            cta = get_cta_action(s)
            self.assertIn("label", cta)
            self.assertIn("action", cta)
            self.assertIn("style", cta)

    def test_filter_records_by_status(self):
        from reimbursement_data import filter_records
        records = get_default_records()
        for s in ALL_STATUSES:
            filtered = filter_records(records, s)
            self.assertTrue(all(r["status"] == s for r in filtered),
                f"filter_records returned wrong status for filter={s}")


class TestH5PagesImport(unittest.TestCase):
    """h5_pages.py must be importable without Streamlit runtime."""

    def test_import_h5_pages(self):
        import h5_pages
        self.assertTrue(hasattr(h5_pages, "render_reimbursement_list_page"))
        self.assertTrue(hasattr(h5_pages, "render_reimbursement_detail_page"))
        self.assertTrue(hasattr(h5_pages, "render_supplement_material_page"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
