from fastapi import Depends, HTTPException, Request
from auth.db_queries import get_email_from_token

async def get_current_user(request: Request):
    data = await request.json()  # Extraemos el token del cuerpo JSON del request.
    token = data["token"]
    email = get_email_from_token(token)

    if not email:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
    return {"email": email}
