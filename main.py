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
from models.qr_code import QrCodeData
from models.scanqr import QRScanInput, QRScanOutput
from models.create_form import FormInput, FormOutput
from models.accounts import AccountCreate, AccountResponse

from datetime import datetime

import json

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


@app.post("/generateqr")
async def generate_qr_code(data: QrCodeData, cursor=Depends(get_cursor), current_user: dict = Depends(get_current_user)):
    # Extraer la información del modelo
    account_id = data.account_id
    description = data.description
    form_id = data.form_id
    image = data.image

    # Obtener la fecha actual
    current_date = datetime.now()

    # Insertar en la base de datos PostgreSQL
    cursor.execute(
        "INSERT INTO codigo_pago(codigo_id, fecha_generacion, descripcion_prellenado, formulario_id, imagen_logo, cuenta_id) VALUES (generar_codigo_aleatorio(%s), %s, %s, %s, %s, %s)",
        (5,current_date, description, form_id, image, account_id)
    )

    cursor.connection.commit()  # No olvides hacer commit si estás haciendo cambios en la base de datos
    
    return {"message": "QR Code data saved successfully!"}


@app.post("/scanqr", response_model=QRScanOutput)
async def scan_qr_code(data: QRScanInput, cursor=Depends(get_cursor), current_user: dict = Depends(get_current_user)):
    # Extraemos el ID del código QR
    qr_code_id = data.qr_code_id
    
    # Buscamos en la base de datos PostgreSQL
    cursor.execute(
        "SELECT formulario_id, cuenta_id FROM codigo_pago WHERE codigo_id = %s",
        (qr_code_id,)
    )

    result = cursor.fetchone()
    if not result:
        raise HTTPException(status_code=404, detail="QR Code not found")

    form_id, account_id = result
    return {"form_id": form_id, "account_id": account_id}

    

@app.post("/create-form", response_model=FormOutput)
async def create_form(data: FormInput, cursor=Depends(get_cursor), current_user: dict = Depends(get_current_user)):
    # Extraer información del modelo
    entidad_id = data.entidad_id
    campos_json = json.dumps([field.model_dump() for field in data.campos])
    
    # Insertar en la base de datos PostgreSQL
    cursor.execute(
        "INSERT INTO formulario(entidad_id, json_campos) VALUES (%s, %s)",
        (entidad_id, campos_json)
    )

    cursor.connection.commit()  # No olvides hacer commit para guardar los cambios en la base de datos
    
    return {"message": "Form created successfully!"}



@app.post("/accounts", response_model=AccountResponse)
async def create_account(account_data: AccountCreate, cursor=Depends(get_cursor), current_user: dict = Depends(get_current_user)):
    hashed_password = get_password_hash(account_data.password)

    cursor.execute(
        "INSERT INTO usuario (entidad_id, nombre_completo, documento_identidad, correo_electronico, numero_contacto, password_hash, qr_permitido, saldo_total) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING usuario_id",
        (current_user["entidad_id"], account_data.nombre_completo, account_data.documento_identidad, account_data.correo_electronico, account_data.numero_contacto, hashed_password, account_data.qr_permitido, account_data.saldo_total)
    )

    usuario_id = cursor.fetchone()[0]
    cursor.connection.commit()

    return {
        "usuario_id": usuario_id,
        "entidad_id": current_user["entidad_id"],
        "nombre_completo": account_data.nombre_completo,
        "documento_identidad": account_data.documento_identidad,
        "correo_electronico": account_data.correo_electronico,
        "numero_contacto": account_data.numero_contacto,
        "qr_permitido": account_data.qr_permitido,
        "saldo_total": account_data.saldo_total
    }