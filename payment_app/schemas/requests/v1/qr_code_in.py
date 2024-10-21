from enum import Enum
from typing import Optional, Literal
from decimal import Decimal

from pydantic import BaseModel, condecimal, validator, root_validator

from payment_app.schemas.requests.v1.make_payment_in import StoreType

class QRUsage(str, Enum):
    single_use = "single_use"
    multiple_use = "multiple_use"
    
class QRType(str, Enum):
    upi_qr = "upi_qr"
    bharat_qr = "bharat_qr"
    
class QRCodeIn(BaseModel):
    driver: Literal[1, 2, '1', '2']
    usage: QRUsage
    type: QRType
    is_fixed_amount: bool
    payment_amount: condecimal(decimal_places=2)
    store_id: str
    source_id: str
    store_type: Optional[StoreType]
    additional_info: Optional[dict]
    
    @root_validator(skip_on_failure=True)
    @classmethod  # Optional, but your linter may like it.
    def check_payment_amount(cls, values):
        if values["is_fixed_amount"] == False and values["payment_amount"] > 0:
            raise ValueError("Payment amount should be 0")
        elif values["is_fixed_amount"] == True and values["payment_amount"] <= 0:
            raise ValueError("Payment amount should greater then 0")
        return values
    class config:
        use_enum_values = True
