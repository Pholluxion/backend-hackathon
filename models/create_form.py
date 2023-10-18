from pydantic import BaseModel
from typing import List

class Field(BaseModel):
    campo: str
    type: str

class FormInput(BaseModel):
    token: str
    entidad_id: int
    campos: List[Field]

class FormOutput(BaseModel):
    message: str
