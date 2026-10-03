from sqlalchemy import Column, Integer, String, Boolean, DateTime, Numeric, ForeignKey
from sqlalchemy.sql import func

from app.database import Base


class Work(Base):
    __tablename__ = "works"

    id = Column(Integer, primary_key=True, index=True)

    request_id = Column(
        Integer,
        ForeignKey("service_requests.id"),
        nullable=False,
        index=True
    )

    scheduled_date = Column(DateTime(timezone=True), nullable=True)

    assigned_to = Column(String(150), nullable=True)

    status = Column(
        String(50),
        nullable=False,
        default="Programado"
    )

    price = Column(
        Numeric(12, 2),
        nullable=False,
        default=0
    )

    notes = Column(String(1000), nullable=True)

    started_at = Column(DateTime(timezone=True), nullable=True)

    completed_at = Column(DateTime(timezone=True), nullable=True)

    is_active = Column(Boolean, default=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )