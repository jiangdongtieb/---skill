# -*- coding: utf-8 -*-
"""
进度清单重建器：扫描 PDF 目录 + 摘要目录，按编号/关键词自动生成 Markdown 进度表。
用法:
    python rebuild_progress.py <清单结构化.json> <PDF目录> <摘要目录> <输出.md>

状态判定优先级: 编号摘要文件 > PDF关键词(>=2词) > 摘要关键词(>=2词) > 弱匹配 > 待确认
"""
import re, json, sys, os, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')


def norm(s):
    return re.sub(r'[^a-z0-9\u4e00-\u9fff]+', '', s.lower())


def kw_match(title, files, min_len=4):
    words = [w for w in re.findall(r'[a-z0-9\u4e00-\u9fff]{%d,}' % min_len, title.lower())]
    best, bs = None, 0
    for f in files:
        fn = f.lower()
        s = sum(1 for w in words if w in fn)
        if s > bs:
            best, bs = f, s
    return best, bs


def rebuild(entries, pdf_dir, abs_dir, out_path):
    pdf_files = [f for f in os.listdir(pdf_dir) if f.lower().endswith('.pdf')]
    abs_files = [f for f in os.listdir(abs_dir) if f.lower().endswith('.txt')]

    abs_by_no = {}
    for f in abs_files:
        m = re.match(r'^(\d{3})_', f)
        if m:
            abs_by_no[int(m.group(1))] = f

    rows = []
    for e in entries:
        no, title = e['no'], e['title']
        absf = abs_by_no.get(no)
        pf, ps = kw_match(title, pdf_files)
        af2, as2 = kw_match(title, abs_files)
        if pf and ps >= 2:
            status, note = '✅', f'PDF: {pf[:48]}'
        elif absf:
            status, note = '📝', f'摘要: {absf[:48]}'
        elif as2 >= 2:
            status, note = '📝', f'摘要: {af2[:48]}'
        elif ps >= 1:
            status, note = '✅', f'PDF(弱): {pf[:48]}'
        elif as2 >= 1:
            status, note = '📝', f'摘要(弱): {af2[:48]}'
        else:
            status, note = '❓', '待确认'
        rows.append((no, title, status, note))

    groups = [('三、公司分析', 99, 134), ('二、行业研报', 52, 98), ('一、学术文献', 1, 51)]
    lines = ['# 文献获取进度清单\n',
             '> 状态: ✅ 已下载 PDF | 📝 已存摘要 | ❓ 待确认\n']
    for gname, lo, hi in groups:
        lines.append(f'## {gname}\n')
        lines.append('| 编号 | 文献 | 状态 | 备注 |')
        lines.append('|---|---|---|---|')
        for no, title, status, note in rows:
            if lo <= no <= hi:
                lines.append(f'| {no} | {title[:48]} | {status} | {note} |')
        lines.append('')

    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    pdf_n = sum(1 for r in rows if r[2] == '✅')
    abs_n = sum(1 for r in rows if r[2] == '📝')
    none_n = sum(1 for r in rows if r[2] == '❓')
    print(f'共 {len(rows)} 条: PDF {pdf_n} | 摘要 {abs_n} | 待确认 {none_n}')
    for r in rows:
        if r[2] == '❓':
            print(f'  #{r[0]} {r[1][:50]}')


if __name__ == '__main__':
    if len(sys.argv) < 5:
        print("用法: python rebuild_progress.py <清单.json> <PDF目录> <摘要目录> <输出.md>")
        sys.exit(1)
    entries = json.load(open(sys.argv[1], encoding='utf-8'))
    rebuild(entries, sys.argv[2], sys.argv[3], sys.argv[4])
