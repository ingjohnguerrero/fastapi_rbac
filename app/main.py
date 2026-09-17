"""FastAPI application. Health does not ping the database."""

from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.roles import router as roles_router
from app.api.users import router as users_router


def create_app() -> FastAPI:
    application = FastAPI(title="fastapi_rbac")
    application.include_router(auth_router)
    application.include_router(users_router)
    application.include_router(roles_router)

    @application.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return application


app = create_app()
