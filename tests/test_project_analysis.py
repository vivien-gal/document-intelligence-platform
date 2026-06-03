import unittest

from app.services.project_analysis import (
    NOT_FOUND,
    _build_project_summary,
    _extract_colon_fields,
    _extract_list_under_headings,
    _unique_keep_order,
)
from app.services.project_analysis import (
    BUDGET_FIELD_PATTERNS,
    DATE_FIELD_PATTERNS,
    RISK_HEADING_PATTERNS,
    STAKEHOLDER_FIELD_PATTERNS,
    TASK_HEADING_PATTERNS,
)

SAMPLE_DOC = """
Projekt neve: Marina Residence AI Dashboard
Projektvezető: Kovács Anna
Kapcsolattartó: Kiss Péter
Határidő: 2026. szeptember 30.
Költségkeret: 18 500 000 Ft
Kockázatok:
- Késhet az Oracle APEX integráció
- Nem minden projektadat strukturált
Nyitott feladatok:
- API kapcsolat kialakítása a Monday.com rendszerrel
- Dashboard frontend fejlesztése Reactben
"""


class ProjectAnalysisExtractionTests(unittest.TestCase):
    def test_extract_dates(self) -> None:
        dates = _extract_colon_fields(SAMPLE_DOC, DATE_FIELD_PATTERNS)
        self.assertTrue(any("Határidő" in d for d in dates))

    def test_extract_budget(self) -> None:
        budget = _extract_colon_fields(SAMPLE_DOC, BUDGET_FIELD_PATTERNS)
        self.assertTrue(any("Költségkeret" in b for b in budget))

    def test_extract_stakeholders(self) -> None:
        people = _extract_colon_fields(SAMPLE_DOC, STAKEHOLDER_FIELD_PATTERNS)
        self.assertIn("Projektvezető: Kovács Anna", people)
        self.assertIn("Kapcsolattartó: Kiss Péter", people)

    def test_extract_risks(self) -> None:
        risks = _extract_list_under_headings(SAMPLE_DOC, RISK_HEADING_PATTERNS)
        self.assertIn("Késhet az Oracle APEX integráció", risks)

    def test_extract_open_tasks(self) -> None:
        tasks = _extract_list_under_headings(SAMPLE_DOC, TASK_HEADING_PATTERNS)
        self.assertTrue(any("Monday.com" in t for t in tasks))

    def test_project_summary(self) -> None:
        summary = _build_project_summary([SAMPLE_DOC])
        self.assertNotEqual(summary, NOT_FOUND)
        self.assertIn("Marina Residence", summary)

    def test_unique_keep_order(self) -> None:
        result = _unique_keep_order(["a", "b", "a", "c"])
        self.assertEqual(result, ["a", "b", "c"])


if __name__ == "__main__":
    unittest.main()
