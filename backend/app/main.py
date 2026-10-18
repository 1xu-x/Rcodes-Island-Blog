import os
import logging
import re
import shutil
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, Field, validator
from sqlalchemy import asc, desc, func, or_
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session

from . import database, models
from .config import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ALGORITHM,
    CORS_ORIGINS,
    ENABLE_IMAGE_UPLOAD,
    PUBLIC_BASE_URL,
    SECRET_KEY,
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)
logger = logging.getLogger("code_journey")

USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_\u4e00-\u9fa5]{3,32}$")
CATEGORIES = ["Python", "计算机基础", "后端开发", "云计算", "项目实践"]
ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}

app = FastAPI(title="Code Journey API", description="技术成长博客后端")


@app.middleware("http")
async def normalize_api_prefix(request: Request, call_next):
    """Accept both /api/* (frontend) and /* (direct backend) paths."""
    path = request.scope.get("path", "")
    if path == "/api":
        request.scope["path"] = "/"
    elif path.startswith("/api/"):
        request.scope["path"] = path[4:]
    return await call_next(request)


app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path(__file__).resolve().parents[1] / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class UserCreate(BaseModel):
    username: str
    password: str

    @validator("username")
    def validate_username(cls, value: str) -> str:
        username = value.strip()
        if not USERNAME_PATTERN.match(username):
            raise ValueError("用户名需为 3-32 位字母、数字、下划线或中文")
        return username

    @validator("password")
    def validate_password(cls, value: str) -> str:
        if len(value) < 6 or len(value) > 72:
            raise ValueError("密码长度需在 6 到 72 个字符之间")
        return value


class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    created_at: Optional[str] = None

    class Config:
        orm_mode = True


class PostCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    content: str = Field(..., min_length=1)
    summary: Optional[str] = ""
    category: Optional[str] = "Python"
    tags: Optional[str] = ""
    cover_url: Optional[str] = ""

    @validator("title")
    def validate_title(cls, value: str) -> str:
        title = value.strip()
        if not title:
            raise ValueError("标题不能为空")
        return title

    @validator("content")
    def validate_content(cls, value: str) -> str:
        content = value.strip()
        if not content:
            raise ValueError("正文不能为空")
        return content

    @validator("summary")
    def validate_summary(cls, value: Optional[str]) -> str:
        return (value or "").strip()[:500]

    @validator("category")
    def validate_category(cls, value: Optional[str]) -> str:
        category = (value or "Python").strip()
        if category not in CATEGORIES:
            return "Python"
        return category

    @validator("cover_url")
    def validate_cover_url(cls, value: Optional[str]) -> str:
        cover_url = (value or "").strip()
        if not cover_url:
            return ""
        if len(cover_url) > 500:
            raise ValueError("封面地址不能超过 500 个字符")
        allowed_prefixes = ("https://", "http://", "images/", "/images/", "uploads/", "/uploads/")
        if not cover_url.lower().startswith(allowed_prefixes):
            raise ValueError("封面地址必须是 http(s) URL 或 images/ 静态路径")
        return cover_url


class PostResponse(BaseModel):
    id: int
    title: str
    summary: Optional[str] = ""
    content: str
    category: Optional[str]
    tags: Optional[str]
    cover_url: Optional[str] = ""
    created_at: Optional[str]
    year: Optional[str]
    date: Optional[str]
    views: int = 0
    likes: int = 0
    comment_count: int = 0
    is_liked: bool = False
    owner_id: int
    owner: UserResponse

    class Config:
        orm_mode = True


class PostListResponse(BaseModel):
    items: List[PostResponse]
    total: int
    categories: List[str] = CATEGORIES


class CommentCreate(BaseModel):
    content: str

    @validator("content")
    def validate_content(cls, value: str) -> str:
        content = value.strip()
        if not content:
            raise ValueError("评论不能为空")
        if len(content) > 1000:
            raise ValueError("评论不能超过 1000 个字符")
        return content


class CommentResponse(BaseModel):
    id: int
    content: str
    created_at: Optional[str] = None
    owner_id: int
    post_id: int
    owner: UserResponse

    class Config:
        orm_mode = True


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def ensure_comment_count(post: models.Post, db: Session, is_liked: bool = False) -> models.Post:
    post.comment_count = (
        db.query(func.count(models.Comment.id)).filter(models.Comment.post_id == post.id).scalar() or 0
    )
    post.is_liked = is_liked
    return post


