# Bhavani Garments ERP

## Backend

Technology:
- FastAPI
- SQLAlchemy 2
- PostgreSQL
- Alembic
- Python

Backend location:
- backend/

FastAPI app:
- backend/app/main.py

## Core Architecture

Product -> Variant -> Stock Buckets

Garment stock buckets:
- K
- R

This architecture is already fixed.
Do not redesign it unless explicitly requested.

## Stock Rules

- Never allow negative stock.
- Deduct only physically delivered stock.
- Ordered quantity and delivered quantity are different.
- Pending quantity must preserve K/R allocation.
- Do not fake stock values to make tests pass.
- Never rerun historical stock-movement backfill unless explicitly requested.

## Billing

Billing supports:
- ordered quantity
- delivered quantity
- pending quantity
- K/R split
- customer dues
- partial/full payment

Do not redesign the working pending-billing flow without approval.

## Tailoring

A tailored item returned by a tailor is reserved for its customer.

It must NOT enter normal free K/R stock.

When a tailored item is delivered:
- update BillItem delivered quantity
- update SaleItem physical quantity
- allow COGS to catch up
- do not change normal free stock

Never represent tailoring as a fake Purchase.

## Payments

Keep these separate:
- Customer Payments
- Supplier Payments
- Tailor Payments

Tailor payment is liability settlement.

The stitching charge is the tailoring expense.

Do not count the actual tailor payment again as another expense.

Do not allow payments above the unpaid tailoring charge.

## Historical Data

Never:
- guess missing variant relationships
- guess sale relationships
- silently modify historical data
- delete old records merely to make an API work

Handle invalid legacy records safely.

## Authentication

Preserve:
- current authentication
- current_user
- shop_id isolation

Do not introduce new hardcoded shop IDs.

## Database Safety

Do not automatically execute destructive database operations.

Never automatically run:
- DROP TABLE
- TRUNCATE
- DELETE business data
- destructive ALTER operations

If a schema change is necessary:
1. explain why;
2. create a migration;
3. show the migration;
4. wait for approval before destructive operations.

## Development Workflow

Before modifying code:

1. Inspect the existing implementation.
2. Understand affected models.
3. Understand schemas.
4. Understand CRUD/services.
5. Understand routes.
6. Make the smallest compatible change.
7. Avoid unrelated refactoring.

## Validation

After backend changes run:

python -m compileall backend/app

and verify the FastAPI app can import.

Report:
- files changed
- commands executed
- tests performed
- unresolved issues

Do not claim a feature works unless it was actually validated.

## Git Safety

Before a new feature:
- inspect git status
- preserve the working checkpoint

Do not automatically:
- git commit
- git push
- git reset --hard
- git restore
- delete files

unless explicitly instructed.

## Main Rule

Preserve working ERP behavior.

Prefer small compatible changes over large rewrites.