# ✦ TaskFlow — Full Stack Task Manager

A full-stack Task Manager demonstrating **FastAPI + Streamlit** with **JWT authentication**.

---

## Architecture

```
Task Manager/
├── backend/
│   ├── main.py          # FastAPI application with JWT auth and task CRUD
│   └── requirements.txt # backend Python dependencies
├── frontend/
│   ├── app.py           # Streamlit entry point and UI logic
│   ├── api_client.py    # HTTP wrapper for FastAPI calls
│   └── requirements.txt # frontend Python dependencies
└── README.md
```
---

## Key Concepts Covered

### 1. FastAPI Dependency Injection
`get_current_user` is injected into protected routes using `Depends()`.
```python
@app.get("/tasks")
def list_tasks(current_user = Depends(get_current_user)):
    ...
```
This validates the JWT and returns the authenticated user or raises 401.

### 2. OAuth2 + JWT Authentication
- Uses `OAuth2PasswordBearer` with the password grant flow.
- `/token` returns a signed JWT when login succeeds.
- Token payload includes `sub` (user email) and `exp` (expiry).
- Passwords are hashed with **bcrypt** using `passlib`.

### 3. Streamlit Session State
State is stored in `st.session_state` for the signed-in user and UI state:
```python
st.session_state.token
st.session_state.email
st.session_state.page
st.session_state.tasks
st.session_state.edit_task_data
```

### 4. Single-File Streamlit Frontend
- `frontend/app.py` contains the full Streamlit UI flow.
- `frontend/api_client.py` centralizes backend HTTP calls.
- No Streamlit multi-page routing folder is required.

---

## Running the App

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend
cd ../frontend
pip install -r requirements.txt
streamlit run app.py
```

| Service       | URL                            |
|---------------|--------------------------------|
| Streamlit UI  | http://localhost:8501          |
| FastAPI       | http://localhost:8000          |
| Swagger Docs  | http://localhost:8000/docs     |
| ReDoc         | http://localhost:8000/redoc    |

---

## API Reference

| Method | Endpoint              | Auth | Description          |
|--------|-----------------------|------|----------------------|
| POST   | /users/               | —    | Register user        |
| POST   | /token                | —    | Login and get JWT    |
| GET    | /users/me/            | JWT  | Get current user     |
| GET    | /tasks/               | JWT  | List tasks           |
| POST   | /tasks/               | JWT  | Create task          |
| GET    | /tasks/{id}           | JWT  | Get task             |
| PUT    | /tasks/{id}           | JWT  | Update task          |
| DELETE | /tasks/{id}           | JWT  | Delete task          |

---

## Task Model

| Field       | Type   | Notes                         |
|-------------|--------|-------------------------------|
| id          | int    | Primary key                   |
| title       | str    | Required                      |
| description | str    | Optional                      |
| completed   | bool   | Task completion flag          |
| owner_id    | int    | User owner foreign key        |

---

