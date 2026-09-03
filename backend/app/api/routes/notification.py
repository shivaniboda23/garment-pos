from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies import get_current_user
from app.crud.notification import get_notifications

router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"],
)


@router.get("/")
def notifications(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):

    return get_notifications(
        db=db,
        shop_id=current_user.shop_id,
    )
