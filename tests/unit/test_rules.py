from decimal import Decimal
import pytest
from src.domain.rules import BusinessError, format_money, to_cents, transfer_rules


@pytest.mark.parametrize("value,expected", [("0", 0), ("10.50", 1050), (Decimal("1.01"), 101), (5, 500)])
def test_convert_to_cents(value, expected):
    assert to_cents(value) == expected


@pytest.mark.parametrize("value", ["-1", "0.001", "abc", "NaN", "Infinity"])
def test_invalid_amount(value):
    with pytest.raises(BusinessError):
        to_cents(value)


def test_money_display():
    assert format_money(105) == "1.05"


def test_valid_transfer():
    assert transfer_rules(1, 2, 1000, 1000) is None


@pytest.mark.parametrize("origin,destination,balance,amount,code", [
    (1, 1, 100, 50, 400), (1, 2, 100, 0, 400), (1, 2, 100, 101, 409),
])
def test_invalid_transfer(origin, destination, balance, amount, code):
    with pytest.raises(BusinessError) as error:
        transfer_rules(origin, destination, balance, amount)
    assert error.value.status_code == code

@pytest.mark.parametrize("origin,destination", [
    (0, 2),
    (-1, 2),
    (1, 0),
    (1, -2),
])
def test_transfer_rejects_invalid_account_ids(origin, destination):
    with pytest.raises(BusinessError) as error:
        transfer_rules(origin, destination, 1000, 100)

    assert error.value.status_code == 400
