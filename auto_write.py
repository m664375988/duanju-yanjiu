# -*- coding: utf-8 -*-
"""
自动写文脚本（云端 CI 用，纯标准库，无第三方依赖）。
- 从 TOPICS 主题池里挑一个尚未写过的长尾 SEO 主题；
- 调用智谱（Zhipu / GLM）API 生成一篇实操文章 JSON，写入 content/posts/；
- 若 ZHIPU_API_KEY 缺失或主题池已写完，则安全跳过（不阻断后续构建）。
文章字段与现有内容一致：title / date / category / description / tags[] / body(html)
"""
import json
import os
import sys
import random
import datetime
import urllib.request
import urllib.error

ROOT = os.path.dirname(os.path.abspath(__file__))
CONTENT = os.path.join(ROOT, "content", "posts")

# 长尾 SEO 主题池（围绕「短剧 / AI 视频 / 剪辑 / 变现」的低竞争方向）。
# slug 固定，用于判重：已存在同名 json 则视为已覆盖，跳过。
TOPICS = [
    {"slug": "hongguo-fencheng-2026", "category": "变现渠道",
     "tags": ["红果短剧", "分成比例", "提现规则"],
     "keyword": "红果短剧 2026 最新分成比例、结算周期与提现规则"},
    {"slug": "jianying-guanjianzhen", "category": "剪辑实操",
     "tags": ["剪映", "关键帧", "动画"],
     "keyword": "剪映关键帧怎么用：让文字/贴纸动起来的实操步骤"},
    {"slug": "jimeng-tupian-zhuan-shipin", "category": "AI工具",
     "tags": ["即梦", "图生视频", "AI视频"],
     "keyword": "即梦 AI 图片转视频教程：上传一张图生成动态镜头"},
    {"slug": "kelin-shipin-shichang", "category": "AI工具",
     "tags": ["可灵", "视频时长", "额度"],
     "keyword": "可灵 AI 视频最长能生成多少秒、免费额度怎么算"},
    {"slug": "duanju-juben-muban", "category": "脚本创作",
     "tags": ["短剧剧本", "模板", "钩子"],
     "keyword": "可直接套用的短剧剧本模板与黄金前三秒钩子写法"},
    {"slug": "douyin-touliu-shoufei", "category": "变现渠道",
     "tags": ["抖音", "短剧投流", "ROI"],
     "keyword": "抖音短剧投流怎么收费、新手如何控制 ROI 不亏"},
    {"slug": "ai-peiyin-ruanjian", "category": "剪辑实操",
     "tags": ["AI配音", "免费软件", "音色"],
     "keyword": "2026 好用的免费 AI 配音软件推荐与避坑"},
    {"slug": "xiaoshuo-tuiwen", "category": "变现渠道",
     "tags": ["小说推文", "赚钱", "剪辑"],
     "keyword": "小说推文怎么做、一条视频能赚多少钱的实操路径"},
    {"slug": "duanju-banquan", "category": "合规风险",
     "tags": ["短剧版权", "侵权", "素材"],
     "keyword": "短剧素材怎么用才不侵权：音乐/字体/影视片段避坑"},
    {"slug": "koubo-bugaoxing", "category": "拍摄技巧",
     "tags": ["口播", "镜头感", "提词"],
     "keyword": "口播视频怎么拍不尴尬：提词器、眼神与机位技巧"},
    {"slug": "ai-shipin-fenbianlv", "category": "AI工具",
     "tags": ["AI视频", "分辨率", "画质"],
     "keyword": "AI 生成视频分辨率与画质怎么选，1080P 够用吗"},
    {"slug": "duanju-shangchao", "category": "变现渠道",
     "tags": ["短剧上架", "平台", "分成"],
     "keyword": "短剧上架哪些平台分成高：红果/番茄/抖音对比"},
]


def load_existing_slugs():
    if not os.path.isdir(CONTENT):
        return set()
    return {f[:-5] for f in os.listdir(CONTENT) if f.endswith(".json")}


def pick_topic():
    existing = load_existing_slugs()
    candidates = [t for t in TOPICS if t["slug"] not in existing]
    if not candidates:
        return None
    return random.choice(candidates)


def build_prompt(topic):
    return f"""你是一个专注「短剧与 AI 视频制作」的 SEO 内容作者，读者是刚入门的普通创作者。
请围绕主题「{topic['keyword']}」写一篇实用、可照做的长尾文章。

要求：
1. 标题自然包含该主题关键词，吸引点击但不过度标题党。
2. 正文 800–1200 字，中文，通俗易懂，给具体步骤/参数/坑点，不要空话。
3. 结构用 HTML：小标题用 <h2>，段落用 <p>，列表用 <ul>/<ol>，重点用 <strong>。
   可在文末用一个提示框：<div class="hint">...</div> 总结注意事项。
4. 给出 4–6 个中文标签，体现长尾搜索词。

请只输出一个严格 JSON 对象（不要 markdown 代码块、不要额外解释），字段如下：
{{
  "title": "文章标题",
  "description": "一句话摘要，用于 SEO description，60字内",
  "tags": ["标签1", "标签2", "标签3", "标签4"],
  "body": "完整 HTML 正文字符串（含 h2/p/ul/div.hint 等）"
}}
"""


def call_zhipu(api_key, topic):
    url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
    payload = {
        "model": "glm-4-flash",
        "temperature": 0.7,
        "response_format": {"type": "json_object"},
        "messages": [{"role": "user", "content": build_prompt(topic)}],
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data,
        headers={"Authorization": f"Bearer {api_key}",
                 "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=90) as r:
        resp = json.loads(r.read().decode("utf-8"))
    content = resp["choices"][0]["message"]["content"].strip()
    # 容错：去掉可能被包裹的 ```json ``` 标记
    if content.startswith("```"):
        content = content.strip("`")
        if content.lower().startswith("json"):
            content = content[4:]
    return json.loads(content)


def main():
    api_key = os.environ.get("ZHIPU_API_KEY")
    if not api_key:
        print("auto_write: 未配置 ZHIPU_API_KEY，跳过写文（已有文章照常构建）")
        return
    topic = pick_topic()
    if not topic:
        print("auto_write: 主题池已全部覆盖，跳过生成（避免重复灌水）")
        return
    try:
        article = call_zhipu(api_key, topic)
    except Exception as e:
        print(f"auto_write: 调用智谱失败，跳过本次写文：{type(e).__name__}: {e}")
        return
    # 补全/校正字段
    article["date"] = datetime.date.today().isoformat()
    article["category"] = topic["category"]
    article["slug"] = topic["slug"]
    if not article.get("tags"):
        article["tags"] = topic["tags"]
    # 校验必要字段
    for field in ("title", "description", "body"):
        if field not in article:
            print(f"auto_write: 模型返回缺少字段 {field}，跳过")
            return
    os.makedirs(CONTENT, exist_ok=True)
    out = os.path.join(CONTENT, topic["slug"] + ".json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(article, f, ensure_ascii=False, indent=2)
    print(f"auto_write: 已生成 {topic['slug']}.json（{article['title']}）")


if __name__ == "__main__":
    main()
