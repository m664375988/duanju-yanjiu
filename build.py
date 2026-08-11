# -*- coding: utf-8 -*-
"""
自动内容站生成器（零依赖，纯标准库）
读取 content/posts/*.json -> 生成静态站点到 site/
文章字段: title, date(YYYY-MM-DD), description, tags[], category, body(html)
"""
import json
import os
import html
import datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
CONTENT = os.path.join(ROOT, "content", "posts")
SITE = os.path.join(ROOT, "site")
SITE_POSTS = os.path.join(SITE, "posts")

# 站点域名。本地/CI 可用环境变量覆盖（CI 传 GitHub Pages 地址）。
# 默认值保留为旧 CloudStudio 临时域名，仅供本地预览；线上以 CI 传入为准。
SITE_URL = os.environ.get("SITE_BASE_URL", "https://99dd442f06a54ed986e70bfe7123563e.sh3.agentos-app.net")
# GitHub Pages 项目站点子路径，如 "/duanju-yanjiu"；根域名部署留空。
BASE = os.environ.get("SITE_BASE_PATH", "")
SITE_TITLE = "短剧研究所"
SITE_DESC = "短剧与 AI 视频制作实操指南：从脚本、分镜、AI 生成到剪辑变现，手把手带你做出能赚钱的短剧。"
SITE_AUTHOR = "短剧研究所"

# IndexNow 密钥（Bing 等引擎免登录收录用）。站点根目录会生成 <KEY>.txt 供引擎验证。
INDEXNOW_KEY = "902163790d4f4e218e1f48e22affac76"

# Google Search Console 验证：主人在 GSC 拿到验证 HTML 文件名与内容后填入，部署即完成验证。
GSC_VERIFY_FILE = ""      # 例如 "google1234abc.html"
GSC_VERIFY_CONTENT = ""   # 该文件应包含的完整内容（GSC 页面会给出）

# 百度搜索资源平台验证文件（预留通道，当前未启用）。
# 注意：本项目部署在 CloudStudio 沙箱临时域名上，百度爬虫连不到，验证无意义。
# 若日后迁移到稳定公网域名（如 GitHub Pages / Cloudflare Pages），再在此填入并填 BAIDU_TOKEN 即可启用。
BAIDU_VERIFY_FILE = ""      # 例如 "baidu_verify_codeva-xxxx.html"
BAIDU_VERIFY_CONTENT = ""   # 该文件应包含的验证字符串

CSS = """
:root{--bg:#ffffff;--fg:#1f2328;--muted:#6b7280;--brand:#e11d48;--brand2:#fb7185;--line:#e5e7eb;--card:#f9fafb;}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;background:var(--bg);color:var(--fg);line-height:1.75;font-size:17px}
a{color:var(--brand);text-decoration:none}
a:hover{text-decoration:underline}
header.site{border-bottom:1px solid var(--line);background:linear-gradient(180deg,#fff,#fff)}
.wrap{max-width:760px;margin:0 auto;padding:0 20px}
.topbar{display:flex;align-items:center;justify-content:space-between;height:64px}
.logo{font-size:22px;font-weight:800;color:var(--brand);letter-spacing:.5px}
.nav a{margin-left:18px;color:var(--muted);font-size:15px}
.nav a:hover{color:var(--brand)}
main{padding:40px 0 60px}
.hero{margin-bottom:36px}
.hero h1{font-size:30px;line-height:1.3;margin-bottom:10px}
.hero p{color:var(--muted);font-size:16px}
.post-list{display:flex;flex-direction:column;gap:22px}
.card{border:1px solid var(--line);border-radius:14px;padding:20px 22px;background:var(--card);transition:.15s}
.card:hover{border-color:var(--brand2);box-shadow:0 6px 20px rgba(225,29,72,.08)}
.card h2{font-size:20px;margin-bottom:8px}
.card .meta{color:var(--muted);font-size:13px;margin-bottom:8px}
.card p{color:#374151;font-size:15px}
.tags{margin-top:10px}
.tag{display:inline-block;background:#ffe4e6;color:var(--brand);font-size:12px;padding:2px 10px;border-radius:999px;margin-right:6px}
article h1{font-size:30px;line-height:1.3;margin-bottom:8px}
article .meta{color:var(--muted);font-size:14px;margin-bottom:26px;border-bottom:1px solid var(--line);padding-bottom:16px}
article h2{font-size:24px;margin:34px 0 12px}
article h3{font-size:19px;margin:24px 0 10px}
article p{margin:14px 0}
article ul,article ol{margin:14px 0 14px 24px}
article li{margin:8px 0}
article blockquote{border-left:4px solid var(--brand2);background:#fff5f6;padding:12px 16px;margin:18px 0;border-radius:0 10px 10px 0;color:#7f1d2b}
article code{background:#f1f5f9;padding:2px 6px;border-radius:6px;font-size:14px}
article pre{background:#0f172a;color:#e2e8f0;padding:16px;border-radius:10px;overflow:auto;font-size:14px;margin:16px 0}
article pre code{background:none;color:inherit;padding:0}
.hint{background:#fffbeb;border:1px solid #fde68a;color:#92400e;padding:12px 16px;border-radius:10px;margin:18px 0;font-size:15px}
.related{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px 16px 14px 34px;margin:30px 0}
.related li{margin:7px 0}
.related a{color:var(--brand)}
footer.site{border-top:1px solid var(--line);color:var(--muted);font-size:13px;text-align:center;padding:24px 0}
"""

