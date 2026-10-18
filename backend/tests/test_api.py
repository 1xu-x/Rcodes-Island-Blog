import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

os.environ["DATABASE_URL"] = "sqlite:///./test_code_journey.db"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["ADMIN_USERNAME"] = "admin"
os.environ["ADMIN_PASSWORD"] = "admin123"
os.environ["CORS_ORIGINS"] = "http://testserver"
os.environ["ENABLE_IMAGE_UPLOAD"] = "false"

from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, SessionLocal, build_database_url, engine  # noqa: E402
from app.main import app, get_password_hash  # noqa: E402
from app import models  # noqa: E402


def _create_user(username: str, password: str, role: str = "user") -> models.User:
    db = SessionLocal()
    user = models.User(
        username=username,
        hashed_password=get_password_hash(password),
        role=role,
        created_at="2026-10-01 00:00:00",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()
    return user


def setup_module():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    admin = _create_user("admin", "admin123", role="admin")
    _create_user("alice", "secret1")
    _create_user("bob", "secret1")

    db = SessionLocal()
    db.add(
        models.Post(
            title="测试文章",
            summary="摘要",
            content="正文内容",
            category="Python",
            tags="test",
            created_at="2026-10-01 00:00:00",
            year="2026",
            date="10.1",
            owner_id=admin.id,
            views=0,
            likes=0,
        )
    )
    db.commit()
    db.close()


def teardown_module():
    try:
        client.close()
    except Exception:
        pass
    engine.dispose()
    Base.metadata.drop_all(bind=engine)
    db_file = ROOT / "test_code_journey.db"
    try:
        if db_file.exists():
            db_file.unlink()
    except OSError:
        pass


client = TestClient(app)


def auth_header(username: str, password: str) -> dict:
    response = client.post("/token", data={"username": username, "password": password})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def get_user_id(username: str) -> int:
    db = SessionLocal()
    user = db.query(models.User).filter(models.User.username == username).first()
    db.close()
    assert user is not None
    return user.id


def test_register_and_login():
    response = client.post("/register", json={"username": "carol", "password": "secret1"})
    assert response.status_code == 200
    assert response.json()["username"] == "carol"
    assert response.json()["role"] == "user"

    duplicate = client.post("/register", json={"username": "carol", "password": "secret1"})
    assert duplicate.status_code == 400

    invalid = client.post("/register", json={"username": "ab", "password": "123"})
    assert invalid.status_code == 422

    login = client.post("/token", data={"username": "carol", "password": "secret1"})
    assert login.status_code == 200
    assert login.json()["access_token"]


def test_guest_cannot_like_or_comment():
    like = client.post("/posts/1/like")
    assert like.status_code == 401
    comment = client.post("/posts/1/comments/", json={"content": "hello"})
    assert comment.status_code == 401


def test_like_toggle_persists_in_database():
    headers = auth_header("alice", "secret1")
    alice_id = get_user_id("alice")

    like = client.post("/posts/1/like", headers=headers)
    assert like.status_code == 200
    assert like.json()["is_liked"] is True
    assert like.json()["likes"] == 1

    db = SessionLocal()
    record = db.query(models.PostLike).filter_by(user_id=alice_id, post_id=1).first()
    db.close()
    assert record is not None

    unlike = client.post("/posts/1/like", headers=headers)
    assert unlike.json()["is_liked"] is False
    assert unlike.json()["likes"] == 0


def test_comment_create_and_permission():
    user_headers = auth_header("alice", "secret1")
    created = client.post("/posts/1/comments/", json={"content": "写得很好"}, headers=user_headers)
    assert created.status_code == 200
    comment_id = created.json()["id"]

    empty = client.post("/posts/1/comments/", json={"content": "   "}, headers=user_headers)
    assert empty.status_code == 422

    comments = client.get("/posts/1/comments/")
    assert comments.status_code == 200
    assert len(comments.json()) == 1

    bob_headers = auth_header("bob", "secret1")
    forbidden = client.delete(f"/comments/{comment_id}", headers=bob_headers)
    assert forbidden.status_code == 403

    admin_headers = auth_header("admin", "admin123")
    deleted = client.delete(f"/comments/{comment_id}", headers=admin_headers)
    assert deleted.status_code == 200


def test_admin_article_permissions():
    user_headers = auth_header("alice", "secret1")
    denied = client.post(
        "/posts/",
        json={"title": "普通用户发文", "content": "不应成功", "category": "Python"},
        headers=user_headers,
    )
    assert denied.status_code == 403

    admin_headers = auth_header("admin", "admin123")
    created = client.post(
        "/posts/",
        json={
            "title": "管理员新文章",
            "content": "这是管理员发布的文章正文。",
            "summary": "管理员摘要",
            "category": "云计算",
            "cover_url": "images/covers/cloud-infra.jpg",
        },
        headers=admin_headers,
    )
    assert created.status_code == 200
    assert created.json()["cover_url"] == "images/covers/cloud-infra.jpg"
    post_id = created.json()["id"]

    listing = client.get("/posts/", params={"category": "云计算", "q": "管理员"})
    assert listing.status_code == 200
    assert listing.json()["total"] >= 1

    deleted = client.delete(f"/posts/{post_id}", headers=user_headers)
    assert deleted.status_code == 403

    deleted_admin = client.delete(f"/posts/{post_id}", headers=admin_headers)
    assert deleted_admin.status_code == 200

    missing = client.get("/posts/9999")
    assert missing.status_code == 404


def test_api_prefix_alias_for_direct_render_access():
    health = client.get("/api/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    posts = client.get("/api/posts/")
    assert posts.status_code == 200
    assert posts.json()["total"] >= 1


def test_database_url_preserves_tls_query_options():
    url = build_database_url(
        "mysql+pymysql://prefix.root:secret@db.example.com:4000/blog_db"
        "?ssl_ca=%2Fetc%2Fssl%2Fcerts%2Fca-certificates.crt"
        "&ssl_verify_cert=true&ssl_verify_identity=true"
    )
    assert url.database == "blog_db"
    assert url.query["charset"] == "utf8mb4"
    assert url.query["ssl_ca"] == "/etc/ssl/certs/ca-certificates.crt"
    assert url.query["ssl_verify_cert"] == "true"
    assert url.query["ssl_verify_identity"] == "true"


def test_cover_url_validation():
    admin_headers = auth_header("admin", "admin123")
    unsafe = client.post(
        "/posts/",
        json={
            "title": "不安全封面",
            "content": "封面地址校验",
            "category": "Python",
            "cover_url": "javascript:alert(1)",
        },
        headers=admin_headers,
    )
    assert unsafe.status_code == 422

    external = client.post(
        "/posts/",
        json={
            "title": "外链封面",
            "content": "稳定外部图片地址",
            "category": "Python",
            "cover_url": "https://images.example.com/cover.webp",
        },
        headers=admin_headers,
    )
    assert external.status_code == 200
    assert external.json()["cover_url"] == "https://images.example.com/cover.webp"
    assert client.delete(f"/posts/{external.json()['id']}", headers=admin_headers).status_code == 200


def test_demo_image_upload_is_disabled():
    admin_headers = auth_header("admin", "admin123")
    response = client.post(
        "/upload",
        files={"file": ("cover.png", b"\x89PNG\r\n\x1a\n", "image/png")},
        headers=admin_headers,
    )
    assert response.status_code == 403
    assert "关闭动态图片上传" in response.json()["detail"]


def test_cors_allows_configured_pages_origin():
    response = client.options(
        "/health",
        headers={
            "Origin": "http://testserver",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://testserver"
