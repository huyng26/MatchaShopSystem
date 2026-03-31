# Matcha Shop System

A comprehensive business management platform for specialty Matcha shop operations, featuring real-time inventory tracking, Point-of-Sale (POS) for counter and delivery orders, delivery batch management, and financial reporting.

## Modules

| Module | Description |
|---|---|
| **Inventory** | Track ingredients, stock levels, purchase history, and ingredient costs |
| **Products** | Manage menu items and their ingredient recipes |
| **POS** | Process counter and delivery orders with payment recording |
| **Delivery** | Group and batch delivery orders for optimized dispatch |
| **Customers** | Store customer profiles and delivery addresses |
| **Finance** | Record operational costs (electricity, water, staff) and compute net profit |
| **Dashboard** | Periodic revenue, COGS, and profitability overview |

---

## Tech Stack

- **Backend**: Python 3.12 · FastAPI · SQLAlchemy (async) · Alembic · PostgreSQL 16
- **Frontend**: React 18 · TypeScript · Vite · Tailwind CSS · shadcn/ui · React Router · Zustand
- **Infrastructure**: Docker · docker-compose

---

## Project Structure

```
MatchaShopSystem/
├── backend/
│   ├── app/
│   │   ├── api/v1/        # Route handlers
│   │   ├── models/        # SQLAlchemy ORM models
│   │   ├── schemas/       # Pydantic schemas
│   │   ├── services/      # Business logic
│   │   ├── crud/          # DB query helpers
│   │   └── core/          # Config, DB session, security
│   ├── alembic/           # DB migrations
│   ├── requirements.txt
│   └── main.py
├── frontend/
│   ├── src/
│   │   ├── components/    # Shared UI components
│   │   ├── pages/         # Module pages
│   │   ├── api/           # Typed API client
│   │   └── store/         # Zustand state
│   └── package.json
├── docker-compose.yml
└── README.md
```

---

## Getting Started

### Prerequisites

- Docker & docker-compose
- (For local dev without Docker) Python 3.12+, Node.js 20+, PostgreSQL 16

### 1. Clone and configure environment

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
# Edit both .env files as needed
```

### 2. Run with Docker

```bash
docker-compose up --build
```

- Backend API: http://localhost:8000
- API Docs (Swagger): http://localhost:8000/docs
- Frontend: http://localhost:5173

### 3. Run database migrations

```bash
docker-compose exec backend alembic upgrade head
```

---

### Local Development (without Docker)

#### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in your local DB credentials
alembic upgrade head
uvicorn main:app --reload
```

#### Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

---

## Financial Model

```
Net Profit = Revenue (sales) - COGS (ingredient costs per order) - Operational Costs (electricity, water, staff, …)
```

Operational costs are manually entered per period (month). Revenue and COGS are derived automatically from order and ingredient purchase data.

---

## Delivery Batching

Delivery orders are assigned to a `DeliveryBatch`. The batch groups multiple customer orders for a single driver trip. The dispatch UI shows pending unassigned orders and allows the operator to create batches manually or let the system suggest groupings.
