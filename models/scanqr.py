from pydantic import BaseModel

class QRScanInput(BaseModel):
    token: str
    qr_code_id: str

class QRScanOutput(BaseModel):
    form_id: int
    account_id: int
