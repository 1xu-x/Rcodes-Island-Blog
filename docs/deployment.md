# Code Journey 部署与课程汇报说明

## 1. 总体架构

```
浏览器
  │
  ▼
Nginx（前端静态资源 + /api、/uploads 反向代理，端口 80/8080）
  │
  ├── /api/*  ──►  FastAPI（Uvicorn，端口 8000）
  │                  └── SQLAlchemy ──► MySQL（端口 3306）
  └── /uploads/* ──► FastAPI 静态文件目录 backend/uploads（仅本地/Docker 持久卷）
```

三个服务通过 Docker Compose 网络 `blog_net` 互联。容器内后端访问数据库的主机名是 `db`，不是 `localhost`。

## 2. 环境变量

复制模板并填写：

```bash
cp .env.example .env
```

关键变量：

| 变量 | 说明 |
| --- | --- |
| `MYSQL_ROOT_PASSWORD` / `MYSQL_PASSWORD` | MySQL root / 业务用户密码 |
| `DATABASE_URL` | 后端数据库连接串；容器内主机名为 `db` |
| `SECRET_KEY` | JWT 签名密钥，务必换成随机长字符串 |
| `ADMIN_USERNAME` / `ADMIN_PASSWORD` | 初始化脚本使用的管理员账号 |
| `CORS_ORIGINS` | 允许的前端来源，多个地址用英文逗号分隔 |

`.env` 已被 `.gitignore` 忽略，不要把真实密码提交到 Git。

## 3. 数据库创建与初始化

MySQL 容器首次启动时，`docker-entrypoint-initdb.d/init.sql` 会执行 `CREATE DATABASE IF NOT EXISTS blog_db`；`MYSQL_DATABASE` 变量本身也会创建同名库。表结构由后端启动时的 `Base.metadata.create_all()` 自动创建，对应：

- `users`：用户、密码哈希、角色、创建时间
- `posts`：文章、摘要、分类、正文、点赞数、浏览量、作者
- `comments`：评论内容、所属文章、评论人、创建时间
- `post_likes`：用户与文章的点赞关系，含 `(user_id, post_id)` 唯一约束

初始化管理员和 3 篇示例文章：

```bash
docker-compose exec backend python -m app.seed
```

脚本是幂等的：已存在的管理员或同标题文章会被跳过。本地开发时在 `backend/` 目录下运行 `python -m app.seed` 即可。

## 4. 本地运行与测试步骤

Docker 方式：

```bash
docker-compose up -d --build
docker-compose exec backend python -m app.seed
```

访问 `http://localhost:8080`，API 文档在 `http://localhost:8080/api/docs`。

本地直跑（见 README）后，按下面清单验收：

1. 未登录浏览文章列表，打开详情页。
2. 未登录点击点赞或评论，前端提示登录，后端返回 401。
3. 注册新账号，在数据库中看到 `users` 表新增一行。
4. 登录后点赞，`post_likes` 表新增一行，刷新页面点赞数不变。
5. 再次点赞取消，记录被删除，计数减一。
6. 发表评论，刷新详情页评论仍存在。
7. 用非本人账号删除该评论，返回 403；本人或管理员删除成功。
8. 普通用户调用 `POST /posts/` 返回 403；管理员可发布、编辑、删除文章。
9. 重启后端，文章、点赞、评论数据仍在。

自动化测试：

```bash
cd backend
python -m pytest -v
```

## 5. 云端部署

### 5.1 需要准备的资源

- 一台带公网 IP 的云主机（2 核 2G 即可做课程演示），建议 Linux（Ubuntu/CentOS/宝塔面板均可）
- 已安装 Docker 与 Docker Compose
- 一个域名（可选；课程演示用 IP 即可）

### 5.2 安全组 / 防火墙端口

在云控制台安全组放行：

- `22`：SSH 远程管理
- `80` / `8080`：前端 Nginx 对外端口
- `8000`（可选，仅在需要直接访问后端调试时开放，演示时可不放行）

MySQL 的 `3306` 不要对公网开放，仅容器网络内访问。

### 5.3 部署步骤

```bash
# 1. 上传代码并进入目录
git clone <你的仓库地址> codejourney && cd codejourney

# 2. 配置环境变量
cp .env.example .env
vi .env   # 修改密码、SECRET_KEY，DATABASE_URL 保持 db 主机名

# 3. 构建并启动
docker-compose up -d --build

# 4. 初始化管理员与示例文章
docker-compose exec backend python -m app.seed

# 5. 验证
curl http://127.0.0.1:8080/api/health
```

### 5.4 前端地址、后端地址与跨域

- 生产环境统一通过 Nginx 的 `80/8080` 访问，浏览器只需要知道前端地址。
- `/api/*` 由 Nginx 反代到容器内 `backend:8000`，因此不存在跨域问题。
- 若把前端与后端分别部署到不同域名/IP，需要把前端公网地址写进 `CORS_ORIGINS`，例如 `CORS_ORIGINS=http://你的前端地址`，并重启后端。

### 5.5 其他提示

- 建议把 `SECRET_KEY`、数据库密码替换为随机强口令。
- 数据持久化在命名卷 `db_data`，`docker-compose down` 不会删除数据；`down -v` 会删除。
- 生产环境建议在 Nginx 前配置 HTTPS（如 Let's Encrypt），并将 HTTP 重定向到 HTTPS。
- Docker Compose 会把 `backend/uploads` 挂载到宿主机；只有在设置 `ENABLE_IMAGE_UPLOAD=true` 且前端以 `VITE_IMAGE_UPLOAD_ENABLED=true` 构建时才启用动态上传。演示部署默认使用 `frontend/public/images` 静态图片。
- Render 免费实例没有持久卷，不能把 `/uploads` 绝对 URL 当持久化存储。迁移说明见 [image-storage-migration.md](image-storage-migration.md)。

## 6. 汇报演示建议流程

1. 展示首页文章列表（说明数据来自 MySQL，而非写死在页面）。
2. 演示搜索与分类筛选。
3. 打开 `/api/docs` 展示注册、登录、点赞、评论、管理员接口。
4. 注册新用户 → 展示数据库 `users` 表新增记录。
5. 点赞/取消点赞 → 展示 `post_likes` 记录变化与唯一约束。
6. 发表评论 → 刷新页面仍在。
7. 普通用户尝试 `POST /posts/` 返回 403，管理员成功发文。
8. 重启后端 → 数据仍在，证明已持久化。

## 7. 本次实际部署记录（2026-10-18）

当前环境没有可用的云服务器 SSH 配置或云平台 CLI 凭据，因此先完成了不依赖云账号的真实公网验证：

- 独立 MySQL 8 实例：`127.0.0.1:3307`，数据目录 `C:\ProgramData\CodexBlog\data`；
- FastAPI：`127.0.0.1:8001`，生产环境变量启动，无 `--reload`；
- 前端：Vite 生产构建 + Preview，`127.0.0.1:4173`；
- 公网入口：Cloudflare Quick Tunnel，`https://upon-philip-suitable-reforms.trycloudflare.com`。

复现命令：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\setup-local-mysql.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start-local-stack.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\start-public-tunnel.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify-public.ps1 -BaseUrl <公网URL>
```

验证结果为 22/22 项通过，并完成了 MySQL 与后端重启后的评论、点赞和管理员登录持久化复核。详细记录见 [verification-report.md](verification-report.md)。

该公网入口是临时的，依赖本机在线，重启隧道后 URL 会变化。永久上线仍需云服务器 SSH 信息（或云平台授权）以及可选域名；有服务器后按第 5 节使用 Docker Compose + Nginx 部署。
