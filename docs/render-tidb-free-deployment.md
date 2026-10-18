# Render + TiDB Cloud Starter 免费部署检查与步骤

本文只描述检查结果和可执行步骤，不代表已经完成公网部署。

## 1. 当前项目检查结果

| 项目 | 当前情况 |
| --- | --- |
| 后端 | FastAPI + SQLAlchemy + PyMySQL + passlib(bcrypt) + python-jose(JWT) |
| 数据库 | MySQL；本地可用 MySQL 8 或 SQLite 测试，生产连接串由 `DATABASE_URL` 提供 |
| 前端 | Vue 3 + Vite + Tailwind CSS；请求路径统一为 `/api/...` |
| 测试 | `python -m pytest -q`：10 项通过 |
| 前端构建 | `npm run build`：构建成功 |
| Git | `main` 比 `origin/main` 领先 1 个提交，存在未提交修改；`origin` 指向原项目仓库，不是个人 Pages 仓库 |

当前代码有两个会影响 Render + GitHub Pages 的问题，已做最小修正：

1. 原 `database.py` 在连接串已有 `?ssl_...` 时仍追加 `?charset=utf8mb4`，会产生两个问号。现在改用 SQLAlchemy `URL` 对象合并查询参数。
2. 前端固定请求 `/api/...`，而 Render 后端直接暴露 `/...`。现在后端增加 `/api/*` 到 `/*` 的兼容处理，前端无需改动全部请求代码。

本地生产模式冒烟测试已通过：启动 seed 自动创建管理员和 3 篇示例文章；`/api/health`、注册、登录、点赞、评论和 CORS 预检均正常；停止并重启后端后，评论和点赞仍能读回。后续还使用本地 MySQL 8 临时库完成了同样的 26 项联调与重启复核。上述结果不代表已经验证 TiDB Cloud 或 Render。

## 2. 方案是否可行

可行，适合个人博客和课程演示，但不属于高可用生产环境。三个免费资源可以组合使用：

- GitHub Pages：托管 Vite 构建后的静态文件。
- Render Free Web Service：运行 FastAPI，使用 `$PORT` 监听，免费计划为 0.1 CPU / 512 MB。
- TiDB Cloud Starter：MySQL 兼容，免费额度为每实例 5 GiB 行存 + 每月 5000 万 RU。

需要接受的免费计划限制：

- Render 免费服务 15 分钟无请求会休眠，下次请求约需 1 分钟唤醒。
- Render 免费服务每月 750 实例小时，文件系统是临时的；上传图片会在重启、重新部署或休眠后丢失。
- 演示版本默认关闭动态上传。固定头像、封面和正文展示图放在 `frontend/public/images`，随 GitHub Pages 发布；数据库只保存相对静态路径或稳定 https 外链。
- 即使保留上传接口，返回的 Render 绝对 URL 也只表示“当前实例可访问”，不代表持久化。文件仍保存在临时文件系统中，重启、重新部署或休眠后可能丢失。
- Render 免费服务没有 Shell 和一次性 Job，因此管理员初始化改为可选的启动时幂等 seed。
- TiDB Starter 要求 TLS；达到免费额度后会拒绝新连接，不会自动升级为付费。
- Render 和 TiDB 之间走公网，免费 Render 服务没有固定出口 IP，因此 TiDB 公网防火墙通常要对全部 IP 开放；请使用强密码并保持 TLS 校验。

## 3. 先创建 TiDB Cloud Starter

1. 登录 TiDB Cloud，创建 **Starter** 实例，兼容模式选择 **MySQL Compatible**。
2. 云厂商和区域优先选择与 Render 服务相同的区域，例如新加坡。
3. 将 **Spending Limit 设为 0**。TiDB 文档说明：限额为 0 时实例保持免费；限额大于 0 才需要绑定信用卡。不要添加支付方式。
4. 在实例的 SQL Editor 执行：

```sql
CREATE DATABASE IF NOT EXISTS blog_db;
```

也可以暂时直接使用实例自带的 `test` 库，但本文统一使用 `blog_db`。

5. 在 **Connect** 对话框生成密码，保存到密码管理器。密码关闭后不会再次显示。
6. 记录以下值：

- Host：例如 `gateway01.ap-southeast-1.prod.aws.tidbcloud.com`
- Port：`4000`
- User：必须带实例前缀，例如 `3pTAoNNegb47Uc8.root`
- Database：`blog_db`
- Password：生成的随机密码

7. 新建实例默认允许全部公网 IP。若已经删除该规则，请确认 Render 能连接；Render Free 的出口 IP 不固定，不能只加入本机 IP。

## 4. 生成数据库连接串

密码中的 `@`、`:`、`/`、`?`、`#`、`%` 等字符必须 URL 编码。可在本地运行：

```powershell
python -c "from urllib.parse import quote; print(quote('把你的数据库密码放这里', safe=''))"
```

最终格式：

