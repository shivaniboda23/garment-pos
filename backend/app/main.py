from fastapi import FastAPI

from fastapi.middleware.cors import (
    CORSMiddleware,
)

from app.api.api import api_router

from app.api.routes import supplier
from app.api.routes import purchase
from app.api.routes import supplier_payment
from app.api.routes import expense

from app.api.routes.sale_return import (
    router as sale_return_router,
)

from app.api.routes.dashboard import (
    router as dashboard_router,
)

from app.api.routes.report import (
    router as report_router,
)

from app.api.routes.notification import (
    router as notification_router,
)

from app.api.routes.customer_payments import (
    router as customer_payments_router,
)

from app.api.routes.stock_movements import (
    router as stock_movements_router,
)

from app.api.routes.tailoring import (
    router as tailoring_router,
)

from app.api.routes.tailor_payment import (
    router as tailor_payment_router,
)


# ==========================================================
# APP
# ==========================================================

app = FastAPI(
    title="Bhavani ERP API",
    version="1.0.0",
)


# ==========================================================
# CORS
# ==========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*"
    ],
    allow_credentials=True,
    allow_methods=[
        "*"
    ],
    allow_headers=[
        "*"
    ],
)


# ==========================================================
# CORE API
# ==========================================================

app.include_router(
    api_router
)


# ==========================================================
# SUPPLIERS / PURCHASES
# ==========================================================

app.include_router(
    supplier.router
)

app.include_router(
    purchase.router
)

app.include_router(
    supplier_payment.router
)


# ==========================================================
# RETURNS
# ==========================================================

app.include_router(
    sale_return_router
)


# ==========================================================
# DASHBOARD / REPORTS
# ==========================================================

app.include_router(
    dashboard_router
)

app.include_router(
    report_router
)

app.include_router(
    expense.router
)

app.include_router(
    notification_router
)


# ==========================================================
# CUSTOMER PAYMENTS
# ==========================================================

app.include_router(
    customer_payments_router
)


# ==========================================================
# STOCK MOVEMENTS
# ==========================================================

app.include_router(
    stock_movements_router
)


# ==========================================================
# TAILORING / PENDING DELIVERY
# ==========================================================

app.include_router(
    tailoring_router
)

app.include_router(
    tailor_payment_router
)


# ==========================================================
# ROOT
# ==========================================================

@app.get("/")
def root():

    return {
        "status":
            "running",

        "project":
            "Bhavani ERP",

        "framework":
            "FastAPI",

        "version":
            "1.0.0",
    }