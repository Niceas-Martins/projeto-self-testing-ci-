from datetime import date, timedelta
from decimal import Decimal

from fastapi import APIRouter, Header, Query
from pydantic import BaseModel, Field
from typing import Literal


def build_routes(service):
    router = APIRouter()

    class AccountInput(BaseModel):
        owner: str = Field(min_length=1)
        initial_balance: Decimal = Decimal("0")

    class TransferInput(BaseModel):
        origin_id: int
        destination_id: int
        amount: Decimal

    @router.get("/health")
    def health():
        return {"status": "ok"}

    @router.post("/accounts", status_code=201)
    def create_account(payload: AccountInput):
        return service.create_account(payload.owner, payload.initial_balance)

    @router.get("/accounts/{account_id}")
    def get_account(account_id: int):
        return service.get_account(account_id)

    @router.post("/transfers", status_code=201)
    def transfer(payload: TransferInput, idempotency_key: str = Header(..., alias="Idempotency-Key")):
        return service.transfer(payload.origin_id, payload.destination_id, payload.amount, idempotency_key)

    @router.get("/accounts/{account_id}/statement")
    def statement(account_id: int, kind: Literal["credit", "debit"] | None = None,
                  start: date | None = Query(None), end: date | None = Query(None)):
        start_iso = start.isoformat() if start else None
        # Inclusivo até o final da data informada (fim exclusivo no SQL).
        end_iso = (end + timedelta(days=1)).isoformat() if end else None
        return service.statement(account_id, kind, start_iso, end_iso)

    return router
