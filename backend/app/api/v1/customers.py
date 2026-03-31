from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.crud import customer as crud
from app.schemas.customer import CustomerCreate, CustomerUpdate, CustomerResponse

router = APIRouter()


@router.get("", response_model=list[CustomerResponse])
async def list_customers(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)):
    return await crud.get_customers(db, skip=skip, limit=limit)


@router.post("", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(data: CustomerCreate, db: AsyncSession = Depends(get_db)):
    return await crud.create_customer(db, data)


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(customer_id: int, db: AsyncSession = Depends(get_db)):
    customer = await crud.get_customer(db, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@router.patch("/{customer_id}", response_model=CustomerResponse)
async def update_customer(customer_id: int, data: CustomerUpdate, db: AsyncSession = Depends(get_db)):
    customer = await crud.get_customer(db, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return await crud.update_customer(db, customer, data)


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_customer(customer_id: int, db: AsyncSession = Depends(get_db)):
    customer = await crud.get_customer(db, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    await crud.delete_customer(db, customer)
