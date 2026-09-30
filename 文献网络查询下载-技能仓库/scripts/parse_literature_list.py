# -*- coding: utf-8 -*-
"""
文献清单解析器：把 Word 提取的清单文本解析为结构化 JSON。
用法:
    python parse_literature_list.py <清单提取.txt> <输出.json> [最大编号]

输入格式（每条）:
    1. 文献标题
    作者 | 年份 | 来源: XXX
    摘要: ...
    DOI: ...
    链接: ...
    下载渠道: ...
"""
import re, sys, json, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


def parse(src_path, out_path, max_no=999):
    with open(src_path, encoding='utf-8') as f:
        lines = [l.rstrip('\n') for l in f.readlines()]

    entries, cur = [], None
    for ln in lines:
        m = re.match(r'^(\d{1,3})\.\s+(.+)$', ln.strip())
        if m and int(m.group(1)) <= max_no:
            if cur:
                entries.append(cur)
            cur = {"no": int(m.group(1)), "title": m.group(2).strip(),
                   "authors": "", "year": "", "source": "",
                   "abstract": "", "doi": "", "url": "", "channel": ""}
            continue
        if cur is not None:
            s = ln.strip()
            if not s:
                continue
            if s.startswith("摘要:"):
                cur["abstract"] = s[3:].strip()
            elif s.startswith("DOI:"):
                cur["doi"] = s[4:].strip()
            elif s.startswith("链接:"):
                cur["url"] = s[3:].strip()
            elif s.startswith("下载渠道:"):
                cur["channel"] = s[5:].strip()
            elif "|" in s and ("来源:" in s or "等" in s):
                parts = [p.strip() for p in s.split("|")]
                cur["authors"] = parts[0]
                if len(parts) > 1:
                    y = re.search(r'(19|20)\d{2}', parts[1])
                    if y:
                        cur["year"] = y.group(0)
                    src = re.search(r'来源:\s*(.+)', s)
                    if src:
                        cur["source"] = src.group(1).strip()
    if cur:
        entries.append(cur)

    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)
    print(f"解析出 {len(entries)} 条 -> {out_path}")
    return entries


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("用法: python parse_literature_list.py <清单提取.txt> <输出.json> [最大编号]")
        sys.exit(1)
    max_no = int(sys.argv[3]) if len(sys.argv) > 3 else 999
    parse(sys.argv[1], sys.argv[2], max_no)
