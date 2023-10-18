from fastapi import FastAPI, Depends, HTTPException
from database import get_connection, release_connection, get_mongo, get_cursor

from auth.db_queries import save_token_to_mongo
from auth.jwt_utils import create_access_token
from auth.password_utils import verify_password, get_password_hash
from auth.dependencies import get_current_user
from models.secure_endpoint import TokenData

from typing import Union

from fastapi import FastAPI, Request
from pydantic import BaseModel

app = FastAPI()

def get_db():
    db = None
    try:
        cursor = get_cursor()
        yield cursor
    finally:
        if db:
            release_connection(db)

@app.get("/")
async def read_root(db=Depends(get_db)):
    # Tu código que usa la conexión a la base de datos
    #db.execute("SELECT ...")  # Ejemplo
    return {"greeting": "Hello, World!", "message": "Welcome to FastAPI!"}


@app.post("/token")
async def login(request: Request, cursor=Depends(get_cursor), mongo_db=Depends(get_mongo)):
    # Verificar que el usuario exista en PostgreSQL
    # Por simplicidad, supongamos que tienes una tabla "users" con los campos "email" y "hashed_password"
    data = await request.json()

    email = data['email']
    password = data['password']

    cursor.execute("SELECT correo_electronico, password_hash FROM usuario WHERE correo_electronico = %s", (email,))
    user = cursor.fetchone()

    
    if not verify_password(password, user[1]):
        raise HTTPException(
            status_code=400,
            detail="Incorrect email or password"
        )

    # Generar el token
    access_token = create_access_token(data={"sub": user[0]})
    
    # Guardar el token en MongoDB
    save_token_to_mongo(user[0], access_token, mongo_db)

    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/secure-endpoint")
async def secure_endpoint(request: Request, current_user: dict = Depends(get_current_user)):
    # Si llegamos aquí, significa que el token es válido.
    # `current_user` contendrá la información del usuario extraída del token.
    email = current_user["email"]

    return {"message": f"Usuario autenticado: {email}"}





