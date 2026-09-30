---
name: 文献网络查询下载（使用链接）
display_name: 文献网络查询下载（使用链接）
description: 按"未获取文献清单"逐篇补齐全文 PDF 或完整摘要：解析 Word/文档清单为结构化数据，按开放获取/付费墙/中文期刊/反爬站点分流，用 Python 直连下载 PDF 直链、浏览器 Blob 下载反爬页面、Semantic Scholar API 批量抓取摘要，全程维护进度清单并避免重复劳动。适用于用户给出大量文献清单（含链接/DOI/摘要片段）要求"能下 PDF 就下、下不了就抄完整摘要"的场景。
---

# 文献网络查询下载（使用链接）

## 适用场景

- 用户给出一份"未获取文献清单"（Word/Excel/Markdown，每条含标题、作者、链接/DOI、残缺摘要片段），要求逐篇补齐全文 PDF 或完整摘要
- 目标是"有免费 PDF 就下载，没有 PDF 就把页面上完整的摘要抄下来存 txt"，产物归入文献库
- 清单很长（数十到一百多篇），需要分类分流处理、维护进度、避免重复下载已持有的文献

## 用户提示词中真正有用的工作指示（已归纳）

用户在描述这类任务时，以下指示对执行质量至关重要，收到类似表述时务必落实：

1. **"从下往上做 / 和另一个 agent 分工（它从上往下）"** —— 用户可能同时让多个 agent 处理同一份清单。开工前先问清楚分工方向（从上往下还是从下往上），避免两个 agent 撞车重复下载。
2. **"能下 PDF 就直接下载，不能下就把完整摘要抄下来放 txt，也放进文献库"** —— 这是核心验收标准：开放获取→PDF；付费墙→完整摘要 txt（不是清单里的残缺片段）。
3. **"开一个纯净的浏览器，不要走 WebVPN/代理"** —— 用户明确要求绕过机构代理/WebVPN 直连。注意：系统可能开着本地代理（如 127.0.0.1:7897），会导致国内站点超时；要用 Python `ProxyHandler({})` 直连或确认浏览器不走代理。
4. **"不要轻易删掉什么东西，你自己的过程文件可以删，其他的别动"** —— 只清理自己产生的临时/垃圾文件（如 0 字节、HTML 跳转残留），绝不改动用户已有文献库文件。
5. **"时不时检查一下，把它从工作清单上划掉"** —— 必须维护一个可见的进度清单（Markdown），每完成一篇就更新状态（✅PDF / 📝摘要 / ⚠️需人工），最终让用户能一眼看到全部 134 条各自的状态。
6. **"慢慢搞不着急"** —— 逐篇处理是正确的；但可以用分类批量法加速（同站点一次抓多篇），不必真的逐篇开浏览器。
7. **"其他 agent 也在干这个活"** —— 开工前先盘点已有产物（PDF/摘要目录里已有哪些），把清单中已完成的条目先划掉，避免重复劳动。

### 用户原话示例（触发参考）

> "你直接一个个把链接点开，然后去操作网页端。看看能不能直接没有PDF，你如果能没有PDF的话，那你肯定能直接下载啊。你就这样一个一个搞就行了，慢慢搞，不着急。"
> "我希望你就是开一个比较纯净的一个浏览器，不要走什么webVPN啥的。"
> "一个一个点进去，然后看看有没有 view PDF，有 PDF 就直接点进去下载下来。没有 view PDF 就把完整摘要抄下来，放到 txt 文件里，也放到那个文献库里。"
> "你也不要轻易删掉什么东西，你自己的过程文件可以删，其他就别动了。"
> "从最后一个往上做。时不时可以检查一下，把它从工作清单上划掉。"

这些口语化表述的共同意图：**逐篇补齐清单，能下 PDF 就下，下不了就存完整摘要，维护进度，不破坏已有文件，绕过代理直连。**

## 执行步骤