def load_posts():
    posts = []
    if not os.path.isdir(CONTENT):
        return posts
    for fn in sorted(os.listdir(CONTENT)):
        if not fn.endswith(".json"):
            continue
        with open(os.path.join(CONTENT, fn), encoding="utf-8") as f:
            data = json.load(f)
        data["slug"] = fn[:-5]
        posts.append(data)
    posts.sort(key=lambda p: p.get("date", ""), reverse=True)
    return posts

def layout(title, desc, body, is_post=False):
    canonical = (SITE_URL + BASE + "/") if not is_post else (SITE_URL + BASE + "/posts/" + title + ".html")
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<link rel="canonical" href="{canonical}">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(desc)}">
<meta property="og:type" content="{'article' if is_post else 'website'}">
<style>{CSS}</style>
</head>
<body>
<header class="site"><div class="wrap topbar">
<a class="logo" href="/">短剧研究所</a>
<nav class="nav"><a href="/">首页</a><a href="/about.html">关于</a></nav>
</div></header>
<main><div class="wrap">
{body}
</div></main>
<footer class="site">© {datetime.date.today().year} 短剧研究所 · 用 AI 把短剧制作门槛打到地板价</footer>
</body>
</html>"""

def render_index(posts):
    cards = []
    for p in posts:
        tags = "".join(f'<span class="tag">{html.escape(t)}</span>' for t in p.get("tags", []))
        cards.append(f"""<a class="card" href="{BASE}/posts/{p['slug']}.html">
<h2>{html.escape(p['title'])}</h2>
<div class="meta">{html.escape(p.get('date',''))} · {html.escape(p.get('category',''))}</div>
<p>{html.escape(p.get('description',''))}</p>
<div class="tags">{tags}</div></a>""")
    body = f"""<section class="hero">
<h1>短剧与 AI 视频制作实操指南</h1>
<p>{html.escape(SITE_DESC)}</p></section>
<div class="post-list">{"".join(cards)}</div>"""
    return layout(SITE_TITLE, SITE_DESC, body, is_post=False)

def related_posts(p, all_posts, n=3):
    """按 同分类(权重2) + 共享标签(权重1) 计算相关度，返回前 n 篇。"""
    others = [x for x in all_posts if x.get("slug") != p.get("slug")]
    def score(x):
        shared = set(p.get("tags", [])) & set(x.get("tags", []))
        cat = 2 if p.get("category") == x.get("category") else 0
        return len(shared) + cat
    others.sort(key=score, reverse=True)
    return others[:n]

def render_post(p, all_posts):
    tags = "".join(f'<span class="tag">{html.escape(t)}</span>' for t in p.get("tags", []))
    related = related_posts(p, all_posts)
    rel_html = ""
    if related:
        items = "".join(
            f'<li><a href="{BASE}/posts/{html.escape(r["slug"])}.html">{html.escape(r["title"])}</a></li>'
            for r in related)
        rel_html = f'<h2>相关阅读</h2><ul class="related">{items}</ul>'
    body = f"""<article>
