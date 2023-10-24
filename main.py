from sqlalchemy.orm import Session


# import models

from sql_app.my_package import schemas, models
from sql_app.my_package.database import SessionLocal, engine

from pyngrok import ngrok
import os

from datetime import datetime, timedelta
from typing import Union

from fastapi import Depends, FastAPI, HTTPException, status, Path
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from typing_extensions import Annotated
from pydantic import BaseModel

# import schemas

models.Base.metadata.create_all(bind=engine)

# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
        "disabled": False,
    }
}

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Union[str, None] = None

class User(BaseModel):
    username: str
    email: Union[str, None] = None
    full_name: Union[str, None] = None
    disabled: Union[bool, None] = None

class UserInDB(User):
    hashed_password: str

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
app = FastAPI()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def get_username(db: Session, username: str):
    user_dict = db.query(models.User).filter(models.User.username == username).first()
    return user_dict

def authenticate_user(db: Session, username: str, password: str):
    user = get_username(db, username)
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user

def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_username(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

@app.post("/register", response_model=schemas.User)
async def register_account(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    created_user = crud.create_user(db=db, user=user)
    user_response = schemas.User(
        email=created_user.email,
        username=created_user.username,
        password=created_user.password,
        alamat=created_user.alamat,
        nomor_hp=created_user.nomor_hp,
        id=created_user.id)
    return user_response

@app.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: Session = Depends(get_db)
):
    user = authenticate_user(db=db, username=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer", "id": user.id}

@app.get("/users/{user_id}", response_model=schemas.UserInfo)
async def read_users_me(
    user_id: int = Path(..., title="User ID"), db: Session = Depends(get_db)
):
    print(user_id)
    user_information = crud.get_user(db, user_id=user_id)
    return user_information


@app.patch("/users/{user_id}", response_model=schemas.UserInfo)
async def update_user_me(
    user_id: int = Path(..., title="User ID"),
    updated_data: schemas.UserUpdate = None,
    db: Session = Depends(get_db)
):
    if updated_data is None:
        raise HTTPException(status_code=400, detail="Invalid request data")

    # Dapatkan data pengguna berdasarkan user_id
    user = crud.get_user(db, user_id=user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # Perbarui atribut-atribut pengguna sesuai dengan data yang dikirim
    for key, value in updated_data.dict(exclude_unset=True).items():
        setattr(user, key, value)

    # Commit perubahan ke database
    db.commit()
    db.refresh(user)

    # Mengembalikan data pengguna yang telah diperbarui
    return user

if __name__ == '__main__':
    import uvicorn
    public_url = ngrok.connect(8080).public_url
    print(f' * Running on {public_url}')
    uvicorn.run(app, host="0.0.0.0", port=8080)