def liked_post_ids(db: Session, user: Optional[models.User], post_ids: List[int]) -> set:
    if not user or not post_ids:
        return set()
    rows = (
        db.query(models.PostLike.post_id)
        .filter(models.PostLike.user_id == user.id, models.PostLike.post_id.in_(post_ids))
        .all()
    )
    return {row[0] for row in rows}


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="请先登录",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise credentials_exception
    return user


async def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme_optional),
    db: Session = Depends(database.get_db),
):
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if not username:
            return None
    except JWTError:
        return None
    return db.query(models.User).filter(models.User.username == username).first()


async def get_current_admin(current_user: models.User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="仅管理员可以执行该操作")
    return current_user


@app.on_event("startup")
def on_startup():
    try:
        models.Base.metadata.create_all(bind=database.engine)
    except OperationalError as exc:
        raise RuntimeError(f"数据库连接失败，请检查 DATABASE_URL：{exc}") from exc

    # Render Free has no shell or one-off jobs, so seeding must be optional at startup.
    if os.getenv("SEED_ON_STARTUP", "0").strip().lower() in {"1", "true", "yes"}:
        from .seed import seed

        db = database.SessionLocal()
        try:
            seed(db)
        finally:
            db.close()


@app.exception_handler(OperationalError)
async def handle_db_connection_error(_, exc: OperationalError):
    from fastapi.responses import JSONResponse

    # 连接串和驱动堆栈只写服务端日志，避免公网响应泄露内部信息。
    logger.error("Database operation failed: %s", exc)
    return JSONResponse(status_code=503, content={"detail": "数据库暂时不可用，请稍后重试"})


@app.get("/")
def read_root():
    return {"name": "Code Journey", "message": "技术成长博客 API"}


@app.get("/health")
def read_health():
    return {"status": "ok"}


@app.get("/categories")
def read_categories():
    return {"items": CATEGORIES}


@app.post("/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(database.get_db)):
    exists = db.query(models.User).filter(models.User.username == user.username).first()
    if exists:
        raise HTTPException(status_code=400, detail="用户名已被注册")
    db_user = models.User(
        username=user.username,
        hashed_password=get_password_hash(user.password),
        role="user",
        created_at=now_str(),
    )
    db.add(db_user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="用户名已被注册")
    db.refresh(db_user)
    return db_user


@app.post("/token", response_model=Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(database.get_db),
):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me", response_model=UserResponse)
def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user


@app.post("/posts/", response_model=PostResponse)
def create_post(
    post: PostCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_admin),
):
    now = datetime.now()
    summary = post.summary or post.content[:160]
    db_post = models.Post(
        title=post.title,
        summary=summary,
        content=post.content,
        category=post.category,
        tags=post.tags or "",
        cover_url=post.cover_url or "",
        created_at=now.strftime("%Y-%m-%d %H:%M:%S"),
        year=str(now.year),
        date=f"{now.month}.{now.day}",
        owner_id=current_user.id,
        views=0,
        likes=0,
    )
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return ensure_comment_count(db_post, db)


@app.get("/posts/", response_model=PostListResponse)
def read_posts(
    skip: int = 0,
    limit: int = 10,
    q: Optional[str] = None,
    category: Optional[str] = None,
    sort_by: Optional[str] = "date",
    order: Optional[str] = "desc",
    db: Session = Depends(database.get_db),
    current_user: Optional[models.User] = Depends(get_current_user_optional),
):
    query = db.query(models.Post)
    if q:
        search = f"%{q.strip()}%"
        query = query.filter(
            or_(
                models.Post.title.like(search),
                models.Post.summary.like(search),
                models.Post.content.like(search),
                models.Post.tags.like(search),
                models.Post.category.like(search),
            )
        )
    if category:
        query = query.filter(models.Post.category == category)

    sort_attr = {
        "views": models.Post.views,
        "likes": models.Post.likes,
    }.get(sort_by, models.Post.id)
    query = query.order_by(asc(sort_attr) if order == "asc" else desc(sort_attr))

    total = query.count()
    posts = query.offset(skip).limit(limit).all()
    liked_ids = liked_post_ids(db, current_user, [post.id for post in posts])
    items = [ensure_comment_count(post, db, post.id in liked_ids) for post in posts]
    return {"items": items, "total": total, "categories": CATEGORIES}


