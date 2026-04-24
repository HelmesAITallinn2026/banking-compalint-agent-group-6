from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from extracting_agent.agent import _build_agent, analyze_document_type

MOCK_DOCS = Path(__file__).parent.parent.parent.parent / "mock_docs"

# DEFINITELY-NOT-INCOME-STATEMENT.pdf — a .pdf file that contains only a scanned image (no text layer)
PDF_IMAGE_ONLY = MOCK_DOCS / "DEFINITELY-NOT-INCOME-STATEMENT.pdf"

# helmes_bank_salary_statement.pdf — a .pdf file with underlying selectable text data
PDF_WITH_TEXT = MOCK_DOCS / "helmes_bank_salary_statement.pdf"


class DocumentTypeToolTests(unittest.TestCase):
    def test_build_agent_returns_langchain_create_agent_graph(self) -> None:
        agent = _build_agent()
        self.assertEqual(type(agent).__name__, "CompiledStateGraph")

    def test_pdf_with_text_layer_is_classified_as_document(self) -> None:
        result = analyze_document_type.invoke(
            {"file_path": str(PDF_WITH_TEXT), "content_type": "application/pdf"}
        )

        self.assertEqual(result["document_type"], "document")
        self.assertGreater(len(result["text"]), 0)

    def test_pdf_without_text_layer_is_classified_as_image(self) -> None:
        result = analyze_document_type.invoke(
            {"file_path": str(PDF_IMAGE_ONLY), "content_type": "application/pdf"}
        )

        self.assertEqual(result["document_type"], "image")
        self.assertEqual(result["text"], "")

    def test_non_pdf_bytes_saved_with_pdf_suffix_still_classify_as_image(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_pdf_path = Path(tmpdir) / "uploaded-image.pdf"
            fake_pdf_path.write_bytes(b"\x89PNG\r\n\x1a\nnot-a-real-pdf")

            result = analyze_document_type.invoke(
                {"file_path": str(fake_pdf_path), "content_type": "image/png"}
            )

        self.assertEqual(result["document_type"], "image")
        self.assertEqual(result["text"], "")


if __name__ == "__main__":
    unittest.main()
