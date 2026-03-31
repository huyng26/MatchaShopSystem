from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.crud import finance as crud
from app.schemas.finance import (
    OperationalCostCreate,
    OperationalCostUpdate,
    OperationalCostResponse,
    ProfitSummary,
)

router = APIRouter()


@router.get("/costs", response_model=list[OperationalCostResponse])
async def list_costs(
    month: int | None = None,
    year: int | None = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    return await crud.get_operational_costs(db, month=month, year=year, skip=skip, limit=limit)


@router.post("/costs", response_model=OperationalCostResponse, status_code=status.HTTP_201_CREATED)
async def create_cost(data: OperationalCostCreate, db: AsyncSession = Depends(get_db)):
    return await crud.create_operational_cost(db, data)


@router.get("/costs/{cost_id}", response_model=OperationalCostResponse)
async def get_cost(cost_id: int, db: AsyncSession = Depends(get_db)):
    cost = await crud.get_operational_cost(db, cost_id)
    if not cost:
        raise HTTPException(status_code=404, detail="Operational cost not found")
    return cost


@router.patch("/costs/{cost_id}", response_model=OperationalCostResponse)
async def update_cost(cost_id: int, data: OperationalCostUpdate, db: AsyncSession = Depends(get_db)):
    cost = await crud.get_operational_cost(db, cost_id)
    if not cost:
        raise HTTPException(status_code=404, detail="Operational cost not found")
    return await crud.update_operational_cost(db, cost, data)


@router.delete("/costs/{cost_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cost(cost_id: int, db: AsyncSession = Depends(get_db)):
    cost = await crud.get_operational_cost(db, cost_id)
    if not cost:
        raise HTTPException(status_code=404, detail="Operational cost not found")
    await crud.delete_operational_cost(db, cost)


@router.get("/summary", response_model=ProfitSummary)
async def profit_summary(
    month: int = Query(..., ge=1, le=12, description="Month (1-12)"),
    year: int = Query(..., ge=2020, description="Year"),
    db: AsyncSession = Depends(get_db),
):
    """Compute revenue, COGS, operational costs, and net profit for a given month/year."""
    return await crud.get_profit_summary(db, month=month, year=year)
