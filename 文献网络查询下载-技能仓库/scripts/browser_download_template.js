# 浏览器 Blob 下载模板（Playwright browser_run_code 粘贴用）

/**
 * 用途：站点有反爬(403)时，用真实浏览器会话页面内 fetch + Blob 触发下载。
 * 前提：先导航到文章页建立会话(带 cookie / JS challenge 令牌)。
 * 注意：下载事件保存到 playwright-artifacts-* 临时目录，拿到 path 后要移动到目标目录。
 */
async (page) => {
  // 1. 先打开文章页（建立会话）
  await page.goto('https://example.org/paper/123', { waitUntil: 'domcontentloaded', timeout: 45000 });

  // 2. 找到页面里的真实 PDF 链接（如 MDPI 的 Download PDF / Preprints 的 /v1/download）
  const pdfUrl = await page.evaluate(() => {
    const links = document.querySelectorAll('a');
    for (const a of links) {
      const href = a.href || '';
      const text = (a.textContent || '').trim();
      if (/\.pdf/i.test(href) || text.toLowerCase().includes('download pdf')) return href;
    }
    return null;
  });

  if (!pdfUrl) return { ok: false, reason: '页面内未找到 PDF 链接' };

  // 3. 监听下载事件
  const dlPromise = page.waitForEvent('download', { timeout: 25000 }).catch(e => null);

  // 4. 页面内 fetch（credentials:'include' 带上 cookie）→ Blob → <a download> 触发下载
  await page.evaluate(async (u) => {
    const r = await fetch(u, { credentials: 'include' });
    const buf = await r.arrayBuffer();
    const blob = new Blob([buf], { type: 'application/pdf' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'temp.pdf';               // 每个文件用不同名，避免覆盖
    document.body.appendChild(a);
    a.click();
  }, pdfUrl);

  const dl = await dlPromise;
  if (dl) return { ok: true, path: await dl.path(), filename: dl.suggestedFilename() };
  return { ok: false, reason: '未触发下载事件' };
}

/**
 * 站点 URL 模式备忘：
 * - MDPI 文章页: 页面内找 "Download PDF" 链接，形如 /xxx/pdf?version=...
 * - Preprints: 下载端点是 https://www.preprints.org/manuscript/<ID>/v1/download（直接返回 application/pdf）
 * - DRS (Digital Commons): viewcontent.cgi 直链，但 Node 侧 context.request.get 仍 403，
 *   必须用"导航到文章页 → 页面内 fetch"方式（浏览器内有 challenge 令牌）
 * - EconStor: 页面里 bitstream/.../xxx.pdf 直链
 * - SSRN/Elgar: Cloudflare 人机验证，不要自动破解，停下交给用户
 */
