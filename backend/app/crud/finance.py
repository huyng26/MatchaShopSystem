from decimal import Decimal
from sqlalchemy import select, func, extract
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.finance import OperationalCost
from app.models.order import Order, OrderItem, Payment, OrderStatus
from app.models.ingredient import IngredientPurchase
from app.models.product import ProductIngredient
from app.schemas.finance import OperationalCostCreate, OperationalCostUpdate, ProfitSummary


async def get_operational_costs(
    db: AsyncSession, month: int | None = None, year: int | None = None, skip: int = 0, limit: int = 100
) -> list[OperationalCost]:
    query = select(OperationalCost)
    if month:
        query = query.where(OperationalCost.period_month == month)
    if year:
        query = query.where(OperationalCost.period_year == year)
    query = query.order_by(OperationalCost.period_year.desc(), OperationalCost.period_month.desc())
    result = await db.execute(query.offset(skip).limit(limit))
    return list(result.scalars().all())


async def get_operational_cost(db: AsyncSession, cost_id: int) -> OperationalCost | None:
    result = await db.execute(select(OperationalCost).where(OperationalCost.id == cost_id))
    return result.scalar_one_or_none()


async def create_operational_cost(db: AsyncSession, data: OperationalCostCreate) -> OperationalCost:
    cost = OperationalCost(**data.model_dump())
    db.add(cost)
    await db.commit()
    await db.refresh(cost)
    return cost


async def update_operational_cost(
    db: AsyncSession, cost: OperationalCost, data: OperationalCostUpdate
) -> OperationalCost:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(cost, field, value)
    await db.commit()
    await db.refresh(cost)
    return cost


async def delete_operational_cost(db: AsyncSession, cost: OperationalCost) -> None:
    await db.delete(cost)
    await db.commit()


async def get_profit_summary(db: AsyncSession, month: int, year: int) -> ProfitSummary:
    # Revenue: sum of payments for completed orders in the period
    revenue_result = await db.execute(
        select(func.coalesce(func.sum(Payment.amount), 0)).join(Order).where(
            Order.status == OrderStatus.completed,
            extract("month", Payment.paid_at) == month,
            extract("year", Payment.paid_at) == year,
        )
    )
    revenue = Decimal(str(revenue_result.scalar()))

    # Order count
    order_count_result = await db.execute(
        select(func.count(Order.id)).join(Payment).where(
            Order.status == OrderStatus.completed,
            extract("month", Payment.paid_at) == month,
            extract("year", Payment.paid_at) == year,
        )
    )
    order_count = int(order_count_result.scalar() or 0)

    # COGS: ingredient purchase costs recorded in the period
    cogs_result = await db.execute(
        select(func.coalesce(func.sum(IngredientPurchase.total_cost), 0)).where(
            extract("month", IngredientPurchase.purchased_at) == month,
            extract("year", IngredientPurchase.purchased_at) == year,
        )
    )
    cogs = Decimal(str(cogs_result.scalar()))

    # Operational costs
    op_cost_result = await db.execute(
        select(func.coalesce(func.sum(OperationalCost.amount), 0)).where(
            OperationalCost.period_month == month,
            OperationalCost.period_year == year,
        )
    )
    operational_costs = Decimal(str(op_cost_result.scalar()))

    return ProfitSummary(
        period_month=month,
        period_year=year,
        revenue=revenue,
        cogs=cogs,
        operational_costs=operational_costs,
        net_profit=revenue - cogs - operational_costs,
        order_count=order_count,
    )
