from datetime import date

from sqlalchemy import extract, func
from sqlalchemy.orm import Session

from app.models.expense import Expense
from app.models.expense_category import ExpenseCategory
from app.models.shop import Shop


# ==========================================================
# EXPENSE CATEGORY CRUD
# ==========================================================

def create_expense_category(
    db: Session,
    shop_id: int,
    data,
):
    shop = (
        db.query(Shop)
        .filter(
            Shop.id == shop_id,
        )
        .first()
    )

    if not shop:
        return None

    category = ExpenseCategory(
        shop_id=shop_id,
        category_name=data.category_name,
        description=data.description,
    )

    db.add(category)
    db.commit()
    db.refresh(category)

    return category


def get_expense_categories(
    db: Session,
    shop_id: int,
):
    return (
        db.query(ExpenseCategory)
        .filter(
            ExpenseCategory.shop_id == shop_id,
            ExpenseCategory.is_active == True,
        )
        .order_by(
            ExpenseCategory.category_name
        )
        .all()
    )


def get_expense_category(
    db: Session,
    shop_id: int,
    category_id: int,
):
    return (
        db.query(ExpenseCategory)
        .filter(
            ExpenseCategory.id == category_id,
            ExpenseCategory.shop_id == shop_id,
        )
        .first()
    )


def update_expense_category(
    db: Session,
    shop_id: int,
    category_id: int,
    data,
):
    category = get_expense_category(
        db=db,
        shop_id=shop_id,
        category_id=category_id,
    )

    if not category:
        return None

    update_data = data.model_dump(
        exclude_unset=True,
    )

    for key, value in update_data.items():
        setattr(
            category,
            key,
            value,
        )

    db.commit()
    db.refresh(category)

    return category


def delete_expense_category(
    db: Session,
    shop_id: int,
    category_id: int,
):
    category = get_expense_category(
        db=db,
        shop_id=shop_id,
        category_id=category_id,
    )

    if not category:
        return None

    expense_count = (
        db.query(Expense)
        .filter(
            Expense.shop_id == shop_id,
            Expense.category_id == category_id,
        )
        .count()
    )

    if expense_count > 0:
        return "HAS_EXPENSES"

    category.is_active = False

    db.commit()

    return True


# ==========================================================
# EXPENSE CRUD
# ==========================================================

def create_expense(
    db: Session,
    shop_id: int,
    data,
):
    shop = (
        db.query(Shop)
        .filter(
            Shop.id == shop_id,
        )
        .first()
    )

    if not shop:
        return None

    category = (
        db.query(ExpenseCategory)
        .filter(
            ExpenseCategory.id == data.category_id,
            ExpenseCategory.shop_id == shop_id,
            ExpenseCategory.is_active == True,
        )
        .first()
    )

    if not category:
        return None

    expense = Expense(
        shop_id=shop_id,
        category_id=data.category_id,
        amount=data.amount,
        payment_method=data.payment_method,
        reference_number=data.reference_number,
        description=data.description,
    )

    if data.expense_date is not None:
        expense.expense_date = data.expense_date

    db.add(expense)
    db.commit()
    db.refresh(expense)

    return expense


def get_expenses(
    db: Session,
    shop_id: int,
):
    return (
        db.query(Expense)
        .filter(
            Expense.shop_id == shop_id,
        )
        .order_by(
            Expense.expense_date.desc()
        )
        .all()
    )


def get_expense(
    db: Session,
    shop_id: int,
    expense_id: int,
):
    return (
        db.query(Expense)
        .filter(
            Expense.id == expense_id,
            Expense.shop_id == shop_id,
        )
        .first()
    )


def update_expense(
    db: Session,
    shop_id: int,
    expense_id: int,
    data,
):
    expense = get_expense(
        db=db,
        shop_id=shop_id,
        expense_id=expense_id,
    )

    if not expense:
        return None

    if data.category_id is not None:

        category = (
            db.query(ExpenseCategory)
            .filter(
                ExpenseCategory.id == data.category_id,
                ExpenseCategory.shop_id == shop_id,
                ExpenseCategory.is_active == True,
            )
            .first()
        )

        if not category:
            return None

    update_data = data.model_dump(
        exclude_unset=True,
    )

    for key, value in update_data.items():
        setattr(
            expense,
            key,
            value,
        )

    db.commit()
    db.refresh(expense)

    return expense


def delete_expense(
    db: Session,
    shop_id: int,
    expense_id: int,
):
    expense = get_expense(
        db=db,
        shop_id=shop_id,
        expense_id=expense_id,
    )

    if not expense:
        return False

    db.delete(expense)
    db.commit()

    return True


# ==========================================================
# REPORTS
# ==========================================================

def get_today_expenses(
    db: Session,
    shop_id: int,
):
    today = date.today()

    return (
        db.query(Expense)
        .filter(
            Expense.shop_id == shop_id,
            extract(
                "year",
                Expense.expense_date,
            ) == today.year,
            extract(
                "month",
                Expense.expense_date,
            ) == today.month,
            extract(
                "day",
                Expense.expense_date,
            ) == today.day,
        )
        .order_by(
            Expense.expense_date.desc()
        )
        .all()
    )


def get_monthly_expenses(
    db: Session,
    shop_id: int,
    month: int,
    year: int,
):
    return (
        db.query(Expense)
        .filter(
            Expense.shop_id == shop_id,
            extract(
                "month",
                Expense.expense_date,
            ) == month,
            extract(
                "year",
                Expense.expense_date,
            ) == year,
        )
        .order_by(
            Expense.expense_date.desc()
        )
        .all()
    )


def get_category_expenses(
    db: Session,
    shop_id: int,
    category_id: int,
):
    return (
        db.query(Expense)
        .filter(
            Expense.shop_id == shop_id,
            Expense.category_id == category_id,
        )
        .order_by(
            Expense.expense_date.desc()
        )
        .all()
    )


def get_total_expense(
    db: Session,
    shop_id: int,
):
    return (
        db.query(
            func.coalesce(
                func.sum(
                    Expense.amount
                ),
                0,
            )
        )
        .filter(
            Expense.shop_id == shop_id,
        )
        .scalar()
    )