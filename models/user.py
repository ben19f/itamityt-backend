from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from db.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    display_name = Column(
        String,
        default="Дисплей нейм пользователя",
        nullable=False,
        index=True
    )
    profile_description = Column(
        String,
        default="немного о профиле или компании",
        nullable=False,
        index=True
    )

    profile_extra_info = Column(
        String,
        default="Дополнительная информация",
        nullable=False,
        index=True
    )

    items = relationship("Item", back_populates="user", cascade="all, delete-orphan")

