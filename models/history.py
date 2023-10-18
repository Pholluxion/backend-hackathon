from pydantic import BaseModel

class HistoryRequest(BaseModel):
    cuenta_id: int
