# 学术助手改动记录

这个文件用于记录基于 nanobot 实现学术研究助手时，第一阶段落下来的核心改动。

## 范围

当前版本是第一阶段 MVP，重点覆盖 CLI 场景下的论文检索与研究工作流引导。

## 已实现内容

- 新增内置工具 `academic_search`。
- 在 `tools.academic` 下新增学术搜索相关配置。
- 在主 Agent 循环和 Subagent 管理器中都注册了学术工具。
- 新增内置 `academic` skill，用于约束以论文检索为主、面向新手友好的研究流程。
- 新增了学术搜索结果解析与聚合的最小单元测试。

## 新增文件

- `nanobot/agent/tools/academic.py`
- `nanobot/skills/academic/SKILL.md`
- `tests/test_academic_tool.py`
- `ACADEMIC_ASSISTANT_CHANGES.md`

## 更新文件

- `nanobot/config/schema.py`
- `nanobot/agent/loop.py`
- `nanobot/agent/subagent.py`
- `nanobot/cli/commands.py`

## 配置

新增配置块如下：

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

## 工具行为

`academic_search` 目前支持：

- `source=auto|arxiv|semantic_scholar|openalex|crossref`
- `query`
- `count`
- `yearFrom`
- `yearTo`
- `sort=relevance|date|citations`
- `includeAbstract=true|false`

该工具会返回统一格式的 JSON 结果，字段包括标题、作者、年份、摘要、URL、PDF URL、DOI、期刊或会议、引用数和主题标签等可用元数据。

## 当前限制

- 当前 MVP 重点是论文检索，不包含 PDF 全文解析。
- 公开讨论内容仍然依赖 `web_search` 和 `web_fetch` 来补充。
- 还没有实现 citation graph 的深入遍历能力。
- Semantic Scholar 的 API key 不是必填，但配置后更适合长期使用。

## 下一步

- 增加论文详情、引用关系和相关论文查询工具。
- 增加面向新手学习路线生成的主题排序模式。
- 增加可选的 PDF 提取和论文笔记持久化能力。
- 在工作流稳定后，把使用示例补充进 README。