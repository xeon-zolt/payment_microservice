from enum import Enum
from typing import Optional
from pydantic import BaseModel, condecimal


class CreatePaymentLinkIn(BaseModel):
    driver_id: Optional[int]
    amount: condecimal(ge=1.0, decimal_places=2)
    description: str
    customer_email: Optional[str]
    customer_phone: str
    customer_name: str
    source_id: str
    store_id: str

class NotifyMedium(str, Enum):
    sms = "sms"
    email = "email"

class ResendNotifyPaymentLinkIn(BaseModel):
    transaction_id: str
    medium: NotifyMedium

    class config:
        use_enum_values = True
        
class PaymentLinkStatus(str, Enum):
    created = "created"
    paid = "paid"
    cancelled = "cancelled"
    expired = "expired"
    failed = "failed"
