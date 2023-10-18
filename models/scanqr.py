from pydantic import BaseModel
from typing import Optional

class QRScanInput(BaseModel):
    qr_code_id: str

class QRScanOutput(BaseModel):
    form_id: int
    account_id: int
    monto: Optional[int] = None
    description: Optional[str] = None
    documento: Optional[int] = None
