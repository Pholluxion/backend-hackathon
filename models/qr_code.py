# models/qr_code.py

from typing import Optional
from pydantic import BaseModel

class QrCodeData(BaseModel):
    token: str
    account_id: int
    description: Optional[str] = None
    form_id: Optional[int] = None
    image: Optional[str] = None
 