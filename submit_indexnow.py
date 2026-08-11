# -*- coding: utf-8 -*-
"""把全站 URL 通过 IndexNow 提交给 Bing 等引擎（免登录、可重复运行）。
读取 content/posts/*.json 构建 URL 列表，POST 到 api.indexnow.org。
"""
import json
import os
import urllib.request
import urllib.error

ROOT = os.path.dirname(os.path.abspath(__file__))
CONTENT = os.path.join(ROOT, "content", "posts")
SITE_URL = os.environ.get("SITE_BASE_URL", "https://99dd442f06a54ed986e70bfe7123563e.sh3.agentos-app.net")
KEY = "902163790d4f4e218e1f48e22affac76"
BASE = os.environ.get("SITE_BASE_PATH", "")

# 百度主动推送 token：主人在「百度搜索资源平台」获取后填入；留空则跳过百度推送。
BAIDU_TOKEN = ""


def submit_baidu(urls):
    if not BAIDU_TOKEN:
        print("baidu: token 未配置，跳过")
        return
    api = f"http://data.zz.baidu.com/urls?site={SITE_URL}&token={BAIDU_TOKEN}"
    body = "\n".join(urls).encode("utf-8")
    req = urllib.request.Request(
        api, data=body, headers={"Content-Type": "text/plain"}
    )
    try:
        r = urllib.request.urlopen(req, timeout=25)
        print(f"baidu_status={r.status} {r.read().decode()[:200]}")
    except urllib.error.HTTPError as e:
        print(f"baidu_http_error={e.code} {e.read().decode()[:200]}")
    except Exception as e:
        print(f"baidu_err={type(e).__name__}: {e}")


def main():
    slugs = [f[:-5] for f in os.listdir(CONTENT) if f.endswith(".json")]
    urls = [f"{SITE_URL}{BASE}/", f"{SITE_URL}{BASE}/about.html"] + \
           [f"{SITE_URL}{BASE}/posts/{s}.html" for s in slugs]
    host = SITE_URL.split("//", 1)[1]
    payload = {
        "host": host,
        "key": KEY,
        "keyLocation": f"{SITE_URL}{BASE}/{KEY}.txt",
        "urlList": urls,
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        "https://api.indexnow.org/indexnow",
        data=data,
        headers={"Content-Type": "application/json"},
    )
    try:
        r = urllib.request.urlopen(req, timeout=25)
        print(f"indexnow_status={r.status} submitted={len(urls)}")
    except urllib.error.HTTPError as e:
        print(f"indexnow_http_error={e.code} {e.read().decode()[:200]}")
    except Exception as e:
        print(f"indexnow_err={type(e).__name__}: {e}")
    # 百度主动推送（token 配置后生效）
    submit_baidu(urls)


if __name__ == "__main__":
    main()
