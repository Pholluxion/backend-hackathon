from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from database import get_connection, release_connection, get_mongo, get_cursor
from auth.db_queries import save_token_to_mongo
from auth.jwt_utils import create_access_token, decode_access_token
from auth.password_utils import verify_password, get_password_hash
from auth.dependencies import get_current_user
from typing import Union
from fastapi import FastAPI, Request
from pydantic import BaseModel

#import models
from models.qr_code import QrCodeData
from models.scanqr import QRScanInput, QRScanOutput
from models.create_form import FormInput, FormOutput
from models.accounts import AccountResponse
from models.retrieve_form import FormRetrieveRequest
from models.forms import FormsRequest
from models.send_form import FormData
from models.qrs import Qrs
from models.users import UserRequest
from models.token_pay import TokenPayRequest
from models.pay import PayRequest
from models.token import LoginData
from models.history import HistoryRequest
from models.set_max_codes import MaxCodeRequest

from datetime import datetime

import json
from typing import List

app = FastAPI()
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    return {"greeting": "Hello, World!", "message": "Welcome to FastAPI!"}


@app.post("/token")
async def login(data: LoginData, cursor=Depends(get_cursor), mongo_db=Depends(get_mongo)):
    # Verificar que el usuario exista en PostgreSQL
    # Por simplicidad, supongamos que tienes una tabla "users" con los campos "email" y "hashed_password"

    email = data.email
    password = data.password

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



@app.post("/generateqr")
async def generate_qr_code(data: QrCodeData, cursor=Depends(get_cursor), current_user: dict = Depends(get_current_user)):

    # Verificar disponibilidad para generar más QRs
    max_code = current_user["max_code"]

    generated_qrs = current_user["qr_generados"]

    if generated_qrs >= max_code:
        return {"error": "Limit reached! You cannot generate more QRs."}

    account_id = data.account_id
    description = data.description
    form_id = data.form_id
    image = data.image
    monto = data.monto
    documento = data.documento
    # Obtener la fecha actual
    current_date = datetime.now()

    # Insertar en la base de datos PostgreSQL
    cursor.execute(
        "INSERT INTO codigo_pago(codigo_id, fecha_generacion, descripcion_prellenado, formulario_id, imagen_logo, cuenta_id, monto_prellenado, documento_prellenado) VALUES (generar_codigo_aleatorio(%s), %s, %s, %s, %s, %s, %s, %s) RETURNING codigo_id",
        (5, current_date, description, form_id, image, account_id, monto, documento)
    )

    codigo_id_inserted = cursor.fetchone()[0]

        # Incrementar el contador de QRs generados
    cursor.execute(
        "UPDATE usuario SET qr_generados = qr_generados + 1 WHERE usuario_id = %s", 
        (current_user["usuario_id"],)
    )

    cursor.connection.commit()  # No olvides hacer commit si estás haciendo cambios en la base de datos
    
    return {"message": "QR Code data saved successfully!", "codigo_id": codigo_id_inserted}



@app.post("/scanqr", response_model=QRScanOutput)
async def scan_qr_code(data: QRScanInput, cursor=Depends(get_cursor)):
    # Extraemos el ID del código QR
    qr_code_id = data.qr_code_id
    
    # Buscamos en la base de datos PostgreSQL
    cursor.execute(
        "SELECT formulario_id, cuenta_id,monto_prellenado,descripcion_prellenado,documento_prellenado FROM codigo_pago WHERE codigo_id = %s",
        (qr_code_id,)
    )

    result = cursor.fetchone()
    if not result:
        raise HTTPException(status_code=404, detail="QR Code not found")

    form_id, account_id, monto, desc, doc = result

    return {"form_id": form_id, "account_id": account_id, "monto": monto, "description": desc, "documento": doc}

    

