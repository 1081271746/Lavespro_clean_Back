from sqlalchemy import Column, Integer, String, Boolean, DateTime, Numeric
from sqlalchemy.sql import func

from app.database import Base


class Service(Base):
    __tablename__ = "services"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    name = Column(
        String(150),
        nullable=False,
        unique=True
    )

    description = Column(
        String(500),
        nullable=True
    )

    base_price = Column(
        Numeric(12, 2),
        nullable=False,
        default=0
    )

    duration = Column(
        String(100),
        nullable=True
    )

    is_active = Column(
        Boolean,
        default=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )