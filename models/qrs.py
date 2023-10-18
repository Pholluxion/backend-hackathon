from pydantic import BaseModel

class Qrs(BaseModel):
    user_id: int
    account_id: int
