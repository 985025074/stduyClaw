# Academic Assistant Changes

This file records the initial implementation work for the academic-research assistant built on top of nanobot.

## Scope

Initial MVP focused on paper discovery and research workflow guidance for CLI-first usage.

## Implemented

- Added `academic_search` as a built-in tool.
- Added academic tool configuration under `tools.academic`.
- Registered the academic tool in both the main agent loop and subagent manager.
- Added a bundled `academic` skill to guide paper-first and newcomer-friendly workflows.
- Added unit tests for academic result parsing and aggregation.

## Files Added

- `nanobot/agent/tools/academic.py`
- `nanobot/skills/academic/SKILL.md`
- `tests/test_academic_tool.py`
- `ACADEMIC_ASSISTANT_CHANGES.md`

## Files Updated

- `nanobot/config/schema.py`
- `nanobot/agent/loop.py`
- `nanobot/agent/subagent.py`
- `nanobot/cli/commands.py`

## Configuration

New config block:

```json
{
  "tools": {
    "academic": {
      "defaultMaxResults": 5,
      "userAgent": "nanobot-academic/0.1",
      "contactEmail": "",
      "arxiv": {"enabled": true, "apiKey": "", "baseUrl": ""},
      "semanticScholar": {"enabled": true, "apiKey": "", "baseUrl": ""},
      "openalex": {"enabled": true, "apiKey": "", "baseUrl": ""},
      "crossref": {"enabled": true, "apiKey": "", "baseUrl": ""}
    }
  }
}
```

## Tool Behavior

`academic_search` supports:

- `source=auto|arxiv|semantic_scholar|openalex|crossref`
- `query`
- `count`
- `yearFrom`
- `yearTo`
- `sort=relevance|date|citations`
- `includeAbstract=true|false`

The tool returns normalized JSON results with title, authors, year, abstract, URL, PDF URL, DOI, venue, citation count, and topics when available.

## Current Limits

- This MVP focuses on paper search, not full-text PDF parsing.
- Public discussion is still expected to use `web_search` and `web_fetch`.
- Citation graph traversal is not implemented yet.
- Semantic Scholar key is optional but recommended for higher limits.

## Next Steps

- Add paper detail and citation/related-paper lookup tools.
- Add topic-specific ranking modes for newcomer roadmap generation.
- Add optional PDF extraction and paper-note persistence.
- Add examples to README after the workflow is stable.