from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import SessionLocal, engine, Base
import models
import schemas

from jose import jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
from datetime import date
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

app = FastAPI()
security = HTTPBearer()

Base.metadata.create_all(bind=engine)

#  DATABASE
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

#  AUTHENTICATION
SECRET_KEY = "mysecretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ROLES = ["viewer", "analyst", "admin"]

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)

def create_token(data: dict):
    data["exp"] = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

#  LOGIN REQUEST 
class LoginRequest(BaseModel):
    email: str
    password: str

#  CURRENT USER 
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")

        user = db.query(models.User).filter(models.User.id == user_id).first()

        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        if not user.is_active:
            raise HTTPException(status_code=403, detail="User inactive")

        return user

    except:
        raise HTTPException(status_code=401, detail="Token expired or invalid")

# ROLE CHECK 
def admin_only(user):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

def analyst_or_admin(user):
    if user.role not in ["admin", "analyst"]:
        raise HTTPException(status_code=403, detail="Not allowed")


# Home
@app.get("/")
def home_page():
    return {"Message": "Welcome to my project by adding /docs in url "}

# LOGIN 
@app.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == data.email).first()

    if not user or not verify_password(data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_token({"user_id": user.id, "role": user.role})

    return {"access_token": token}

# USERS
@app.post("/create-users", response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):

    if user.role not in ROLES:
        raise HTTPException(status_code=400, detail="Invalid role")

    existing = db.query(models.User).filter(models.User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email exists")

    new_user = models.User(
        name=user.name,
        email=user.email,
        password=hash_password(user.password),
        role=user.role
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user

# SHOW USERS
@app.get("/users", response_model=list[schemas.UserResponse])
def get_users(user = Depends(get_current_user), db: Session = Depends(get_db)): 
    admin_only(user)
    return db.query(models.User).all()

# RECORDS
@app.post("/records", response_model=schemas.RecordResponse)
def create_record(
    record: schemas.RecordCreate,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    admin_only(user)

    if record.type not in ["income", "expense"]:
        raise HTTPException(status_code=400, detail="Invalid type")

    r = models.Record(**record.dict())
    db.add(r)
    db.commit()
    db.refresh(r)

    return r


@app.get("/records", response_model=list[schemas.RecordResponse])
def get_records(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    analyst_or_admin(user)
    return db.query(models.Record).offset(skip).limit(limit).all()

#  FILTER 
@app.get("/filter-records", response_model=list[schemas.RecordResponse])
def filter_records(
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
    type: Optional[str] = None,
    category: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
):
    analyst_or_admin(user)

    query = db.query(models.Record)

    if type:
        query = query.filter(models.Record.type == type)

    if category:
        query = query.filter(models.Record.category == category)

    if start_date:
        query = query.filter(models.Record.date >= start_date)

    if end_date:
        query = query.filter(models.Record.date <= end_date)

    return query.all()
 
# UPDATE RECORD
@app.put("/records/{record_id}", response_model=schemas.RecordResponse)
def update_record(
    record_id: int,
    data: schemas.RecordUpdate,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    admin_only(user)

    r = db.query(models.Record).filter(models.Record.id == record_id).first()

    if not r:
        raise HTTPException(status_code=404, detail="Not found")

    update_data = data.dict(exclude_unset=True)

    # Protect date field
    if "date" in update_data and update_data["date"] is None:
        raise HTTPException(status_code=400, detail="Date cannot be null")

    # Validate type
    if "type" in update_data and update_data["type"] not in ["income", "expense"]:
        raise HTTPException(status_code=400, detail="Invalid type")

    #Apply update safely
    for key, value in update_data.items():
        setattr(r, key, value)

    try:
        db.commit()
        db.refresh(r)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    return r

#DELETE RECORD
@app.delete("/records/{record_id}")
def delete_record(
    record_id: int,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    admin_only(user)

    r = db.query(models.Record).filter(models.Record.id == record_id).first()

    if not r:
        raise HTTPException(status_code=404, detail="Not found")

    db.delete(r)
    db.commit()

    return {"message": "Deleted"}

# ROLE CHECK 
def viewer_access(user):
    if user.role not in ["admin", "analyst", "viewer"]:
        raise HTTPException(status_code=403, detail="Not allowed")


#  DASHBOARD 

# Summary
@app.get("/summary")
def summary(
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    viewer_access(user)

    data = db.query(
        models.Record.type,
        func.sum(models.Record.amount)
    ).group_by(models.Record.type).all()

    income = 0
    expense = 0

    for t, amount in data:
        if t == "income":
            income = amount
        elif t == "expense":
            expense = amount

    return {
        "income": income,
        "expense": expense,
        "balance": income - expense
    }


# Recent Transactions
@app.get("/recent", response_model=list[schemas.RecordResponse])
def recent(
    limit: int = 5,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    viewer_access(user)

    if limit > 20:
        limit = 20

    return db.query(models.Record)\
        .order_by(models.Record.date.desc())\
        .limit(limit)\
        .all()


# Category-wise Summary
@app.get("/category-summary")
def category_summary(
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    viewer_access(user)

    data = db.query(
        models.Record.category,
        func.sum(models.Record.amount).label("total")
    ).group_by(models.Record.category).all()

    return [
        {"category": c, "total": t}
        for c, t in data
    ]


# Monthly Summary (Trend)
from sqlalchemy import extract

@app.get("/monthly-summary")
def monthly_summary(
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    viewer_access(user)

    data = db.query(
        extract('month', models.Record.date).label("month"),
        func.sum(models.Record.amount).label("total")
    ).group_by("month").all()

    return [
        {"month": int(m), "total": t}
        for m, t in data
    ]
