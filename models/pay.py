from pydantic import BaseModel

class PayRequest(BaseModel):
    token: str
    cuenta_id: int
    monto: float
    ip: str
