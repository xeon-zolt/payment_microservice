from pydantic import BaseModel, condecimal


class MakePaymentOut(BaseModel):
    total_amount: condecimal(ge=1.0, decimal_places=2)
    amount: condecimal(ge=1.0, decimal_places=2)
    source_id: str
    payment_type: str
    status: str
    response: dict
    store_id: str
    additional_info: dict | None = None
    client_version: str
