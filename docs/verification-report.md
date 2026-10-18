# Code Journey 实际部署验证报告

验证日期：2026-10-18  
公网入口：<https://upon-philip-suitable-reforms.trycloudflare.com>  
验证方式：公网 HTTPS 请求 + PowerShell API 测试；另见文末浏览器测试状态。

## 1. 实际运行架构

```
公网浏览器
  │ HTTPS
  ▼
Cloudflare Quick Tunnel（免费、临时）
  │
  ▼
Vite Preview / 前端生产构建（127.0.0.1:4173）
  │ /api、/uploads 反向代理
  ▼
FastAPI / Uvicorn（127.0.0.1:8001）
  │ SQLAlchemy + PyMySQL
  ▼
MySQL 8.0（127.0.0.1:3307，独立数据目录，仅回环地址）
```

本机另有系统 MySQL 服务监听 3306，但本次部署使用独立实例，未改动或迁移原有数据库。

## 2. 验证结果

自动化脚本：`scripts/verify-public.ps1`  
原始结果：`.runtime/verification.json`（本地，已被 Git 忽略）

| 检查项 | 结果 |
| --- | --- |
| 公网首页、CSS、JS 静态资源 | 通过，HTTP 200 |
| `/api/health` | 通过，`status=ok` |
| 外部网络可达性 | 通过，第三方 Jina Reader 抓取公网健康接口返回 `{"status":"ok"}` |
| 注册普通用户 | 通过 |
| 登录与 `/users/me` 身份读取 | 通过，JWT Bearer 正常 |
| 文章列表、详情、中文内容 | 通过，共 3 篇示例文章 |
| 点赞、取消点赞、再次点赞 | 通过，计数与 `is_liked` 一致 |
| 发表评论并回读 | 通过 |
| 其他普通用户删除评论 | 通过，返回 403 |
| 本人删除评论 | 通过 |
| 管理员登录 | 通过，`role=admin` |
| 管理员删除评论 | 通过 |
| 普通用户创建文章 | 通过，返回 403 |
| 管理员创建、更新、删除文章 | 通过 |

汇总：**22 / 22 项通过**。

## 3. 持久化复核

停止并重新启动 FastAPI 与独立 MySQL 后：

- 浏览器测试前，文章点赞数为 1、评论数为 1；
- 评论内容仍可经公网接口读取；
- `post_likes` 和 `comments` 表记录仍在；
- 管理员可重新登录；
- 公网 `/api/health` 恢复为 `ok`。

随后浏览器测试又新增了 1 个点赞和 1 条评论。最终公网 API 返回 `likes=2`、`comment_count=2`，与页面截图一致，说明新增数据也正常写入并持久化。

## 4. 安全处理

- 已从 Git 索引移除 `.env`、`backend/venv`、`frontend/dist`、`__pycache__` 和 `backend/uploads`；本地文件未删除。
- Docker 与本地运行凭据均重新生成，使用随机长字符串；真实值只存在于被忽略的 `.env` / `.env.local`。
- 独立 MySQL 仅监听 `127.0.0.1:3307`，未对公网开放。
- FastAPI 以生产配置启动，未使用 `--reload`；数据库异常响应改为通用提示，详细错误只写服务端日志。
- CORS 与前端同源反代部署兼容；Nginx 配置增加基础安全响应头。
- 注意：旧 `.env` 曾存在于公开 Git 历史中，相关旧密码已作废并轮换；若这些旧值曾在其他服务器使用，仍需在对应服务器上更换。

## 5. 浏览器测试

2026-10-18 在应用内 Chromium 浏览器直接打开公网地址完成了页面级验证：

- 首页文章列表、分类、搜索框和静态资源正常渲染；
- 通过页面表单注册新用户 `uitest_86652844`，注册成功后切换为登录状态；
- 页面显示 `ROLE: USER`，说明 JWT 登录态在浏览器中生效；
- 打开文章详情，LIKES 计数从 1 更新到 2，刷新后仍为 2；
- 通过页面输入框发表评论，评论区显示 2 条评论，包含新评论内容；
- 页面加载评论时有短暂异步等待，随后正常显示，不是数据丢失。

证据截图：

- [公网首页与登录状态](screenshots/public-home.png)
- [文章详情与点赞数](screenshots/public-detail-comments.png)
- [评论区与两条评论](screenshots/public-comments.png)

## 6. 限制与待完成

- 当前公网地址是 Cloudflare Quick Tunnel，免费、临时，URL 可能变化，且需要本机保持开机和进程运行。
- 还没有永久云服务器、固定公网 IP、自有域名和受控 HTTPS 证书。
- 本次未完成云平台控制台截图；需要服务器 SSH 地址/用户或云账号授权后才能做永久部署。
- 目前使用 Vite Preview 提供前端生产资源；正式云服务器应使用仓库中的 Docker Compose + Nginx。

## 7. PPT 截图清单

1. Cloudflare 隧道终端输出中的公网 URL。
2. 公网首页和文章列表。
3. 文章详情页与评论。
4. 注册/登录后的用户状态。
5. 点赞前后的计数变化。
6. `scripts/verify-public.ps1` 的 22 项 PASS 输出。
7. MySQL 中 `users`、`posts`、`comments`、`post_likes` 的查询结果（遮挡密码）。
8. 后端与 MySQL 重启前后的健康检查和持久化结果。
9. Git 中 `.env` 已不被跟踪的状态。

## 8. 2026-10-18 图片与部署配置最终检查

本轮使用本地 MySQL 8 临时库、FastAPI 生产配置和 Vite 生产构建完成，不代表 TiDB Cloud、Render 或 GitHub Pages 已经上线。

| 检查 | 结果 |
| --- | --- |
| 后端自动化测试 | 10 / 10 通过 |
| GitHub Pages 子路径构建 | `VITE_BASE_PATH=/demo-blog/`，构建成功 |
| 子路径静态资源 | 首页、头像、3 类图片、音频均返回 HTTP 200 |
| 浏览器图片渲染 | 头像 `naturalWidth=512`；封面和正文示意图 `naturalWidth=1200` |
| 旧 `/uploads/...` 映射 | 已知文件重写为 `/<base>/images/...` 并成功加载 |
| 本地 MySQL 联调脚本 | 26 / 26 通过（含 4 个静态图片检查） |
| 后端重启持久化 | 登录、点赞状态与评论均保留 |
| 动态上传开关 | 生产配置下返回 403，不写入临时磁盘 |
| CORS | 配置来源预检通过，未列出来源拒绝 |

当前仍缺少 TiDB Cloud、Render 和 GitHub Pages 控制台凭据，因此三项线上部署、TiDB TLS 实际握手和 Pages/Render 跨域均未在本轮验证。
