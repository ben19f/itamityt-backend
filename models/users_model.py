from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship

from db.base import Base
from sqlalchemy import Boolean, Column, Integer, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict

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
    
    email_verified = Column(
        Boolean,
        nullable=False,
        default=False
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

    tags = Column(
        MutableDict.as_mutable(JSONB),
        nullable=False,
        default=dict,
        server_default="{}"
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




class UserPhoto(Base):
    __tablename__ = "user_photos"

    id = Column(
        Integer,
        primary_key=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    image_url = Column(
        String,
        nullable=False
    )

    position = Column(
        Integer,
        nullable=False,
        default=0
    )

    user = relationship(
        "User",
        back_populates="photos"
    )
