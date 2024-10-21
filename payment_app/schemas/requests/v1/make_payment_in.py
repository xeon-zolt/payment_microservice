from decimal import Decimal
from typing import Optional, Literal
from enum import Enum

from pydantic import BaseModel, condecimal

class StoreType(str, Enum):
    NT_STORE_ID = "nt_store_id"
    POS_STORE_ID = "pos_store_id"
    BD_STORE_ID = "bd_store_id"


class MakePaymentInRazorpay(BaseModel):
    driver_id: Literal[1,2,'1','2']
    total_amount: condecimal(ge=Decimal(1.0), decimal_places=2)
    amount_to_pay: condecimal(ge=Decimal(1.0), decimal_places=2)
    payment_type: str
    source_id: str
    store_id: str
    additional_info: Optional[dict]

class MakePaymentInPaytm(BaseModel):
    driver_id: Literal['3',3]
    total_amount: condecimal(ge=Decimal(1.0), decimal_places=2)
    amount_to_pay: condecimal(ge=Decimal(1.0), decimal_places=2)
    payment_type: str
    source_id: str
    customer_id: str
    store_id: str
    additional_info: Optional[dict]
