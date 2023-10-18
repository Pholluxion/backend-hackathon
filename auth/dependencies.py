from fastapi import Depends, HTTPException, Request
from auth.db_queries import get_email_from_token

def get_current_user(request: Request):
    token = request.json()["token"]  # Extraemos el token del cuerpo JSON del request.
    email = get_email_from_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
    return {"email": email}
