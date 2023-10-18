from pydantic import BaseModel

class FormsRequest(BaseModel):
    entidad_id: int