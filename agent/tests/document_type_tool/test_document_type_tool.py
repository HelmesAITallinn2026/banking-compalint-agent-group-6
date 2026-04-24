from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from extracting_agent.agent import _build_agent, analyze_document_type


def _write_pdf(path: Path, stream: str) -> None:
    objects = [
        "1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
        "2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n",
        (
            "3 0 obj\n"
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 144] "
            "/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\n"
            "endobj\n"
        ),
        f"4 0 obj\n<< /Length {len(stream.encode('utf-8'))} >>\nstream\n{stream}\nendstream\nendobj\n",
        "5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n",
    ]

    content = "%PDF-1.4\n"
    offsets = [0]
    for obj in objects:
        offsets.append(len(content.encode("utf-8")))
        content += obj

    xref_offset = len(content.encode("utf-8"))
    content += f"xref\n0 {len(objects) + 1}\n"
    content += "0000000000 65535 f \n"
    for offset in offsets[1:]:
        content += f"{offset:010d} 00000 n \n"
    content += (
        "trailer\n"
        f"<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        "startxref\n"
        f"{xref_offset}\n"
        "%%EOF\n"
    )
    path.write_bytes(content.encode("utf-8"))


class DocumentTypeToolTests(unittest.TestCase):
    def test_build_agent_returns_langchain_create_agent_graph(self) -> None:
        agent = _build_agent()
        self.assertEqual(type(agent).__name__, "CompiledStateGraph")

    def test_pdf_with_text_layer_is_classified_as_document(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = Path(tmpdir) / "text-layer.pdf"
            _write_pdf(
                pdf_path,
                "BT\n/F1 18 Tf\n72 720 Td\n(Bank complaint text layer) Tj\nET",
            )

            result = analyze_document_type.invoke(
                {"file_path": str(pdf_path), "content_type": "application/pdf"}
            )

        self.assertEqual(result["document_type"], "document")
        self.assertIn("Bank complaint text layer", result["text"])

    def test_pdf_without_text_layer_is_classified_as_image(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = Path(tmpdir) / "scan.pdf"
            _write_pdf(pdf_path, "")

            result = analyze_document_type.invoke(
                {"file_path": str(pdf_path), "content_type": "application/pdf"}
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
