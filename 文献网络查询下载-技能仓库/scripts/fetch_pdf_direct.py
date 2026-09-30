# -*- coding: utf-8 -*-
"""
PDF 直连下载器：绕过系统代理下载 PDF 直链，验证 %PDF- 头。
用法:
    python fetch_pdf_direct.py <url> <输出路径> [referer]

适用: MDPI/arXiv/SSRN/中文OA期刊/任何返回 application/pdf 的直链。
注意: 系统代理(如 127.0.0.1:7897)会导致国内站点超时, 这里用 ProxyHandler({}) 显式绕过。
"""
import urllib.request, ssl, sys, os, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
opener = urllib.request.build_opener(
    urllib.request.ProxyHandler({}),
    urllib.request.HTTPSHandler(context=ctx)
)

DEFAULT_UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0'


def fetch(url, timeout=50, referer=None):
    headers = {'User-Agent': DEFAULT_UA}
    if referer:
        headers['Referer'] = referer
    req = urllib.request.Request(url, headers=headers)
    return opener.open(req, timeout=timeout)


def download(url, out_path, referer=None, timeout=50, min_size=50000):
    """下载并验证 PDF；返回 (bool, 说明)"""
    try:
        r = fetch(url, timeout=timeout, referer=referer)
        data = r.read()
        ctype = r.headers.get('Content-Type', '')
        is_pdf = data[:5] == b'%PDF-' and data.rfind(b'%%EOF') > 0
        if is_pdf:
            os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
            with open(out_path, 'wb') as f:
                f.write(data)
            return True, f"OK {len(data)//1024}KB {ctype[:30]}"
        if len(data) < min_size and 'pdf' not in ctype.lower():
            return False, f"非PDF(可能是HTML跳转页) len={len(data)} head={data[:30]!r}"
        # 是 HTML 页面: 尝试在页面里找真实 PDF 链接
        import re
        txt = data.decode('utf-8', errors='replace')
        links = re.findall(r'(?:href|src)=["\']([^"\']*\.pdf[^"\']*)["\']', txt, re.I)
        return False, f"页面含PDF链接: {links[:3]}"
    except Exception as e:
        return False, f"{type(e).__name__}: {str(e)[:120]}"


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("用法: python fetch_pdf_direct.py <url> <输出路径> [referer]")
        sys.exit(1)
    ref = sys.argv[3] if len(sys.argv) > 3 else None
    ok, msg = download(sys.argv[1], sys.argv[2], referer=ref)
    print(('SAVED: ' if ok else 'FAIL: ') + msg)
    sys.exit(0 if ok else 1)
