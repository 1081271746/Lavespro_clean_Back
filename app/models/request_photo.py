from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func

from app.database import Base


class RequestPhoto(Base):
    __tablename__ = "request_photos"

    id = Column(Integer, primary_key=True, index=True)

    request_id = Column(
        Integer,
        ForeignKey("service_requests.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    file_name = Column(String(255), nullable=False)

    file_path = Column(String(500), nullable=False)

    content_type = Column(String(100), nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )