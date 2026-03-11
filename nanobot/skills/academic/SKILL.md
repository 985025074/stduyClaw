---
name: academic
description: Search academic papers and combine them with open web commentary for newcomer-friendly research guidance.
metadata: {"nanobot":{"emoji":"📚"}}
---

# Academic Research

Use this skill when the user asks for any of the following:
- find core papers for a topic
- explain a research area to a beginner
- compare major papers or methods
- track recent papers or discussions
- combine academic sources with blogs, tutorials, or public commentary

## Core tools

- `academic_search` for papers, surveys, metadata, and canonical references
- `web_search` for tutorials, blog posts, project pages, and public discussion pages
- `web_fetch` for extracting readable text from public pages after you find useful URLs

## Working style

1. Clarify scope when the topic is broad.
2. Start with 5-10 representative papers, not an exhaustive dump.
3. Prefer survey papers, foundational papers, and strong recent updates.
4. Explain terminology in plain language for newcomers.
5. When citing discussion or commentary, separate it from paper facts.
6. Do not invent papers, authors, venues, or citation counts.

## Suggested workflow

1. Search papers with `academic_search`.
2. If the user needs practical context, search the web for tutorials and public discussion.
3. Group papers by role: survey, foundational, method family, recent trend.
4. End with a reading order and concrete next questions.

## Example prompts

- "Give me a beginner roadmap for diffusion models."
- "Find the main papers on retrieval-augmented generation and compare them."
- "Search recent graph foundation model papers and summarize the landscape."
- "Find arXiv papers and public discussion for mechanistic interpretability."