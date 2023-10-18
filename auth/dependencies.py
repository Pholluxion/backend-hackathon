from fastapi import Depends, HTTPException, Request
from auth.db_queries import get_email_from_token, get_codedata_from_token, get_id_from_token

async def get_current_user(request: Request):
    data = await request.json()  # Extraemos el token del cuerpo JSON del request.
    token = data["token"]

    email = get_email_from_token(token)
    qr_generados, max_code = get_codedata_from_token(token)
    id = get_id_from_token(token)

    if max_code is None:
        max_code = 99999999

    if not email:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
    return {"email": email, "max_code": max_code, 'qr_generados': qr_generados, 'usuario_id': id}
