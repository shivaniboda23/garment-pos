import random
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.product_variant import ProductVariant
from app.models.sale import Sale
from app.models.sale_item import SaleItem
from app.models.shop import Shop
from sqlalchemy import String
from sqlalchemy.orm import joinedload


from datetime import datetime

def generate_invoice():
    return f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}"


def create_sale(db: Session, data):

    # -----------------------------
    # Validate Shop
    # -----------------------------
    shop = (
        db.query(Shop)
        .filter(Shop.id == data.shop_id)
        .first()
    )

    if not shop:
        return None

    # -----------------------------
    # Validate Customer
    # -----------------------------
    if data.customer_id:

        customer = (
            db.query(Customer)
            .filter(Customer.id == data.customer_id)
            .first()
        )

        if not customer:
            return None

    subtotal = Decimal("0")
    gst_total = Decimal("0")

    sale_items = []

    # -----------------------------
    # Validate Items
    # -----------------------------
    for item in data.items:

        variant = (
            db.query(ProductVariant)
            .filter(ProductVariant.id == item.variant_id)
            .first()
        )

        if not variant:
            raise Exception(
                f"Variant {item.variant_id} not found."
            )

        if not variant.stock:
            raise Exception(
                f"No stock found for Variant {variant.id}"
            )

        # Quantity validation
        if item.quantity != (item.k_quantity + item.r_quantity):
            raise Exception(
                f"Total quantity must equal K Quantity + R Quantity for SKU {variant.sku}"
            )

        # Validate K Stock
        if item.k_quantity > variant.stock.k_stock:
            raise Exception(
                f"Not enough K Stock for SKU {variant.sku}"
            )

        # Validate R Stock
        if item.r_quantity > variant.stock.r_stock:
            raise Exception(
                f"Not enough R Stock for SKU {variant.sku}"
            )

        unit_price = Decimal(variant.selling_price)

        line_total = unit_price * Decimal(item.quantity)

        line_total -= Decimal(item.discount)

        gst = (
            line_total
            * Decimal(variant.product.gst_percentage)
            / Decimal("100")
        )

        subtotal += line_total
        gst_total += gst

        sale_items.append(
            {
                "variant": variant,
                "quantity": item.quantity,
                "k_quantity": item.k_quantity,
                "r_quantity": item.r_quantity,
                "unit_price": unit_price,
                "discount": Decimal(item.discount),
                "gst": gst,
                "total": line_total + gst,
            }
        )

    grand_total = subtotal + gst_total - Decimal(data.discount)

    invoice = generate_invoice()

    while (
        db.query(Sale)
        .filter(Sale.invoice_number == invoice)
        .first()
    ):
        invoice = generate_invoice()

    sale = Sale(
        shop_id=data.shop_id,
        customer_id=data.customer_id,
        invoice_number=invoice,
        subtotal=subtotal,
        discount=Decimal(data.discount),
        gst_amount=gst_total,
        total_amount=grand_total,
        payment_method=data.payment_method,
        status="Completed",
    )

    db.add(sale)

    db.flush()

    # -----------------------------
    # Save Items & Reduce Stock
    # -----------------------------
    for row in sale_items:

        variant = row["variant"]

        stock = variant.stock

        if stock.k_stock < row["k_quantity"]:
            raise Exception("Insufficient K Stock")

        if stock.r_stock < row["r_quantity"]:
            raise Exception("Insufficient R Stock")

        sale_item = SaleItem(
            sale_id=sale.id,
            variant_id=variant.id,
            quantity=row["quantity"],
            k_quantity=row["k_quantity"],
            r_quantity=row["r_quantity"],
            unit_price=row["unit_price"],
            discount=row["discount"],
            gst=row["gst"],
            total_price=row["total"],
        )

        db.add(sale_item)

    db.commit()

    db.refresh(sale)

    return sale
# ==========================================================
# SALES HISTORY
# ==========================================================


from app.models.sale import Sale


def get_all_sales(
    db: Session,
    shop_id: int,
    invoice: str | None = None,
    customer_id: int | None = None,
    date: str | None = None,
):

    query = (
        db.query(Sale)
        .options(
            joinedload(Sale.customer),
            joinedload(Sale.items)
        )
        .filter(
            Sale.shop_id == shop_id
        )
    )

    if invoice:

        query = query.filter(
            Sale.invoice_number.ilike(
                f"%{invoice}%"
            )
        )

    if customer_id:

        query = query.filter(
            Sale.customer_id == customer_id
        )

    if date:

        query = query.filter(
            Sale.created_at.cast(String).like(
                f"{date}%"
            )
        )

    sales = (
        query.order_by(
            Sale.created_at.desc()
        )
        .all()
    )

    return sales


# ==========================================================
# SALE DETAILS
# ==========================================================

def get_sale_by_id(
    db: Session,
    sale_id: int,
    shop_id: int,
):

    sale = (
        db.query(Sale)
        .options(
            joinedload(Sale.customer),
            joinedload(Sale.items)
            .joinedload(SaleItem.variant)
        )
        .filter(
            Sale.id == sale_id,
            Sale.shop_id == shop_id,
        )
        .first()
    )

    return sale