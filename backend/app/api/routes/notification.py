from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.crud.notification import get_notifications

router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"],
)


@router.get("/")
def notifications(
    shop_id: int,
    db: Session = Depends(get_db),
):

    return get_notifications(
        db=db,
        shop_id=shop_id,
    )