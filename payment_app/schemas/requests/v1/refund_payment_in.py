from typing import Optional
from pydantic import BaseModel, condecimal


class RefundPaymentIn(BaseModel):
    amount_to_refund: Optional[condecimal(ge=1.0, decimal_places=2)] = None
    payment_transaction_id: str
    notes: Optional[dict]
    receipt: Optional[str]
