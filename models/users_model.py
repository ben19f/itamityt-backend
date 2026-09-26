from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship

from db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True
    )

    username = Column(
        String,
        unique=True,
        index=True,
        nullable=False
    )

    email = Column(
        String,
        unique=True,
        index=True,
        nullable=True
    )

    hashed_password = Column(
        String,
        nullable=True
    )

    display_name = Column(
        String,
        nullable=True
    )

    profile_description = Column(
        Text,
        nullable=True
    )

    profile_extra_info = Column(
        Text,
        nullable=True
    )

    avatar_url = Column(
        String,
        nullable=True
    )

    owner_verified = Column(
        String(1),
        nullable=True
    )

    service_verified = Column(
        String(1),
        nullable=True
    )

    items = relationship(
        "Item",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    photos = relationship(
        "UserPhoto",
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="UserPhoto.position"
    )