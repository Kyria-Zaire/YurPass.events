"""Authentication HTTP routes."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.repository import AuthRepository
from app.modules.auth.schemas import LoginRequest, LoginResponse, RegisterRequest, RegisterResponse
from app.modules.auth.service import AuthService

router = APIRouter()


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """Provide AuthService with a database session."""
    return AuthService(AuthRepository(db))


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    payload: RegisterRequest,
    service: AuthService = Depends(get_auth_service),
) -> RegisterResponse:
    """Create a new account with email and password."""
    return service.register(
        email=str(payload.email),
        password=payload.password,
        full_name=payload.full_name,
    )


@router.post("/login", response_model=LoginResponse)
def login(
    payload: LoginRequest,
    service: AuthService = Depends(get_auth_service),
) -> LoginResponse:
    """Authenticate with email and password."""
    return service.login(email=str(payload.email), password=payload.password)
