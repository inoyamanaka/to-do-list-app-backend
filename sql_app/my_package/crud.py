from sqlalchemy.orm import Session
from . import schemas, models
from passlib.context import CryptContext
from typing import Annotated, Union
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from main import verify_password

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
# AUTHTENTICATION  
def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


# USER INFORMATION
def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_password(db: Session, password: str):
    return db.query(models.User).filter(models.User.password == password).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.UserCreate):
    pass_hash = pwd_context.hash(user.password)
    db_user = models.User(email=user.email, password=pass_hash, username=user.username, alamat=user.alamat,nomor_hp=user.nomor_hp)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: int):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user:
        db.delete(user)
        db.commit()
        return user

    return None

def update_user(db: Session, user_id: int, updated_data: dict):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user:
        # Perbarui atribut pengguna dengan nilai dari updated_data
        for key, value in updated_data.items():
            setattr(user, key, value)
        
        db.commit()
        db.refresh(user)
        return user
    
    return None

## ------------------ ITEMS -------------------- ##
