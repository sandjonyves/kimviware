# Auth Service - Python/FastAPI

Authentication microservice for KIMVIEware testing.

## Features
- User registration with validation
- JWT authentication
- Token verification
- ~25 conditional branches for symbolic execution

## Endpoints

**POST /auth/register**
```json
{
  "email": "student@university.cm",
  "username": "student123",
  "password": "SecurePass123"
}
```

**POST /auth/login**
```json
{
  "username": "student123",
  "password": "SecurePass123"
}
```

**POST /auth/verify**
```json
{
  "token": "eyJhbGc..."
}
```

## Run
```bash
pip install -r requirements.txt
python -m uvicorn src.main:app --reload
```

## Symbolic Execution

Expected paths: **80-120 trajectories**
Branches: **~25 decision points**
