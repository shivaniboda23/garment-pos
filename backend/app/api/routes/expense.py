from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.dependencies import get_current_user

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
# EXPENSE CATEGORIES
# ==========================================================

@router.post(
    "/categories",
    response_model=ExpenseCategoryResponse,
)
def add_expense_category(
    request: ExpenseCategoryCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    category = create_expense_category(
        db=db,
        shop_id=current_user.shop_id,
        data=request,
    )

    if category is None:
        raise HTTPException(
            status_code=404,
            detail="Shop not found",
        )

    return category


@router.get(
    "/categories",
    response_model=list[ExpenseCategoryResponse],
)
def list_expense_categories(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return get_expense_categories(
        db=db,
        shop_id=current_user.shop_id,
    )


@router.get(
    "/category/{category_id}",
    response_model=ExpenseCategoryResponse,
)
def expense_category_details(
    category_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    category = get_expense_category(
        db=db,
        shop_id=current_user.shop_id,
        category_id=category_id,
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
    current_user=Depends(get_current_user),
):
    category = update_expense_category(
        db=db,
        shop_id=current_user.shop_id,
        category_id=category_id,
        data=request,
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
    current_user=Depends(get_current_user),
):
    result = delete_expense_category(
        db=db,
        shop_id=current_user.shop_id,
        category_id=category_id,
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Expense Category not found",
        )

    if result == "HAS_EXPENSES":
        raise HTTPException(
            status_code=400,
            detail=(
                "This category has expense records and "
                "cannot be deleted. Deactivate it instead."
            ),
        )

    return {
        "message": "Expense Category deactivated successfully"
    }


# ==========================================================
# EXPENSE REPORT ENDPOINTS
#
# These MUST come before /{expense_id}
# ==========================================================

@router.get(
    "/today",
)
def today_expenses(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return get_today_expenses(
        db=db,
        shop_id=current_user.shop_id,
    )


@router.get(
    "/monthly",
)
def monthly_expenses(
    month: int,
    year: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return get_monthly_expenses(
        db=db,
        shop_id=current_user.shop_id,
        month=month,
        year=year,
    )


@router.get(
    "/total",
)
def total_expense(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return {
        "total_expense": get_total_expense(
            db=db,
            shop_id=current_user.shop_id,
        )
    }


@router.get(
    "/category/{category_id}",
)
def expenses_by_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return get_category_expenses(
        db=db,
        shop_id=current_user.shop_id,
        category_id=category_id,
    )


# ==========================================================
# EXPENSE CRUD
# ==========================================================

@router.post(
    "",
    response_model=ExpenseResponse,
)
def add_expense(
    request: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    expense = create_expense(
        db=db,
        shop_id=current_user.shop_id,
        data=request,
    )

    if expense is None:
        raise HTTPException(
            status_code=404,
            detail="Shop or Category not found",
        )

    return expense


@router.get(
    "",
    response_model=list[ExpenseResponse],
)
def list_expenses(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return get_expenses(
        db=db,
        shop_id=current_user.shop_id,
    )


# ==========================================================
# EXPENSE DETAILS
#
# Keep this LAST because /{expense_id} is dynamic.
# ==========================================================

@router.get(
    "/{expense_id}",
    response_model=ExpenseResponse,
)
def expense_details(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    expense = get_expense(
        db=db,
        shop_id=current_user.shop_id,
        expense_id=expense_id,
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
    current_user=Depends(get_current_user),
):
    expense = update_expense(
        db=db,
        shop_id=current_user.shop_id,
        expense_id=expense_id,
        data=request,
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
    current_user=Depends(get_current_user),
):
    deleted = delete_expense(
        db=db,
        shop_id=current_user.shop_id,
        expense_id=expense_id,
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Expense not found",
        )

    return {
        "message": "Expense deleted successfully"
    }