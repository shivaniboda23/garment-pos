from datetime import datetime

from sqlalchemy.orm import Session, joinedload

from app.models.purchase import Purchase
from app.models.purchase_item import PurchaseItem
from app.models.product import Product


# ==========================================================
# Generate Purchase Number
# ==========================================================

def generate_purchase_number(shop_id: int):
    now = datetime.now()
    return f"PUR-{shop_id}-{now.strftime('%Y%m%d%H%M%S')}"


# ==========================================================
# Create Purchase
# ==========================================================

def create_purchase(
    db: Session,
    shop_id: int,
    data,
):

    purchase = Purchase(

        shop_id=shop_id,

        supplier_id=data.supplier_id,

        invoice_number=generate_purchase_number(shop_id),

        supplier_invoice=data.supplier_invoice,

        subtotal=data.subtotal,

        discount=data.discount,

        gst=data.gst,

        grand_total=data.grand_total,

        paid_amount=data.paid_amount,

        balance_amount=data.balance_amount,

        status="Completed"
        if data.balance_amount == 0
        else "Pending",
    )

    db.add(purchase)

    db.flush()

    for item in data.items:

        product = (
            db.query(Product)
            .filter(
                Product.id == item.product_id,
                Product.shop_id == shop_id,
            )
            .first()
        )

        if not product:
            raise Exception(
                f"Product {item.product_id} not found"
            )

        # ----------------------------
        # Update Stock
        # ----------------------------

        if item.stock_type == "K":

            product.k_stock += item.quantity

        elif item.stock_type == "R":

            product.r_stock += item.quantity

        else:

            raise Exception(
                "Invalid Stock Type"
            )

        purchase_item = PurchaseItem(

            purchase_id=purchase.id,

            product_id=item.product_id,

            quantity=item.quantity,

            stock_type=item.stock_type,

            cost_price=item.cost_price,

            gst_percentage=item.gst_percentage,

            discount=item.discount,

            total=item.total,
        )

        db.add(purchase_item)

    db.commit()

    db.refresh(purchase)

    return purchase


# ==========================================================
# Purchase History
# ==========================================================

def get_all_purchases(

    db: Session,

    shop_id: int,

    invoice: str | None = None,

    supplier_id: int | None = None,

    status: str | None = None,

    from_date: datetime | None = None,

    to_date: datetime | None = None,

):

    query = (

        db.query(Purchase)

        .options(

            joinedload(Purchase.supplier)

        )

        .filter(

            Purchase.shop_id == shop_id

        )

    )

    if invoice:

        query = query.filter(

            Purchase.invoice_number.ilike(

                f"%{invoice}%"

            )

        )

    if supplier_id:

        query = query.filter(

            Purchase.supplier_id == supplier_id

        )

    if status:

        query = query.filter(

            Purchase.status == status

        )

    if from_date:

        query = query.filter(

            Purchase.created_at >= from_date

        )

    if to_date:

        query = query.filter(

            Purchase.created_at <= to_date

        )

    purchases = (

        query.order_by(

            Purchase.created_at.desc()

        )

        .all()

    )

    return purchases


# ==========================================================
# Purchase Details
# ==========================================================

def get_purchase_by_id(

    db: Session,

    purchase_id: int,

    shop_id: int,

):

    purchase = (

        db.query(Purchase)

        .options(

            joinedload(Purchase.supplier),

            joinedload(Purchase.items)

            .joinedload(PurchaseItem.product),

        )

        .filter(

            Purchase.id == purchase_id,

            Purchase.shop_id == shop_id,

        )

        .first()

    )

    return purchase


# ==========================================================
# Search Purchase By Invoice
# ==========================================================

def search_purchase_invoice(

    db: Session,

    shop_id: int,

    invoice: str,

):

    return (

        db.query(Purchase)

        .filter(

            Purchase.shop_id == shop_id,

            Purchase.invoice_number.ilike(

                f"%{invoice}%"

            ),

        )

        .all()

    )


# ==========================================================
# Search Purchase By Supplier
# ==========================================================

def search_purchase_supplier(

    db: Session,

    shop_id: int,

    supplier_id: int,

):

    return (

        db.query(Purchase)

        .filter(

            Purchase.shop_id == shop_id,

            Purchase.supplier_id == supplier_id,

        )

        .order_by(

            Purchase.created_at.desc()

        )

        .all()

    )


# ==========================================================
# Pending Purchases
# ==========================================================

def get_pending_purchases(

    db: Session,

    shop_id: int,

):

    return (

        db.query(Purchase)

        .filter(

            Purchase.shop_id == shop_id,

            Purchase.status == "Pending",

        )

        .order_by(

            Purchase.created_at.desc()

        )

        .all()

    )


# ==========================================================
# Completed Purchases
# ==========================================================

def get_completed_purchases(

    db: Session,

    shop_id: int,

):

    return (

        db.query(Purchase)

        .filter(

            Purchase.shop_id == shop_id,

            Purchase.status == "Completed",

        )

        .order_by(

            Purchase.created_at.desc()

        )

        .all()

    )