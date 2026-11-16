from uuid import uuid4

from src.domain.rules import BusinessError, format_money, to_cents, transfer_rules
from src.repositories.sqlite_repository import utc_now


class IdentityValidator:
    """Stub substitui esta dependência nos testes de integração."""
    def is_valid(self, owner: str) -> bool:
        return bool(owner.strip())


class AntifraudGateway:
    """Gateway fictício; em produção seria um cliente HTTP de webhook."""
    def notify(self, payload: dict) -> None:
        # Não enviamos dados para nenhum serviço real.
        return None


class WalletService:
    def __init__(self, repo, validator=None, antifraud=None):
        self.repo = repo
        self.validator = validator or IdentityValidator()
        self.antifraud = antifraud or AntifraudGateway()

    def create_account(self, owner: str, initial_balance):
        if not self.validator.is_valid(owner):
            raise BusinessError("Cadastro inválido")
        cents = to_cents(initial_balance)
        result = self.repo.create_account(owner.strip(), cents)
        return self._public_account(result)

    @staticmethod
    def _public_account(account):
        return {"id": account["id"], "owner": account["owner"],
                "balance": format_money(account["balance_cents"])}

    def get_account(self, account_id: int):
        account = self.repo.get_account(account_id)
        if account is None:
            raise BusinessError("Conta não encontrada", 404)
        return self._public_account(account)

    def transfer(self, origin_id: int, destination_id: int, amount, idempotency_key: str):
        if not idempotency_key.strip():
            raise BusinessError("Idempotency-Key obrigatório")
        cents = to_cents(amount)
        # Apenas o banco determina se a operação já aconteceu.
        with self.repo.transaction() as conn:
            existing = conn.execute("SELECT * FROM transfers WHERE idempotency_key=?",
                                    (idempotency_key,)).fetchone()
            if existing is not None:
                if (existing["origin_id"], existing["destination_id"], existing["amount_cents"]) != (origin_id, destination_id, cents):
                    raise BusinessError("Chave de idempotência reutilizada com outros dados", 409)
                return {"transfer_id": existing["id"], "status": "completed", "replayed": True}
            origin = conn.execute("SELECT * FROM accounts WHERE id=?", (origin_id,)).fetchone()
            destination = conn.execute("SELECT * FROM accounts WHERE id=?", (destination_id,)).fetchone()
            if origin is None or destination is None:
                raise BusinessError("Conta não encontrada", 404)
            transfer_rules(origin_id, destination_id, origin["balance_cents"], cents)
            transfer_id = str(uuid4())
            timestamp = utc_now()
            conn.execute("UPDATE accounts SET balance_cents=balance_cents-? WHERE id=?", (cents, origin_id))
            conn.execute("UPDATE accounts SET balance_cents=balance_cents+? WHERE id=?", (cents, destination_id))
            conn.execute("INSERT INTO transfers(id,idempotency_key,origin_id,destination_id,amount_cents,created_at) VALUES (?,?,?,?,?,?)",
                         (transfer_id, idempotency_key, origin_id, destination_id, cents, timestamp))
            conn.executemany("INSERT INTO entries(account_id, transfer_id, kind, amount_cents, created_at) VALUES (?,?,?,?,?)", [
                (origin_id, transfer_id, "debit", cents, timestamp),
                (destination_id, transfer_id, "credit", cents, timestamp),
            ])
        # Falha do serviço externo não deve reverter a transação já confirmada.
        try:
            self.antifraud.notify({"transfer_id": transfer_id, "origin_id": origin_id,
                                   "destination_id": destination_id, "amount": format_money(cents)})
        except Exception:
            pass  # Limitação documentada: produção exigiria outbox + retentativas.
        return {"transfer_id": transfer_id, "status": "completed", "replayed": False}

    def statement(self, account_id: int, kind=None, start=None, end=None):
        if start and end and start >= end:
            raise BusinessError("Intervalo de datas inválido")
        entries = self.repo.statement(account_id, kind, start, end)
        return [{"id": e["id"], "kind": e["kind"], "amount": format_money(e["amount_cents"]),
                 "transfer_id": e["transfer_id"], "created_at": e["created_at"]} for e in entries]