```text
mysql+pymysql://<prefix>.root:<url-encoded-password>@<host>:4000/blog_db?charset=utf8mb4&ssl_ca=/etc/ssl/certs/ca-certificates.crt&ssl_verify_cert=true&ssl_verify_identity=true
```

要点：

- 驱动是 `mysql+pymysql`。
- 端口是 TiDB Starter 的公网端口 `4000`。
- `ssl_ca`、`ssl_verify_cert=true`、`ssl_verify_identity=true` 三项必须保留。
- Render 的 Python 原生运行时使用 Debian 系统的 CA 路径 `/etc/ssl/certs/ca-certificates.crt`。
- 如果在 Windows 本地直连 TiDB 测试，可下载 Let's Encrypt 的公开证书 [ISRG Root X1](https://letsencrypt.org/certs/isrgrootx1.pem)，把 `ssl_ca` 改成该 PEM 的绝对路径，例如 `C:/certs/isrgrootx1.pem`。
- CA 证书是公开文件，不是密钥；数据库密码和 JWT 密钥才是必须保密的凭据。

## 5. 部署 Render 后端

### 5.1 先把代码放到个人仓库

当前本地 `origin` 指向 `Acselerator/Rcodes-Island-Blog`，不能直接作为你的 Pages 部署仓库。请先创建或确认自己的 GitHub 仓库，再添加远程并推送；不要把 `.env`、`.env.local` 或任何真实凭据提交。

仓库根目录已经提供 `render.yaml`，也可以在 Render 控制台手动创建服务。

### 5.2 使用 Blueprint（推荐）

1. 在 Render 新建 **Blueprint**，选择个人 GitHub 仓库。
2. 确认使用 `render.yaml`，计算计划必须是 **Free**。
3. 按提示填写：

```text
DATABASE_URL=mysql+pymysql://...blog_db?charset=utf8mb4&ssl_ca=/etc/ssl/certs/ca-certificates.crt&ssl_verify_cert=true&ssl_verify_identity=true
ADMIN_PASSWORD=<随机强密码>
CORS_ORIGINS=https://<你的GitHub用户名>.github.io
```

`SECRET_KEY` 由 Blueprint 自动生成。`ENABLE_IMAGE_UPLOAD` 固定为 `false`；此时 `PUBLIC_BASE_URL` 不参与图片存储，也不能把 Render 地址误认为对象存储。

### 5.3 手动创建 Web Service 时填写

| 配置 | 值 |
| --- | --- |
| Root Directory | `backend` |
| Runtime | Python 3.12 |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Health Check Path | `/health` |
| Instance Type | `Free` |

环境变量：

| 变量 | 说明 |
| --- | --- |
| `ENVIRONMENT` | `production` |
| `DATABASE_URL` | 第 4 节生成的 TiDB TLS 连接串 |
| `SECRET_KEY` | 随机长字符串，不要提交到 Git |
| `ADMIN_USERNAME` | 管理员用户名，例如 `admin` |
| `ADMIN_PASSWORD` | 管理员初始密码，只用于 seed；种子完成后修改环境变量不会自动改已有密码 |
| `CORS_ORIGINS` | 精确的前端 Origin，例如 `https://name.github.io`，不要带结尾 `/` |
| `SEED_ON_STARTUP` | `true`；Render 免费实例没有 Shell，启动时幂等创建管理员和示例文章 |
| `ENABLE_IMAGE_UPLOAD` | `false`；课程演示使用前端静态图片，关闭临时磁盘上传 |
| `PUBLIC_BASE_URL` | 仅在上传开关为 `true` 时用于拼接临时文件 URL；不是持久化存储 |
| `DB_POOL_RECYCLE` | `240` |
| `DB_POOL_SIZE` | `5` |
| `DB_MAX_OVERFLOW` | `5` |

部署后先打开：

```text
https://<你的服务名>.onrender.com/health
https://<你的服务名>.onrender.com/api/health
```

两者都应返回 `{"status":"ok"}`。第一次打开可能需要约 1 分钟冷启动。

## 6. 连接 GitHub Pages 前端

前端在构建时读取 Vite 变量，不会在运行时读取 Render 的环境变量：

```text
VITE_API_BASE_URL=https://<你的服务名>.onrender.com
VITE_BASE_PATH=/<仓库名>/
VITE_IMAGE_UPLOAD_ENABLED=false
```

- Pages 地址是 `https://<用户名>.github.io/` 时，`VITE_BASE_PATH` 用 `/`。
- Pages 地址是 `https://<用户名>.github.io/<仓库名>/` 时，`VITE_BASE_PATH` 用 `/<仓库名>/`。
- `VITE_API_BASE_URL` 只写到 Origin，不要加结尾 `/`，也不要写成 `.../api`。前端请求仍保留 `/api/...`，后端已做路径兼容。
- 所有 `frontend/public/images/...` 路径都通过 Vite `BASE_URL` 解析。例如项目站点会生成 `https://name.github.io/repo/images/avatar.png`，不会错误地请求域名根目录。

