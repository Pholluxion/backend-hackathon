from fastapi import FastAPI, Depends, HTTPException
from database import get_connection, release_connection

app = FastAPI()

def get_db():
    db = None
    try:
        cursor = get_connection()
        yield cursor
    finally:
        if db:
            release_connection(db)

@app.get("/")
async def read_root(db=Depends(get_db)):
    # Tu código que usa la conexión a la base de datos
    db.execute("SELECT ...")  # Ejemplo
    return {"greeting": "Hello, World!", "message": "Welcome to FastAPI!"}
