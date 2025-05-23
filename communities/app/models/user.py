from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import db

user_communities = db.Table(
    'user_communities',
    db.metadata,
    db.Column('user_id', db.ForeignKey('users.id'), primary_key=True),
    db.Column('community_id', db.ForeignKey('communities.id'), primary_key=True)
)

class User(db.Model):
    from .community import Community
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(unique=True)
    password: Mapped[str] = mapped_column()
    is_admin: Mapped[bool] = mapped_column(default=False)

    communities: Mapped[list["Community"]] = relationship(
        secondary=user_communities,
        back_populates="members"
    )

    owned_communities: Mapped[list["Community"]] = relationship(
        "Community",
        back_populates="owner",
        foreign_keys="Community.owner_id",
        cascade="all, delete-orphan"
    )