<h1>{html.escape(p['title'])}</h1>
<div class="meta">{html.escape(p.get('date',''))} · {html.escape(p.get('category',''))} · {html.escape(SITE_AUTHOR)}</div>
{p.get('body','')}
<div class="tags" style="margin-top:30px">{tags}</div>
{rel_html}
<p style="margin-top:24px"><a href="/">← 返回首页</a></p>
</article>"""
    return layout(p["title"], p.get("description", ""), body, is_post=True)

def render_about():
    body = """<article>
<h1>关于本站</h1>
<div class="meta">用 AI 把短剧制作门槛打到地板价</div>
<p>「短剧研究所」专注一件事：把短剧和 AI 视频的实战制作方法，拆成普通人能照做的步骤。</p>
<p>我们不堆工具名词，只讲真实流程、参数、踩坑点。内容由自动化工作流持续更新——检索热点、写成实操文章、公开上线，尽量让你不用动手也能持续获得可用经验。</p>
<h2>你会看到</h2>
<ul>
<li>短剧脚本结构与爆款钩子写法</li>
<li>即梦 / 可灵 / 海螺等 AI 视频工具的真实分工与参数</li>
<li>角色一致性、成本控制、剪辑节奏等硬核技巧</li>
<li>平台分成、小说推文、商单等变现路径</li>
</ul>
</article>"""
    return layout("关于本站", "短剧研究所的定位与内容方向", body, is_post=False)

def render_sitemap(posts):
    urls = [f"  <url><loc>{SITE_URL}{BASE}/</loc></url>",
            f"  <url><loc>{SITE_URL}{BASE}/about.html</loc></url>"]
    for p in posts:
        urls.append(f"  <url><loc>{SITE_URL}{BASE}/posts/{p['slug']}.html</loc></url>")
    return '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(urls) + "\n</urlset>"

def main():
    posts = load_posts()
    os.makedirs(SITE_POSTS, exist_ok=True)
    with open(os.path.join(SITE, "index.html"), "w", encoding="utf-8") as f:
        f.write(render_index(posts))
    with open(os.path.join(SITE, "about.html"), "w", encoding="utf-8") as f:
        f.write(render_about())
    for p in posts:
        with open(os.path.join(SITE_POSTS, p["slug"] + ".html"), "w", encoding="utf-8") as f:
            f.write(render_post(p, posts))
    with open(os.path.join(SITE, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(render_sitemap(posts))
    with open(os.path.join(SITE, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}{BASE}/sitemap.xml\n")
    # IndexNow 验证文件：站点根目录 <KEY>.txt，内容为 KEY 本身
    with open(os.path.join(SITE, INDEXNOW_KEY + ".txt"), "w", encoding="utf-8") as f:
        f.write(INDEXNOW_KEY)
    # Google Search Console 验证文件（主人提供文件名+内容后自动部署验证）
    if GSC_VERIFY_FILE:
        with open(os.path.join(SITE, GSC_VERIFY_FILE), "w", encoding="utf-8") as f:
            f.write(GSC_VERIFY_CONTENT)
    # 百度搜索资源平台验证文件（主人提供文件名+内容后自动部署验证）
    if BAIDU_VERIFY_FILE:
        with open(os.path.join(SITE, BAIDU_VERIFY_FILE), "w", encoding="utf-8") as f:
            f.write(BAIDU_VERIFY_CONTENT)
    print(f"OK: built {len(posts)} posts -> {SITE}")

if __name__ == "__main__":
    main()
