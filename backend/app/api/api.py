from fastapi import APIRouter

from app.api.routes import (
    auth,
    products,
    product_variant,
    customer,
    stock,
    sale,
    billing,
    purchase_return,
)

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(products.router)
api_router.include_router(product_variant.router)
api_router.include_router(customer.router)
api_router.include_router(sale.router)
api_router.include_router(stock.router)
api_router.include_router(billing.router)
api_router.include_router(purchase_return.router)