仓库已提供 `.github/workflows/deploy-pages.yml`。在 GitHub 仓库的 **Settings → Secrets and variables → Actions → Variables** 新增：

```text
VITE_API_BASE_URL=https://<你的服务名>.onrender.com
```

工作流会自动根据仓库名推导 `VITE_BASE_PATH`；自定义域名可额外设置 `VITE_BASE_PATH=/`。缺少 API 变量时构建会直接失败，避免发布一个请求 localhost 的 Pages 站点。

本地验证子路径构建示例：

```powershell
Set-Location frontend
$env:VITE_API_BASE_URL = 'https://<你的服务名>.onrender.com'
$env:VITE_BASE_PATH = '/<仓库名>/'
$env:VITE_IMAGE_UPLOAD_ENABLED = 'false'
npm ci
npm run build
```

修改 API 地址后必须重新构建 Pages，单纯修改 Render 环境变量不会改变已经构建好的前端文件。

## 7. 验证注册、登录、点赞、评论和持久化

### 7.1 浏览器验收

1. 打开 Pages 首页，确认文章列表来自 Render，而不是写死在页面中。
2. 注册一个新用户，再登录；刷新页面后登录状态应通过 JWT 恢复。
3. 打开任意文章，点赞，刷新详情页，点赞状态和数量应保持。
4. 再点一次取消点赞，数量应减一。
5. 发表一条评论，刷新详情页，评论仍存在。
6. 用另一个普通用户删除该评论应失败；本人或管理员删除应成功。

### 7.2 SQL 验收

在 TiDB SQL Editor 中执行：

```sql
SELECT id, username, role, created_at
FROM users
ORDER BY id DESC
LIMIT 5;

SELECT id, user_id, post_id
FROM post_likes
ORDER BY id DESC
LIMIT 5;

SELECT id, post_id, owner_id, content, created_at
FROM comments
ORDER BY id DESC
LIMIT 5;
```

新注册用户应出现在 `users`，点赞应出现在 `post_likes`，评论应出现在 `comments`。

### 7.3 持久化验收

1. 记下刚创建的评论和点赞。
2. 在 Render 控制台重启后端，或等待 15 分钟让免费服务休眠后再打开页面。
3. 冷启动完成后刷新文章详情，评论和点赞仍在，说明数据在 TiDB 中，而不是 Render 的临时文件系统。
4. 可选：重新部署后端一次，再次检查同样的数据。

### 7.4 自动化验收

项目已有 `scripts/verify-public.ps1`，会用 26 项检查覆盖首页、4 个静态图片、健康检查、注册、登录、身份、文章、点赞、评论、权限和管理员发文。它需要 `.env.local` 中的 `ADMIN_USERNAME` 和 `ADMIN_PASSWORD` 与目标环境一致：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\verify-public.ps1 `
  -ApiBaseUrl https://<你的服务名>.onrender.com `
  -FrontendBaseUrl https://<用户名>.github.io/<仓库名>/
```

脚本会把结果写入 `.runtime/verification.json`；`.runtime/` 已被 Git 忽略。

## 8. 常见问题

| 现象 | 优先检查 |
| --- | --- |
| `Access denied` | 用户名是否带实例前缀；密码是否做了 URL 编码 |
| TLS/证书错误 | `ssl_ca` 路径是否存在；是否正确使用 `ssl_ca`、`ssl_verify_cert=true`、`ssl_verify_identity=true` |
| 前端请求 404 | `VITE_API_BASE_URL` 是否只写 Origin；Pages 是否重新构建 |
| CORS 错误 | `CORS_ORIGINS` 是否精确等于浏览器地址栏的 Origin，且没有结尾 `/` |
| Render 502 | Start Command 是否绑定 `0.0.0.0` 并使用 `$PORT` |
| 管理员不存在 | `SEED_ON_STARTUP=true`，并检查 `ADMIN_USERNAME`、`ADMIN_PASSWORD` |
| 图片重启后消失 | Render 免费实例没有持久磁盘；课程演示应使用 Pages 静态图片或稳定的外部 https 地址 |
| Pages 图片 404 | 检查 `VITE_BASE_PATH` 是否与仓库路径一致，重新构建后确认 URL 形如 `/repo/images/...` |
| 首次访问很慢 | Render Free 冷启动，约 1 分钟；不是数据库丢失 |

## 9. 不要做的事情

- 不要升级 Render 付费实例或添加支付方式。
- 不要把 TiDB Spending Limit 调到 0 以上。
- 不要把 `DATABASE_URL`、数据库密码、`SECRET_KEY` 或 `ADMIN_PASSWORD` 写入 README、源码、`render.yaml` 或前端变量。
- 不要用 `git add -f .env`；当前 `.gitignore` 已忽略 `.env`、`.env.*`（仅保留 `.env.example`）。
