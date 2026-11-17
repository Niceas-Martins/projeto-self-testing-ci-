from decimal import Decimal, InvalidOperation


class BusinessError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def to_cents(value: Decimal | str | int) -> int:
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise BusinessError("Valor monetário inválido") from None
    if not amount.is_finite() or amount < 0 or amount != amount.quantize(Decimal("0.01")):
        raise BusinessError("Valor deve ser não negativo e ter no máximo duas casas decimais")
    return int(amount * 100)


def transfer_rules(origin: int, destination: int, balance_cents: int, amount_cents: int) -> None:
    if origin <= 0 or destination <= 0:
       raise BusinessError("IDs das contas devem ser positivos")
    if origin == destination:
        raise BusinessError("Contas de origem e destino devem ser diferentes")
    if amount_cents <= 0:
        raise BusinessError("Transferência deve ser maior que zero")
    if balance_cents < amount_cents:
        raise BusinessError("Saldo insuficiente", 409)


def format_money(cents: int) -> str:
    return f"{Decimal(cents) / 100:.2f}"
