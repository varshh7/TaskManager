from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import uuid

# ─── App Setup ────────────────────────────────────────────────────────────────
app = FastAPI(title="Task Manager API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Config ───────────────────────────────────────────────────────────────────
SECRET_KEY = "your-super-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# ─── Password Hashing ─────────────────────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# ─── In-Memory "Database" ─────────────────────────────────────────────────────
# users: { username: { username, hashed_password, full_name } }
fake_users_db = {}

# tasks: { task_id: { id, title, description, status, priority, owner, created_at, due_date } }
fake_tasks_db = {}

# ─── Pydantic Models ──────────────────────────────────────────────────────────
class UserCreate(BaseModel):
    username: str
    password: str
    full_name: str

class UserOut(BaseModel):
    username: str
    full_name: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = ""
    priority: str = "medium"    # low | medium | high
    due_date: Optional[str] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None   # todo | in_progress | done
    priority: Optional[str] = None
    due_date: Optional[str] = None

class TaskOut(BaseModel):
    id: str
    title: str
    description: str
    status: str
    priority: str
    owner: str
    created_at: str
    due_date: Optional[str]

# ─── Auth Helpers ─────────────────────────────────────────────────────────────
def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode["exp"] = expire
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def authenticate_user(username: str, password: str):
    user = fake_users_db.get(username)
    if not user or not verify_password(password, user["hashed_password"]):
        return None
    return user

# ─── Dependency: Get Current User ─────────────────────────────────────────────
async def get_current_user(token: str = Depends(oauth2_scheme)):
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

    user = fake_users_db.get(token_data.username)
    if user is None:
        raise credentials_exception
    return user

# ─── Auth Routes ──────────────────────────────────────────────────────────────
@app.post("/auth/register", response_model=UserOut, status_code=201)
def register(user: UserCreate):
    if user.username in fake_users_db:
        raise HTTPException(status_code=400, detail="Username already registered")
    fake_users_db[user.username] = {
        "username": user.username,
        "full_name": user.full_name,
        "hashed_password": hash_password(user.password),
    }
    return UserOut(username=user.username, full_name=user.full_name)

@app.post("/auth/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(
        data={"sub": user["username"]},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return Token(access_token=token, token_type="bearer")

@app.get("/auth/me", response_model=UserOut)
def get_me(current_user=Depends(get_current_user)):
    return UserOut(username=current_user["username"], full_name=current_user["full_name"])

# ─── Task Routes ──────────────────────────────────────────────────────────────
@app.get("/tasks", response_model=List[TaskOut])
def list_tasks(
    status_filter: Optional[str] = None,
    priority_filter: Optional[str] = None,
    current_user=Depends(get_current_user),
):
    """Return all tasks for the logged-in user, with optional filters."""
    tasks = [
        t for t in fake_tasks_db.values()
        if t["owner"] == current_user["username"]
    ]
    if status_filter:
        tasks = [t for t in tasks if t["status"] == status_filter]
    if priority_filter:
        tasks = [t for t in tasks if t["priority"] == priority_filter]
    # Sort newest first
    tasks.sort(key=lambda t: t["created_at"], reverse=True)
    return tasks

@app.post("/tasks", response_model=TaskOut, status_code=201)
def create_task(task: TaskCreate, current_user=Depends(get_current_user)):
    task_id = str(uuid.uuid4())
    new_task = {
        "id": task_id,
        "title": task.title,
        "description": task.description or "",
        "status": "todo",
        "priority": task.priority,
        "owner": current_user["username"],
        "created_at": datetime.utcnow().isoformat(),
        "due_date": task.due_date,
    }
    fake_tasks_db[task_id] = new_task
    return new_task

@app.get("/tasks/{task_id}", response_model=TaskOut)
def get_task(task_id: str, current_user=Depends(get_current_user)):
    task = fake_tasks_db.get(task_id)
    if not task or task["owner"] != current_user["username"]:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.put("/tasks/{task_id}", response_model=TaskOut)
def update_task(task_id: str, update: TaskUpdate, current_user=Depends(get_current_user)):
    task = fake_tasks_db.get(task_id)
    if not task or task["owner"] != current_user["username"]:
        raise HTTPException(status_code=404, detail="Task not found")
    update_data = update.dict(exclude_none=True)
    task.update(update_data)
    fake_tasks_db[task_id] = task
    return task

@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: str, current_user=Depends(get_current_user)):
    task = fake_tasks_db.get(task_id)
    if not task or task["owner"] != current_user["username"]:
        raise HTTPException(status_code=404, detail="Task not found")
    del fake_tasks_db[task_id]

# ─── Stats Route ──────────────────────────────────────────────────────────────
@app.get("/tasks/stats/summary")
def get_stats(current_user=Depends(get_current_user)):
    tasks = [t for t in fake_tasks_db.values() if t["owner"] == current_user["username"]]
    return {
        "total": len(tasks),
        "todo": sum(1 for t in tasks if t["status"] == "todo"),
        "in_progress": sum(1 for t in tasks if t["status"] == "in_progress"),
        "done": sum(1 for t in tasks if t["status"] == "done"),
        "high": sum(1 for t in tasks if t["priority"] == "high"),
        "medium": sum(1 for t in tasks if t["priority"] == "medium"),
        "low": sum(1 for t in tasks if t["priority"] == "low"),
    }
