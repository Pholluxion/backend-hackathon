from pydantic import BaseModel

class MaxCodeRequest(BaseModel):
    max_code: int
