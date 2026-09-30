# -*- coding: utf-8 -*-
"""
Semantic Scholar API 批量摘要抓取器：付费墙文献最省力的摘要来源。
用法:
    python ss_abstract_batch.py <papers.json> <摘要目录>
    papers.json: [{"no": 15, "doi": "10.xxx/yyy"}, ...]

注意: 每次请求后 sleep 限速, 避免 429; 摘要缺失(404/空)的条目会列出, 转用 websearch/浏览器。
"""
import urllib.request, json, sys, os, time, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

API = 'https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}?fields=title,abstract,year,authors'
UA = {'User-Agent': 'Mozilla/5.0 (research assistant)'}


def get_abstract(doi, timeout=30):
    url = API.format(doi=doi)
    req = urllib.request.Request(url, headers=UA)
    data = json.loads(urllib.request.urlopen(req, timeout=timeout).read())
    return data


def save_abstract(no, data, out_dir):
    title = data.get('title', '')
    abstract = data.get('abstract') or ''
    if not abstract:
        return False
    fname = f'{int(no):03d}_SS_abstract.txt'
    content = (
        f'# {title}\n\n'
        f'- 作者：{", ".join(a["name"] for a in data.get("authors", [])[:5])} | {data.get("year", "")}\n'
        f'- 来源：Semantic Scholar API（付费墙文献，未获取全文 PDF）\n'
        f'- 获取日期：{time.strftime("%Y-%m-%d")}\n\n'
        f'## 完整摘要\n\n{abstract}\n'
    )
    with open(os.path.join(out_dir, fname), 'w', encoding='utf-8') as f:
        f.write(content)
    return True


def batch(papers, out_dir, interval=1.0):
    os.makedirs(out_dir, exist_ok=True)
    ok, miss = 0, []
    for p in papers:
        try:
            d = get_abstract(p['doi'])
            if save_abstract(p['no'], d, out_dir):
                ok += 1
                print(f"#{p['no']} OK: {d.get('title','')[:50]}")
            else:
                miss.append((p['no'], p['doi'], '无摘要'))
                print(f"#{p['no']} 无摘要")
        except Exception as e:
            miss.append((p['no'], p['doi'], f'{type(e).__name__}'))
            print(f"#{p['no']} ERR {type(e).__name__}: {str(e)[:60]}")
        time.sleep(interval)
    print(f"\n完成: {ok} 篇摘要已存, {len(miss)} 篇缺失/失败")
    for no, doi, reason in miss:
        print(f"  #{no} {doi} -> {reason}")
    return ok


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("用法: python ss_abstract_batch.py <papers.json> <摘要目录>")
        sys.exit(1)
    papers = json.load(open(sys.argv[1], encoding='utf-8'))
    batch(papers, sys.argv[2])
