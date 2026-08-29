# FastUI Sales Platform

An internal CRM and Sales automation platform designed specifically for the FastUI team to discover, manage, and close website design deals.

## Architecture
- **Frontend**: Next.js 14 (App Router), React, Tailwind CSS, shadcn/ui.
- **Backend**: FastAPI, SQLAlchemy, PostgreSQL, JWT Authentication.
- **Workers**: Python async workers for background lead discovery and deduplication.

## Getting Started (Local Development)

### Prerequisites
- Docker & Docker Compose
- Node.js (v20+) & pnpm
- Python 3.11+

### Running Manually

#### 1. Database
Set up a Supabase Postgres instance or run a local Postgres database. Copy `.env.example` to `.env` and fill in the connection details.

#### 2. Backend (FastAPI)
```bash
cd services/api
python -m venv venv
source venv/bin/activate # or venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn main:app --reload
```

#### 3. Frontend (Next.js)
```bash
cd apps/sales
pnpm install
pnpm dev
```
