from __future__ import annotations

from pydantic import BaseModel
from typing import Annotated, Union

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Union[str, None] = None

class UserBase(BaseModel):
    email: str

class UserCreate(UserBase):
    username: str
    password: str
    alamat: str = None  
    nomor_hp: str = None 

class UserInfo(UserBase):
    username: str
    alamat: str = None  
    nomor_hp: str = None 

class UserLogin(BaseModel):
    email: str
    password: str

class UserUpdate(UserBase):
    username: str
    alamat: str = None  
    nomor_hp: str = None 


class User(UserBase):
    username: str
    password: str
    id: int

class UserLoginSuccessResponse(BaseModel):
    status: str = "success"
    message: str = "Login berhasil"
    user: dict

class UserLoginErrorResponse(BaseModel):
    status: str = "error"
    message: str = "Email atau kata sandi salah"
