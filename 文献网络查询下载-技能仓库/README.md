# 文献网络查询下载（使用链接）

**文献批量获取与摘要补全（清单逐篇处理法）**

从实战中沉淀的技能：当用户给出一份"未获取文献清单"（含标题/链接/DOI/残缺摘要），要求逐篇补齐全文 PDF 或完整摘要时使用。

## 结构

```
文献网络查询下载（使用链接）/
├── SKILL.md                      # 主文档：适用场景、用户提示词归纳、7步流程、禁止事项、技术备忘
└── scripts/
    ├── parse_literature_list.py  # 清单解析器：txt → 结构化 JSON
    ├── fetch_pdf_direct.py       # PDF 直连下载器：绕过系统代理，验证 %PDF- 头
    ├── ss_abstract_batch.py      # Semantic Scholar API 批量摘要抓取
    ├── rebuild_progress.py       # 进度清单重建器：扫描产物目录自动统计
    └── browser_download_template.js  # 浏览器 Blob 下载模板（Playwright 粘贴用）
```

## 核心方法论（30 秒速览）

1. **解析清单** → 结构化 JSON，先匹配已有 PDF 划掉已完成条目（避免重复劳动）
2. **按渠道分流**：
   - 开放获取/直链 → `fetch_pdf_direct.py`（Python 直连绕过代理）
   - 反爬站点(403) → 浏览器 + Blob 下载（见 js 模板）
   - 付费墙 → `ss_abstract_batch.py`（Semantic Scholar API 批量摘要）
   - 中文 OA 期刊 → 期刊系统 URL 模式（工程院 `CN/PDF/<DOI>`、工业技术经济 `downloadArticleFile.do?id=<ID>` 等）
   - Cloudflare 人机验证 → 停下交给用户，不破解
3. **维护进度** → Markdown 进度清单，`rebuild_progress.py` 自动重建
4. **最终汇报** → 总数/PDF数/摘要数/需人工条目/产物绝对路径

## 关键陷阱提醒

- Windows 系统代理（127.0.0.1:7897）会让国内站点超时 → `ProxyHandler({})` 绕过
- 下载后必须验证 `%PDF-` 头 + `%%EOF`，HTML 跳转页不能当 PDF 存
- Playwright Node 侧 `context.request.get` 可能 403，页面内 `fetch` 才有效
- 不要破解 Cloudflare 验证码，停下列清单让用户手动完成
