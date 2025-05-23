from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import db
from .user import user_communities


class Community(db.Model):
    __tablename__ = "communities"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
    # A template to welcome users when they first join
    welcome_template: Mapped[str] = mapped_column()

    owner_id = Column(Integer, ForeignKey("users.id"))
    owner: Mapped["User"] = relationship(
        "User",
        back_populates="owned_communities",
        foreign_keys=[owner_id]
    )

    members: Mapped[list["User"]] = relationship(
        secondary=user_communities,
        back_populates="communities"
    )

    posts: Mapped[list["Post"]] = relationship(
        back_populates="community"
    )
