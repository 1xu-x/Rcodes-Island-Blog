from sqlalchemy import Column, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default="user", nullable=False)
    created_at = Column(String(50))

    posts = relationship("Post", back_populates="owner")
    comments = relationship("Comment", back_populates="owner")
    likes = relationship("PostLike", back_populates="user", cascade="all, delete-orphan")


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), index=True, nullable=False)
    summary = Column(String(500), default="")
    category = Column(String(50), default="Python", index=True)
    tags = Column(String(200), default="")
    content = Column(Text, nullable=False)
    cover_url = Column(String(500), default="")
    created_at = Column(String(50))
    year = Column(String(10))
    date = Column(String(20))
    views = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    owner = relationship("User", back_populates="posts")
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")
    like_records = relationship("PostLike", back_populates="post", cascade="all, delete-orphan")


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    created_at = Column(String(50))
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    owner = relationship("User", back_populates="comments")
    post = relationship("Post", back_populates="comments")


class PostLike(Base):
    __tablename__ = "post_likes"
    __table_args__ = (UniqueConstraint("user_id", "post_id", name="uq_user_post_like"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False, index=True)

    user = relationship("User", back_populates="likes")
    post = relationship("Post", back_populates="like_records")
