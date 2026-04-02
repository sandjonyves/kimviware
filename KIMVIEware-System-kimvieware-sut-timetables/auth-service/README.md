# Auth Service - Python/FastAPI

Authentication microservice for the Timetables SUT.

## Prerequisites

*   Python 3.8+

## Setup

Install the required Python packages:
```bash
pip install -r requirements.txt
```

## Usage

To start the service, run the following command from this directory:
```bash
python -m uvicorn src.main:app --reload --port 8001
```

The service will be available at `http://localhost:8001`.

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

## Symbolic Execution

*   **Expected paths**: 80-120 trajectories
*   **Branches**: ~25 decision points
