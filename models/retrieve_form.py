from pydantic import BaseModel

# 1. Define el modelo para el request.
class FormRetrieveRequest(BaseModel):
    form_id: int
