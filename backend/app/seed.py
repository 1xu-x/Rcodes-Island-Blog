"""Initialize admin account and sample articles."""

from sqlalchemy.orm import Session

from .config import ADMIN_PASSWORD, ADMIN_USERNAME
from .database import SessionLocal, engine
from .main import get_password_hash
from . import models


SAMPLE_POSTS = [
    {
        "title": "Python 文件处理与 JSON 数据持久化",
        "category": "Python",
        "cover_url": "images/covers/python.svg",
        "tags": "Python,JSON,文件处理",
        "summary": "从文本读写到 JSON 序列化，用最少依赖把程序状态可靠地保存到磁盘。",
        "content": """## 为什么要从文件开始

很多课程练习会先把数据放在内存列表里。程序一退出，数据就消失了。个人博客、配置信息和学习笔记都需要持久化。Python 标准库已经足够完成这件事。

## 读写文本文件

```python
from pathlib import Path

path = Path("notes.txt")
path.write_text("今天学习了 FastAPI\\n", encoding="utf-8")
print(path.read_text(encoding="utf-8"))
```

使用 `pathlib` 比拼接字符串路径更安全，也更容易跨平台。始终显式指定 `encoding="utf-8"`，避免 Windows 默认编码导致中文乱码。

## JSON 作为简单数据库

当数据是字典或列表时，JSON 是最直观的存储格式：

```python
import json
from pathlib import Path

articles = [
    {"id": 1, "title": "第一篇笔记", "likes": 0}
]
Path("articles.json").write_text(
    json.dumps(articles, ensure_ascii=False, indent=2),
    encoding="utf-8",
)
```

读取时注意文件不存在和 JSON 损坏两种异常：

```python
def load_articles(path="articles.json"):
    p = Path(path)
    if not p.exists():
        return []
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        raise ValueError("articles.json 已损坏，请检查文件内容")
```

## 适用边界

JSON 文件适合作业、原型和小型工具。用户注册、点赞唯一约束和并发写入，应交给 MySQL 这类关系数据库。本博客的文章、评论和点赞都保存在数据库中，而不是写死在页面里。
""",
    },
    {
        "title": "FastAPI 后端开发入门",
        "category": "后端开发",
        "cover_url": "images/covers/backend.svg",
        "tags": "FastAPI,JWT,SQLAlchemy",
        "summary": "用 FastAPI、SQLAlchemy 和 JWT 搭建可验证的博客接口：注册、登录、权限和数据校验。",
        "content": """## FastAPI 适合课程实践的原因

FastAPI 用类型注解生成请求校验和 OpenAPI 文档。本地启动后打开 `/docs`，就能直接调试注册、登录、点赞和评论接口。

## 最小应用

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}
```

运行：

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 分层思路

1. **模型**：SQLAlchemy 映射 `users`、`posts`、`comments`、`post_likes`。
2. **校验**：Pydantic 负责用户名、密码和评论长度。
3. **认证**：密码用 bcrypt 哈希，登录后签发 JWT。
4. **授权**：浏览公开；点赞和评论必须登录；发布文章必须是管理员。

## 权限不要只靠前端

前端隐藏“发布文章”按钮只是体验优化。真正的保护在后端依赖项里：未登录返回 401，普通用户调用管理接口返回 403。可以用未登录账号直接请求 `/posts/` POST 来验证。

## 下一步

把接口和 MySQL 连起来后，刷新页面、重新登录、重启服务，数据都应该还在。这就是“数据确实写入数据库”的直观证明。
""",
    },
    {
        "title": "从本地开发到云端网站部署",
        "category": "云计算",
        "cover_url": "images/covers/cloud-infra.jpg",
        "tags": "云计算,Docker,MySQL,部署",
        "summary": "梳理本地、Docker 和云服务器三套环境，把前端、后端和数据库一起跑起来。",
        "content": """## 本地开发要先跑通

本地最小组合是：

- 前端：Vite 开发服务器，默认 `http://localhost:5173`
- 后端：Uvicorn，默认 `http://127.0.0.1:8000`
- 数据库：MySQL，库名 `blog_db`

前端通过 Vite 代理把 `/api` 转到后端，开发时不必处理跨域。

![GitHub Pages、Render 与 TiDB 的部署分工](images/posts/deployment-flow.svg)

图中前端静态文件由 GitHub Pages 提供，FastAPI 运行在 Render，用户、文章、点赞和评论保存在 TiDB。图片放静态目录，避免依赖 Render 的临时文件系统。

## 环境变量

数据库密码、JWT 密钥和 CORS 来源都放在 `.env`，不要写进源码。提交仓库时只保留 `.env.example`。

## Docker Compose

`docker-compose.yml` 把前端 Nginx、FastAPI 和 MySQL 编排在同一网络。容器里后端访问数据库的主机名是 `db`，不是 `localhost`。

## 云服务器需要准备什么

1. 一台有公网 IP 的云主机（2 核 2G 即可做课程演示）。
2. 安全组放行 `22`、`80`、`8000`（或你实际使用的端口）。
3. 安装 Docker，或直接安装 Python、Node.js 和 MySQL。
4. 把 `CORS_ORIGINS` 改成云主机公网地址。
5. 修改 `DATABASE_URL` 指向云上的 MySQL。

## 验收清单

- 浏览器能打开首页并看到 3 篇示例文章。
- 新用户可以注册，MySQL 的 `users` 表新增一行。
- 点赞后 `post_likes` 表有记录，刷新后数字不变。
- 重启后端后再打开网站，文章和评论还在。

没有购买云资源时，先把上述清单在本地走通，再按同样步骤迁移到云主机。
""",
    },
]


def seed(db: Session) -> None:
    if not ADMIN_PASSWORD:
        raise RuntimeError("请先在环境变量 ADMIN_PASSWORD 中设置管理员密码")

    models.Base.metadata.create_all(bind=engine)

    admin = db.query(models.User).filter(models.User.username == ADMIN_USERNAME).first()
    if not admin:
        admin = models.User(
            username=ADMIN_USERNAME,
            hashed_password=get_password_hash(ADMIN_PASSWORD),
            role="admin",
            created_at="2026-10-01 09:00:00",
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
    elif admin.role != "admin":
        admin.role = "admin"
        db.commit()

    existing_titles = {row[0] for row in db.query(models.Post.title).all()}
    created = 0
    for index, item in enumerate(SAMPLE_POSTS, start=1):
        if item["title"] in existing_titles:
            continue
        db.add(
            models.Post(
                title=item["title"],
                summary=item["summary"],
                content=item["content"],
                category=item["category"],
                tags=item["tags"],
                cover_url=item.get("cover_url", ""),
                created_at=f"2026-10-0{index} 10:00:00",
                year="2026",
                date=f"10.{index}",
                views=index * 12,
                likes=0,
                owner_id=admin.id,
            )
        )
        created += 1
    db.commit()
    print(f"管理员: {admin.username}")
    print(f"新增示例文章: {created} 篇")


def main() -> None:
    db = SessionLocal()
    try:
        seed(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
