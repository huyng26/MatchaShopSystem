from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.crud import delivery as crud
from app.schemas.delivery import (
    DeliveryBatchCreate,
    DeliveryBatchUpdate,
    DeliveryBatchResponse,
    AssignOrdersToBatch,
    DeliveryOrderResponse,
)
from app.services.delivery_service import suggest_batches

router = APIRouter()


@router.get("/batches", response_model=list[DeliveryBatchResponse])
async def list_batches(skip: int = 0, limit: int = 50, db: AsyncSession = Depends(get_db)):
    return await crud.get_batches(db, skip=skip, limit=limit)


@router.post("/batches", response_model=DeliveryBatchResponse, status_code=status.HTTP_201_CREATED)
async def create_batch(data: DeliveryBatchCreate, db: AsyncSession = Depends(get_db)):
    return await crud.create_batch(db, data)


@router.get("/batches/suggest", response_model=list[list[int]])
async def suggest_batch_groupings(
    max_per_batch: int = 10, db: AsyncSession = Depends(get_db)
):
    """Returns suggested order groupings for batching (list of order ID lists)."""
    return await suggest_batches(db, max_per_batch=max_per_batch)


@router.get("/batches/{batch_id}", response_model=DeliveryBatchResponse)
async def get_batch(batch_id: int, db: AsyncSession = Depends(get_db)):
    batch = await crud.get_batch(db, batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Delivery batch not found")
    return batch


@router.patch("/batches/{batch_id}", response_model=DeliveryBatchResponse)
async def update_batch(batch_id: int, data: DeliveryBatchUpdate, db: AsyncSession = Depends(get_db)):
    batch = await crud.get_batch(db, batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Delivery batch not found")
    return await crud.update_batch(db, batch, data)


@router.post("/batches/{batch_id}/assign", response_model=DeliveryBatchResponse)
async def assign_orders(batch_id: int, data: AssignOrdersToBatch, db: AsyncSession = Depends(get_db)):
    batch = await crud.get_batch(db, batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Delivery batch not found")
    return await crud.assign_orders_to_batch(db, batch, data)


@router.get("/orders/unassigned", response_model=list[DeliveryOrderResponse])
async def list_unassigned_orders(db: AsyncSession = Depends(get_db)):
    return await crud.get_unassigned_delivery_orders(db)
