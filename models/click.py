from sqlalchemy import Column, Integer, String, ForeignKey
from db.base import Base


class Click(Base):
    __tablename__ = "clicks"

    id = Column(Integer, primary_key=True)
    link_id = Column(String(50), ForeignKey("items.link_id", ondelete="CASCADE"))