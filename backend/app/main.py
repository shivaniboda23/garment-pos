from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.api import api_router
from app.api.routes import supplier
from app.api.routes import purchase
from app.api.routes.sale_return import router as sale_return_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.report import router as report_router
from app.api.routes import expense
from app.api.routes.notification import router as notification_router

app = FastAPI(
    title="Bhavani ERP API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
app.include_router(supplier.router)
app.include_router(purchase.router)
app.include_router(sale_return_router)
app.include_router(dashboard_router)
app.include_router(report_router)
app.include_router(
    expense.router,
    prefix="/expenses",
    tags=["Expenses"],
)
app.include_router(notification_router)

@app.get("/")
def root():
    return {
        "status": "running",
        "project": "Bhavani ERP",
        "framework": "FastAPI",
        "version": "1.0.0",
    }