from pydantic import BaseModel
from typing import List

class Field(BaseModel):
    campo: str
    type: str

class FormInput(BaseModel):
    entidad_id: int
    campos: List[Field]
    nombre: str

class FormOutput(BaseModel):
    message: str
