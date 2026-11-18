"""Integration tests for the Flask GUI API endpoints (Section 4.1)."""

from __future__ import annotations

import unittest

from gui.app import create_app


class TestGUIWebEndpoints(unittest.TestCase):
    def setUp(self) -> None:
        app = create_app()
        app.testing = True
        self.client = app.test_client()

    def test_index_and_catalog(self) -> None:
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Griductive Solver", resp.data)

        cat = self.client.get("/api/puzzles").get_json()
        self.assertGreaterEqual(len(cat["puzzles"]), 13)

    def test_gameplay_verdicts_hint_highlight_and_autosolve(self) -> None:
        # Load tutorial stage 3x3_01_core_intro
        resp = self.client.post("/api/load", json={"puzzle_id": "3x3_01_core_intro"})
        self.assertEqual(resp.status_code, 200)

        # Highlight opening card A1
        hl = self.client.get("/api/highlight/A1").get_json()
        self.assertTrue(hl["ok"])
        self.assertEqual(set(hl["highlight"]["primary"]), {"A1", "B1", "C1"})

        # Unrevealed card highlight must fail with 400
        bad_hl = self.client.get("/api/highlight/B2")
        self.assertEqual(bad_hl.status_code, 400)

        # NOT_PROVABLE rejection on unforced B2
        v_np = self.client.post(
            "/api/verdict", json={"cell_id": "B2", "verdict": "CRIMINAL"}
        ).get_json()
        self.assertEqual(v_np["submission"]["status_code"], "NOT_PROVABLE")

        # CONTRADICTED rejection on forced B1 (forced CRIMINAL, called INNOCENT)
        v_ct = self.client.post(
            "/api/verdict", json={"cell_id": "B1", "verdict": "INNOCENT"}
        ).get_json()
        self.assertEqual(v_ct["submission"]["status_code"], "CONTRADICTED")

        # Hint check
        hint = self.client.post("/api/hint").get_json()["hint"]
        self.assertTrue(hint["available"])
        self.assertEqual(hint["target_cell"], "B1")

        # Live CNF Inspector check at initial KB_0
        cnf_resp = self.client.get("/api/cnf").get_json()
        self.assertTrue(cnf_resp["ok"])
        self.assertEqual(cnf_resp["cnf"]["num_primary_vars"], 9)
        self.assertGreater(cnf_resp["cnf"]["num_clauses"], 0)
        self.assertIn("p cnf", cnf_resp["cnf"]["dimacs_text"])

        # Manual ACCEPTED move on B1 must also append a [Manual] trace entry!
        v_ok = self.client.post(
            "/api/verdict", json={"cell_id": "B1", "verdict": "CRIMINAL"}
        ).get_json()
        self.assertEqual(v_ok["submission"]["status_code"], "ACCEPTED")
        self.assertEqual(len(v_ok["telemetry"]["traces"]), 1)
        self.assertIn("[Manual]", v_ok["telemetry"]["traces"][0]["chosen_character"])

        # Single automated step + remaining Auto Solve + Uniqueness check
        st2 = self.client.post("/api/step").get_json()
        self.assertEqual(st2["step_trace"]["chosen_cell"], "C1")

        auto = self.client.post("/api/auto_solve").get_json()
        self.assertTrue(auto["state"]["is_solved"])

        uniq = self.client.post("/api/uniqueness").get_json()["uniqueness"]
        self.assertTrue(uniq["is_unique"])


if __name__ == "__main__":
    unittest.main()
