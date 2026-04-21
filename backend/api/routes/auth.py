"""backend/api/routes/auth.py — Authentication API endpoints"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from pydantic import BaseModel
import jwt
import bcrypt
from datetime import datetime, timedelta, timezone

from backend.db.session import get_session
from backend.models.conversation import Customer
from backend.core.config import settings

# Wait, check if SECRET_KEY exists in settings. If not, use a dummy one for now.
SECRET_KEY = getattr(settings, 'SECRET_KEY', 'supersecuresecretkey-change-in-prod')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 # 7 days

router = APIRouter(prefix="/auth", tags=["Authentication"])


class AuthRequest(BaseModel):
    email: str
    password: str
    name: str | None = None  # Only required for signup

class AuthResponse(BaseModel):
    access_token: str
    token_type: str
    email: str
    name: str

def get_password_hash(password: str) -> str:
    # Hash password with bcrypt directly
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


@router.post("/signup", response_model=AuthResponse)
def signup(req: AuthRequest, db: Session = Depends(get_session)):
    query = select(Customer).where(Customer.email == req.email)
    existing = db.exec(query).first()
    
    if existing:
        if existing.hashed_password:
            raise HTTPException(status_code=400, detail="User already exists.")
        # If they exist but have no password (legacy), let them claim the account
        existing.hashed_password = get_password_hash(req.password)
        if req.name:
            existing.name = req.name
        db.add(existing)
        db.commit()
        db.refresh(existing)
        user = existing
    else:
        user = Customer(
            email=req.email,
            name=req.name or req.email.split('@')[0],
            hashed_password=get_password_hash(req.password),
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    token = create_access_token({"sub": user.email})
    return AuthResponse(access_token=token, token_type="bearer", email=user.email, name=user.name)


@router.post("/login", response_model=AuthResponse)
def login(req: AuthRequest, db: Session = Depends(get_session)):
    query = select(Customer).where(Customer.email == req.email)
    user = db.exec(query).first()

    if not user or not user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    
    if not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    token = create_access_token({"sub": user.email})
    return AuthResponse(access_token=token, token_type="bearer", email=user.email, name=user.name)

