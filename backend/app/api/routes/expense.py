from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db

from app.schemas.expense import (
    ExpenseCategoryCreate,
    ExpenseCategoryUpdate,
    ExpenseCategoryResponse,
    ExpenseCreate,
    ExpenseUpdate,
    ExpenseResponse,
)

from app.crud.expense import (
    create_expense_category,
    get_expense_categories,
    get_expense_category,
    update_expense_category,
    delete_expense_category,
    create_expense,
    get_expenses,
    get_expense,
    update_expense,
    delete_expense,
    get_today_expenses,
    get_monthly_expenses,
    get_category_expenses,
    get_total_expense,
)

router = APIRouter(
    prefix="/expenses",
    tags=["Expenses"],
)

# ==========================================================
# Expense Category
# ==========================================================

@router.post(
    "/categories",
    response_model=ExpenseCategoryResponse,
)
def add_expense_category(
    request: ExpenseCategoryCreate,
    db: Session = Depends(get_db),
):
    category = create_expense_category(db, request)

    if category is None:
        raise HTTPException(
            status_code=404,
            detail="Shop not found",
        )

    return category


@router.get(
    "/categories/{shop_id}",
    response_model=list[ExpenseCategoryResponse],
)
def list_expense_categories(
    shop_id: int,
    db: Session = Depends(get_db),
):
    return get_expense_categories(
        db,
        shop_id,
    )


@router.get(
    "/category/{category_id}",
    response_model=ExpenseCategoryResponse,
)
def expense_category_details(
    category_id: int,
    db: Session = Depends(get_db),
):
    category = get_expense_category(
        db,
        category_id,
    )

    if not category:
        raise HTTPException(
            status_code=404,
            detail="Expense Category not found",
        )

    return category


@router.put(
    "/category/{category_id}",
    response_model=ExpenseCategoryResponse,
)
def edit_expense_category(
    category_id: int,
    request: ExpenseCategoryUpdate,
    db: Session = Depends(get_db),
):
    category = update_expense_category(
        db,
        category_id,
        request,
    )

    if category is None:
        raise HTTPException(
            status_code=404,
            detail="Expense Category not found",
        )

    return category


@router.delete(
    "/category/{category_id}",
)
def remove_expense_category(
    category_id: int,
    db: Session = Depends(get_db),
):
    deleted = delete_expense_category(
        db,
        category_id,
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Expense Category not found",
        )

    return {
        "message": "Expense Category deleted successfully"
    }


# ==========================================================
# Expenses
# ==========================================================

@router.post(
    "",
    response_model=ExpenseResponse,
)
def add_expense(
    request: ExpenseCreate,
    db: Session = Depends(get_db),
):
    expense = create_expense(
        db,
        request,
    )

    if expense is None:
        raise HTTPException(
            status_code=404,
            detail="Shop or Category not found",
        )

    return expense


@router.get(
    "/shop/{shop_id}",
    response_model=list[ExpenseResponse],
)
def list_expenses(
    shop_id: int,
    db: Session = Depends(get_db),
):
    return get_expenses(
        db,
        shop_id,
    )


@router.get(
    "/{expense_id}",
    response_model=ExpenseResponse,
)
def expense_details(
    expense_id: int,
    db: Session = Depends(get_db),
):
    expense = get_expense(
        db,
        expense_id,
    )

    if not expense:
        raise HTTPException(
            status_code=404,
            detail="Expense not found",
        )

    return expense


@router.put(
    "/{expense_id}",
    response_model=ExpenseResponse,
)
def edit_expense(
    expense_id: int,
    request: ExpenseUpdate,
    db: Session = Depends(get_db),
):
    expense = update_expense(
        db,
        expense_id,
        request,
    )

    if expense is None:
        raise HTTPException(
            status_code=404,
            detail="Expense not found",
        )

    return expense


@router.delete(
    "/{expense_id}",
)
def remove_expense(
    expense_id: int,
    db: Session = Depends(get_db),
):
    deleted = delete_expense(
        db,
        expense_id,
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Expense not found",
        )

    return {
        "message": "Expense deleted successfully"
    }


# ==========================================================
# Reports
# ==========================================================

@router.get("/today/{shop_id}")
def today_expenses(
    shop_id: int,
    db: Session = Depends(get_db),
):
    return get_today_expenses(
        db,
        shop_id,
    )


@router.get("/monthly/{shop_id}")
def monthly_expenses(
    shop_id: int,
    month: int,
    year: int,
    db: Session = Depends(get_db),
):
    return get_monthly_expenses(
        db,
        shop_id,
        month,
        year,
    )


@router.get("/category/{shop_id}/{category_id}")
def expenses_by_category(
    shop_id: int,
    category_id: int,
    db: Session = Depends(get_db),
):
    return get_category_expenses(
        db,
        shop_id,
        category_id,
    )


@router.get("/total/{shop_id}")
def total_expense(
    shop_id: int,
    db: Session = Depends(get_db),
):
    return {
        "total_expense": get_total_expense(
            db,
            shop_id,
        )
    }