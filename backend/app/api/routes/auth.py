from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.auth import (
    ShopRegisterRequest,
    TokenResponse,
)
from app.crud.auth import (
    register_shop,
    authenticate_user,
)
from app.core.token import create_access_token

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post("/register")
def register(
    request: ShopRegisterRequest,
    db: Session = Depends(get_db),
):
    try:
        shop = register_shop(db, request)

        return {
            "message": "Shop created successfully",
            "shop_id": shop.id,
            "shop_name": shop.shop_name,
        }

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):

    user = authenticate_user(
        db,
        form_data.username,
        form_data.password,
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    token = create_access_token(
        {
            "user_id": user.id,
            "shop_id": user.shop_id,
            "role": user.role.value,
        }
    )

    return {
        "access_token": token,
        "token_type": "bearer",
    }