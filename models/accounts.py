# models/accounts.py

from typing import Optional
from pydantic import BaseModel

from pydantic import BaseModel

class AccountCreate(BaseModel):
    nombre_completo: str
    documento_identidad: str
    correo_electronico: str
    numero_contacto: str
    password: str
    qr_permitido: bool
    saldo_total: float

class AccountResponse(BaseModel):
    usuario_id: int
    entidad_id: int
    nombre_completo: str
    documento_identidad: str
    correo_electronico: str
    numero_contacto: str
    qr_permitido: bool
    saldo_total: float

 