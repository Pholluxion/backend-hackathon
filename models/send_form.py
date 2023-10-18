from pydantic import BaseModel


# Define el modelo para el request.
class FormData(BaseModel):
    pse: bool
    data: dict  # Este campo recibirá cualquier objeto JSON.