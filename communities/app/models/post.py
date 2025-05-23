from typing import List
from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import db
from .user import User
from .community import Community


class Post(db.Model):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column()
    content: Mapped[str] = mapped_column()

    author_id = Column(Integer, ForeignKey("users.id"))
    author: Mapped["User"] = relationship()
    
    community_id = Column(Integer, ForeignKey("communities.id"))
    community: Mapped["Community"] = relationship()