@app.put("/posts/{post_id}", response_model=PostResponse)
def update_post(
    post_id: int,
    post: PostCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_admin),
):
    db_post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if db_post is None:
        raise HTTPException(status_code=404, detail="文章不存在")
    db_post.title = post.title
    db_post.content = post.content
    db_post.summary = post.summary or post.content[:160]
    db_post.category = post.category
    db_post.tags = post.tags or ""
    db_post.cover_url = post.cover_url or db_post.cover_url or ""
    db.commit()
    db.refresh(db_post)
    return ensure_comment_count(db_post, db)


@app.delete("/posts/{post_id}")
def delete_post(
    post_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_admin),
):
    db_post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if db_post is None:
        raise HTTPException(status_code=404, detail="文章不存在")
    db.delete(db_post)
    db.commit()
    return {"message": "文章已删除"}


@app.get("/posts/{post_id}", response_model=PostResponse)
def read_post(
    post_id: int,
    db: Session = Depends(database.get_db),
    current_user: Optional[models.User] = Depends(get_current_user_optional),
):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if post is None:
        raise HTTPException(status_code=404, detail="文章不存在")
    post.views = (post.views or 0) + 1
    db.commit()
    db.refresh(post)
    is_liked = False
    if current_user:
        is_liked = (
            db.query(models.PostLike)
            .filter(models.PostLike.post_id == post_id, models.PostLike.user_id == current_user.id)
            .first()
            is not None
        )
    return ensure_comment_count(post, db, is_liked)


@app.post("/posts/{post_id}/like")
def like_post(
    post_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="文章不存在")

    existing_like = (
        db.query(models.PostLike)
        .filter(models.PostLike.post_id == post_id, models.PostLike.user_id == current_user.id)
        .first()
    )
    if existing_like:
        db.delete(existing_like)
        post.likes = max(0, (post.likes or 0) - 1)
        is_liked = False
    else:
        db.add(models.PostLike(post_id=post_id, user_id=current_user.id))
        post.likes = (post.likes or 0) + 1
        is_liked = True
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="请勿重复点赞")
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=500, detail="点赞操作失败")
    return {"likes": post.likes, "is_liked": is_liked}


@app.post("/posts/{post_id}/comments/", response_model=CommentResponse)
def create_comment(
    post_id: int,
    comment: CommentCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    db_post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if db_post is None:
        raise HTTPException(status_code=404, detail="文章不存在")
    db_comment = models.Comment(
        content=comment.content,
        post_id=post_id,
        owner_id=current_user.id,
        created_at=now_str(),
    )
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment


@app.get("/posts/{post_id}/comments/", response_model=List[CommentResponse])
def read_comments(post_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db)):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if post is None:
        raise HTTPException(status_code=404, detail="文章不存在")
    return (
        db.query(models.Comment)
        .filter(models.Comment.post_id == post_id)
        .order_by(models.Comment.id.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )


@app.delete("/comments/{comment_id}")
def delete_comment(
    comment_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    db_comment = db.query(models.Comment).filter(models.Comment.id == comment_id).first()
    if db_comment is None:
        raise HTTPException(status_code=404, detail="评论不存在")
    if db_comment.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权删除该评论")
    db.delete(db_comment)
    db.commit()
    return {"message": "评论已删除"}


@app.post("/upload")
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_admin),
):
    if not ENABLE_IMAGE_UPLOAD:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="演示环境已关闭动态图片上传，请使用静态资源或稳定外部图片 URL",
        )

    file_extension = os.path.splitext(file.filename or "")[1].lower()
    if file_extension not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(status_code=400, detail="仅支持 PNG、JPG、WEBP 或 GIF 图片")

    file_name = f"{uuid.uuid4()}{file_extension}"
    file_path = UPLOAD_DIR / file_name
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    public_base = PUBLIC_BASE_URL or str(request.base_url).rstrip("/")
    return {
        "url": f"{public_base}/uploads/{file_name}",
        "storage": "ephemeral",
        "persistent": False,
        "warning": "文件保存在当前实例本地磁盘，重启、重新部署或休眠后可能丢失",
    }
