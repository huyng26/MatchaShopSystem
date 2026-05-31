from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import ingredients, orders, payments, products
from app.core.config import settings
from app.core.integration_contracts import SharedContractUnavailable
from app.services.errors import DomainError

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


@app.exception_handler(DomainError)
async def handle_domain_error(_: Request, exc: DomainError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


@app.exception_handler(SharedContractUnavailable)
async def handle_shared_contract_unavailable(_: Request, exc: SharedContractUnavailable):
    return JSONResponse(status_code=503, content={"detail": str(exc)})


app.include_router(ingredients.router, prefix="/api/v1", tags=["Inventory"])
app.include_router(products.router, prefix="/api/v1", tags=["Products"])
app.include_router(orders.router, prefix="/api/v1", tags=["Orders"])
app.include_router(payments.router, prefix="/api/v1", tags=["Payments"])


@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "service": "Matcha Shop System"}


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy"}


@app.get("/api/v1/status", tags=["Health"])
async def api_status():
    return {"status": "healthy", "api_version": "v1"}
