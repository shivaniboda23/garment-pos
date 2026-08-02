from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Numeric,
    Boolean,
    DateTime,
    func,
)

from sqlalchemy.orm import relationship

from app.db.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    shop_id = Column(
        Integer,
        ForeignKey(
            "shops.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    category_id = Column(
        Integer,
        ForeignKey("categories.id"),
        nullable=True,
    )

    brand_id = Column(
        Integer,
        ForeignKey("brands.id"),
        nullable=True,
    )

    product_name = Column(
        String(200),
        nullable=False,
    )

    product_code = Column(
        String(50),
        unique=True,
        nullable=False,
    )

    sku = Column(
        String(50),
        unique=True,
        nullable=True,
    )

    barcode = Column(
        String(100),
        unique=True,
        nullable=True,
    )

    description = Column(
        String(500),
    )

    hsn_code = Column(
        String(20),
    )

    gst_percentage = Column(
        Numeric(5, 2),
        default=0,
    )

    cost_price = Column(
        Numeric(10, 2),
        default=0,
    )

    selling_price = Column(
        Numeric(10, 2),
        default=0,
    )

    k_stock = Column(
        Integer,
        default=0,
        nullable=False,
    )

    r_stock = Column(
        Integer,
        default=0,
        nullable=False,
    )

    minimum_stock = Column(
        Integer,
        default=5,
        nullable=False,
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
        back_populates="products",
    )

    category = relationship(
        "Category",
        back_populates="products",
    )

    brand = relationship(
        "Brand",
        back_populates="products",
    )

    variants = relationship(
        "ProductVariant",
        back_populates="product",
        cascade="all, delete-orphan",
    )