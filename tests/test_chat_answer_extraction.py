import unittest

from app.schemas import SearchResult
from app.services.chat import NO_RELEVANT_INFO, build_answer


def source(content: str, score: float = 0.9) -> SearchResult:
    return SearchResult(
        chunk_id=1,
        document_id=1,
        filename="doc.pdf",
        chunk_index=0,
        content=content,
        score=score,
    )


class ChatAnswerExtractionTests(unittest.TestCase):
    def test_project_manager_field_answer(self) -> None:
        question = "Ki a projektvezetője?"
        sources = [
            source("Projekt neve: Marina Residence AI Dashboard"),
            source("Projektvezető: Kovács Anna"),
        ]
        answer = build_answer(question, sources)
        self.assertEqual(answer, "Projektvezető: Kovács Anna")

    def test_budget_field_answer(self) -> None:
        question = "Mi a költségkeret?"
        sources = [
            source("Határidő: 2026. szeptember 30."),
            source("Költségkeret: 18 500 000 Ft"),
        ]
        answer = build_answer(question, sources)
        self.assertEqual(answer, "Költségkeret: 18 500 000 Ft")

    def test_deadline_field_answer(self) -> None:
        question = "Mi a projekt határideje?"
        sources = [
            source("Projektvezető: Kovács Anna"),
            source("Határidő: 2026. szeptember 30."),
        ]
        answer = build_answer(question, sources)
        self.assertEqual(answer, "Határidő: 2026. szeptember 30.")

    def test_contract_expiration_field_answer(self) -> None:
        question = "Mikor a szerződés lejárata?"
        sources = [
            source("Szerződés lejárata: 2027. január 31."),
            source("Kapcsolattartó: Szabó Péter"),
        ]
        answer = build_answer(question, sources)
        self.assertEqual(answer, "Szerződés lejárata: 2027. január 31.")

    def test_contact_person_field_answer(self) -> None:
        question = "Ki a kapcsolattartó?"
        sources = [
            source("Kapcsolattartó: Szabó Péter"),
            source("Projektvezető: Kovács Anna"),
        ]
        answer = build_answer(question, sources)
        self.assertEqual(answer, "Kapcsolattartó: Szabó Péter")

    def test_monthly_fee_field_answer(self) -> None:
        question = "Mennyi a havi díj?"
        sources = [
            source("Havi díj:\n18 500 000 Ft + ÁFA"),
        ]
        answer = build_answer(question, sources)
        self.assertEqual(answer, "Havi díj: 18 500 000 Ft + ÁFA")

    def test_risk_list_extraction(self) -> None:
        question = "Mik a kockázatok listája?"
        sources = [
            source(
                "Kockázatok:\n- Külső API limit\n- Erőforráshiány\n- Beszállítói késés\n\nNyitott feladatok:\n- Tesztelés"
            ),
        ]
        answer = build_answer(question, sources)
        self.assertEqual(
            answer,
            "Kockázatok: Külső API limit; Erőforráshiány; Beszállítói késés",
        )

    def test_project_manager_accusative_variant(self) -> None:
        question = "Ki a projektvezetőt jelölték ki?"
        sources = [
            source("Projektvezető: Kovács Anna"),
        ]
        answer = build_answer(question, sources)
        self.assertEqual(answer, "Projektvezető: Kovács Anna")

    def test_phone_number_not_present(self) -> None:
        question = "Mi a projekt telefonszáma?"
        sources = [
            source("Projekt neve: Marina Residence AI Dashboard"),
            source("Projektvezető: Kovács Anna"),
            source("Költségkeret: 18 500 000 Ft"),
            source("Határidő: 2026. szeptember 30."),
        ]
        answer = build_answer(question, sources)
        self.assertEqual(answer, NO_RELEVANT_INFO)


if __name__ == "__main__":
    unittest.main()
