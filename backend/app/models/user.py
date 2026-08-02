from sqlalchemy import (
    Boolean,
    Column,
    Enum,
    ForeignKey,
    Integer,
    String,
    DateTime,
    func,
)

from sqlalchemy.orm import relationship

from app.db.database import Base
from app.core.enums import UserRole


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    shop_id = Column(
        Integer,
        ForeignKey("shops.id", ondelete="CASCADE"),
        nullable=False,
    )

    full_name = Column(
        String(150),
        nullable=False,
    )

    email = Column(
        String(150),
        unique=True,
        nullable=False,
    )

    password = Column(
        String(255),
        nullable=False,
    )

    role = Column(
        Enum(UserRole),
        nullable=False,
        default=UserRole.CASHIER,
    )

    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    shop = relationship(
        "Shop",
        back_populates="users",
    )