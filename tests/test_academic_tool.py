import asyncio
import json

from nanobot.agent.tools.academic import AcademicSearchTool
from nanobot.config.schema import AcademicToolsConfig


async def test_academic_search_auto_dedupes_and_sorts(monkeypatch) -> None:
    tool = AcademicSearchTool(config=AcademicToolsConfig())

    async def fake_semantic(*args, **kwargs):
        return [
            {
                "source": "semantic_scholar",
                "id": "s2:1",
                "title": "Attention Is All You Need",
                "authors": ["A"],
                "year": 2017,
                "published": "2017-06-12",
                "abstract": "transformers",
                "url": "https://example.com/s2",
                "pdfUrl": "",
                "doi": "10.1000/xyz",
                "venue": "NeurIPS",
                "citationCount": 100,
                "topics": ["Transformers"],
            }
        ]

    async def fake_arxiv(*args, **kwargs):
        return [
            {
                "source": "arxiv",
                "id": "1706.03762",
                "title": "Attention Is All You Need",
                "authors": ["A", "B"],
                "year": 2017,
                "published": "2017-06-12",
                "abstract": "",
                "url": "https://arxiv.org/abs/1706.03762",
                "pdfUrl": "https://arxiv.org/pdf/1706.03762.pdf",
                "doi": "10.1000/xyz",
                "venue": "arXiv",
                "citationCount": None,
                "topics": ["Sequence Modeling"],
            },
            {
                "source": "arxiv",
                "id": "2024.00001",
                "title": "A New Paper",
                "authors": ["C"],
                "year": 2024,
                "published": "2024-01-01",
                "abstract": "new",
                "url": "https://arxiv.org/abs/2024.00001",
                "pdfUrl": "",
                "doi": "",
                "venue": "arXiv",
                "citationCount": None,
                "topics": [],
            },
        ]

    async def fake_openalex(*args, **kwargs):
        return []

    async def fake_crossref(*args, **kwargs):
        return []

    monkeypatch.setattr(tool, "_search_semantic_scholar", fake_semantic)
    monkeypatch.setattr(tool, "_search_arxiv", fake_arxiv)
    monkeypatch.setattr(tool, "_search_openalex", fake_openalex)
    monkeypatch.setattr(tool, "_search_crossref", fake_crossref)

    result = json.loads(await tool.execute(query="transformers", source="auto", count=5))

    assert result["returnedCount"] == 2
    assert result["results"][0]["title"] == "Attention Is All You Need"
    assert sorted(result["results"][0]["sources"]) == ["arxiv", "semantic_scholar"]
    assert result["results"][0]["pdfUrl"] == "https://arxiv.org/pdf/1706.03762.pdf"


def test_parse_arxiv_entries_extracts_core_fields() -> None:
    xml_text = """
    <feed xmlns="http://www.w3.org/2005/Atom">
      <entry>
        <id>http://arxiv.org/abs/1706.03762v7</id>
        <published>2017-06-12T17:57:11Z</published>
        <title> Attention Is All You Need </title>
        <summary> Transformer paper </summary>
        <author><name>Alice</name></author>
        <author><name>Bob</name></author>
        <link href="http://arxiv.org/abs/1706.03762v7" rel="alternate" type="text/html" />
        <link title="pdf" href="http://arxiv.org/pdf/1706.03762v7" rel="related" type="application/pdf" />
        <category term="cs.CL" />
      </entry>
    </feed>
    """

    result = AcademicSearchTool._parse_arxiv_entries(xml_text)

    assert len(result) == 1
    assert result[0]["id"] == "1706.03762v7"
    assert result[0]["year"] == 2017
    assert result[0]["authors"] == ["Alice", "Bob"]
    assert result[0]["pdfUrl"] == "http://arxiv.org/pdf/1706.03762v7"
    assert result[0]["topics"] == ["cs.CL"]


def test_disabled_source_returns_empty_results() -> None:
    config = AcademicToolsConfig()
    config.arxiv.enabled = False
    config.semantic_scholar.enabled = False
    config.openalex.enabled = False
    config.crossref.enabled = False

    tool = AcademicSearchTool(config=config)
    result = json.loads(asyncio.run(tool.execute(query="graph neural networks", source="auto")))

    assert result["error"] == "No academic sources are enabled."