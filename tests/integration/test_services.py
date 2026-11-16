from concurrent.futures import ThreadPoolExecutor
from unittest.mock import Mock
import pytest

from src.domain.rules import BusinessError
from src.services.wallet_service import WalletService


class CadastroStub:
    def __init__(self, accepted):
        self.accepted = accepted

    def is_valid(self, owner):
        return owner in self.accepted


def test_stub_controls_registration(repo):
    service = WalletService(repo, validator=CadastroStub({"Maria"}))
    assert service.create_account("Maria", "10")["balance"] == "10.00"
    with pytest.raises(BusinessError, match="Cadastro inválido"):
        service.create_account("Desconhecido", "10")


def test_mock_antifraud_call_and_parameters(repo):
    gateway = Mock()
    service = WalletService(repo, antifraud=gateway)
    a = service.create_account("Maria", "100")
    b = service.create_account("João", "0")
    result = service.transfer(a["id"], b["id"], "12.50", "k-1")
    assert result["status"] == "completed"
    gateway.notify.assert_called_once_with({
        "transfer_id": result["transfer_id"], "origin_id": a["id"],
        "destination_id": b["id"], "amount": "12.50"})
    replay = service.transfer(a["id"], b["id"], "12.50", "k-1")
    assert replay["replayed"] is True
    gateway.notify.assert_called_once()


def test_same_key_different_amount_fails(repo):
    svc = WalletService(repo)
    a = svc.create_account("A", "30")
    b = svc.create_account("B", "0")
    svc.transfer(a["id"], b["id"], "5", "unique")
    with pytest.raises(BusinessError) as e:
        svc.transfer(a["id"], b["id"], "6", "unique")
    assert e.value.status_code == 409


def test_unknown_account_and_insufficient_funds(repo):
    svc = WalletService(repo)
    a = svc.create_account("A", "10")
    with pytest.raises(BusinessError) as error:
        svc.get_account(9999)
    assert error.value.status_code == 404
    with pytest.raises(BusinessError) as error:
        svc.transfer(a["id"], 9999, "1", "missing")
    assert error.value.status_code == 404
    b = svc.create_account("B", "0")
    with pytest.raises(BusinessError) as error:
        svc.transfer(a["id"], b["id"], "11", "insufficient")
    assert error.value.status_code == 409


def test_gateway_failure_does_not_undo_transfer(repo):
    gateway = Mock()
    gateway.notify.side_effect = RuntimeError("simulação de indisponibilidade")
    svc = WalletService(repo, antifraud=gateway)
    a = svc.create_account("A", "20")
    b = svc.create_account("B", "0")
    assert svc.transfer(a["id"], b["id"], "5", "webhook-error")["status"] == "completed"
    assert svc.get_account(a["id"])["balance"] == "15.00"


def test_concurrent_transfers_preserve_balance(repo):
    svc = WalletService(repo)
    a = svc.create_account("A", "100")
    b = svc.create_account("B", "0")

    def worker(i):
        try:
            svc.transfer(a["id"], b["id"], "3", f"concurrent-{i}")
            return True
        except BusinessError as error:
            assert error.status_code == 409
            return False

    with ThreadPoolExecutor(max_workers=50) as pool:
        outcomes = list(pool.map(worker, range(50)))
    assert sum(outcomes) == 33
    assert svc.get_account(a["id"])["balance"] == "1.00"
    assert svc.get_account(b["id"])["balance"] == "99.00"


def test_statement_filters_and_invalid_range(repo):
    svc = WalletService(repo)
    a = svc.create_account("A", "20")
    b = svc.create_account("B", "0")
    svc.transfer(a["id"], b["id"], "2", "statement")
    assert len(svc.statement(a["id"], "debit")) == 1
    assert len(svc.statement(a["id"], "credit")) == 1
    assert svc.statement(a["id"], start="2100-01-01") == []
    assert svc.statement(a["id"], end="2000-01-01") == []
    with pytest.raises(BusinessError):
        svc.statement(a["id"], start="2026-02-01", end="2026-01-01")
    with pytest.raises(BusinessError):
        svc.statement(9999)


def test_account_without_opening_entry(repo):
    svc = WalletService(repo)
    account = svc.create_account("A", "0")
    assert svc.statement(account["id"]) == []
