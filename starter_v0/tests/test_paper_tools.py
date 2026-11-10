"""Offline checks for the arXiv tools when the public API is rate limited."""

from __future__ import annotations

from pathlib import Path

from tools.paper_text import tool as paper_text_module
from tools.papers import tool as papers_module


def test_papers_parses_arxiv_atom_response(monkeypatch) -> None:
    atom = """<?xml version="1.0" encoding="UTF-8"?>
    <feed xmlns="http://www.w3.org/2005/Atom"
          xmlns:opensearch="http://a9.com/-/spec/opensearch/1.1/"
          xmlns:arxiv="http://arxiv.org/schemas/atom">
      <opensearch:totalResults>1</opensearch:totalResults>
      <entry>
        <id>https://arxiv.org/abs/1706.03762</id>
        <title>Attention Is All You Need</title>
        <summary>A transformer architecture.</summary>
        <author><name>A. Researcher</name></author>
        <link title="pdf" href="https://arxiv.org/pdf/1706.03762.pdf"/>
        <arxiv:primary_category term="cs.CL"/>
      </entry>
    </feed>"""

    class Response:
        text = atom

        def raise_for_status(self) -> None:
            return None

    monkeypatch.setattr(papers_module, "_arxiv_get", lambda *_args, **_kwargs: Response())
    result = papers_module.arxiv_search(query="transformer", max_results=1)
    assert result["total_results"] == 1
    assert result["items"][0]["arxiv_id"] == "1706.03762"
    assert result["items"][0]["title"] == "Attention Is All You Need"
    assert result["items"][0]["primary_category"] == "cs.CL"


def test_paper_text_returns_excerpt_and_writes_file(monkeypatch, tmp_path: Path) -> None:
    pdf_path = tmp_path / "1706.03762.pdf"
    monkeypatch.setattr(
        paper_text_module,
        "_download_arxiv_pdf",
        lambda *_args: ("1706.03762", pdf_path, "https://arxiv.org/pdf/1706.03762.pdf"),
    )
    monkeypatch.setattr(paper_text_module, "_extract_pdf_text", lambda *_args, **_kwargs: ("Paper text", 3))
    result = paper_text_module.get_arxiv_paper_text(
        arxiv_url="https://arxiv.org/abs/1706.03762", max_pages=1, max_chars=1000
    )
    assert result["items"][0]["summary"] == "Paper text"
    assert Path(result["txt_path"]).read_text(encoding="utf-8") == "Paper text"
    assert result["pages_read"] == 1
