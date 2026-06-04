import pytest
from pydantic import ValidationError

from app.schemas.customer import CustomerCreate, CustomerUpdate


def test_customer_create_normalizes_text_fields() -> None:
    payload = CustomerCreate(name="  Nguyen An  ", phone=" 0912345678 ")

    assert payload.name == "Nguyen An"
    assert payload.phone == "0912345678"
    assert payload.loyalty_points == 0


def test_customer_phone_rejects_invalid_characters() -> None:
    with pytest.raises(ValidationError):
        CustomerCreate(name="Nguyen An", phone="not-a-phone")


def test_customer_update_rejects_null_loyalty_points() -> None:
    with pytest.raises(ValidationError):
        CustomerUpdate(loyalty_points=None)
