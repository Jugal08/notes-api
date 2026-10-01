# postgresql://neondb_owner:npg_RAM7EiYvuK0C@ep-withered-shadow-b5pozwt1-pooler.c-7.us-east-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require
import os
from dotenv import load_dotenv
from datetime import datetime
from pydantic import BaseModel, Field
from pydantic import BaseModel
from fastapi import FastAPI
from sqlalchemy.orm import Session
from fastapi import Depends
from database import SessionLocal
from models import NoteModel, UserModel
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer



load_dotenv()

secret_key = os.environ.get("SECRET_KEY")
ALGORITHM = "HS256"

app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "Hello, Jugal"}


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


class Note(BaseModel):
    title: str
    content: str


class Note(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    content: str = Field(..., min_length=1)


notes = []


class NoteCreate(BaseModel):
    title: str
    content: str


class NoteResponse(BaseModel):
    id: int
    title: str
    content: str
    created_at: datetime


class UserCreate(BaseModel):
    email: str
    password: str


def create_access_token(data: dict, expires_minutes: int = 60):
    to_encode = data.copy()
    to_encode["exp"] = datetime.now() + timedelta(minutes=expires_minutes)
    return jwt.encode(to_encode, secret_key, algorithm=ALGORITHM)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_query_params(skip: int = 0, limit: int = 10):
    return {"skip": skip, "limit": limit}


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, secret_key, algorithms=[ALGORITHM])
    except:
        raise HTTPException(status_code=401, detail="invalid token")


@app.post("/signup")
def signup(user: UserCreate, db: Session = Depends(get_db)):
    hashed = hash_password(user.password)
    db_user = UserModel(email=user.email, hashed_password=hashed)
    db.add(db_user)
    db.commit()
    return {"message": "User Created"}


@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    db_user = db.query(UserModel).filter(
        UserModel.email == form_data.username).first()
    if not db_user or not verify_password(form_data.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid Credentials")
    token = create_access_token({"sub": db_user.email})
    return {"access_token": token, "token_type": "bearer"}


@app.post("/notes", response_model=NoteResponse)
async def create_notes(note: NoteCreate, db: Session = Depends(get_db)):
    db_note = NoteModel(title=note.title, content=note.content)
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    return db_note


@app.get("/notes", response_model=list[NoteResponse])
async def get_notes(db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    return db.query(NoteModel).all()
