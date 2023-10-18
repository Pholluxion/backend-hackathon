from pydantic import BaseModel

class TokenPayRequest(BaseModel):
    confirm: bool
    monto: float
