from pydantic import BaseModel


# ==========================================
# Create Stock
# ==========================================

class StockCreate(BaseModel):

    variant_id: int

    k_stock: int = 0

    r_stock: int = 0

    minimum_stock: int = 0

    maximum_stock: int = 0


# ==========================================
# Update Stock
# ==========================================

class StockUpdate(BaseModel):

    k_stock: int

    r_stock: int

    minimum_stock: int = 0

    maximum_stock: int = 0


# ==========================================
# Response
# ==========================================

class StockResponse(BaseModel):

    id: int

    variant_id: int

    k_stock: int

    r_stock: int

    minimum_stock: int

    maximum_stock: int

    quantity: int

    class Config:
        from_attributes = True