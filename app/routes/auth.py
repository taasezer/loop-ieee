from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app.models.orm import User, UserRole
from app.auth.security import verify_password, get_password_hash, create_access_token, create_refresh_token, oauth2_scheme
from app.dependencies import get_current_active_user
from pydantic import BaseModel, EmailStr

router = APIRouter()

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    phone_number: str
    role: UserRole = UserRole.CUSTOMER
    company_name: str | None = None
    supplier_code: str | None = None

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    is_active: bool
    supplier_code: str | None = None
    company_name: str | None = None

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    # Check if user exists
    result = await db.execute(select(User).where(User.email == user.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    result = await db.execute(select(User).where(User.phone_number == user.phone_number))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Phone number already registered")

    hashed_password = get_password_hash(user.password)
    import secrets
    import string
    
    supplier_code = None
    if user.role == UserRole.SUPPLIER:
        chars = string.ascii_uppercase + string.digits
        supplier_code = "SUP-" + "".join(secrets.choice(chars) for _ in range(6))

    new_user = User(
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name,
        phone_number=user.phone_number,
        role=user.role,
        company_name=user.company_name,
        supplier_code=supplier_code
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    # Kurye ise otomatik profil oluştur ve tedarikçiye bağla
    if user.role == UserRole.COURIER:
        from app.models.orm import Courier
        
        target_supplier_id = None
        if user.supplier_code:
            supplier_result = await db.execute(select(User).where(User.supplier_code == user.supplier_code.upper()))
            supplier = supplier_result.scalar_one_or_none()
            if supplier:
                target_supplier_id = supplier.id
                
        new_courier = Courier(
            user_id=new_user.id,
            supplier_id=target_supplier_id,
            is_online=False
        )
        db.add(new_courier)
        await db.commit()
    return new_user

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(subject=user.id)
    refresh_token = create_refresh_token(subject=user.id)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }
@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user
