from pydantic import BaseModel

class UserRequest(BaseModel):
    entidad_id: int