@app.post("/create-form", response_model=FormOutput)
async def create_form(data: FormInput, cursor=Depends(get_cursor), current_user: dict = Depends(get_current_user)):
    # Extraer información del modelo
    entidad_id = data.entidad_id
    campos = json.dumps([field.model_dump() for field in data.campos])
    
    # Insertar en la base de datos PostgreSQL
    cursor.execute(
        "INSERT INTO formulario(entidad_id, datos_json) VALUES (%s, %s)",
        (entidad_id, campos)
    )

    cursor.connection.commit()  # No olvides hacer commit para guardar los cambios en la base de datos
    
    return {"message": "Form created successfully!"}


@app.post("/retrieve-form")
async def retrieve_form(data: FormRetrieveRequest, cursor=Depends(get_cursor)):
    # 3. Ejecuta una consulta para obtener datos_json.
    cursor.execute("SELECT datos_json FROM formulario WHERE formulario_id = %s", (data.form_id,))
    result = cursor.fetchone()

    # Verificar si el formulario existe.
    if not result:
        raise HTTPException(status_code=404, detail="Form not found")

    # 4. Retorna el campo datos_json.
    return {"datos_json": result[0]}


@app.post("/forms")
async def get_forms(data: FormsRequest, cursor=Depends(get_cursor)):
    # 3. Ejecuta una consulta para obtener los IDs.
    cursor.execute("SELECT formulario_id,datos_json,nombre FROM formulario WHERE entidad_id = %s", (data.entidad_id,))
    results = cursor.fetchall()

    # Verificar si hay formularios para esa entidad.
    if not results:
        raise HTTPException(status_code=404, detail="No forms found for the given entity")

    data = []
    for result in results:
        data.append({"form_id": result[0], "num_campos": len(result[1]) , "nombre":  str(result[2])})

    # 4. Retorna la lista de IDs.
    return {"forms": data}


@app.post("/send-form")
async def send_form(data: FormData, mongo_db=Depends(get_mongo), current_user: dict = Depends(get_current_user)):
    collection = mongo_db.form_submissions
    submission = data.dict()
    submission["user_email"] = current_user["email"]
    collection.insert_one(submission)
    
    return {"message": "Form data saved successfully!"}


@app.post("/qrs")
async def retrieve_qrs(qr_request: Qrs, cursor=Depends(get_cursor), current_user: dict = Depends(get_current_user)):
    # Si necesitas validar el user_id con el token, puedes hacerlo aquí usando current_user

    # Consulta a la base de datos para recuperar los QRs asociados con el account_id
    cursor.execute("SELECT * FROM codigo_pago WHERE cuenta_id = %s", (qr_request.account_id,))
    
    # Obtén los nombres de las columnas
    column_names = [desc[0] for desc in cursor.description]

    # Transforma los resultados a una lista de diccionarios
    qrs = [dict(zip(column_names, row)) for row in cursor.fetchall()]

    # Convierte los resultados a una lista de diccionarios u otra estructura según prefieras
    # Por ahora, simplemente retornaremos los resultados brutos.
    return {"qrs": qrs}


@app.post("/users")
async def retrieve_users(user_request: UserRequest, cursor=Depends(get_cursor), current_user: dict = Depends(get_current_user)):
    # Si necesitas validar el user_id con el token, puedes hacerlo aquí usando current_user

    # Consulta a la base de datos para recuperar los usuarios asociados con el entidad_id
    cursor.execute(
        "SELECT usuario_id, nombre_completo, qr_permitido, max_code, qr_generados documento_identidad FROM usuario WHERE entidad_id = %s",
        (user_request.entidad_id,)
    )

    # Obtén los nombres de las columnas
    column_names = [desc[0] for desc in cursor.description]

    # Transforma los resultados a una lista de diccionarios
    users = [dict(zip(column_names, row)) for row in cursor.fetchall()]

    return {"users": users}


@app.post("/accounts")
async def list_accounts(cursor=Depends(get_cursor), current_user: str = Depends(get_current_user)):
    # Buscar cuentas asociadas al user_id en la base de datos
    cursor.execute(
        "SELECT numero_cuenta, saldo, tipo, cuenta_id FROM cuenta_ahorro WHERE usuario_id = %s",
        (current_user['usuario_id'],)
    )

    # Construir la respuesta
    accounts = [
        { "account_id": row[3], "numero_cuenta": row[0], "saldo": row[1], "tipo": row[2]}
        for row in cursor.fetchall()
    ]

    return {"accounts": accounts}