### 第 1 步：解析清单为结构化数据

- 用 Word 技能提取 docx 文本（`python scripts/extract_text.py 清单.docx 提取.txt`），按 `编号. 标题` 正则切分为条目。
- 把每条解析为结构化 JSON：`{no, title, authors, year, source, abstract, doi, url, channel}`。
- 同时扫描用户文献库已有的 PDF 文件名，用标题关键词与清单条目匹配，**先划掉已经持有 PDF 的条目**（避免重复下载）。

```python
# 解析清单脚本要点（伪代码）
import re, json
lines = open('清单提取.txt', encoding='utf-8').read().splitlines()
entries, cur = [], None
for ln in lines:
    m = re.match(r'^(\d{1,3})\.\s+(.+)$', ln.strip())
    if m and int(m.group(1)) <= 134:
        if cur: entries.append(cur)
        cur = {"no": int(m.group(1)), "title": m.group(2).strip(),
               "abstract": "", "doi": "", "url": "", "channel": ""}
        continue
    if cur:
        s = ln.strip()
        if s.startswith("摘要:"): cur["abstract"] = s[3:].strip()
        elif s.startswith("DOI:"): cur["doi"] = s[4:].strip()
        elif s.startswith("链接:"): cur["url"] = s[3:].strip()
        elif s.startswith("下载渠道:"): cur["channel"] = s[5:].strip()
json.dump(entries, open('清单_结构化.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
```

### 第 2 步：建立进度清单

建一个 Markdown 进度文件（放文献库目录下），列出全部条目（分组：公司分析/行业研报/学术文献），每篇一行，状态列：`⬜ 待处理 | ✅ 已下载 PDF | 📝 已存摘要 | ⚠️ 需人工核查`。每完成一篇就更新；最终重建时用脚本扫描产物目录自动统计。

### 第 3 步：按"下载渠道"分流处理

处理前先看每条清单标注的"下载渠道"（IEEE/Springer/机构订阅/开放获取等），按类型批量处理：

**A. 开放获取 / PDF 直链（MDPI、arXiv、SSRN、中文 OA 期刊、Preprints、EconStor、MERICS 报告等）→ 直接下载**

- 若 URL 本身以 `.pdf` 结尾，先用 Python 直连下载（见第 4 步代码）。
- MDPI 文章页有 `Download PDF` 链接（形如 `/xxx/pdf?version=...`），在页面内 fetch 该链接即可。
- Preprints 下载端点是 `/manuscript/<ID>/v1/download`（返回 application/pdf）。
- EconStor 页面里有 `bitstream/.../*.pdf` 直链。
- 中文期刊（中国工程院院刊/机械工程学报/信息与控制/工业技术经济等）系统 URL 有固定模式：
  - 工程院：文章页 HTML → 真实 PDF 是 `https://www.engineering.org.cn/sscae/CN/PDF/<DOI>`
  - 机械工程学报（qikan.cmes.org）：`CN/PDF/<DOI>` 或 `CN/article/downloadArticleFile.do?attachType=PDF&id=<文章ID>`
  - 信息与控制（xk.sia.cn）：`cn/article/pdf/preview/<DOI>.pdf`
  - 工业技术经济（gyjsjj.com）：先进目录页找文章详情页 → 详情页 HTML 里找 `downloadArticleFile.do?attachType=PDF&id=XXXX`，取 `id` 下载
  - 北师大学报（wkxb.bnu.edu.cn）：`CN/article/downloadArticleFile.do?attachType=PDF&id=<ID>`
  - 科技进步与对策（kjjb.org）：`CN/PDF/<DOI>`

**B. 反爬站点（DRS、SSRN 等返回 403）→ 浏览器 + Blob 下载**

- 用 Playwright 浏览器打开文章页（真实浏览器环境会带上 cookie/JS challenge 令牌）。
- 页面内 fetch 目标 PDF URL（带 `credentials: 'include'`），拿到二进制后转 Blob，创建 `<a download>` 触发下载事件，Playwright 捕获 download 事件并拿到临时路径。
- 详见第 5 步代码。

