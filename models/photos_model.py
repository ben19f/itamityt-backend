from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from db.base import Base


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