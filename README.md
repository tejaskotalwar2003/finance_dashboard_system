#  Finance Data Processing Backend

## Overview
This is a FastAPI backend project that manages financial records with role-based access control (RBAC).

## Features
- User Authentication (JWT)
- Role-Based Access (Admin, Analyst, Viewer)
- CRUD operations for financial records
- Filtering (date, type, category)
- Dashboard APIs:
  - Summary
  - Category-wise analysis
  - Monthly trends

### Configure Database Credentials

Update the database configuration in your project before running:

```python
DB_USER = "Enter your username"
DB_PASSWORD = "Enter your password"
DB_HOST = "localhost"
DB_NAME = "finance_db"
```

## Tech Stack
- FastAPI
- PostgreSQL
- SQLAlchemy
- JWT Authentication

## API Endpoints

### Auth
- POST /login

### Users
- POST /create-users
- GET /users

### Records
- POST /records
- GET /records
- PUT /records/{id}
- DELETE /records/{id}

### Dashboard
- GET /summary
- GET /recent
- GET /category-summary
- GET /monthly-summary

## Run Project
- uvicorn main:app --reload
