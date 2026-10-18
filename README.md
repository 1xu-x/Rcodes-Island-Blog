# Code Journey · 技术成长博客

一个现代、简洁的全栈个人技术博客，记录 Python、计算机基础、后端开发、云计算与项目实践的学习成果。

本项目基于开源项目 [Rcodes-Island-Blog](https://github.com/Acselerator/Rcodes-Island-Blog)（作者 Acselerator，README 声明 MIT）二次开发，保留其 FastAPI + SQLAlchemy + MySQL 的数据链路与 Vue 3 前端结构，补齐注册登录、管理员发文、点赞、评论、示例数据初始化和部署文档。

## 功能

- 文章列表与详情：标题、摘要、分类、发布时间、静态封面、正文图片、浏览量、点赞数、评论数
- 按标题搜索、按分类筛选、按日期/浏览量/点赞数排序、分页
- 用户注册、登录、退出（JWT），密码 bcrypt 哈希存储，用户名唯一
- 登录用户点赞/取消点赞，`post_likes` 唯一约束防止重复点赞
- 登录用户发表评论，本人或管理员可删除评论
- 管理员发布、编辑、删除文章（后端强制鉴权，不依赖前端隐藏按钮）
- 关于我页面
- 响应式布局，适配桌面与移动端

## 技术栈

- 后端：FastAPI、SQLAlchemy、PyMySQL、passlib(bcrypt)、python-jose(JWT)
- 数据库：MySQL（开发测试亦可使用 SQLite）
- 前端：Vue 3、Vite、Tailwind CSS、marked、Lucide
- 部署：GitHub Pages + Render Free + TiDB Cloud Starter；本地另支持 Docker Compose + Nginx

## 目录结构

```
├── backend/             # FastAPI 后端
│   ├── app/
│   │   ├── main.py      # 路由、鉴权、校验
│   │   ├── models.py    # User / Post / Comment / PostLike
│   │   ├── database.py  # SQLAlchemy 引擎与会话
│   │   ├── config.py    # 环境变量配置
│   │   └── seed.py      # 初始化管理员与示例文章
│   ├── tests/           # API 测试
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/            # Vue 3 前端
│   └── public/images/   # 随 Pages 发布的头像、封面和正文展示图
├── db/init.sql          # MySQL 初始化脚本
├── .github/workflows/   # GitHub Pages 自动构建与部署
├── docs/deployment.md   # 部署说明
├── docker-compose.yml
├── .env.example         # 环境变量模板
└── README.md
```

## 快速开始（Docker）

1. 准备环境变量

```bash
cp .env.example .env   # Windows: Copy-Item .env.example .env
```

编辑 `.env`，把 `MYSQL_ROOT_PASSWORD`、`MYSQL_PASSWORD`、`SECRET_KEY`、`ADMIN_PASSWORD` 改成自己的值。

2. 构建并启动

```bash
docker-compose up -d --build
```

3. 初始化管理员与示例文章

```bash
docker-compose exec backend python -m app.seed
```

4. 访问

- 前端页面：`http://localhost:8080`
- API 文档：`http://localhost:8080/api/docs`（Swagger）
- 健康检查：`http://localhost:8080/api/health`

## 本地开发（不使用 Docker）

需要本机安装 Python 3.10+、Node.js 18+ 和 MySQL（或先用 SQLite 快速体验）。

```bash
# 后端
cd backend
python -m venv venv
venv\Scripts\activate        # Linux/macOS: source venv/bin/activate
pip install -r requirements.txt
Copy-Item ..\.env.example ..\.env   # 并按需修改 DATABASE_URL 等
python -m app.seed           # 初始化管理员与示例文章
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

```bash
# 前端（另开一个终端）
cd frontend
npm install
npm run dev                  # 默认 http://localhost:5173
```

开发模式下前端通过 Vite 代理把 `/api`、`/uploads` 转发到 `http://127.0.0.1:8000`，无需额外跨域配置。

使用 SQLite 快速体验时，在 `backend/.env` 或环境变量中设置：

```env
DATABASE_URL=sqlite:///./blog_dev.db
SECRET_KEY=<用随机长字符串替换>
ADMIN_USERNAME=admin
ADMIN_PASSWORD=<用随机强密码替换>
```

可用 `python -c "import secrets; print(secrets.token_hex(32))"` 生成密钥和密码，不要把真实值写进 README 或提交到 Git。

## 运行测试

```bash
cd backend
python -m pytest -v
```

测试使用 SQLite 覆盖：注册与登录、未登录点赞/评论被拒、点赞切换与数据库记录、评论创建与删除权限、管理员发文权限、封面 URL 校验、上传关闭和 CORS 等；当前共 10 项。

## 环境变量

参见 [.env.example](.env.example)。真实密码、密钥只写入本地 `.env`，该文件已被 `.gitignore` 忽略，不会提交到 Git。

## 图片存储

课程演示版本默认关闭动态上传，固定图片放在 `frontend/public/images/`，通过 Vite `BASE_URL` 适配 GitHub Pages 项目子路径。编辑器可选择内置封面、粘贴稳定 https 外链，或插入内置正文图片。

Render 免费实例的 `backend/uploads` 是临时文件系统，`https://<service>.onrender.com/uploads/...` 不是持久化存储；服务重启、重新部署或休眠后文件可能丢失。旧路径和迁移步骤见 [docs/image-storage-migration.md](docs/image-storage-migration.md)。

## 云端部署

完整步骤（安全组、端口、跨域、数据库、HTTPS 提示）见 [docs/deployment.md](docs/deployment.md)。

完全免费的 GitHub Pages + Render Free Web Service + TiDB Cloud Starter 组合见 [docs/render-tidb-free-deployment.md](docs/render-tidb-free-deployment.md)。仓库包含 `.github/workflows/deploy-pages.yml`，构建时会校验 `VITE_API_BASE_URL` 并自动推导项目子路径。该组合尚未实际部署。

## 本次部署验证

2026-10-18 已用本地 MySQL 8 + FastAPI + Vue 生产构建完成 `/blog-demo/` 子路径联调：26 项检查通过，并完成后端重启后的登录、点赞和评论持久化复核。此前还通过临时 Cloudflare 隧道完成过一次公网链路验证；该入口依赖本机运行，不是永久云主机。

GitHub Pages、Render 和 TiDB Cloud 的线上部署尚未执行。验证记录、实际命令、限制和截图清单见 [docs/verification-report.md](docs/verification-report.md)。

## 许可与署名

基础代码来自 [Acselerator/Rcodes-Island-Blog](https://github.com/Acselerator/Rcodes-Island-Blog)，原 README 声明采用 MIT 许可。注意：该仓库根目录并未包含 LICENSE 文件，若计划在课程之外公开发布或商用，建议与原作者确认授权。本二次开发保留原项目的署名信息，未删除任何版权声明。

---

*Designed & Developed by [Acselerator](https://github.com/Acselerator) · 二次开发：Code Journey（技术成长博客）*
