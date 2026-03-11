"""Academic paper search tool."""

from __future__ import annotations

import json
import os
import xml.etree.ElementTree as ET
from typing import Any

import httpx
from loguru import logger

from nanobot.agent.tools.base import Tool

DEFAULT_BASE_URLS = {
    "arxiv": "http://export.arxiv.org/api/query",
    "semantic_scholar": "https://api.semanticscholar.org/graph/v1/paper/search",
    "openalex": "https://api.openalex.org/works",
    "crossref": "https://api.crossref.org/works",
}

ENV_API_KEYS = {
    "semantic_scholar": "SEMANTIC_SCHOLAR_API_KEY",
}

SOURCE_PRIORITY = {
    "semantic_scholar": 4,
    "openalex": 3,
    "crossref": 2,
    "arxiv": 1,
}


def _normalize_doi(value: str | None) -> str:
    if not value:
        return ""
    value = value.strip().lower()
    return value.removeprefix("https://doi.org/").removeprefix("doi:")


def _normalize_title(value: str | None) -> str:
    if not value:
        return ""
    return " ".join(value.lower().split())


class AcademicSearchTool(Tool):
    """Search academic papers across multiple sources."""

    name = "academic_search"
    description = (
        "Search academic papers across arXiv, Semantic Scholar, OpenAlex, and Crossref. "
        "Use this for papers, surveys, citations, and canonical references."
    )
    parameters = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Paper topic, keywords, or title", "minLength": 2},
            "source": {
                "type": "string",
                "description": "Academic source or auto for multi-source search",
                "enum": ["auto", "arxiv", "semantic_scholar", "openalex", "crossref"],
            },
            "count": {"type": "integer", "description": "Number of results", "minimum": 1, "maximum": 20},
            "yearFrom": {"type": "integer", "description": "Start publication year", "minimum": 1900, "maximum": 2100},
            "yearTo": {"type": "integer", "description": "End publication year", "minimum": 1900, "maximum": 2100},
            "sort": {
                "type": "string",
                "description": "Ranking mode",
                "enum": ["relevance", "date", "citations"],
            },
            "includeAbstract": {
                "type": "boolean",
                "description": "Include abstract text in the result payload",
            },
        },
        "required": ["query"],
    }

    def __init__(self, config: Any | None = None, proxy: str | None = None):
        self.config = config
        self.proxy = proxy

    async def execute(
        self,
        query: str,
        source: str = "auto",
        count: int | None = None,
        yearFrom: int | None = None,
        yearTo: int | None = None,
        sort: str = "relevance",
        includeAbstract: bool = True,
        **kwargs: Any,
    ) -> str:
        requested_count = min(max(count or self._default_count(), 1), 20)
        source_names = self._resolve_sources(source)
        if not source_names:
            return json.dumps(
                {"error": "No academic sources are enabled.", "query": query},
                ensure_ascii=False,
            )

        results: list[dict[str, Any]] = []
        warnings: list[str] = []

        logger.debug("AcademicSearch: sources={} query={!r}", source_names, query)
        async with httpx.AsyncClient(proxy=self.proxy, timeout=20.0) as client:
            for source_name in source_names:
                try:
                    search_fn = getattr(self, f"_search_{source_name}")
                    results.extend(
                        await search_fn(
                            client=client,
                            query=query,
                            count=requested_count,
                            year_from=yearFrom,
                            year_to=yearTo,
                            sort=sort,
                            include_abstract=includeAbstract,
                        )
                    )
                except Exception as exc:
                    logger.error("AcademicSearch {} failed: {}", source_name, exc)
                    warnings.append(f"{source_name}: {type(exc).__name__}")

        merged = self._sort_and_dedupe_results(results, sort=sort, count=requested_count)
        payload = {
            "query": query,
            "source": source,
            "requestedCount": requested_count,
            "returnedCount": len(merged),
            "results": merged,
        }
        if warnings:
            payload["warnings"] = warnings
        return json.dumps(payload, ensure_ascii=False)

    def _default_count(self) -> int:
        if self.config and getattr(self.config, "default_max_results", None):
            return self.config.default_max_results
        return 5

    def _resolve_sources(self, source: str) -> list[str]:
        if source != "auto":
            return [source] if self._source_enabled(source) else []
        ordered = ["semantic_scholar", "arxiv", "openalex", "crossref"]
        return [name for name in ordered if self._source_enabled(name)]

    def _source_enabled(self, source: str) -> bool:
        cfg = getattr(self.config, source, None) if self.config else None
        return True if cfg is None else bool(cfg.enabled)

    def _source_api_key(self, source: str) -> str:
        cfg = getattr(self.config, source, None) if self.config else None
        if cfg and getattr(cfg, "api_key", ""):
            return cfg.api_key
        env_name = ENV_API_KEYS.get(source)
        return os.environ.get(env_name, "") if env_name else ""

    def _source_base_url(self, source: str) -> str:
        cfg = getattr(self.config, source, None) if self.config else None
        if cfg and getattr(cfg, "base_url", ""):
            return cfg.base_url
        return DEFAULT_BASE_URLS[source]

    def _user_agent(self) -> str:
        if self.config and getattr(self.config, "user_agent", None):
            return self.config.user_agent
        return "nanobot-academic/0.1"

    def _contact_email(self) -> str:
        if self.config and getattr(self.config, "contact_email", None):
            return self.config.contact_email
        return ""

    async def _search_arxiv(
        self,
        client: httpx.AsyncClient,
        query: str,
        count: int,
        year_from: int | None,
        year_to: int | None,
        sort: str,
        include_abstract: bool,
    ) -> list[dict[str, Any]]:
        params = {
            "search_query": f'all:"{query}"',
            "start": 0,
            "max_results": count,
            "sortBy": "submittedDate" if sort == "date" else "relevance",
            "sortOrder": "descending",
        }
        response = await client.get(
            self._source_base_url("arxiv"),
            params=params,
            headers={"User-Agent": self._user_agent()},
        )
        response.raise_for_status()
        items = self._parse_arxiv_entries(response.text, include_abstract=include_abstract)
        return self._filter_by_year(items, year_from, year_to)

    @staticmethod
    def _parse_arxiv_entries(xml_text: str, include_abstract: bool = True) -> list[dict[str, Any]]:
        root = ET.fromstring(xml_text)
        ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
        results = []
        for entry in root.findall("atom:entry", ns):
            title = (entry.findtext("atom:title", default="", namespaces=ns) or "").strip()
            abstract = (entry.findtext("atom:summary", default="", namespaces=ns) or "").strip()
            published = (entry.findtext("atom:published", default="", namespaces=ns) or "").strip()
            paper_url = (entry.findtext("atom:id", default="", namespaces=ns) or "").strip()
            arxiv_id = paper_url.rsplit("/", 1)[-1] if paper_url else ""
            authors = [
                (author.findtext("atom:name", default="", namespaces=ns) or "").strip()
                for author in entry.findall("atom:author", ns)
            ]
            categories = [category.attrib.get("term", "") for category in entry.findall("atom:category", ns)]
            pdf_url = ""
            for link in entry.findall("atom:link", ns):
                if link.attrib.get("title") == "pdf":
                    pdf_url = link.attrib.get("href", "")
                    break
            results.append(
                {
                    "source": "arxiv",
                    "id": arxiv_id,
                    "title": title,
                    "authors": [name for name in authors if name],
                    "year": AcademicSearchTool._extract_year(published),
                    "published": published,
                    "abstract": abstract if include_abstract else "",
                    "url": paper_url,
                    "pdfUrl": pdf_url,
                    "doi": "",
                    "venue": "arXiv",
                    "citationCount": None,
                    "topics": [name for name in categories if name],
                }
            )
        return results

    async def _search_semantic_scholar(
        self,
        client: httpx.AsyncClient,
        query: str,
        count: int,
        year_from: int | None,
        year_to: int | None,
        sort: str,
        include_abstract: bool,
    ) -> list[dict[str, Any]]:
        del sort
        params = {
            "query": query,
            "limit": count,
            "fields": (
                "title,abstract,year,authors,url,venue,citationCount,publicationDate,"
                "externalIds,openAccessPdf,fieldsOfStudy"
            ),
        }
        if year_from or year_to:
            params["year"] = f"{year_from or '*'}-{year_to or '*'}"
        headers = {"User-Agent": self._user_agent()}
        if api_key := self._source_api_key("semantic_scholar"):
            headers["x-api-key"] = api_key
        response = await client.get(self._source_base_url("semantic_scholar"), params=params, headers=headers)
        response.raise_for_status()
        data = response.json().get("data", [])
        results = []
        for item in data:
            external_ids = item.get("externalIds") or {}
            pdf = item.get("openAccessPdf") or {}
            results.append(
                {
                    "source": "semantic_scholar",
                    "id": item.get("paperId") or "",
                    "title": item.get("title") or "",
                    "authors": [author.get("name") for author in item.get("authors") or [] if author.get("name")],
                    "year": item.get("year"),
                    "published": item.get("publicationDate") or "",
                    "abstract": (item.get("abstract") or "") if include_abstract else "",
                    "url": item.get("url") or "",
                    "pdfUrl": pdf.get("url") or "",
                    "doi": external_ids.get("DOI") or "",
                    "venue": item.get("venue") or "",
                    "citationCount": item.get("citationCount"),
                    "topics": item.get("fieldsOfStudy") or [],
                }
            )
        return results

    async def _search_openalex(
        self,
        client: httpx.AsyncClient,
        query: str,
        count: int,
        year_from: int | None,
        year_to: int | None,
        sort: str,
        include_abstract: bool,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {
            "search": query,
            "per-page": count,
            "sort": self._openalex_sort(sort),
        }
        filters = []
        if year_from:
            filters.append(f"from_publication_date:{year_from}-01-01")
        if year_to:
            filters.append(f"to_publication_date:{year_to}-12-31")
        if filters:
            params["filter"] = ",".join(filters)
        if contact_email := self._contact_email():
            params["mailto"] = contact_email
        response = await client.get(
            self._source_base_url("openalex"),
            params=params,
            headers={"User-Agent": self._user_agent()},
        )
        response.raise_for_status()
        data = response.json().get("results", [])
        results = []
        for item in data:
            authorships = item.get("authorships") or []
            locations = item.get("locations") or []
            primary_location = item.get("primary_location") or {}
            topics = [topic.get("display_name") for topic in item.get("concepts") or [] if topic.get("display_name")]
            abstract = self._openalex_abstract(item) if include_abstract else ""
            results.append(
                {
                    "source": "openalex",
                    "id": item.get("id") or "",
                    "title": item.get("display_name") or "",
                    "authors": [
                        authorship.get("author", {}).get("display_name")
                        for authorship in authorships
                        if authorship.get("author", {}).get("display_name")
                    ],
                    "year": item.get("publication_year"),
                    "published": item.get("publication_date") or "",
                    "abstract": abstract,
                    "url": primary_location.get("landing_page_url") or item.get("id") or "",
                    "pdfUrl": self._first_pdf_url([primary_location, *locations]),
                    "doi": _normalize_doi(item.get("doi")),
                    "venue": item.get("primary_location", {}).get("source", {}).get("display_name") or "",
                    "citationCount": item.get("cited_by_count"),
                    "topics": topics,
                }
            )
        return results

    async def _search_crossref(
        self,
        client: httpx.AsyncClient,
        query: str,
        count: int,
        year_from: int | None,
        year_to: int | None,
        sort: str,
        include_abstract: bool,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {
            "query.bibliographic": query,
            "rows": count,
            "sort": self._crossref_sort(sort),
            "order": "desc",
        }
        filters = []
        if year_from:
            filters.append(f"from-pub-date:{year_from}")
        if year_to:
            filters.append(f"until-pub-date:{year_to}")
        if filters:
            params["filter"] = ",".join(filters)
        if contact_email := self._contact_email():
            params["mailto"] = contact_email
        response = await client.get(
            self._source_base_url("crossref"),
            params=params,
            headers={"User-Agent": self._user_agent()},
        )
        response.raise_for_status()
        items = response.json().get("message", {}).get("items", [])
        results = []
        for item in items:
            title_list = item.get("title") or []
            published_parts = item.get("published-print") or item.get("published-online") or {}
            date_parts = (published_parts.get("date-parts") or [[None]])[0]
            published = "-".join(str(part) for part in date_parts if part)
            authors = []
            for author in item.get("author") or []:
                name = " ".join(part for part in [author.get("given"), author.get("family")] if part)
                if name:
                    authors.append(name)
            abstract = item.get("abstract") or ""
            results.append(
                {
                    "source": "crossref",
                    "id": item.get("DOI") or "",
                    "title": title_list[0] if title_list else "",
                    "authors": authors,
                    "year": date_parts[0] if date_parts and date_parts[0] else None,
                    "published": published,
                    "abstract": abstract if include_abstract else "",
                    "url": item.get("URL") or "",
                    "pdfUrl": "",
                    "doi": _normalize_doi(item.get("DOI")),
                    "venue": (item.get("container-title") or [""])[0],
                    "citationCount": item.get("is-referenced-by-count"),
                    "topics": [],
                }
            )
        return results

    @staticmethod
    def _filter_by_year(
        items: list[dict[str, Any]],
        year_from: int | None,
        year_to: int | None,
    ) -> list[dict[str, Any]]:
        if not year_from and not year_to:
            return items
        results = []
        for item in items:
            year = item.get("year")
            if year is None:
                continue
            if year_from and year < year_from:
                continue
            if year_to and year > year_to:
                continue
            results.append(item)
        return results

    @staticmethod
    def _extract_year(value: str | None) -> int | None:
        if not value or len(value) < 4:
            return None
        try:
            return int(value[:4])
        except ValueError:
            return None

    @staticmethod
    def _openalex_sort(sort: str) -> str:
        if sort == "date":
            return "publication_date:desc"
        if sort == "citations":
            return "cited_by_count:desc"
        return "relevance_score:desc"

    @staticmethod
    def _crossref_sort(sort: str) -> str:
        if sort == "date":
            return "published"
        if sort == "citations":
            return "is-referenced-by-count"
        return "relevance"

    @staticmethod
    def _openalex_abstract(item: dict[str, Any]) -> str:
        inverted = item.get("abstract_inverted_index") or {}
        if not inverted:
            return ""
        words: list[tuple[int, str]] = []
        for token, positions in inverted.items():
            for pos in positions:
                words.append((pos, token))
        words.sort(key=lambda part: part[0])
        return " ".join(token for _, token in words)

    @staticmethod
    def _first_pdf_url(locations: list[dict[str, Any]]) -> str:
        for location in locations:
            pdf_url = location.get("pdf_url")
            if pdf_url:
                return pdf_url
        return ""

    @classmethod
    def _sort_and_dedupe_results(
        cls,
        items: list[dict[str, Any]],
        sort: str,
        count: int,
    ) -> list[dict[str, Any]]:
        merged: dict[str, dict[str, Any]] = {}
        for item in items:
            key = cls._result_key(item)
            if key not in merged:
                merged[key] = {**item, "sources": [item.get("source", "")]}
                continue
            merged[key] = cls._merge_result(merged[key], item)
        deduped = list(merged.values())
        deduped.sort(key=lambda item: cls._sort_key(item, sort), reverse=True)
        return deduped[:count]

    @staticmethod
    def _result_key(item: dict[str, Any]) -> str:
        doi = _normalize_doi(item.get("doi"))
        if doi:
            return f"doi:{doi}"
        if item.get("source") == "arxiv" and item.get("id"):
            return f"arxiv:{item['id']}"
        if item.get("id"):
            return f"{item.get('source')}:{item['id']}"
        return f"title:{_normalize_title(item.get('title'))}:{item.get('year') or ''}"

    @classmethod
    def _merge_result(cls, base: dict[str, Any], extra: dict[str, Any]) -> dict[str, Any]:
        result = dict(base)
        result_sources = list(result.get("sources") or [])
        if extra.get("source") and extra["source"] not in result_sources:
            result_sources.append(extra["source"])
        result["sources"] = result_sources

        for key in ["title", "published", "abstract", "url", "pdfUrl", "doi", "venue"]:
            if not result.get(key) and extra.get(key):
                result[key] = extra[key]

        for key in ["year", "citationCount"]:
            if result.get(key) is None and extra.get(key) is not None:
                result[key] = extra[key]

        authors = list(dict.fromkeys([*(result.get("authors") or []), *(extra.get("authors") or [])]))
        topics = list(dict.fromkeys([*(result.get("topics") or []), *(extra.get("topics") or [])]))
        result["authors"] = authors
        result["topics"] = topics

        base_source = result.get("source", "")
        extra_source = extra.get("source", "")
        if SOURCE_PRIORITY.get(extra_source, 0) > SOURCE_PRIORITY.get(base_source, 0):
            result["source"] = extra_source
        if (extra.get("citationCount") or 0) > (result.get("citationCount") or 0):
            result["citationCount"] = extra.get("citationCount")
        return result

    @staticmethod
    def _sort_key(item: dict[str, Any], sort: str) -> tuple[int, int, int]:
        citations = item.get("citationCount") or 0
        year = item.get("year") or 0
        source_score = max(SOURCE_PRIORITY.get(src, 0) for src in item.get("sources") or [item.get("source", "")])
        if sort == "date":
            return (year, citations, source_score)
        if sort == "citations":
            return (citations, year, source_score)
        return (source_score, citations, year)