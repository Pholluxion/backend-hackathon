from pydantic import BaseModel
from typing import List

class AccountResponse(BaseModel):
    token: str
    numero_cuenta: str
    pin: str
    saldo: float
    tipo: str
    proposito: str

class AccountListResponse(BaseModel):
    accounts: List[AccountResponse]

