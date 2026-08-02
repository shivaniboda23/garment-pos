from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Numeric,
    DateTime,
    Boolean,
    func,
)

from sqlalchemy.orm import relationship

from app.db.database import Base


class ProductVariant(Base):
    __tablename__ = "product_variants"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    product_id = Column(
        Integer,
        ForeignKey(
            "products.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    size = Column(
        String(20),
        nullable=False,
    )

    color = Column(
        String(50),
        nullable=True,
    )

    barcode = Column(
        String(100),
        unique=True,
        nullable=False,
    )

    sku = Column(
        String(100),
        unique=True,
        nullable=False,
    )

    reorder_level = Column(
        Integer,
        default=5,
        nullable=False,
    )

    cost_price = Column(
        Numeric(10, 2),
        default=0,
    )

    selling_price = Column(
        Numeric(10, 2),
        default=0,
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

    # -------------------------
    # Relationships
    # -------------------------

    product = relationship(
        "Product",
        back_populates="variants",
    )

    stock = relationship(
        "Stock",
        back_populates="variant",
        uselist=False,
        cascade="all, delete-orphan",
    )

    sale_items = relationship(
        "SaleItem",
        back_populates="variant",
    )

    bill_items = relationship(
        "BillItem",
        back_populates="variant",
    )
    # -------------------------
    # Virtual quantity field
    # -------------------------

    @property
    def quantity(self):
        if self.stock:
            return self.stock.quantity
        return 0