**C. 付费墙（IEEE、Springer、Wiley、Emerald、ACM、ScienceDirect 等）→ 抓完整摘要存档**

- **Semantic Scholar 公开 API 是最高效的批量摘要来源**：`https://api.semanticscholar.org/graph/v1/paper/DOI:<DOI>?fields=title,abstract,year,authors`，一次可批量几十篇，注意限速（sleep 1 秒）。
- 摘要不在 SS API 的（中文期刊、部分章节）→ 用浏览器打开文章页抓 `Abstract` 段落文本，或 websearch 检索完整摘要。
- 无任何公开摘要的 → 用清单里的原始片段 + 出版信息归档，标注"付费墙，未获取到完整摘要"。

**D. Cloudflare 人机验证（SSRN、Elgar 等）→ 停下交给用户**

- 浏览器页面显示"正在进行安全验证/Cloudflare"时，**不要尝试破解验证码**。
- 标记该条目为"⚠️ 需人工验证"，把摘要（若 websearch 能搜到）先归档，PDF 留给用户手动打开链接过验证后下载，并明确告知。

### 第 4 步：Python 直连下载（绕过系统代理）

Windows 上系统代理（如 CuteCloud/Clash 的 `127.0.0.1:7897`）会让**国内站点直连超时**（`ERR_TIMED_OUT` 或 SSL 握手超时），但百度等又能通。对策是显式绕过代理：

```python
import urllib.request, ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
# 关键：ProxyHandler({}) 显式不走系统代理
opener = urllib.request.build_opener(
    urllib.request.ProxyHandler({}),
    urllib.request.HTTPSHandler(context=ctx)
)
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0'}

url = 'https://example.com/article.pdf'
req = urllib.request.Request(url, headers=UA)
r = opener.open(req, timeout=50)
data = r.read()
if data[:5] == b'%PDF-':          # 验证确实是 PDF
    open('output.pdf', 'wb').write(data)
```

要点：
- 每次下载后**验证 `data[:5] == b'%PDF-'` 且末尾有 `%%EOF`**，否则可能是 HTML 跳转页/错误页，不要存成 pdf。
- 中文 URL 参数必须 `urllib.parse.quote` 编码。
- 失败时不要反复重试同一个 URL，而是去看页面 HTML 里真实的 PDF 链接（正则找 `href=...\.pdf` 或 `downloadArticleFile`）。

### 第 5 步：浏览器 Blob 下载（处理 403/反爬）

```javascript
// Playwright browser_run_code
async (page) => {
  // 1. 先导航到文章页建立会话
  await page.goto('https://example.org/paper/123', { waitUntil: 'domcontentloaded' });
  // 2. 监听下载事件
  const dlPromise = page.waitForEvent('download', { timeout: 25000 }).catch(e => null);
  // 3. 页面内 fetch PDF（带上 cookie），转 Blob 触发下载
  await page.evaluate(async (u) => {
    const r = await fetch(u, { credentials: 'include' });
    const buf = await r.arrayBuffer();
    const blob = new Blob([buf], { type: 'application/pdf' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'paper.pdf';
    document.body.appendChild(a);
    a.click();
  }, 'https://example.org/paper/123/pdf');
  const dl = await dlPromise;
  if (dl) return { path: await dl.path(), filename: dl.suggestedFilename() };
}
```

- 下载事件保存到 `playwright-artifacts-*/` 或 `playwright-mcp-output/<会话ID>/` 临时目录，拿到 path 后**移到文献库目录**并验证。
- 同名文件会被覆盖（如 temp.pdf），批量下载时每个文件用不同 download 名，或下载后立即移动。

### 第 6 步：批量抓摘要（Semantic Scholar API）