@app.post("/token-pay")
async def create_payment_token(token_request: TokenPayRequest, mongo_db=Depends(get_mongo)):
    # Verificar si el confirm es True
    if not token_request.confirm:
        return {"message": "Token creation denied"}

    # Crear un token
    token_data = {"monto": token_request.monto}
    access_token = create_access_token(data=token_data)

    # Almacenar el token en MongoDB
    mongo_db.tokens_pay.insert_one({
        "token": access_token,
        "monto": token_request.monto
    })

    return {"token": access_token}



@app.post("/pay")
async def process_payment(pay_request: PayRequest, mongo_db=Depends(get_mongo), cursor=Depends(get_cursor)):
    
    # Decodificar el token y obtener el monto
    token_data = decode_access_token(pay_request.token)

    try:
        stored_monto = mongo_db.tokens_pay.find_one({"token": pay_request.token})["monto"]
    except TypeError:  # Si find_one devuelve None, se lanza un TypeError al intentar acceder al campo "monto"
        raise HTTPException(status_code=400, detail="Token not found or expired")


    # Verificar si el monto del token coincide con el monto enviado
    if token_data["monto"] != stored_monto or stored_monto != pay_request.monto:
        raise HTTPException(status_code=400, detail="Invalid monto or token")

    
    # Inserta la transacción en MongoDB
    transaction = {
        "cuenta_id": pay_request.cuenta_id,
        "monto": pay_request.monto,
        "ip": pay_request.ip,
        "fecha": datetime.now()
    }
    mongo_db.transacciones.insert_one(transaction)

    # Actualiza el saldo de la cuenta en PostgreSQL
    cursor.execute(
        "UPDATE cuenta_ahorro SET saldo = saldo + %s WHERE cuenta_id = %s",
        (pay_request.monto, pay_request.cuenta_id)
    )
    cursor.connection.commit()

    mongo_db.tokens_pay.delete_one({"token": pay_request.token})

    return {"message": "Payment processed successfully"}


@app.post("/history")
async def transaction_history(data: HistoryRequest, cursor=Depends(get_cursor), mongo_db=Depends(get_mongo), current_user: dict = Depends(get_current_user)):
    # Comprobación de seguridad: Asegurarse de que la cuenta pertenece al usuario actual.
    # Esto es opcional pero es una buena práctica para asegurarse de que un usuario no pueda ver las transacciones de otro.

    cursor.execute(
        "SELECT 1 FROM cuenta_ahorro WHERE usuario_id = %s AND cuenta_id = %s",
        (current_user['usuario_id'], data.cuenta_id)
    )
    if not cursor.fetchone():
        raise HTTPException(status_code=403, message="Not authorized to view this account's history.")
    
    # Buscar transacciones asociadas al cuenta_id en la base de datos
    # Asumiendo que tienes una tabla "transacciones" con los campos que quieras mostrar
    result = mongo_db.transacciones.find({"cuenta_id": data.cuenta_id})

    # Convertir el cursor en una lista y luego en una lista de diccionarios para la respuesta
    transactions = [{"fecha": txn["fecha"], "monto": txn["monto"], "ip": txn["ip"]} for txn in result]

    return {"transactions": transactions}



@app.post("/set-max-codes")
async def set_max_codes(data: MaxCodeRequest, cursor=Depends(get_cursor), current_user: dict = Depends(get_current_user)):
    # Actualizar el campo max_code en la base de datos para el usuario
    cursor.execute(
        "UPDATE usuario SET max_code = %s WHERE usuario_id = %s",
        (data.max_code, current_user['usuario_id'])
    )

    cursor.connection.commit()  # No olvides hacer commit si estás haciendo cambios en la base de datos

    return {"message": "Max codes updated successfully!"}
