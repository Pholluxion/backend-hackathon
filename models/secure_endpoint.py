from pydantic import BaseModel

class TokenData(BaseModel):
    token: str
    other_data: str  # Puedes modificar esta línea con cualquier otro campo que necesites.
