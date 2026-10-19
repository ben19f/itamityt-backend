from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from db.base import Base


class Click(Base):
    __tablename__ = "clicks"

    id = Column(Integer, primary_key=True)
    link_id = Column(
        String(50),
        ForeignKey("items.link_id", ondelete="CASCADE"),
        index=True,
    )
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    clicked_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    item = relationship("Item", back_populates="clicks")
