from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    Numeric,
    ForeignKey
)
from sqlalchemy.sql import func

from app.database import Base


class ServiceRequest(Base):
    __tablename__ = "service_requests"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    client_id = Column(
        Integer,
        ForeignKey("clients.id"),
        nullable=False
    )

    service_id = Column(
        Integer,
        ForeignKey("services.id"),
        nullable=False
    )

    requested_date = Column(
        DateTime(timezone=True),
        nullable=True
    )

    address = Column(
        String(255),
        nullable=False
    )

    notes = Column(
        Text,
        nullable=True
    )

    status = Column(
        String(50),
        nullable=False,
        default="Pendiente"
    )

    estimated_price = Column(
        Numeric(12, 2),
        nullable=False,
        default=0
    )

    is_active = Column(
        Boolean,
        default=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )