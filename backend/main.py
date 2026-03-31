from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1 import inventory, products, pos, delivery, customers, finance

app = FastAPI(
    title="Matcha Shop System",
    description="Business management platform for specialty Matcha shop operations.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(inventory.router, prefix="/api/v1/inventory", tags=["Inventory"])
app.include_router(products.router, prefix="/api/v1/products", tags=["Products"])
app.include_router(pos.router, prefix="/api/v1/pos", tags=["POS"])
app.include_router(delivery.router, prefix="/api/v1/delivery", tags=["Delivery"])
app.include_router(customers.router, prefix="/api/v1/customers", tags=["Customers"])
app.include_router(finance.router, prefix="/api/v1/finance", tags=["Finance"])


@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "service": "Matcha Shop System"}


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy"}
