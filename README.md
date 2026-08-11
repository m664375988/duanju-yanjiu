# 短剧研究所（自动内容站）

纯静态 SEO 内容站，围绕「短剧 / AI 视频 / 剪辑 / 变现」输出长尾实操文章。
整站零后端、零依赖，由 GitHub Actions 每周自动写文 → 构建 → 部署到 GitHub Pages。

## 工作流（全自动，本地关机也跑）
- `auto_write.py`：调智谱 GLM 从主题池挑未覆盖的主题生成一篇文章 JSON 到 `content/posts/`。
- `build.py`：读 `content/posts/*.json` 生成静态站点到 `site/`（含内链、sitemap、robots、IndexNow 验证文件）。
- GitHub Actions（`publish.yml`）每周一北京时间 09:00 触发：写文 → 构建 → 部署 Pages → 提交 IndexNow（Bing 收录）。
- 主题池写完后脚本自动跳过，不会重复灌水。

## 本地预览
```bash
python build.py
# 然后用任意静态服务器打开 site/，例如：
python -m http.server -d site 8000
```
默认 `SITE_URL` 指向旧的 CloudStudio 临时域名，仅供本地预览；线上由 CI 用环境变量覆盖为 GitHub Pages 地址。

## 上线所需（一次性配置，之后全自动）
1. 创建 GitHub 仓库并 push 本目录（首次需 GitHub PAT，用完可撤销）。
2. 仓库 **Settings → Secrets and variables → Actions** 添加 `ZHIPU_API_KEY`（智谱开放平台 API key）。
3. 仓库 **Settings → Pages → Build and deployment → Source** 选「GitHub Actions」。
4. 仓库 **Settings → Actions → General → Workflow permissions** 设为「Read and write」（让 GITHUB_TOKEN 能把新文章推回仓库）。

## 备注
- 站点地址形如 `https://<用户名>.github.io/<仓库名>/`，是公网稳定域名，百度/Google 都能正常抓取（解决了此前 CloudStudio 沙箱被搜索引擎拒连的收录死路）。
- 真变现（AdSense / 平台分成）仍需主人一次性开账户，与自动化无关。
