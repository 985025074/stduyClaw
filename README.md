# StudyClaw

StudyClaw 是一个基于 nanobot 定制的学术研究助手项目，目标是帮助新手更快进入某个研究方向，完成论文检索、主题梳理、阅读路线规划和公开讨论内容补充。


拓展功能有：

- 按主题搜索核心论文
- 为新手生成入门学习路线
- 汇总某个方向的代表性工作
- 结合公开网页内容补充教程、博客和讨论

## 项目结构

当前工作区主要包含以下内容：

- `nanobot/`：定制后的 nanobot 主体代码
- `nanobot/nanobot_README.md`：原始 nanobot README 备份
- `nanobot/ACADEMIC_ASSISTANT_CHANGES.md`：本项目对 nanobot 的改动记录

学术助手相关核心文件：

- `nanobot/nanobot/agent/tools/academic.py`：学术论文搜索工具
- `nanobot/nanobot/skills/academic/SKILL.md`：学术研究工作流 skill
- `nanobot/tests/test_academic_tool.py`：最小测试覆盖

## 当前能力

当前已经实现的第一阶段能力包括：

- 新增内置工具 `academic_search`
- 支持 `arxiv`、`semantic_scholar`、`openalex`、`crossref` 多源搜索
- 支持 `auto` 聚合检索、基础去重和排序
- 支持通过 `web_search` 和 `web_fetch` 补充公开网页内容
- 支持通过 skill 约束输出为面向新手的研究辅助风格

## 快速开始

推荐使用虚拟环境运行项目。

### 1. 创建并进入虚拟环境

```bash
cd /home/shiyicong/studyclaw/nanobot
python3 -m venv .venv
source .venv/bin/activate
```

### 2. 安装项目

```bash
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e '.[dev]'
```

如果当前终端没有正确激活虚拟环境，也可以直接使用：

```bash
.venv/bin/python -m pip install -e '.[dev]'
```

### 3. 初始化配置

```bash
.venv/bin/python -m nanobot onboard
```

### 4. 启动 CLI

```bash
.venv/bin/python -m nanobot agent
```

## 配置说明

nanobot 的配置文件默认位于用户目录下的 `.nanobot/config.json`。

最少需要配置一组模型提供商，例如 `minimax`。
推荐使用minimax + opencode进行配置。 

示例：

```json
{
	"providers": {
		"minimax": {
			"apiKey": "YOUR_MINIMAX_API_KEY",
			"apiBase": "https://api.minimaxi.com/v1"
		}
	},
	"agents": {
		"defaults": {
			"provider": "minimax",
			"model": "MiniMax-M2.1"
		}
	}
}
```

学术搜索配置示例：

```json
{
	"tools": {
		"academic": {
			"defaultMaxResults": 5,
			"userAgent": "nanobot-academic/0.1",
			"contactEmail": "your_email@example.com",
			"arxiv": {"enabled": true, "apiKey": "", "baseUrl": ""},
			"semanticScholar": {"enabled": true, "apiKey": "", "baseUrl": ""},
			"openalex": {"enabled": true, "apiKey": "", "baseUrl": ""},
			"crossref": {"enabled": true, "apiKey": "", "baseUrl": ""}
		}
	}
}
```

说明：

- `semanticScholar.apiKey` 不是必填，但建议配置
- `contactEmail` 建议在 OpenAlex 或 Crossref 请求里使用真实邮箱
- 如果只做最小验证，可以先只配置模型，不配置 academic API key

## 使用方式

建议从以下几类问题开始测试：

- “给我一份 diffusion models 的新手入门路线”
- “搜索 RAG 的代表性论文并做对比”
- “找近几年 graph foundation model 的主要工作”
- “帮我梳理 mechanistic interpretability 的核心论文和公开讨论”

## 仓库维护

当前推荐的维护方式是：

- 本地保留 `main`，用于同步 nanobot 上游
- 使用 `academic-main` 作为你的定制开发分支
- GitHub 远端默认展示 `academic-main`
- 原始 nanobot 文档单独保存在 `nanobot/nanobot_README.md`

同步上游时可参考：

```bash
git fetch upstream
git checkout main
git merge upstream/main

git checkout academic-main
git merge main
```

## 现阶段限制

当前还是第一阶段实现，暂时不包含：

- PDF 全文解析
- 深度 citation graph 遍历
- 登录态评论抓取
- Web UI

## 相关文档

- `nanobot/nanobot_README.md`：原始 nanobot README
- `nanobot/ACADEMIC_ASSISTANT_CHANGES.md`：学术助手改动记录
