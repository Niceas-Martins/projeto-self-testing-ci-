import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.controllers.routes import build_routes
from src.domain.rules import BusinessError
from src.repositories.sqlite_repository import SQLiteRepository
from src.services.wallet_service import WalletService


def create_app(repo=None, validator=None, antifraud=None):
    app = FastAPI(title="Wallet API", version="1.0.0")
    repository = repo or SQLiteRepository(os.getenv("DATABASE_URL", "wallet.db"))
    service = WalletService(repository, validator, antifraud)

    @app.exception_handler(BusinessError)
    async def business_error_handler(request: Request, exc: BusinessError):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

    @app.get("/")
    def home():
        return {"message": "Wallet API ativa", "docs": "/docs"}

    app.include_router(build_routes(service))
    return app


app = create_app()
