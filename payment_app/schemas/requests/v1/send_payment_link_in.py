from typing import Optional
from pydantic import BaseModel, condecimal


class SendPaymentLinkIn(BaseModel):
    driver_id: Optional[int]
    amount: condecimal(ge=1.0, decimal_places=2)
    description: str
    customer_email: str
    customer_phone: str
    customer_name: str
    source_id: str
