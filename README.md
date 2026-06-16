# DILP - Digital Integration Learning Platform

DILP is a modern, multi-tenant educational platform designed to deliver structured learning programmes to children. It provides a secure and compliant environment where learning is supervised by teachers and authorized by parents, with a clean separation between application logic and rich educational content.

## 🌟 Key Features

- **Multi-Tenancy**: Support for multiple organizations (tenants) with isolated data and schools.
- **RBAC (Role-Based Access Control)**: Specialized interfaces for Admins, Teachers, Parents, Children, and read-only Auditors.
- **CMS-Driven Content**: Learning materials are managed in Strapi CMS, allowing for rich, flexible content delivery.
- **GDPR Compliant**: Built-in consent management, PII soft-delete, and data export features.
- **Progress Tracking**: Real-time tracking of student progress through modules and lessons.
- **Secure Child Login**: Simplified and secure login for children using username and PIN.
- **Activity & Audit Logging**: HTTP activity and ORM-level audit logs, viewable by admins and auditors via `/logs`.

## 🏗️ Architecture & Tech Stack

DILP follows a layered architecture to ensure maintainability and scalability.

- **Backend**: FastAPI (Python 3.11)
  - **Database**: MySQL 8 (managed via SQLAlchemy & Alembic)
  - **Auth**: JWT with Argon2 password hashing
- **Frontend**: React (TypeScript) with Vite
- **CMS**: Strapi 4 (PostgreSQL)
- **Containerization**: Docker & Docker Compose

## 👥 User Roles

| Role | Responsibilities |
|------|------------------|
| **Parent** | Registers via email, manages child accounts, grants/revokes GDPR consent, and monitors progress. |
| **Child** | Accesses assigned learning programmes using a username and PIN. |
| **Teacher** | Manages student groups, assigns programmes, and authors content for their groups. |
| **Admin** | Manages tenants, schools, and teachers. Oversees global and tenant-specific programmes. |
| **Auditor** | Read-only access to activity and audit logs for compliance review. Provisioned via the `create-auditor` CLI. |

## 🚀 Getting Started

### Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Node.js 18+

### 1. Infrastructure Setup

Start the core services (MySQL, Strapi, PostgreSQL):

```bash
docker compose -f docker-compose.local.yml up -d
```

### 2. Backend Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env      # Configure your environment variables
alembic upgrade head
uvicorn app.main:app --reload
```

### 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

## 📂 Project Structure

- `backend/`: FastAPI application, database models, and migrations.
- `frontend/`: React application with Vite.
- `cms_service/`: Custom Strapi implementation and configurations.
- `docs/`: Comprehensive technical documentation.

## ⚖️ License

This project is proprietary. All rights reserved.

