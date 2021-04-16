from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from sqlalchemy import Column, Integer, String, ForeignKey, Table

Base = declarative_base()

class UrlMixin:
    url = Column(String, nullable=False, unique=True)

class IdMixin:
    id = Column(Integer, primary_key=True, autoincrement=True)


tag_post = Table(
    "tag_post",
    Base.metadata,
    Column("post_id", Integer, ForeignKey("post.id")),
    Column("tag_id", Integer, ForeignKey("tag.id"))
)


class NameMixin:
    name = Column(String)

class Post(Base, UrlMixin, IdMixin):
    __tablename__ = "post"
    title = Column(String, nullable=False)
    author_id = Column(Integer, ForeignKey("author.id"))
    author = relationship("Author")
    tags = relationship("Tag", secondary=tag_post)

class Author(Base, UrlMixin, IdMixin, NameMixin):
    __tablename__ = "author"
    posts = relationship("Post")

class Tag(Base, UrlMixin, IdMixin, NameMixin):
    __tablename__ = "tag"
    posts = relationship(Post, secondary=tag_post)