```python
import urllib.request, json, time, os

def ss_abstract(doi):
    url = f'https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}?fields=title,abstract,year,authors'
    req = urllib.request.Request(url, headers={'User-Agent': 'research-assistant'})
    data = json.loads(urllib.request.urlopen(req, timeout=30).read())
    return data  # {'title':..., 'abstract':..., 'year':..., 'authors':[...]}

for no, doi in papers:  # 批量处理
    d = ss_abstract(doi)
    if d.get('abstract'):
        fname = f'{int(no):03d}_SS_abstract.txt'
        open(os.path.join(ABS_DIR, fname), 'w', encoding='utf-8').write(
            f'# {d["title"]}\n\n## 完整摘要\n\n{d["abstract"]}\n')
    time.sleep(1.0)  # 限速，避免 429
```

- 失败（404）说明该 DOI 在 SS 没有记录 → 换 websearch 或浏览器抓。
- 摘要文件命名用 `编号_来源.txt`（如 `015_SS_abstract.txt`），方便后期按编号核对进度。

### 第 7 步：进度管理与最终核对

- 每处理完一批就更新 Markdown 进度清单（用 edit 修改对应行状态）。
- 全部处理完后，用脚本扫描 PDF 目录 + 摘要目录，按标题关键词/编号匹配自动统计：`PDF N 篇 / 摘要 M 篇 / 未匹配 K 条`。
- 对"未匹配"条目逐条人工核对（可能是文件名用了中文/缩写导致关键词没匹配上，不代表真缺失）。
- 向用户汇报：总数、PDF 数、摘要数、需人工处理的（Cloudflare）清单、产物绝对路径。

## 禁止事项

- **不要破解/绕过 Cloudflare 人机验证**（SSRN/Elgar 等）：必须停下，标记"需人工验证"，让用户手动完成。
- **不要用 WebVPN/系统代理下载**：用户明确要求纯净直连；代理会导致国内站点超时，用 `ProxyHandler({})` 绕过。
- **不要删除用户已有文件**：只清理自己产生的过程文件（0 字节 PDF、HTML 跳转残留、临时脚本可选保留）。
- **不要把 HTML 跳转页/错误页存成 PDF**：必须验证 `%PDF-` 头 + `%%EOF` 尾。
- **不要在同一浏览器会话里假设 cookie 共享**：Playwright 的 Node 侧 `context.request.get` 可能仍 403（缺少页面内 JS challenge 令牌），页面内 `fetch` 才有效。
- **不要重复下载已持有的文献**：开工前先匹配已有 PDF，把已完成的条目划掉。
- **不要把用户的具体项目名、学校、机构名、具体文献标题清单写进技能正文**（本技能用"文献/清单"等通用表述）。
- **不要假装下载成功**：每次下载后必须验证文件确实存在且是合法 PDF，否则如实报告失败原因（当前 URL、已完成步骤、卡住位置、建议下一步）。

## 关键技术备忘

| 场景 | 方法 | 关键点 |
|---|---|---|
| 清单解析 | 正则切分 + JSON 结构化 | `^\d+\.\s+.+` 匹配条目行 |
| 直连下载 | `urllib.request` + `ProxyHandler({})` | 绕过系统代理；验证 `%PDF-` 头 |
| 反爬站点 | Playwright 页面内 fetch + Blob + download 事件 | `credentials:'include'`；下载到临时目录后移动 |
| 批量摘要 | Semantic Scholar Graph API | `DOI:<doi>` 查询；sleep 限速 |
| 中文 OA 期刊 | 期刊系统 URL 模式 | 工程院 `CN/PDF/<DOI>`；工业技术经济 `downloadArticleFile.do?attachType=PDF&id=<ID>` |
| 进度管理 | Markdown 进度清单 + 脚本重建 | 编号匹配 + 关键词匹配双重校验 |
| 人机验证 | 停下交还用户 | 标记 ⚠️ 需人工验证，不破解 |
